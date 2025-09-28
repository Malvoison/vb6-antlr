# VB6 Parser-to-JSON Converter

A parser-driven toolchain for transforming legacy Visual Basic 6 source files (`.bas`, `.cls`, `.frm`) into structured JSON suitable for modernization workflows, static analysis, and visualization.

## Project Highlights
- Leverages the official VB6 grammar from ANTLR to maximize syntax coverage.
- Emits deterministic, schema-driven JSON that preserves module metadata, declarations, UI layout, and diagnostics.
- Provides both a CLI and library API for batch processing and integration with downstream tooling.

## Repository Layout
- `design/high-level-design.md` — architecture, component boundaries, and roadmap.
- `design/tool-configuration.md` — environment setup, tooling, and open decisions.
- `grammars/` (planned) — VB6 lexer/parser grammar sources.
- `src/` (planned) — core Python package, IR builders, serializers.
- `tests/` (planned) — unit and integration test suites.

## Getting Started

### 1. Clone & prerequisites
```bash
git clone https://github.com/<your-org>/vb6-antlr.git
cd vb6-antlr
```
Ensure the following are installed (see `design/tool-configuration.md` for full guidance):
- Python 3.10+ (3.11 recommended)
- Java 11+ (OpenJDK)
- Git, Make, build-essential (Ubuntu) or equivalents
- `pipx` for managing Poetry and pre-commit

### 2. Install Poetry & bootstrap the project
```bash
pipx install poetry
pipx install pre-commit
poetry init --name vb6-antlr --description "VB6 parser to JSON converter" \
  --license MIT --python '^3.11' --dependency antlr4-python3-runtime \
  --dev-dependency pytest --no-interaction
poetry install
poetry run pre-commit install
```
If you prefer the interactive wizard, run `poetry init` without flags. Export `requirements.txt` for non-Poetry users via `poetry export -f requirements.txt --output requirements.txt`.

If `poetry install` complains about `No file/folder found for package vb6-antlr`, adjust the package mapping and create the source root:
```bash
sed -i 's/packages = \[{ include = "vb6-antlr"/packages = [{ include = "vb6_antlr"/' pyproject.toml || true
mkdir -p src/vb6_antlr
touch src/vb6_antlr/__init__.py
```
Ensure `[tool.poetry] packages` points to `vb6_antlr` (underscore) from `src/` before rerunning `poetry install`.

### 3. Fetch ANTLR tooling
```bash
mkdir -p tools/antlr
curl -L -o tools/antlr/antlr-4.13.1-complete.jar \
  https://www.antlr.org/download/antlr-4.13.1-complete.jar
```
Add the helper aliases (append to `.bashrc`/`.zshrc`):
```bash
export ANTLR4_JAR=$PWD/tools/antlr/antlr-4.13.1-complete.jar
alias antlr4='java -Xmx2G -jar "$ANTLR4_JAR"'
alias grun='java org.antlr.v4.gui.TestRig'
```

### 4. Generate the parser (after grammar sync)
```bash
antlr4 -Dlanguage=Python3 -o src/vb6_grammar \
  grammars/VB6.g4 grammars/VB6Lexer.g4
```
Capture these steps in a Makefile target (`make generate`) to streamline regeneration.

## Development Workflow
1. Implement parser walkers and IR builders under `src/`.
2. Add tests to `tests/` and run them with `poetry run pytest` or `make test` once scripted.
3. Use `pre-commit` to keep formatting and linting consistent.
4. Document architectural updates in the `design/` directory.

## Roadmap Snapshot
Refer to `design/high-level-design.md` for the full roadmap. Near-term focus:
- Scaffold ANTLR grammar integration and parser pipeline.
- Stand up the intermediate representation (IR) layer with targeted unit tests.
- Deliver the JSON serializer and schema documentation.

## Contributing
- Create feature branches off `main` and open pull requests with clear descriptions.
- Ensure `poetry run pytest` and formatting checks pass before requesting reviews.
- Keep documentation updated alongside code changes.

## License
Project license will be finalized during initialization (currently set to MIT in the `poetry init` template). Update the `LICENSE` file as needed.

