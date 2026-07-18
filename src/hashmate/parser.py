"""自由格式文本的哈希值解析器。

设计目标：易扩展。新增解析规则时，只需写一个继承 ``BaseExtractor`` 的类，
并通过 ``register_extractor`` 注册即可，无需改动其它代码。

内置两条规则：
1. ``LabeledExtractor``：按常见标签（MD5 / SHA1 / SHA-256 ……）识别，置信度最高。
2. ``BareExtractor``：按十六进制串长度推断（如 32 位→MD5、64 位→SHA-256），
   作为兜底，置信度较低，交由用户在界面中人工确认/纠错。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# --------------------------------------------------------------------------- #
# 哈希类型定义
# --------------------------------------------------------------------------- #

HEX = r"[0-9a-fA-F]"


@dataclass(frozen=True)
class HashType:
    """一种哈希算法的元数据。"""

    key: str  # 内部键，如 "sha256"
    label: str  # 显示名，如 "SHA-256"
    length: int  # 十六进制摘要长度（字符数）
    algorithm: str  # hashlib 算法名


HASH_TYPES: dict[str, HashType] = {
    "md5": HashType("md5", "MD5", 32, "md5"),
    "sha1": HashType("sha1", "SHA-1", 40, "sha1"),
    "sha224": HashType("sha224", "SHA-224", 56, "sha224"),
    "sha256": HashType("sha256", "SHA-256", 64, "sha256"),
    "sha384": HashType("sha384", "SHA-384", 96, "sha384"),
    "sha512": HashType("sha512", "SHA-512", 128, "sha512"),
}


# 标签同义词：用于 ``LabeledExtractor``。后续追加新格式，只需在此扩展。
# 匹配时忽略大小写，并兼容全角 / 半角冒号。
LABEL_SYNONYMS: dict[str, list[str]] = {
    "md5": ["md5"],
    "sha1": ["sha1", "sha-1", "sha 1"],
    "sha224": ["sha224", "sha-224"],
    "sha256": ["sha256", "sha-256", "sha 256"],
    "sha384": ["sha384", "sha-384"],
    "sha512": ["sha512", "sha-512"],
}


# --------------------------------------------------------------------------- #
# 解析结果数据结构
# --------------------------------------------------------------------------- #


@dataclass
class HashMatch:
    value: str  # 解析出的十六进制摘要（已小写）
    hash_type: str | None  # 推断出的类型 key；无法推断时为 None
    confidence: float  # 置信度：1.0 标签识别，0.6 裸串推断
    start: int  # 在原文中的起始下标
    end: int  # 结束下标（不含）
    source: str  # 上下文片段，便于人工核对


@dataclass
class ParseResult:
    matches: list[HashMatch] = field(default_factory=list)

    def __iter__(self):
        return iter(self.matches)

    def __len__(self):
        return len(self.matches)


# --------------------------------------------------------------------------- #
# 解析器基类与注册表
# --------------------------------------------------------------------------- #


class BaseExtractor:
    """所有解析规则的基类。子类实现 ``extract`` 即可。"""

    name: str = "base"

    def extract(self, text: str) -> list[HashMatch]:  # pragma: no cover
        raise NotImplementedError


_REGISTRY: list[BaseExtractor] = []


def register_extractor(extractor: BaseExtractor) -> BaseExtractor:
    """注册一个解析规则。返回原对象，便于装饰器式使用。"""
    _REGISTRY.append(extractor)
    return extractor


def get_extractors() -> list[BaseExtractor]:
    """获取已注册规则；首次调用时自动注册内置规则。"""
    if not _REGISTRY:
        _register_builtins()
    return list(_REGISTRY)


def _register_builtins() -> None:
    register_extractor(LabeledExtractor())
    register_extractor(BareExtractor())


# --------------------------------------------------------------------------- #
# 内置规则
# --------------------------------------------------------------------------- #


class LabeledExtractor(BaseExtractor):
    """按标签 + 冒号 + 摘要 的格式识别，例如 ``MD5： 6c80...`` 或 ``SHA-256: 591a...``。"""

    name = "labeled"

    def extract(self, text: str) -> list[HashMatch]:
        matches: list[HashMatch] = []
        for key, ht in HASH_TYPES.items():
            synonyms = LABEL_SYNONYMS.get(key, [key])
            alts = "|".join(re.escape(s) for s in sorted(synonyms, key=len, reverse=True))
            pattern = re.compile(
                rf"(?<![0-9a-fA-F])(?P<label>{alts})"
                rf"\s*[:：]\s*"
                rf"(?P<value>{HEX}{{{ht.length}}})(?![0-9a-fA-F])",
                re.IGNORECASE,
            )
            for m in pattern.finditer(text):
                value = m.group("value").lower()
                snippet = text[max(0, m.start() - 12) : m.end() + 12]
                matches.append(HashMatch(value, key, 1.0, m.start(), m.end(), snippet))
        return matches


class BareExtractor(BaseExtractor):
    """兜底规则：按十六进制串长度推断类型，置信度较低。"""

    name = "bare"

    def extract(self, text: str) -> list[HashMatch]:
        matches: list[HashMatch] = []
        for key, ht in HASH_TYPES.items():
            pattern = re.compile(rf"(?<![0-9a-fA-F])(?P<value>{HEX}{{{ht.length}}})(?![0-9a-fA-F])")
            for m in pattern.finditer(text):
                value = m.group("value").lower()
                snippet = text[max(0, m.start() - 12) : m.end() + 12]
                matches.append(HashMatch(value, key, 0.6, m.start(), m.end(), snippet))
        return matches


# --------------------------------------------------------------------------- #
# 编排：运行全部规则并去重 / 消歧
# --------------------------------------------------------------------------- #


def parse_text(text: str) -> ParseResult:
    """解析文本，返回去重后的哈希候选列表。"""
    if not text:
        return ParseResult(matches=[])

    all_matches: list[HashMatch] = []
    for extractor in get_extractors():
        all_matches.extend(extractor.extract(text))

    # 高置信度优先；同置信度则按出现顺序。
    all_matches.sort(key=lambda m: (-m.confidence, m.start, m.end))

    accepted: list[HashMatch] = []
    covered: list[tuple[int, int]] = []
    for m in all_matches:
        # 与已接受结果重叠 → 视为重复（被更高置信度覆盖），跳过。
        if any(not (m.end <= s or m.start >= e) for s, e in covered):
            continue
        # 完全一致的 值+类型 去重。
        if any(a.value == m.value and a.hash_type == m.hash_type for a in accepted):
            continue
        accepted.append(m)
        covered.append((m.start, m.end))

    accepted.sort(key=lambda m: m.start)
    return ParseResult(matches=accepted)
