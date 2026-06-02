"""Tests for BRK-Code container read/write."""

import json
import tempfile
from pathlib import Path

import pytest

from brk_code.container import BRKCodeContainer
from brk_code.constants import MAGIC, CODEC_ZLIB
from brk_code.errors import InvalidBRKMagic, UnsupportedCodec


def _sample_container_data():
    return {
        "header": {
            "magic": "BRKC1",
            "format_version": "0.1.0",
            "profile": "BRK-Code-Python",
            "flags": {
                "lossless": False,
                "bit_exact_reconstruction": False,
                "semantic_equivalent": True,
                "ai_learning_optimized": True,
            },
        },
        "model_binding": {},
        "contract": {"lossless": False, "semantic_equivalent": True},
        "repo_graph": {"root": "test", "files": [], "directories": []},
        "ast_semantic_graph": {"modules": [], "classes": [], "functions": []},
        "symbol_table": {"symbols": []},
        "dependency_graph": {"imports": [], "edges": []},
        "function_contracts": {"contracts": []},
        "test_map": {"tests": []},
        "security_report": {"secrets_redacted": 0, "findings": []},
        "learning_tasks": [],
        "sparse_source_residual": {"policy": "minimal_snippets_only", "snippets": []},
        "task_outputs": {},
        "semantic_checksum": {"algorithm": "sha256", "type": "semantic", "digest": "abc123"},
    }


class TestBRKCodeWriteReadRoundtrip:
    def test_roundtrip(self, tmp_path):
        data = _sample_container_data()
        container = BRKCodeContainer(data)
        path = tmp_path / "test.brk"
        container.write(path)

        read_back = BRKCodeContainer.read(path)
        assert read_back.data["header"]["magic"] == "BRKC1"
        assert read_back.data["header"]["flags"]["lossless"] is False
        assert read_back.data["header"]["flags"]["semantic_equivalent"] is True
        assert read_back.data["header"]["flags"]["ai_learning_optimized"] is True

    def test_roundtrip_preserves_all_sections(self, tmp_path):
        data = _sample_container_data()
        container = BRKCodeContainer(data)
        path = tmp_path / "test.brk"
        container.write(path)

        read_back = BRKCodeContainer.read(path)
        assert "repo_graph" in read_back.data
        assert "ast_semantic_graph" in read_back.data
        assert "symbol_table" in read_back.data
        assert "dependency_graph" in read_back.data
        assert "security_report" in read_back.data
        assert "learning_tasks" in read_back.data
        assert "sparse_source_residual" in read_back.data
        assert "semantic_checksum" in read_back.data


class TestBRKCodeMagicValidation:
    def test_invalid_magic(self, tmp_path):
        path = tmp_path / "bad.brk"
        path.write_bytes(b"XXXXXX\n" + b"\x00" * 100)
        with pytest.raises(InvalidBRKMagic):
            BRKCodeContainer.read(path)

    def test_empty_file(self, tmp_path):
        path = tmp_path / "empty.brk"
        path.write_bytes(b"")
        with pytest.raises(InvalidBRKMagic):
            BRKCodeContainer.read(path)

    def test_truncated_file(self, tmp_path):
        path = tmp_path / "trunc.brk"
        path.write_bytes(MAGIC[:3])
        with pytest.raises(InvalidBRKMagic):
            BRKCodeContainer.read(path)

    def test_unsupported_codec(self, tmp_path):
        path = tmp_path / "bad_codec.brk"
        path.write_bytes(MAGIC + b"\x99" + b"\x00" * 100)
        with pytest.raises(UnsupportedCodec):
            BRKCodeContainer.read(path)


class TestSemanticChecksumDetection:
    def test_tampered_payload_detected(self, tmp_path):
        data = _sample_container_data()
        container = BRKCodeContainer(data)
        path = tmp_path / "test.brk"
        container.write(path)

        # Read, verify it works
        read_back = BRKCodeContainer.read(path)
        assert read_back.data["header"]["magic"] == "BRKC1"

        # Tamper with the file
        raw = bytearray(path.read_bytes())
        # Flip a byte in the compressed payload area
        if len(raw) > 20:
            raw[-1] ^= 0xFF
        tampered_path = tmp_path / "tampered.brk"
        tampered_path.write_bytes(raw)

        # Should fail to read (decompression error or JSON parse error)
        with pytest.raises(Exception):
            BRKCodeContainer.read(tampered_path)
