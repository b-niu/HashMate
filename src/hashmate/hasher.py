"""文件哈希计算：单遍读取，同时计算多种算法。"""

from __future__ import annotations

import hashlib
from pathlib import Path

from .parser import HASH_TYPES

CHUNK_SIZE = 1 << 16  # 64 KB


def compute_hashes(
    path: str | Path,
    algorithms: list[str] | None = None,
) -> dict[str, str]:
    """计算文件的多类哈希值。

    ``algorithms`` 为算法 key（见 ``HASH_TYPES``）；为空时计算全部已知类型。
    单次读取文件、增量更新所有 hasher，避免重复 IO。
    """
    algorithms = algorithms or list(HASH_TYPES.keys())
    hashers = {algo: hashlib.new(algo) for algo in algorithms}

    with open(path, "rb") as fh:
        while True:
            chunk = fh.read(CHUNK_SIZE)
            if not chunk:
                break
            for h in hashers.values():
                h.update(chunk)

    return {algo: h.hexdigest() for algo, h in hashers.items()}
