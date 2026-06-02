"""Tests for BRK-Code CLI."""

import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture
def sample_project(tmp_path):
    """Create a sample project for CLI testing."""
    proj = tmp_path / "sample_project"
    proj.mkdir()

    (proj / "app.py").write_text(
        'import json\nfrom utils import normalize_name\n\n'
        'API_KEY = "should_be_redacted"\n\n'
        'class UserService:\n'
        '    def login(self, username: str, password: str):\n'
        '        """Validate a user login request."""\n'
        '        name = normalize_name(username)\n'
        '        if not password:\n'
        '            raise ValueError("password required")\n'
        '        return {"user": name, "ok": True}\n\n'
        'def unsafe_eval(expr: str):\n'
        '    return eval(expr)\n',
        encoding="utf-8",
    )

    (proj / "utils.py").write_text(
        'def normalize_name(name: str) -> str:\n'
        '    """Normalize user name."""\n'
        '    return name.strip().lower()\n',
        encoding="utf-8",
    )

    (proj / "test_app.py").write_text(
        'from app import UserService\n\n'
        'def test_login():\n'
        '    service = UserService()\n'
        '    result = service.login("Alice", "pass")\n'
        '    assert result["ok"] is True\n',
        encoding="utf-8",
    )

    return proj


class TestCLIScan:
    def test_scan_basic(self, sample_project, tmp_path):
        output = tmp_path / "output.brk"
        result = subprocess.run(
            [sys.executable, "-m", "brk_code", "scan", str(sample_project), str(output)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert output.exists()

    def test_scan_with_all_exports(self, sample_project, tmp_path):
        output = tmp_path / "output.brk"
        sqlite_out = tmp_path / "out.sqlite"
        html_out = tmp_path / "out.html"
        jsonl_out = tmp_path / "out.jsonl"

        result = subprocess.run(
            [
                sys.executable, "-m", "brk_code", "scan",
                str(sample_project), str(output),
                "--sqlite", str(sqlite_out),
                "--html", str(html_out),
                "--jsonl", str(jsonl_out),
                "--include-snippets",
            ],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert output.exists()
        assert sqlite_out.exists()
        assert html_out.exists()
        assert jsonl_out.exists()

    def test_scan_quiet(self, sample_project, tmp_path):
        output = tmp_path / "output.brk"
        result = subprocess.run(
            [sys.executable, "-m", "brk_code", "scan", str(sample_project), str(output), "--quiet"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert output.exists()
        # Quiet mode should still produce the file but less output
        assert "BRK-Code scan complete" not in result.stdout

    def test_scan_nonexistent_dir(self, tmp_path):
        output = tmp_path / "output.brk"
        result = subprocess.run(
            [sys.executable, "-m", "brk_code", "scan", "/nonexistent/path", str(output)],
            capture_output=True, text=True,
        )
        assert result.returncode != 0


class TestCLIInspect:
    def test_inspect(self, sample_project, tmp_path):
        output = tmp_path / "output.brk"
        subprocess.run(
            [sys.executable, "-m", "brk_code", "scan", str(sample_project), str(output)],
            capture_output=True, text=True,
        )

        result = subprocess.run(
            [sys.executable, "-m", "brk_code", "inspect", str(output)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "BRK-Code-Python" in result.stdout
        assert "Lossless: False" in result.stdout
        assert "Semantic equivalent: True" in result.stdout
        assert "AI learning optimized: True" in result.stdout


class TestCLIVerify:
    def test_verify_valid(self, sample_project, tmp_path):
        output = tmp_path / "output.brk"
        subprocess.run(
            [sys.executable, "-m", "brk_code", "scan", str(sample_project), str(output)],
            capture_output=True, text=True,
        )

        result = subprocess.run(
            [sys.executable, "-m", "brk_code", "verify", str(output)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "Verification passed" in result.stdout


class TestCLIExportHTML:
    def test_export_html(self, sample_project, tmp_path):
        output = tmp_path / "output.brk"
        html_out = tmp_path / "report.html"

        subprocess.run(
            [sys.executable, "-m", "brk_code", "scan", str(sample_project), str(output)],
            capture_output=True, text=True,
        )

        result = subprocess.run(
            [sys.executable, "-m", "brk_code", "export-html", str(output), str(html_out)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert html_out.exists()
        content = html_out.read_text(encoding="utf-8")
        assert "BRK-Code Report" in content
        assert "lossless" in content.lower()


class TestCLIExportJSONL:
    def test_export_jsonl(self, sample_project, tmp_path):
        output = tmp_path / "output.brk"
        jsonl_out = tmp_path / "tasks.jsonl"

        subprocess.run(
            [sys.executable, "-m", "brk_code", "scan", str(sample_project), str(output)],
            capture_output=True, text=True,
        )

        result = subprocess.run(
            [sys.executable, "-m", "brk_code", "export-jsonl", str(output), str(jsonl_out)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert jsonl_out.exists()
        lines = jsonl_out.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) > 0

        import json
        for line in lines:
            task = json.loads(line)
            assert "task_type" in task
            assert "prompt" in task
