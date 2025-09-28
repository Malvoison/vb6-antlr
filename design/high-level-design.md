# VB6 Parser-to-JSON Converter High-Level Design

## 1. Project Overview
- Build a parser-driven converter that turns legacy Visual Basic 6 source artifacts (`.bas`, `.cls`, `.frm`) into structured JSON.
- Leverage the official VB6 grammar from the ANTLR grammars-v4 repository to guarantee syntactic fidelity.
- Produce JSON suitable for static analysis, modernization tooling, automated refactoring, and visualization workflows.

## 2. Goals and Non-Goals
### Goals
- Parse VB6 projects and standalone files with high grammar coverage.
- Emit lossless JSON describing the syntactic structure, metadata, and semantic hints (where inference is possible without execution).
- Provide a CLI and library API for batch conversions and downstream integrations.
- Ensure outputs are deterministic and stable across runs for the same inputs and configuration.

### Non-Goals
- Runtime execution, interpretation, or compilation of VB6 code.
- Automatic code refactoring or translation to other programming languages (beyond exposing JSON for external tools).
- Visual tooling or UI beyond command-line utilities.

## 3. Architectural Overview
```
+-----------------+     +---------------------+     +------------------+
| Input Collector  | --> | Parsing Pipeline    | --> | JSON Serializer  |
| (CLI/API)        |     | (ANTLR-based)       |     | + Output Manager |
+-----------------+     +---------------------+     +------------------+
         |                        |                           |
         v                        v                           v
  Config Loader            Intermediate AST           File system / stdout
         |                        |                           |
         +------------------> Diagnostics <-------------------+
```

## 4. Major Components
- **CLI Frontend**: Parses user arguments, resolves file lists, loads configuration, coordinates batch processing, and provides exit codes and summaries.
- **Core Parser Library**:
  - Bundles the VB6 ANTLR grammar and runtime.
  - Manages parse trees, error listeners, and incremental parsing options.
  - Provides adapters to feed source code from files, strings, or streams.
- **Intermediate Representation (IR) Builder**:
  - Walks ANTLR parse trees and constructs a normalized, language-agnostic IR capturing modules, members, statements, expressions, controls, attributes, and comments.
  - Preserves token positions, original text snippets, and lexical trivia where feasible.
- **Semantic Enrichment Layer**:
  - Applies lightweight static analysis (e.g., resolve module/member kinds, type hints from `As` clauses, control properties) to augment the IR.
  - Flags unsupported or ambiguous constructs for diagnostics.
- **JSON Serializer**:
  - Transforms the IR into stable JSON adhering to the project schema version.
  - Handles pretty-printing, streaming to files, or emitting to stdout.
- **Diagnostics & Logging**:
  - Collects syntax errors, warnings about unsupported features, and processing metrics.
  - Offers configurable verbosity and machine-readable logs when requested.
- **Configuration Manager**:
  - Reads CLI flags and optional project config file (e.g., `converter.config.json`).
  - Controls include output directory, schema version, file grouping, and feature toggles.
- **Plugin / Extension Hooks (Future)**:
  - Provide extension points for custom IR visitors or output transformers.

## 5. Data Flow
1. **Input Discovery**: Traverse provided paths, filter for `.bas`, `.cls`, `.frm`; optionally respect VB6 project files for module ordering.
2. **Preprocessing (Optional)**: Normalize line endings, handle encoding (default Windows-1252 fallback to UTF-8), and strip BOMs.
3. **Parsing**: Use ANTLR-generated lexer and parser with custom error listeners to produce parse trees per file.
4. **IR Construction**: Convert parse trees into IR nodes that capture structure plus metadata (identifiers, signatures, UI layouts, event bindings).
5. **Semantic Enrichment**: Annotate IR nodes with inferred types, control hierarchies, and cross-references where gathered without full type checking.
6. **JSON Serialization**: Serialize IR to JSON with schema version metadata, file-level and project-level outputs.
7. **Output Management**: Write per-file JSON outputs and, if configured, an aggregated project JSON manifest.
8. **Diagnostics Reporting**: Emit warnings/errors to stderr, log files, or JSON report.

## 6. JSON Schema Highlights
- **Document Envelope**: `{ "schemaVersion": "1.0.0", "source": { ... }, "body": { ... }, "diagnostics": [ ... ] }`.
- **Source Metadata**: File path, checksum, encoding, timestamps, module kind (standard, class, form).
- **Structural Elements**: Modules, declarations, procedures, controls, UI layout tree, event handlers, expressions.
- **Token Positioning**: Line/column spans and original text slices for reversible transformations.
- **Diagnostics Array**: Structured issues with severity, location, message, and optional remediation hints.

## 7. Configuration & Deployment
- Ship as a Python-based CLI (default) and reusable package; consider optional Node.js wrapper if integrating with JS tooling.
- Offer configuration via command-line flags, env vars, and optional project config file.
- Support dependency pinning for ANTLR runtime versions and grammar revisions.
- Provide containerized environment (Dockerfile) for reproducible execution and CI.

## 8. Error Handling & Diagnostics
- Gracefully continue processing after recoverable parse errors; include partial outputs with embedded diagnostics when allowed.
- Promote fatal errors (e.g., unreadable inputs, configuration conflicts) to non-zero exit codes.
- Logging levels: `quiet`, `normal`, `verbose`, `debug`.
- Optional machine-readable diagnostics output (`--diagnostics-json`).

## 9. Performance & Scalability
- Batch files and reuse parser instances to minimize grammar reload costs.
- Parallelize at file level using worker pools when CPU-bound and safe (watch thread-safety of ANTLR runtime in chosen language binding).
- Stream JSON outputs to avoid high memory usage for large projects.
- Cache derived IR or token streams for incremental runs.

## 10. Testing Strategy
- **Grammar Regression**: Unit tests with curated VB6 snippets covering language constructs and edge cases.
- **Golden Files**: Compare generated JSON against expected fixtures for representative modules and forms.
- **Round-Trip Validation**: Spot-check that JSON can be re-rendered into syntactically equivalent VB6 (manual verification or automated future work).
- **Performance Benchmarks**: Track parsing time and memory consumption on real-world projects.
- **Integration Tests**: CLI end-to-end runs using sample VB6 projects.

## 11. Extensibility Considerations
- Versioned JSON schema with compatibility policy and migration scripts.
- Plugin interface for custom visitors or serializers without forking core parser.
- Clear boundaries between parsing, IR, and serialization to swap implementations (e.g., alternative target formats).

## 12. Tooling & Dependencies
- **ANTLR 4 Tooling**: Grammar, code generation, and runtime library.
- **Language Runtime**: Prefer Python 3.10+ with `antlr4-python3-runtime`; evaluate Java-based driver if performance demands.
- **Packaging**: Use Poetry or setuptools for Python; publish to PyPI. Provide CLI entry point `vb6-antlr-converter`.
- **Dev Tooling**: Makefile or invoke-based tasks for generating parser, running tests, linting. Use pre-commit hooks for formatting (e.g., `black`, `isort`).

## 13. Security & Compliance
- Sandbox execution to avoid executing or loading arbitrary VB6 binaries.
- Validate file paths to mitigate directory traversal when running in service contexts.
- Respect licensing for grammars-v4 (BSD-style) and ensure attribution.
- Provide guidance for handling sensitive codebases (local-only processing, no telemetry by default).

## 14. Open Questions & Risks
- How to handle VB6 language features not covered by the official grammar (e.g., third-party controls, inline binary form data)?
- Do we need to support embedded resources (`.frx`) alongside `.frm` files?
- Level of semantic analysis: Should we infer runtime-specific constructs (e.g., DAO, ADO) or leave for downstream tools?
- Performance constraints for very large legacy codebases (10k+ modules) and strategies for incremental parsing.
- Use of schema evolution tooling to manage breaking changes in JSON output.

## 15. Roadmap Snapshot
1. Bootstrap repository with ANTLR grammar, generation scripts, and basic CLI scaffold.
2. Implement parsing pipeline with file discovery and parse tree generation.
3. Build IR layer with unit tests for key constructs.
4. Implement JSON serializer and schema documentation.
5. Add diagnostics, configuration management, and documentation.
6. Optimize performance, add parallel processing, and harden error handling.
7. Release beta with sample outputs and developer onboarding guide.

