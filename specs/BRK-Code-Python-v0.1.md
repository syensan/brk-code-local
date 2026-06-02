# BRK-Code-Python v0.1 Specification

> BRK-Code does not break Shannon's theorem.
> BRK-Code is not a universal lossless source-code compressor.
> BRK-Code stores an AI-learning-optimized semantic representation of code.

## 1. Overview

BRK-Code-Python is a profile of the BRK container format designed for Python source code repositories. It transforms Python projects into structured semantic graphs optimized for AI understanding, search, review, and learning.

### Safety Invariants

These must ALWAYS be enforced:

- `header.flags.lossless = false`
- `header.flags.bit_exact_reconstruction = false`
- `header.flags.semantic_equivalent = true`
- `header.flags.ai_learning_optimized = true`
- `contract.lossless = false`
- `contract.semantic_equivalent = true`
- `contract.ai_learning_optimized = true`

## 2. Container Format

```
MAGIC (6 bytes) + CODEC_BYTE (1 byte) + zlib(canonical_json)
```

- MAGIC: `b"BRKC1\n"`
- CODEC: `0x01` (zlib compressed canonical JSON)
- canonical JSON: `json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")`

## 3. Top-Level JSON Structure

```json
{
  "header": {},
  "model_binding": {},
  "contract": {},
  "repo_graph": {},
  "ast_semantic_graph": {},
  "symbol_table": {},
  "dependency_graph": {},
  "function_contracts": {},
  "test_map": {},
  "security_report": {},
  "learning_tasks": [],
  "sparse_source_residual": {},
  "task_outputs": {},
  "semantic_checksum": {}
}
```

## 4. Section Specifications

### 4.1 header

```json
{
  "magic": "BRKC1",
  "format_version": "0.1.0",
  "profile": "BRK-Code-Python",
  "created_by": "brk-code-local",
  "created_at": "<UTC ISO8601>",
  "flags": {
    "lossless": false,
    "bit_exact_reconstruction": false,
    "semantic_equivalent": true,
    "ai_learning_optimized": true
  },
  "source_root_name": "<project folder name>",
  "file_count": 0,
  "python_file_count": 0
}
```

### 4.2 model_binding

```json
{
  "model_family": "BRK-Code-Analytic",
  "model_id": "python-ast-symbolic-v0",
  "version": "0.1.0",
  "weights_hash": null,
  "decoder": "semantic_code_graph_reader",
  "note": "Analytic local AST-based code understanding model. No neural weights."
}
```

### 4.3 contract

```json
{
  "mode": "brk-code",
  "domain": "python_repository",
  "lossless": false,
  "bit_exact_reconstruction": false,
  "semantic_equivalent": true,
  "ai_learning_optimized": true,
  "tasks": [
    "code_understanding",
    "semantic_search",
    "bug_localization",
    "test_mapping",
    "refactoring_assistance",
    "security_review",
    "training_data_generation"
  ],
  "hard_constraints": [
    "must_not_claim_lossless",
    "must_not_store_secrets",
    "must_mark_redacted_secrets",
    "must_not_claim_bit_exact_source_reconstruction"
  ]
}
```

### 4.4 repo_graph

File inventory with SHA-256 hashes, line counts, import lists, and test classification.

### 4.5 ast_semantic_graph

Modules, classes (with methods and bases), and functions (with args, returns, calls, decorators, raises, complexity estimates) extracted via Python `ast` module.

### 4.6 symbol_table

Flattened name-to-definition mapping with qualified names, kinds, and signatures.

### 4.7 dependency_graph

Import relationships classified as `stdlib_or_external` or `local`, with dependency edges.

### 4.8 function_contracts

Rule-based behavior hints for each function: purpose, inputs, outputs, side_effects, preconditions, postconditions, risk_notes.

### 4.9 test_map

Guess-based mapping from test functions to target functions.

### 4.10 security_report

Security findings with severity levels and secret redaction counts.

### 4.11 learning_tasks

Auto-generated AI training tasks of types: explain_function, summarize_module, find_security_risk, write_test, infer_dependencies, refactor_suggestion, bug_fix_from_static_finding.

### 4.12 sparse_source_residual

Minimal source snippets (opt-in via `--include-snippets`). NOT a full source snapshot.

### 4.13 semantic_checksum

SHA-256 over canonical JSON of: contract, repo_graph, ast_semantic_graph, symbol_table, dependency_graph, task_outputs, header.flags. NOT a bit-exact checksum of source files.

## 5. CLI Commands

- `brk-code scan <source_dir> <output.brk>` — Scan and create container
- `brk-code inspect <file.brk>` — Display metadata
- `brk-code verify <file.brk>` — Validate container integrity
- `brk-code export-html <file.brk> <output.html>` — Generate HTML report
- `brk-code export-jsonl <file.brk> <output.jsonl>` — Export learning tasks

## 6. Security

- Secret values are replaced with `[REDACTED_SECRET]`
- `.env` files are not read
- Security findings include: hardcoded secrets, eval/exec, shell=True, pickle.loads, yaml.unsafe_load, SQL concatenation, URL tokens

## 7. Exclusions

The scanner excludes: `.git`, `.venv`, `venv`, `env`, `__pycache__`, `node_modules`, `dist`, `build`, `.mypy_cache`, `.pytest_cache`, `*.pyc`, `.env`
