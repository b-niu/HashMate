"""HashMate：自由格式文本的哈希智能解析与文件校验工具。"""

from .hasher import compute_hashes
from .parser import (
    HASH_TYPES,
    HashMatch,
    HashType,
    ParseResult,
    parse_text,
    register_extractor,
)

__all__ = [
    "parse_text",
    "HASH_TYPES",
    "HashType",
    "HashMatch",
    "ParseResult",
    "register_extractor",
    "compute_hashes",
]
