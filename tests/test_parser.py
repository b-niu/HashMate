"""解析器单元测试。"""

from hashmate.parser import parse_text

SAMPLE = """此格式包含一个PDF文件归档。
文件名: R440R540T440_BIOS.2.27.0_RN.pdf
文件大小: 263.98 KB
MD5： 6c8000da9731a35fa6ad37132c4005ee
SHA1： 24d8a2e91672db579ca73cee4084918e97343431
SHA-256： 591ae6d22871a6e7918fbe8ccc0c9d0279c771a0b0a3d8e7dbec4abfe78335b7"""


def test_parse_labels_with_fullwidth_colon():
    result = parse_text(SAMPLE)
    by_type = {m.hash_type: m.value for m in result}

    assert by_type["md5"] == "6c8000da9731a35fa6ad37132c4005ee"
    assert by_type["sha1"] == "24d8a2e91672db579ca73cee4084918e97343431"
    assert by_type["sha256"] == "591ae6d22871a6e7918fbe8ccc0c9d0279c771a0b0a3d8e7dbec4abfe78335b7"


def test_labeled_has_higher_confidence_than_bare():
    result = parse_text(SAMPLE)
    for m in result:
        if m.hash_type in ("md5", "sha1", "sha256"):
            assert m.confidence == 1.0


def test_halfwidth_colon_and_uppercase():
    text = "md5: ABCDEF0123456789ABCDEF0123456789\nSHA-256: " + "a" * 64
    result = parse_text(text)
    by_type = {m.hash_type: m.value for m in result}
    assert by_type["md5"] == "abcdef0123456789abcdef0123456789"
    assert by_type["sha256"] == "a" * 64


def test_empty_text():
    assert len(parse_text("")) == 0
    assert len(parse_text("没有任何哈希的文件名 report final")) == 0


def test_no_false_positive_on_size():
    # "263.98 KB" 不应被误识别为哈希。
    result = parse_text("文件大小: 263.98 KB")
    assert len(result) == 0
