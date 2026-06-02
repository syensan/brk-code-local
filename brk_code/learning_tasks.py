"""Learning task generation for BRK-Code."""

from __future__ import annotations

from typing import Any

from .ast_analyzer import ASTResult
from .constants import LEARNING_TASK_TYPES


def generate_learning_tasks(
    ast_result: ASTResult,
    security_report: dict,
) -> list[dict[str, Any]]:
    """Generate AI learning tasks from AST analysis and security findings.

    Each task has: task_type, prompt, input, expected_output_hint
    """
    tasks: list[dict[str, Any]] = []

    # 1. explain_function tasks
    for func in ast_result.functions:
        if func.name.startswith("_") and func.name != "__init__":
            continue  # Skip private helpers (but include __init__)

        calls_str = ", ".join(func.calls[:5]) if func.calls else "none"
        args_str = ", ".join(func.args)
        docstring_str = func.docstring or "No docstring available."

        tasks.append({
            "task_type": "explain_function",
            "prompt": (
                f"Explain what the function {func.qualified_name} does based on "
                f"its signature, docstring, and calls."
            ),
            "input": {
                "symbol": func.qualified_name,
                "args": func.args,
                "returns": func.returns,
                "calls": func.calls[:5],
                "docstring": func.docstring,
                "is_async": func.is_async,
                "complexity_estimate": func.complexity_estimate,
            },
            "expected_output_hint": (
                "Explain purpose, inputs, outputs, side effects, and risks."
            ),
        })

    # 2. summarize_module tasks
    for module in ast_result.modules:
        if not module.docstring:
            # Only generate if we'd be adding value
            class_count = sum(
                1 for c in ast_result.classes if c.file == module.file
            )
            func_count = sum(
                1 for f in ast_result.functions
                if f.file == module.file and not f.name.startswith("test_")
            )
            if class_count + func_count == 0:
                continue

        module_classes = [
            c.name for c in ast_result.classes if c.file == module.file
        ]
        module_funcs = [
            f.name for f in ast_result.functions
            if f.file == module.file and not f.name.startswith("test_")
        ]

        tasks.append({
            "task_type": "summarize_module",
            "prompt": (
                f"Summarize the Python module {module.file}, including its "
                f"purpose, main classes, and key functions."
            ),
            "input": {
                "file": module.file,
                "docstring": module.docstring,
                "imports": module.imports,
                "classes": module_classes,
                "functions": module_funcs,
            },
            "expected_output_hint": (
                "Provide a module summary covering purpose, structure, "
                "dependencies, and usage patterns."
            ),
        })

    # 3. find_security_risk tasks (from security findings)
    for finding in security_report.get("findings", []):
        tasks.append({
            "task_type": "find_security_risk",
            "prompt": (
                f"Analyze the security finding in {finding['file']} at line "
                f"{finding['line']}: {finding['type']} - {finding['message']}"
            ),
            "input": {
                "file": finding["file"],
                "line": finding["line"],
                "severity": finding["severity"],
                "type": finding["type"],
                "message": finding["message"],
            },
            "expected_output_hint": (
                "Explain the vulnerability, its potential impact, and "
                "suggest a fix or mitigation."
            ),
        })

    # 4. write_test tasks
    for func in ast_result.functions:
        if func.name.startswith("test_"):
            continue
        if func.name.startswith("_") and func.name != "__init__":
            continue

        tasks.append({
            "task_type": "write_test",
            "prompt": (
                f"Write a unit test for the function {func.qualified_name}."
            ),
            "input": {
                "symbol": func.qualified_name,
                "args": func.args,
                "returns": func.returns,
                "docstring": func.docstring,
                "calls": func.calls[:5],
                "raises": func.raises,
            },
            "expected_output_hint": (
                "Write a pytest-compatible test function covering normal "
                "cases, edge cases, and error conditions."
            ),
        })

    # 5. infer_dependencies tasks
    for module in ast_result.modules:
        if not module.imports:
            continue
        tasks.append({
            "task_type": "infer_dependencies",
            "prompt": (
                f"Infer the dependency structure of {module.file} from its "
                f"import statements."
            ),
            "input": {
                "file": module.file,
                "imports": module.imports,
                "from_imports": [
                    [fi[0], fi[1]] for fi in module.from_imports
                ],
            },
            "expected_output_hint": (
                "Classify each import as stdlib, third-party, or local. "
                "Describe the dependency relationships."
            ),
        })

    # 6. refactor_suggestion tasks
    for func in ast_result.functions:
        if func.complexity_estimate >= 5:
            tasks.append({
                "task_type": "refactor_suggestion",
                "prompt": (
                    f"Suggest refactoring for {func.qualified_name} which has "
                    f"estimated cyclomatic complexity of "
                    f"{func.complexity_estimate}."
                ),
                "input": {
                    "symbol": func.qualified_name,
                    "args": func.args,
                    "calls": func.calls[:5],
                    "complexity_estimate": func.complexity_estimate,
                    "raises": func.raises,
                },
                "expected_output_hint": (
                    "Simplify the function by extracting helper methods, "
                    "reducing branching, or reorganizing logic."
                ),
            })

    # 7. bug_fix_from_static_finding tasks
    for finding in security_report.get("findings", []):
        if finding["severity"] == "high":
            tasks.append({
                "task_type": "bug_fix_from_static_finding",
                "prompt": (
                    f"Fix the security issue in {finding['file']} at line "
                    f"{finding['line']}: {finding['type']} - "
                    f"{finding['message']}"
                ),
                "input": {
                    "file": finding["file"],
                    "line": finding["line"],
                    "type": finding["type"],
                    "message": finding["message"],
                },
                "expected_output_hint": (
                    "Provide a corrected version of the code that "
                    "eliminates the security vulnerability."
                ),
            })

    return tasks
