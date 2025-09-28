"""Builders that translate ANTLR parse trees into JSON-ready IR structures."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from antlr4 import ParseTreeWalker, ParserRuleContext

from ..config import DEFAULT_SCHEMA_VERSION
from ..diagnostics import Diagnostic
from ..parser import ParserOutput
from vb6_grammar.grammars.VisualBasic6Parser import VisualBasic6Parser
from vb6_grammar.grammars.VisualBasic6ParserListener import (
    VisualBasic6ParserListener,
)


@dataclass(slots=True)
class IRModule:
    """Intermediary representation for a parsed VB6 module."""

    source_path: Path
    body: dict[str, Any] = field(default_factory=dict)
    diagnostics: list[Diagnostic] = field(default_factory=list)


class ModuleCollector(VisualBasic6ParserListener):
    """Listener that projects parse tree nodes into structured module data."""

    def __init__(self, source_path: Path) -> None:
        self.source_path = source_path
        self.module_name: str | None = None
        self.module_version: str | None = None
        self.header_kind: str | None = None
        self.attributes: list[dict[str, Any]] = []
        self.options: list[dict[str, Any]] = []
        self.members: list[dict[str, Any]] = []
        self.is_private_module: bool = False
        self._option_seen: set[tuple[str, Any]] = set()

    # --- Module level -----------------------------------------------------

    def exitModuleHeader(self, ctx: VisualBasic6Parser.ModuleHeaderContext) -> None:
        if ctx.doubleLiteral():
            self.module_version = ctx.doubleLiteral().getText()
        if ctx.CLASS():
            self.header_kind = "class"

    def exitAttributeStmt(self, ctx: VisualBasic6Parser.AttributeStmtContext) -> None:
        name = ctx.implicitCallStmt_InStmt().getText()
        values = [
            self._normalize_literal(literal.getText()) for literal in ctx.literal()
        ]
        record = {
            "name": name,
            "values": values,
            "location": self._location(ctx),
            "raw": ctx.getText(),
        }
        self.attributes.append(record)
        if name.lower() == "vb_name" and values:
            # First VB_Name literal defines the module's logical name.
            self.module_name = str(values[0])

    def exitOptionBaseStmt(self, ctx: VisualBasic6Parser.OptionBaseStmtContext) -> None:
        value = (
            self._normalize_literal(ctx.integerLiteral().getText())
            if ctx.integerLiteral()
            else None
        )
        self._add_option("base", value, ctx)

    def exitOptionCompareStmt(
        self, ctx: VisualBasic6Parser.OptionCompareStmtContext
    ) -> None:
        mode = "binary" if ctx.BINARY() else "text"
        self._add_option("compare", mode, ctx)

    def exitOptionExplicitStmt(
        self, ctx: VisualBasic6Parser.OptionExplicitStmtContext
    ) -> None:
        self._add_option("explicit", True, ctx)

    def exitOptionPrivateModuleStmt(
        self, ctx: VisualBasic6Parser.OptionPrivateModuleStmtContext
    ) -> None:
        self.is_private_module = True
        self._add_option("privateModule", True, ctx)

    # --- Routine declarations ---------------------------------------------

    def exitSubStmt(self, ctx: VisualBasic6Parser.SubStmtContext) -> None:
        self.members.append(self._build_routine(ctx, kind="sub"))

    def exitFunctionStmt(self, ctx: VisualBasic6Parser.FunctionStmtContext) -> None:
        member = self._build_routine(ctx, kind="function")
        member["returnType"] = self._normalize_type_clause(ctx.asTypeClause())
        self.members.append(member)

    def exitPropertyGetStmt(
        self, ctx: VisualBasic6Parser.PropertyGetStmtContext
    ) -> None:
        member = self._build_routine(ctx, kind="propertyGet")
        member["returnType"] = self._normalize_type_clause(ctx.asTypeClause())
        self.members.append(member)

    def exitPropertyLetStmt(
        self, ctx: VisualBasic6Parser.PropertyLetStmtContext
    ) -> None:
        self.members.append(self._build_routine(ctx, kind="propertyLet"))

    def exitPropertySetStmt(
        self, ctx: VisualBasic6Parser.PropertySetStmtContext
    ) -> None:
        self.members.append(self._build_routine(ctx, kind="propertySet"))

    # --- Helpers ----------------------------------------------------------

    def _add_option(
        self,
        option_type: str,
        value: Any,
        ctx: VisualBasic6Parser.ModuleOptionContext,
    ) -> None:
        key = (option_type, self._hashable(value))
        if key in self._option_seen:
            return
        record: dict[str, Any] = {"type": option_type, "location": self._location(ctx)}
        if value is not None:
            record["value"] = value
        self.options.append(record)
        self._option_seen.add(key)

    def _build_routine(self, ctx: ParserRuleContext, *, kind: str) -> dict[str, Any]:
        name = (
            ctx.ambiguousIdentifier().getText()
            if hasattr(ctx, "ambiguousIdentifier") and ctx.ambiguousIdentifier()
            else None
        )
        visibility = self._normalize_visibility(
            ctx.visibility().getText()
            if hasattr(ctx, "visibility") and ctx.visibility()
            else None
        )
        modifiers: list[str] = []
        if hasattr(ctx, "STATIC") and ctx.STATIC():
            modifiers.append("Static")
        parameters = (
            self._collect_parameters(ctx.argList())
            if hasattr(ctx, "argList") and ctx.argList()
            else []
        )
        member = {
            "kind": kind,
            "name": name,
            "visibility": visibility,
            "modifiers": modifiers,
            "parameters": parameters,
            "startLine": ctx.start.line if getattr(ctx, "start", None) else None,
            "endLine": ctx.stop.line if getattr(ctx, "stop", None) else None,
        }
        return member

    def _collect_parameters(
        self, arg_list: VisualBasic6Parser.ArgListContext
    ) -> list[dict[str, Any]]:
        params: list[dict[str, Any]] = []
        for arg in arg_list.arg():
            name = (
                arg.ambiguousIdentifier().getText()
                if arg.ambiguousIdentifier()
                else None
            )
            modifiers: list[str] = []
            if arg.OPTIONAL():
                modifiers.append("Optional")
            if arg.PARAMARRAY():
                modifiers.append("ParamArray")
            if arg.BYVAL():
                modifiers.append("ByVal")
            if arg.BYREF():
                modifiers.append("ByRef")
            param: dict[str, Any] = {
                "name": name,
                "modifiers": modifiers,
                "type": self._normalize_type_clause(arg.asTypeClause()),
                "typeHint": arg.typeHint().getText() if arg.typeHint() else None,
                "defaultValue": None,
            }
            if arg.argDefaultValue():
                value_stmt = arg.argDefaultValue().valueStmt()
                if value_stmt:
                    param["defaultValue"] = self._normalize_literal(
                        value_stmt.getText()
                    )
            params.append(param)
        return params

    @staticmethod
    def _normalize_literal(text: str) -> Any:
        raw = text.strip()
        if not raw:
            return raw
        lowered = raw.lower()
        if lowered == "true":
            return True
        if lowered == "false":
            return False
        if (raw.startswith('"') and raw.endswith('"')) or (
            raw.startswith("'") and raw.endswith("'")
        ):
            inner = raw[1:-1].replace('""', '"').replace("''", "'")
            return inner
        try:
            if "#" in raw or raw.startswith("&"):
                raise ValueError
            return int(raw)
        except ValueError:
            try:
                return float(raw)
            except ValueError:
                return raw

    @staticmethod
    def _normalize_type_clause(
        clause: VisualBasic6Parser.AsTypeClauseContext | None,
    ) -> str | None:
        if not clause:
            return None
        text = clause.getText().strip()
        if text.lower().startswith("as"):
            text = text[2:].strip()
        return text or None

    @staticmethod
    def _normalize_visibility(value: str | None) -> str | None:
        if not value:
            return None
        return value.lower()

    @staticmethod
    def _location(ctx: ParserRuleContext) -> dict[str, int] | None:
        token = getattr(ctx, "start", None)
        if token is None:
            return None
        return {"line": token.line, "column": token.column}

    @staticmethod
    def _hashable(value: Any) -> Any:
        if isinstance(value, list):
            return tuple(ModuleCollector._hashable(v) for v in value)
        if isinstance(value, dict):
            return tuple(
                sorted((k, ModuleCollector._hashable(v)) for k, v in value.items())
            )
        return value


class IRBuilder:
    """Transforms raw parser output into the intermediate representation."""

    def build(self, output: ParserOutput) -> IRModule:
        """Translate a single parser output into an IR module."""

        body: dict[str, Any] = {"schemaVersion": DEFAULT_SCHEMA_VERSION}
        if output.parse_tree is None:
            module = {
                "name": output.source_path.stem,
                "kind": self._infer_module_kind(output.source_path, None, False),
                "attributes": [],
                "options": [],
                "members": [],
            }
            body["module"] = module
            return IRModule(
                source_path=output.source_path,
                body=body,
                diagnostics=output.diagnostics,
            )

        collector = ModuleCollector(output.source_path)
        walker = ParseTreeWalker()
        walker.walk(collector, output.parse_tree)

        module_kind = self._infer_module_kind(
            output.source_path, collector.header_kind, collector.is_private_module
        )
        module_name = collector.module_name or output.source_path.stem
        module_payload: dict[str, Any] = {
            "name": module_name,
            "kind": module_kind,
            "attributes": collector.attributes,
            "options": collector.options,
            "members": collector.members,
            "isPrivateModule": collector.is_private_module,
        }
        if collector.module_version is not None:
            module_payload["version"] = collector.module_version

        body["module"] = module_payload
        return IRModule(
            source_path=output.source_path, body=body, diagnostics=output.diagnostics
        )

    @staticmethod
    def _infer_module_kind(
        path: Path, header_kind: str | None, is_private: bool
    ) -> str:
        if header_kind:
            return header_kind
        suffix = path.suffix.lower()
        mapping = {
            ".bas": "standard",
            ".cls": "class",
            ".frm": "form",
            ".ctl": "control",
        }
        kind = mapping.get(suffix, "standard")
        if kind == "standard" and is_private:
            return "privateModule"
        return kind
