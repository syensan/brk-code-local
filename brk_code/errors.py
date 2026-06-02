"""BRK-Code error hierarchy."""


class BRKCodeError(Exception):
    """Base error for BRK-Code."""


class InvalidBRKMagic(BRKCodeError):
    """Invalid magic bytes in .brk-code file."""


class UnsupportedCodec(BRKCodeError):
    """Unsupported codec byte in .brk-code file."""


class InvalidBRKCodeContainer(BRKCodeError):
    """Invalid container structure."""


class SemanticChecksumError(BRKCodeError):
    """Semantic checksum mismatch."""


class SourceScanError(BRKCodeError):
    """Error scanning source directory."""


class ASTAnalysisError(BRKCodeError):
    """Error during AST analysis of a file."""


class SecurityRedactionError(BRKCodeError):
    """Error during security redaction."""
