"""BRK-Code format constants."""

# Binary container format
MAGIC: bytes = b"BRKC1\n"
CODEC_ZLIB: int = 0x01
FORMAT_VERSION: str = "0.1.0"
PROFILE_NAME: str = "BRK-Code-Python"
CREATED_BY: str = "brk-code-local"

# Model binding
MODEL_FAMILY: str = "BRK-Code-Analytic"
MODEL_ID: str = "python-ast-symbolic-v0"
DECODER: str = "semantic_code_graph_reader"

# Scanning
DEFAULT_EXCLUDE_DIRS: frozenset[str] = frozenset({
    ".git", ".venv", "venv", "env", "__pycache__",
    "node_modules", "dist", "build", ".mypy_cache",
    ".pytest_cache", ".tox", ".eggs", "*.egg-info",
})

DEFAULT_EXCLUDE_PATTERNS: frozenset[str] = frozenset({
    "*.pyc", "*.pyo", ".env",
})

TARGET_EXTENSIONS: frozenset[str] = frozenset({".py"})

# Security - secret detection patterns
SECRET_VAR_NAMES: frozenset[str] = frozenset({
    "API_KEY", "SECRET_KEY", "SECRET", "TOKEN", "PASSWORD",
    "PRIVATE_KEY", "ACCESS_KEY", "AUTH_KEY", "CREDENTIAL",
})

SECRET_VALUE_PATTERNS: frozenset[str] = frozenset({
    "-----BEGIN PRIVATE KEY-----",
    "-----BEGIN RSA PRIVATE KEY-----",
    "-----BEGIN OPENSSH PRIVATE KEY-----",
})

DANGEROUS_CALLS: frozenset[str] = frozenset({
    "eval", "exec", "pickle.loads",
})

DANGEROUS_IMPORTS: frozenset[str] = frozenset({
    "pickle", "yaml",
})

# Learning task types
LEARNING_TASK_TYPES: frozenset[str] = frozenset({
    "explain_function",
    "summarize_module",
    "find_security_risk",
    "write_test",
    "infer_dependencies",
    "refactor_suggestion",
    "bug_fix_from_static_finding",
})

# Sparse source residual policy
DEFAULT_MAX_SNIPPET_LINES: int = 20

# Contract tasks
CONTRACT_TASKS: list[str] = [
    "code_understanding",
    "semantic_search",
    "bug_localization",
    "test_mapping",
    "refactoring_assistance",
    "security_review",
    "training_data_generation",
]

# Hard constraints
HARD_CONSTRAINTS: list[str] = [
    "must_not_claim_lossless",
    "must_not_store_secrets",
    "must_mark_redacted_secrets",
    "must_not_claim_bit_exact_source_reconstruction",
]
