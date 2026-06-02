# BRK-Code — AI-Learning-Optimized Semantic Code Container

> **BRK-Code does not break Shannon's theorem.**
> **BRK-Code is not a universal lossless source-code compressor.**
> **BRK-Code stores an AI-learning-optimized semantic representation of code.**

> **BRK-Code は Shannon の定理を破るものではありません。**
> **BRK-Code はソースコードを完全可逆圧縮する形式ではありません。**
> **BRK-Code はAI学習・解析向けにコードの意味構造を保存する形式です。**

---

## What is BRK-Code?

BRK-Code is a **semantic / AI-learning-optimized code container format** with the `.brk` extension (MAGIC: `BRKC1`). Instead of compressing source code for bit-exact archival, BRK-Code transforms Python repositories into structured semantic graphs that AI systems can understand, search, review, and learn from.

### What BRK-Code Is NOT

- ❌ A universal lossless source-code compressor
- ❌ A format that breaks Shannon's theorem
- ❌ A way to reconstruct original source files bit-for-bit
- ❌ A replacement for version control or backup systems
- ❌ Suitable for scenarios requiring exact source preservation

### What BRK-Code IS

- ✅ An AI-learning-optimized semantic code container
- ✅ A tool that extracts AST structure, dependencies, symbols, and security findings
- ✅ A format that generates training tasks for code AI models
- ✅ A local/on-premises tool — no cloud, no serverless, no external AI APIs
- ✅ A format that clearly states it is NOT lossless

---

## BRK-Code-Python Profile v0.1

The first profile is **BRK-Code-Python**, designed for Python repositories. It:

1. **Scans** a project directory for `.py` files
2. **Parses** each file using Python's `ast` module
3. **Extracts** classes, functions, arguments, calls, imports, docstrings
4. **Builds** symbol tables, dependency graphs, and function contracts
5. **Scans** for security issues (hardcoded secrets, eval, shell=True, etc.)
6. **Generates** AI learning tasks (explain_function, write_test, find_security_risk, etc.)
7. **Outputs** a `.brk` container, SQLite database, HTML report, and JSONL training data

---

## Installation

```bash
# Clone or download the repository
cd brk-code-local

# Install in development mode
pip install -e .

# Or just run directly
python -m brk_code --help
```

### Requirements

- Python 3.11+
- Standard library only (no external dependencies)
- pytest (for running tests)

---

## CLI Usage

### Help

```bash
brk-code --help
python -m brk_code --help
```

### Scan a Project

```bash
brk-code scan examples/sample_project output.brk \
  --sqlite project_code.sqlite \
  --html project_code_report.html \
  --jsonl training_tasks.jsonl \
  --include-snippets
```

Options:
- `--sqlite <path>`: Export to SQLite database
- `--html <path>`: Export HTML report
- `--jsonl <path>`: Export JSONL learning tasks
- `--include-snippets`: Include minimal source snippets
- `--max-snippet-lines <n>`: Max lines per snippet (default: 20)
- `--quiet`: Suppress informational output

### Inspect a .brk-code Container

```bash
brk-code inspect output.brk
```

Shows profile, file count, function count, class count, security findings, and safety flags.

### Verify a .brk-code Container

```bash
brk-code verify output.brk
```

Validates: magic, codec, required flags, and semantic checksum.

### Export HTML Report

```bash
brk-code export-html output.brk report.html
```

Generates a standalone HTML report with search, file/class/function tables, security findings, and learning tasks.

### Export JSONL Learning Tasks

```bash
brk-code export-jsonl output.brk tasks.jsonl
```

Exports learning tasks in JSONL format for AI training pipelines.

---

## Container Format

```
.brk file = MAGIC + CODEC_BYTE + zlib(canonical_json(container))

MAGIC: b"BRKC1\n" (6 bytes)
CODEC: 0x01 (zlib compressed)
```

### Top-Level Structure

| Section | Description |
|---------|-------------|
| `header` | Format metadata, safety flags |
| `model_binding` | Decoder specification (analytic, no neural weights) |
| `contract` | Reconstruction contract and hard constraints |
| `repo_graph` | File inventory and directory structure |
| `ast_semantic_graph` | Modules, classes, functions from AST analysis |
| `symbol_table` | Name-to-definition mapping |
| `dependency_graph` | Import edges and module dependencies |
| `function_contracts` | Rule-based function behavior hints |
| `test_map` | Test-to-function mapping |
| `security_report` | Security findings and secret redaction |
| `learning_tasks` | Auto-generated AI training tasks |
| `sparse_source_residual` | Minimal source snippets (opt-in only) |
| `task_outputs` | Summary counts |
| `semantic_checksum` | SHA-256 over semantic graph (NOT bit-exact) |

### Safety Invariants (always enforced)

- `header.flags.lossless` = `false`
- `header.flags.bit_exact_reconstruction` = `false`
- `header.flags.semantic_equivalent` = `true`
- `header.flags.ai_learning_optimized` = `true`
- `contract.lossless` = `false`
- `contract.semantic_equivalent` = `true`
- `contract.ai_learning_optimized` = `true`

---

## Security Features

BRK-Code scans for and redacts:

- Hardcoded API keys, secret keys, passwords, tokens, private keys
- `eval()` and `exec()` usage
- `subprocess(..., shell=True)`
- `pickle.loads()`
- `yaml.load()` without SafeLoader
- SQL string concatenation patterns
- URLs containing token parameters

All secret values are replaced with `[REDACTED_SECRET]`.

---

## Learning Task Types

| Task Type | Description |
|-----------|-------------|
| `explain_function` | Explain a function's purpose and behavior |
| `summarize_module` | Summarize a module's structure and purpose |
| `find_security_risk` | Analyze a security finding |
| `write_test` | Generate unit tests for a function |
| `infer_dependencies` | Classify and describe module dependencies |
| `refactor_suggestion` | Suggest refactoring for complex functions |
| `bug_fix_from_static_finding` | Fix a static analysis security finding |

---

## SQLite Schema

The SQLite export includes searchable tables:

- `files` — Source file inventory
- `symbols` — Symbol table
- `functions` — Function definitions
- `classes` — Class definitions
- `imports` — Import relationships
- `security_findings` — Security scan results
- `learning_tasks` — Generated AI training tasks
- `metadata` — Container metadata

---

## Running Tests

```bash
cd brk-code-local
pytest -v
```

---

## Project Structure

```
brk-code-local/
├─ pyproject.toml
├─ README.md
├─ LICENSE
├─ .gitignore
├─ specs/
│  └─ BRK-Code-Python-v0.1.md
├─ brk_code/
│  ├─ __init__.py
│  ├─ __main__.py
│  ├─ cli.py
│  ├─ constants.py
│  ├─ container.py
│  ├─ checksum.py
│  ├─ errors.py
│  ├─ scanner.py
│  ├─ ast_analyzer.py
│  ├─ dependency.py
│  ├─ security.py
│  ├─ learning_tasks.py
│  ├─ sparse_source_residual.py
│  ├─ sqlite_export.py
│  ├─ html_report.py
│  ├─ jsonl_export.py
│  └─ util.py
├─ examples/
│  └─ sample_project/
│     ├─ app.py
│     ├─ utils.py
│     └─ test_app.py
└─ tests/
   ├─ test_container.py
   ├─ test_ast_analyzer.py
   ├─ test_security.py
   ├─ test_learning_tasks.py
   └─ test_cli.py
```

---

## AI Learning Data Usage

The JSONL export is designed for AI training pipelines:

```python
import json

with open("training_tasks.jsonl") as f:
    for line in f:
        task = json.loads(line)
        # task_type: "explain_function", "write_test", etc.
        # prompt: Instruction for the AI
        # input: Structured code context
        # expected_output_hint: What a good answer should cover
```

---

## License

MIT License. See [LICENSE](LICENSE) for details.
