"""Tests for learning task generation."""

from pathlib import Path

import pytest

from brk_code.ast_analyzer import ASTAnalyzer, FunctionInfo, ASTResult, ModuleInfo, ClassInfo, SymbolInfo, ImportInfo
from brk_code.learning_tasks import generate_learning_tasks


class TestExplainFunctionTask:
    def test_generates_explain_function(self):
        ast_result = ASTResult(
            modules=[ModuleInfo(file="app.py", docstring=None, imports=["json"], from_imports=[])],
            classes=[],
            functions=[
                FunctionInfo(
                    name="login", qualified_name="app.py.login", file="app.py",
                    line=5, end_line=10, args=["username", "password"],
                    returns=None, docstring="Validate a user.", calls=["hash_password"],
                    decorators=[], raises=["ValueError"], is_async=False,
                    complexity_estimate=2,
                ),
            ],
            symbols=[], imports=[], dependency_edges=[], errors=[],
        )
        tasks = generate_learning_tasks(ast_result, {"findings": []})
        explain_tasks = [t for t in tasks if t["task_type"] == "explain_function"]
        assert len(explain_tasks) >= 1
        task = explain_tasks[0]
        assert "login" in task["prompt"]
        assert task["input"]["symbol"] == "app.py.login"
        assert "username" in task["input"]["args"]

    def test_skips_private_functions(self):
        ast_result = ASTResult(
            modules=[],
            classes=[],
            functions=[
                FunctionInfo(
                    name="_helper", qualified_name="app.py._helper", file="app.py",
                    line=1, end_line=3, args=[], returns=None, docstring=None,
                    calls=[], decorators=[], raises=[], is_async=False,
                    complexity_estimate=1,
                ),
            ],
            symbols=[], imports=[], dependency_edges=[], errors=[],
        )
        tasks = generate_learning_tasks(ast_result, {"findings": []})
        explain_tasks = [t for t in tasks if t["task_type"] == "explain_function"]
        assert len(explain_tasks) == 0


class TestSecurityTaskGeneration:
    def test_generates_security_task(self):
        ast_result = ASTResult(
            modules=[], classes=[], functions=[], symbols=[],
            imports=[], dependency_edges=[], errors=[],
        )
        security_report = {
            "findings": [
                {
                    "file": "app.py",
                    "line": 10,
                    "severity": "high",
                    "type": "eval_usage",
                    "message": "Use of eval() is dangerous.",
                },
            ],
        }
        tasks = generate_learning_tasks(ast_result, security_report)
        sec_tasks = [t for t in tasks if t["task_type"] == "find_security_risk"]
        assert len(sec_tasks) >= 1
        assert "eval_usage" in sec_tasks[0]["prompt"]


class TestWriteTestTask:
    def test_generates_write_test(self):
        ast_result = ASTResult(
            modules=[],
            classes=[],
            functions=[
                FunctionInfo(
                    name="calculate", qualified_name="app.py.calculate", file="app.py",
                    line=1, end_line=5, args=["x", "y"], returns="int",
                    docstring="Calculate something.", calls=[], decorators=[],
                    raises=[], is_async=False, complexity_estimate=1,
                ),
            ],
            symbols=[], imports=[], dependency_edges=[], errors=[],
        )
        tasks = generate_learning_tasks(ast_result, {"findings": []})
        test_tasks = [t for t in tasks if t["task_type"] == "write_test"]
        assert len(test_tasks) >= 1
        assert "calculate" in test_tasks[0]["prompt"]


class TestRefactorTask:
    def test_generates_refactor_for_complex(self):
        ast_result = ASTResult(
            modules=[],
            classes=[],
            functions=[
                FunctionInfo(
                    name="complex_func", qualified_name="app.py.complex_func", file="app.py",
                    line=1, end_line=30, args=["data"], returns=None,
                    docstring=None, calls=[], decorators=[], raises=[],
                    is_async=False, complexity_estimate=8,
                ),
            ],
            symbols=[], imports=[], dependency_edges=[], errors=[],
        )
        tasks = generate_learning_tasks(ast_result, {"findings": []})
        refactor_tasks = [t for t in tasks if t["task_type"] == "refactor_suggestion"]
        assert len(refactor_tasks) >= 1
