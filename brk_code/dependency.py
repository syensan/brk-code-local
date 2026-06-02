"""Dependency analysis for BRK-Code."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .ast_analyzer import ASTResult, FunctionInfo


def build_function_contracts(
    ast_result: ASTResult,
    security_findings: list[dict[str, Any]],
) -> dict:
    """Build function_contracts section from AST analysis and security findings.

    Generates rule-based contracts that help LLMs understand function behavior.
    """
    # Map security findings by file:line
    sec_map: dict[str, list[dict]] = {}
    for finding in security_findings:
        key = f"{finding.get('file', '')}:{finding.get('line', 0)}"
        sec_map.setdefault(key, []).append(finding)

    contracts: list[dict] = []
    for func in ast_result.functions:
        side_effects: list[str] = []
        risk_notes: list[str] = []
        preconditions: list[str] = []
        postconditions: list[str] = []

        # Analyze calls for side effects
        for call in func.calls:
            call_lower = call.lower()
            if any(kw in call_lower for kw in ("open", "read", "write", "file")):
                side_effects.append("possible_io")
            if any(kw in call_lower for kw in ("query", "execute", "cursor", "db")):
                side_effects.append("possible_database_access")
            if any(kw in call_lower for kw in ("request", "fetch", "urllib", "http")):
                side_effects.append("possible_network_access")
            if any(kw in call_lower for kw in ("print", "log")):
                side_effects.append("possible_logging")

        # Check for raises
        for exc in func.raises:
            if exc == "ValueError":
                preconditions.append(f"Input validation may raise {exc}")
            elif exc == "TypeError":
                preconditions.append(f"Type checking may raise {exc}")

        # Check docstring for hints
        if func.docstring:
            ds_lower = func.docstring.lower()
            if "return" in ds_lower:
                postconditions.append("Documented return behavior")
            if "raise" in ds_lower or "exception" in ds_lower:
                risk_notes.append("Documented exception behavior")

        # Check security findings for this function
        for line in range(func.line, func.end_line + 1):
            key = f"{func.file}:{line}"
            if key in sec_map:
                for finding in sec_map[key]:
                    risk_notes.append(f"Security: {finding.get('type', 'unknown')}")

        # Deduplicate side effects
        side_effects = sorted(set(side_effects))
        risk_notes = sorted(set(risk_notes))

        # Derive purpose hint
        purpose_parts: list[str] = []
        if func.docstring:
            first_line = func.docstring.strip().split("\n")[0]
            purpose_parts.append(first_line)
        else:
            purpose_parts.append("Derived from name/docstring/calls.")

        contracts.append({
            "function": func.qualified_name,
            "purpose_hint": " ".join(purpose_parts),
            "inputs": func.args,
            "outputs": [func.returns] if func.returns else [],
            "side_effects": side_effects,
            "preconditions": preconditions,
            "postconditions": postconditions,
            "risk_notes": risk_notes,
        })

    return {"contracts": contracts}


def build_test_map(ast_result: ASTResult) -> dict:
    """Build test_map section by analyzing test files.

    Guesses which functions are tested based on test function names and calls.
    """
    # Collect all test functions
    test_functions: list[FunctionInfo] = []
    for func in ast_result.functions:
        if func.name.startswith("test_") or func.file.startswith("test_"):
            test_functions.append(func)

    # Collect all non-test functions for matching
    all_names: dict[str, str] = {}  # name -> qualified_name
    for func in ast_result.functions:
        if not func.name.startswith("test_"):
            all_names[func.name] = func.qualified_name

    tests: list[dict] = []
    for tf in test_functions:
        targets: list[str] = []

        # Guess from test name: test_login_success -> login
        name_body = tf.name
        if name_body.startswith("test_"):
            name_body = name_body[5:]

        # Split by underscore and try to find matches
        parts = name_body.split("_")
        for part in parts:
            if part in all_names and part not in targets:
                targets.append(part)

        # Also check calls within the test function
        for call in tf.calls:
            call_name = call.split(".")[-1]  # e.g., "service.login" -> "login"
            if call_name in all_names and call_name not in targets:
                targets.append(call_name)

        # Convert target names to qualified names
        target_qualified = [all_names[t] for t in targets if t in all_names]

        tests.append({
            "test_file": tf.file,
            "test_function": tf.name,
            "targets_guess": target_qualified,
            "purpose": "Guessed from test name and calls.",
        })

    return {"tests": tests}
