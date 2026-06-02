"""Tests for security scanner."""

from pathlib import Path

import pytest

from brk_code.security import SecurityScanner


def _write_py(path: Path, source: str) -> Path:
    path.write_text(source, encoding="utf-8")
    return path


class TestAPIKeyDetection:
    def test_detect_api_key(self, tmp_path):
        source = 'API_KEY = "sk-1234567890abcdef1234"\n'
        f = _write_py(tmp_path / "app.py", source)
        scanner = SecurityScanner()
        findings = scanner.scan_file(f, "app.py")
        assert any(f.type == "possible_secret" for f in findings)

    def test_detect_secret_key(self, tmp_path):
        source = 'SECRET_KEY = "mysecret1234567890abcd"\n'
        f = _write_py(tmp_path / "app.py", source)
        scanner = SecurityScanner()
        findings = scanner.scan_file(f, "app.py")
        assert any(f.type == "possible_secret" for f in findings)


class TestPasswordVariableDetection:
    def test_detect_password_variable(self, tmp_path):
        source = 'PASSWORD = "hardcoded_pass_12345678"\n'
        f = _write_py(tmp_path / "app.py", source)
        scanner = SecurityScanner()
        findings = scanner.scan_file(f, "app.py")
        assert any(f.type == "possible_secret" for f in findings)


class TestEvalDetection:
    def test_detect_eval(self, tmp_path):
        source = '''
def unsafe(expr):
    return eval(expr)
'''
        f = _write_py(tmp_path / "app.py", source)
        scanner = SecurityScanner()
        findings = scanner.scan_file(f, "app.py")
        assert any(f.type == "eval_usage" for f in findings)
        eval_f = next(f for f in findings if f.type == "eval_usage")
        assert eval_f.severity == "high"


class TestShellTrueDetection:
    def test_detect_shell_true(self, tmp_path):
        source = '''
import subprocess
def run(cmd):
    subprocess.Popen(cmd, shell=True)
'''
        f = _write_py(tmp_path / "app.py", source)
        scanner = SecurityScanner()
        findings = scanner.scan_file(f, "app.py")
        assert any(f.type == "shell_true" for f in findings)


class TestExecDetection:
    def test_detect_exec(self, tmp_path):
        source = '''
def run_code(code):
    exec(code)
'''
        f = _write_py(tmp_path / "app.py", source)
        scanner = SecurityScanner()
        findings = scanner.scan_file(f, "app.py")
        assert any(f.type == "exec_usage" for f in findings)


class TestPickleDetection:
    def test_detect_pickle_loads(self, tmp_path):
        source = '''
import pickle
def load_data(raw):
    return pickle.loads(raw)
'''
        f = _write_py(tmp_path / "app.py", source)
        scanner = SecurityScanner()
        findings = scanner.scan_file(f, "app.py")
        assert any(f.type == "pickle_loads" for f in findings)


class TestYamlUnsafeLoad:
    def test_detect_yaml_unsafe_load(self, tmp_path):
        source = '''
import yaml
def load_config(text):
    return yaml.load(text)
'''
        f = _write_py(tmp_path / "app.py", source)
        scanner = SecurityScanner()
        findings = scanner.scan_file(f, "app.py")
        assert any(f.type == "yaml_unsafe_load" for f in findings)


class TestSecretRedaction:
    def test_secrets_are_redacted(self, tmp_path):
        source = 'API_KEY = "super_secret_value_12345"\n'
        f = _write_py(tmp_path / "app.py", source)
        scanner = SecurityScanner()
        findings = scanner.scan_file(f, "app.py")
        for finding in findings:
            if finding.type == "possible_secret":
                assert finding.value == "[REDACTED_SECRET]"
                assert "super_secret" not in finding.value
