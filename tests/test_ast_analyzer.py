"""Tests for AST analyzer."""

from pathlib import Path

import pytest

from brk_code.ast_analyzer import ASTAnalyzer, analyze_project, build_ast_semantic_graph
from brk_code.scanner import ScannedFile


def _write_py(path: Path, source: str) -> Path:
    """Write a Python file and return its path."""
    path.write_text(source, encoding="utf-8")
    return path


class TestFunctionExtraction:
    def test_extract_function(self, tmp_path):
        source = '''
def hello(name: str) -> str:
    """Say hello."""
    return f"Hello, {name}"
'''
        f = _write_py(tmp_path / "mod.py", source)
        analyzer = ASTAnalyzer(local_modules=set())
        result = analyzer.analyze_file(f, "mod.py")
        assert len(result.functions) == 1
        func = result.functions[0]
        assert func.name == "hello"
        assert "name" in func.args
        assert func.docstring == "Say hello."
        assert func.returns is not None
        assert func.is_async is False

    def test_extract_async_function(self, tmp_path):
        source = '''
async def fetch_data(url: str):
    """Fetch data from URL."""
    return await request(url)
'''
        f = _write_py(tmp_path / "mod.py", source)
        analyzer = ASTAnalyzer(local_modules=set())
        result = analyzer.analyze_file(f, "mod.py")
        assert len(result.functions) == 1
        assert result.functions[0].is_async is True

    def test_extract_function_calls(self, tmp_path):
        source = '''
def process(data):
    result = normalize(data)
    return validate(result)
'''
        f = _write_py(tmp_path / "mod.py", source)
        analyzer = ASTAnalyzer(local_modules=set())
        result = analyzer.analyze_file(f, "mod.py")
        assert len(result.functions) == 1
        call_names = result.functions[0].calls
        assert "normalize" in call_names
        assert "validate" in call_names


class TestClassExtraction:
    def test_extract_class(self, tmp_path):
        source = '''
class UserService:
    """User service class."""
    def login(self, username):
        return True

    def logout(self):
        pass
'''
        f = _write_py(tmp_path / "mod.py", source)
        analyzer = ASTAnalyzer(local_modules=set())
        result = analyzer.analyze_file(f, "mod.py")
        assert len(result.classes) == 1
        cls = result.classes[0]
        assert cls.name == "UserService"
        assert "login" in cls.methods
        assert "logout" in cls.methods
        assert cls.docstring == "User service class."

    def test_extract_class_with_bases(self, tmp_path):
        source = '''
class MyError(Exception):
    pass
'''
        f = _write_py(tmp_path / "mod.py", source)
        analyzer = ASTAnalyzer(local_modules=set())
        result = analyzer.analyze_file(f, "mod.py")
        assert len(result.classes) == 1
        assert "Exception" in result.classes[0].bases


class TestImportsExtraction:
    def test_extract_imports(self, tmp_path):
        source = '''
import json
import os
from pathlib import Path
'''
        f = _write_py(tmp_path / "mod.py", source)
        analyzer = ASTAnalyzer(local_modules=set())
        result = analyzer.analyze_file(f, "mod.py")
        import_modules = [imp.module for imp in result.imports]
        assert "json" in import_modules
        assert "os" in import_modules
        assert "pathlib" in import_modules

    def test_local_import_classification(self, tmp_path):
        source = '''
from utils import normalize_name
import json
'''
        f = _write_py(tmp_path / "mod.py", source)
        analyzer = ASTAnalyzer(local_modules={"utils"})
        result = analyzer.analyze_file(f, "mod.py")
        # utils should be classified as local
        local_imports = [imp for imp in result.imports if imp.kind == "local"]
        ext_imports = [imp for imp in result.imports if imp.kind == "stdlib_or_external"]
        assert any(imp.module == "utils" for imp in local_imports)
        assert any(imp.module == "json" for imp in ext_imports)


class TestCallsExtraction:
    def test_method_calls(self, tmp_path):
        source = '''
class Service:
    def run(self):
        self.start()
        self.stop()
'''
        f = _write_py(tmp_path / "mod.py", source)
        analyzer = ASTAnalyzer(local_modules=set())
        result = analyzer.analyze_file(f, "mod.py")
        assert len(result.functions) == 1
        calls = result.functions[0].calls
        assert "self.start" in calls
        assert "self.stop" in calls


class TestSyntaxErrorHandling:
    def test_syntax_error_returns_errors(self, tmp_path):
        source = "def broken(\n"
        f = _write_py(tmp_path / "bad.py", source)
        analyzer = ASTAnalyzer(local_modules=set())
        result = analyzer.analyze_file(f, "bad.py")
        assert len(result.errors) > 0
        assert "bad.py" in result.errors[0]["file"]
