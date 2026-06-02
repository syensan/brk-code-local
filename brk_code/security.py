"""Security scanner for BRK-Code."""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .constants import SECRET_VAR_NAMES, SECRET_VALUE_PATTERNS
from .errors import SecurityRedactionError
from .util import is_test_file


@dataclass
class SecurityFinding:
    file: str
    line: int
    severity: str  # "high", "medium", "low"
    type: str
    message: str
    value: str  # redacted value


# Patterns for secret detection
_SECRET_VAR_PATTERN = re.compile(
    r"^\s*("
    + "|".join(re.escape(name) for name in SECRET_VAR_NAMES)
    + r")\s*=\s*(.+)$",
    re.MULTILINE | re.IGNORECASE,
)

# Hardcoded string pattern with long base64/hex
_POSSIBLE_SECRET_VALUE = re.compile(
    r'^["\']([A-Za-z0-9+/=_-]{20,})["\']$'
)

# SQL concatenation pattern
_SQL_CONCAT_PATTERN = re.compile(
    r'["\'].*\+\s*\w+.*(?:SELECT|INSERT|UPDATE|DELETE|DROP)',
    re.IGNORECASE,
)

# URL with token pattern
_URL_TOKEN_PATTERN = re.compile(
    r'https?://\S+(?:token|key|secret|password|api_key)=\S+',
    re.IGNORECASE,
)


class SecurityScanner:
    """Scan Python source files for security issues."""

    def __init__(self) -> None:
        self.findings: list[SecurityFinding] = []
        self.secrets_redacted: int = 0

    def scan_file(self, file_path: Path, rel_path: str) -> list[SecurityFinding]:
        """Scan a single file for security issues."""
        findings: list[SecurityFinding] = []

        try:
            source = file_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return findings

        lines = source.splitlines()

        # 1. AST-based checks
        try:
            tree = ast.parse(source, filename=rel_path)
            findings.extend(self._check_ast(tree, rel_path, lines))
        except SyntaxError:
            pass

        # 2. Line-based checks (for patterns AST can't catch)
        findings.extend(self._check_lines(lines, rel_path))

        # 3. Secret variable detection
        findings.extend(self._check_secrets(lines, rel_path))

        self.findings.extend(findings)
        return findings

    def _check_ast(
        self, tree: ast.Module, rel_path: str, lines: list[str]
    ) -> list[SecurityFinding]:
        findings: list[SecurityFinding] = []

        for node in ast.walk(tree):
            # eval() call
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name) and func.id == "eval":
                    findings.append(SecurityFinding(
                        file=rel_path, line=node.lineno,
                        severity="high", type="eval_usage",
                        message="Use of eval() is dangerous and should be avoided.",
                        value="[REDACTED_EVAL]",
                    ))

                # exec() call
                if isinstance(func, ast.Name) and func.id == "exec":
                    findings.append(SecurityFinding(
                        file=rel_path, line=node.lineno,
                        severity="high", type="exec_usage",
                        message="Use of exec() is dangerous and should be avoided.",
                        value="[REDACTED_EXEC]",
                    ))

                # subprocess with shell=True
                # Handles both: subprocess.Popen(..., shell=True) and subprocess.call(..., shell=True)
                func_name = None
                if isinstance(func, ast.Name):
                    func_name = func.id
                elif isinstance(func, ast.Attribute):
                    func_name = func.attr

                if func_name in ("Popen", "call", "run", "check_output", "check_call"):
                    for kw in node.keywords:
                        if kw.arg == "shell":
                            if isinstance(kw.value, ast.Constant) and kw.value.value is True:
                                findings.append(SecurityFinding(
                                    file=rel_path, line=node.lineno,
                                    severity="high", type="shell_true",
                                    message="subprocess with shell=True is dangerous.",
                                    value="[REDACTED_SHELL_TRUE]",
                                ))

                # pickle.loads
                if isinstance(func, ast.Attribute):
                    if func.attr == "loads" and isinstance(func.value, ast.Name):
                        if func.value.id == "pickle":
                            findings.append(SecurityFinding(
                                file=rel_path, line=node.lineno,
                                severity="high", type="pickle_loads",
                                message="Use of pickle.loads() can execute arbitrary code.",
                                value="[REDACTED_PICKLE]",
                            ))

            # yaml.load without SafeLoader
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr == "load" and isinstance(node.func.value, ast.Name):
                        if node.func.value.id == "yaml":
                            has_safe = any(
                                kw.arg == "Loader" for kw in node.keywords
                            )
                            if not has_safe:
                                findings.append(SecurityFinding(
                                    file=rel_path, line=node.lineno,
                                    severity="medium", type="yaml_unsafe_load",
                                    message="yaml.load() without SafeLoader is unsafe. Use yaml.safe_load().",
                                    value="[REDACTED_YAML]",
                                ))

        return findings

    def _check_lines(self, lines: list[str], rel_path: str) -> list[SecurityFinding]:
        findings: list[SecurityFinding] = []

        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            # SQL concatenation
            if _SQL_CONCAT_PATTERN.search(stripped):
                findings.append(SecurityFinding(
                    file=rel_path, line=i,
                    severity="medium", type="sql_concatenation",
                    message="Possible SQL string concatenation detected.",
                    value="[REDACTED_SQL]",
                ))

            # URL with token
            if _URL_TOKEN_PATTERN.search(stripped):
                findings.append(SecurityFinding(
                    file=rel_path, line=i,
                    severity="high", type="url_with_token",
                    message="URL containing token/secret parameter detected.",
                    value="[REDACTED_URL_TOKEN]",
                ))

        return findings

    def _check_secrets(self, lines: list[str], rel_path: str) -> list[SecurityFinding]:
        findings: list[SecurityFinding] = []

        for i, line in enumerate(lines, 1):
            # Check for secret variable assignments
            match = _SECRET_VAR_PATTERN.match(line)
            if match:
                var_name = match.group(1).upper()
                value_part = match.group(2).strip()
                # Only flag if it looks like a hardcoded value
                if _POSSIBLE_SECRET_VALUE.match(value_part) or (
                    value_part.startswith(("'", '"')) and not value_part.startswith(("'os.", '"os.', "''", '""'))
                ):
                    self.secrets_redacted += 1
                    findings.append(SecurityFinding(
                        file=rel_path, line=i,
                        severity="high", type="possible_secret",
                        message="Possible hardcoded secret redacted.",
                        value="[REDACTED_SECRET]",
                    ))

            # Check for private key patterns
            for pattern in SECRET_VALUE_PATTERNS:
                if pattern in line:
                    self.secrets_redacted += 1
                    findings.append(SecurityFinding(
                        file=rel_path, line=i,
                        severity="high", type="private_key",
                        message="Private key detected and redacted.",
                        value="[REDACTED_SECRET]",
                    ))

        return findings

    def build_security_report(self) -> dict:
        """Build the security_report section."""
        return {
            "secrets_redacted": self.secrets_redacted,
            "findings": [
                {
                    "file": f.file,
                    "line": f.line,
                    "severity": f.severity,
                    "type": f.type,
                    "message": f.message,
                    "value": f.value,
                }
                for f in self.findings
            ],
        }


def scan_security(
    source_dir: Path,
    files: list[Any],  # list of ScannedFile
) -> dict:
    """Scan all Python files for security issues.

    Returns security_report dict.
    """
    scanner = SecurityScanner()
    for f in files:
        file_path = source_dir / f.path
        if file_path.exists() and not is_test_file(file_path):
            scanner.scan_file(file_path, f.path)
        elif file_path.exists():
            # Also scan test files but with lower severity expectations
            scanner.scan_file(file_path, f.path)
    return scanner.build_security_report()
