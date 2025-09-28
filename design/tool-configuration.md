# Tooling & Environment Setup

This document captures the tooling and configuration steps required to bootstrap the VB6 parser-to-JSON converter project.

## 1. Core Prerequisites
- **Git**: Version control for source management.
- **Python 3.10+**: Primary implementation language (recommend 3.11 for long-term support).
- **Java 11+ (OpenJDK)**: Required to run the ANTLR grammar generator.
- **Make** (or `ninja` on Windows): Convenience for build/test orchestration.
- **C/C++ Build Tools**: Some Python dependencies may need native compilation (e.g., MSVC Build Tools on Windows, Xcode CLT on macOS, `build-essential` on Linux).
- **Ubuntu on WSL**: Follow the Ubuntu steps below; ensure the WSL distro is upgraded (`sudo apt update && sudo apt upgrade`) and avoid editing the repo via the Windows filesystem for best performance.

### Install examples
```bash
# Ubuntu / Debian
sudo apt update && sudo apt install -y git python3 python3-venv python3-pip openjdk-17-jdk make build-essential

# macOS with Homebrew
brew install git python@3.11 openjdk@17 make
sudo xcode-select --install  # ensures Command Line Tools are present

# Windows (PowerShell)
winget install --id Git.Git
winget install --id Python.Python.3.11
winget install --id EclipseAdoptium.Temurin.17.JDK
winget install --id GnuWin32.Make
winget install --id Microsoft.VisualStudio.2022.BuildTools
```

## 2. Python Toolchain
1. **Version management** (optional but recommended): install [`pyenv`](https://github.com/pyenv/pyenv) or use `asdf` to pin interpreter versions per project.
2. **Virtual environment**: create an isolated environment for dependencies.
3. **Dependency manager**: standardize on [`poetry`](https://python-poetry.org/) for reproducible builds and publishing; keep a `requirements.txt` export for consumers who cannot use Poetry.

```bash
# Install poetry via pipx (preferred)
pipx install poetry

# Create and activate the project environment
poetry env use 3.11
poetry install

# Alternatively with venv + pip
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip setuptools wheel
pip install -r requirements.txt
```

If `poetry install` reports that no `pyproject.toml` is present, initialize the project first:
```bash
poetry init --name vb6-antlr --description "VB6 parser to JSON converter" \
  --license MIT --python '^3.11' --dependency antlr4-python3-runtime \
  --dev-dependency pytest --no-interaction
# or run `poetry init` with the interactive prompts
```


After initialization, ensure the package mapping matches your source layout:
- Edit `pyproject.toml` so `[tool.poetry]` contains `packages = [{ include = "vb6_antlr", from = "src" }]` (use an underscore).
- Create the package directory and an `__init__.py` placeholder:
```bash
mkdir -p src/vb6_antlr
touch src/vb6_antlr/__init__.py
```
This prevents the "No file/folder found for package" error during `poetry install`.

**Testing & linting stack** (to be added to `pyproject.toml`/`requirements-dev.txt`): `pytest`, `coverage`, `black`, `isort`, `ruff`, `mypy`.

## 3. ANTLR Toolchain
1. Download ANTLR tool JAR and place it under `tools/antlr/antlr-4.13.1-complete.jar` (location can be adjusted via Makefile/task runner).
```bash
mkdir -p tools/antlr
curl -L -o tools/antlr/antlr-4.13.1-complete.jar \
  https://www.antlr.org/download/antlr-4.13.1-complete.jar
```
2. Add a convenience wrapper to your shell profile:
```bash
export ANTLR4_JAR=$PWD/tools/antlr/antlr-4.13.1-complete.jar
alias antlr4='java -Xmx2G -jar "$ANTLR4_JAR"'
alias grun='java org.antlr.v4.gui.TestRig'
```
3. Install the Python runtime once the project package is scaffolded:
```bash
poetry add antlr4-python3-runtime
# or
pip install antlr4-python3-runtime
```
4. Grammar generation (example target, to be scripted via Makefile):
```bash
antlr4 -Dlanguage=Python3 -o src/vb6_grammar \
  grammars/VB6.g4 grammars/VB6Lexer.g4
```

## 4. Build & Task Automation
- **Makefile**: capture commands for parser generation, formatting, linting, docs, and packaging:
  - `make setup` → install tooling and pre-commit hooks.
  - `make generate` → run ANTLR against the grammar files.
  - `make test` → execute `pytest` with coverage.
- Evaluate [`invoke`](https://www.pyinvoke.org/) or [`task`](https://taskfile.dev/) for cross-platform task runners if `make` is a barrier on Windows.

## 5. Development Experience
- **Editor tooling**: VS Code + Python extension, IntelliJ IDEA with ANTLR plugin, or JetBrains Fleet.
- **Grammar authoring**: Install the ANTLR4 VS Code extension for syntax highlighting and quick parse tree visualization.
- **Pre-commit hooks**:
```bash
pipx install pre-commit
pre-commit install
```
- **Logging & diagnostics**: plan to use `rich` or `loguru` for structured CLI output (add via Poetry once decided).

## 6. Containerization & CI (Optional, staged)
- Plan Dockerfile work after the core parsing pipeline is functional; capture the requirement as an M4 milestone.
- Use GitHub Actions (or preferred CI) to run lint/test workflows in headless mode once the test suite is meaningful.
- Cache ANTLR artifacts and Python dependencies for faster CI runs when CI is introduced.

## 7. Verification Checklist
- `python --version` reports 3.10+.
- `java -version` reports 11+ and can run the ANTLR JAR.
- `antlr4` alias resolves and generates parser code into the repository.
- `poetry install` (or `pip install`) succeeds and installs lint/test dependencies.
- `make test` (once implemented) runs unit tests successfully.

## Decisions & Next Actions
- **Dependency manager**: Use Poetry as the default; export `requirements.txt` via `poetry export` for environments without Poetry.
- **Containerization**: Defer Docker image work until after the parser and JSON serializer reach MVP; track as a follow-up task.
- **Development OS focus**: Target Linux/WSL first; revisit native Windows and macOS support once CLI automation stabilizes.
