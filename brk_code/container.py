"""BRK-Code container read/write."""

from __future__ import annotations

import json
import zlib
from pathlib import Path
from typing import Any

from .constants import MAGIC, CODEC_ZLIB
from .errors import InvalidBRKMagic, UnsupportedCodec, InvalidBRKCodeContainer
from .util import canonical_serialize


class BRKCodeContainer:
    """Read and write .brk-code container files.

    Format: MAGIC (6 bytes) + CODEC_BYTE (1 byte) + zlib(canonical_json)
    """

    def __init__(self, data: dict[str, Any]) -> None:
        self.data = data

    def write(self, path: Path) -> None:
        """Write container to disk."""
        payload = canonical_serialize(self.data)
        compressed = zlib.compress(payload)
        with open(path, "wb") as f:
            f.write(MAGIC)
            f.write(bytes([CODEC_ZLIB]))
            f.write(compressed)

    @classmethod
    def read(cls, path: Path) -> BRKCodeContainer:
        """Read container from disk."""
        with open(path, "rb") as f:
            raw = f.read()

        if len(raw) < len(MAGIC) + 1:
            raise InvalidBRKMagic("File too short to contain BRK-Code header.")

        magic = raw[: len(MAGIC)]
        if magic != MAGIC:
            raise InvalidBRKMagic(
                f"Invalid magic: expected {MAGIC!r}, got {magic!r}"
            )

        codec_byte = raw[len(MAGIC)]
        if codec_byte != CODEC_ZLIB:
            raise UnsupportedCodec(
                f"Unsupported codec: 0x{codec_byte:02x}"
            )

        compressed_payload = raw[len(MAGIC) + 1 :]
        try:
            decompressed = zlib.decompress(compressed_payload)
        except zlib.error as e:
            raise InvalidBRKCodeContainer(f"Failed to decompress payload: {e}") from e

        try:
            data = json.loads(decompressed.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            raise InvalidBRKCodeContainer(f"Failed to parse JSON payload: {e}") from e

        if not isinstance(data, dict):
            raise InvalidBRKCodeContainer("Container root must be a JSON object.")

        return cls(data)

    @property
    def header(self) -> dict[str, Any]:
        return self.data.get("header", {})

    @property
    def contract(self) -> dict[str, Any]:
        return self.data.get("contract", {})

    @property
    def flags(self) -> dict[str, Any]:
        return self.header.get("flags", {})
