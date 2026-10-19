# -*- coding: utf-8 -*-
"""diy-editorial-review 引擎文本统计件：全表常量＋词数口径与 md/yaml 切节、目标读取（stats 纯读侧）。."""

import io
import re
import yaml

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import v, walk_strings  # noqa: E402
from diyc_lib_base import load_yaml_text  # noqa: E402

REVIEW_FILE = "editorial-review.yaml"
LENSES = ("结构", "文风")
SLOTS = (("结构", "structure"), ("文风", "prose"))
READER_TYPES = ("人类", "LLM")
STATUSES = ("草稿", "已定稿")
STRUCTURE_MODELS = ("教程线性", "参考 MECE", "解释抽象到具体", "任务式 meta-first",
                    "战略金字塔")
CATEGORIES = ("CUT", "MERGE", "MOVE", "CONDENSE", "QUESTION", "PRESERVE")
LENGTH_TARGETS = ("是", "否", "未设目标")
REVIEW_ID_RE = re.compile(r"ER-\d{3}\Z")
HEADING_RE = re.compile(r"^(#{1,3})[ \t]+(.*?)[ \t]*#*[ \t]*$")
CJK_RE = re.compile(r"[㐀-䶿一-鿿豈-﫿]")
WORD_RE = re.compile(r"[A-Za-z0-9_]+")
YAML_SUFFIXES = (".yaml", ".yml")
PROJECT_KEYS = ("name", "created", "updated")
ASSUMPTION = "[假设]"
NL = "\n"

# trace: B4 diy-editorial-review 契约（违规项统一 {code, where, msg} 形态）

# trace: B4 diy-editorial-review 契约（非空判定：None / 空白字符串均视为空）

# trace: B4 diy-editorial-review 契约（整数判定：布尔不得充当整数）

# trace: B4 diy-editorial-review stats（递归收集任意节点的字符串值，只看值不看键）

# trace: B4 diy-editorial-review 契约（YAML 安全装载：(data, err)；缺失 (None, None)、损坏 (None, 原因)）

# trace: B4 diy-editorial-review 契约（--json 单行 / 人读行）

# ---------------------------------------------------------------- stats：结构统计

# trace: B4 diy-editorial-review stats（词数口径：中文按字计 + 西文按分词计）
def word_count(text):
    return len(CJK_RE.findall(text)) + len(WORD_RE.findall(text))

# trace: B4 diy-editorial-review stats（md 切节：`#` 是文档标题；节由 `##`/`###` 切）
def md_sections(text, fallback):
    sections = []
    pending = []
    current = None
    for line in text.splitlines():
        match = HEADING_RE.match(line)
        if match is None:
            pending.append(line)
            continue
        if len(match.group(1)) == 1:
            continue  # `#` 文档标题：不计词、不切节（标题不是正文）
        if current is None:
            head_words = word_count(NL.join(pending))
            if head_words:
                sections.append({"name": fallback, "words": head_words})
        else:
            sections.append({"name": current, "words": word_count(NL.join(pending))})
        current = match.group(2).strip() or fallback
        pending = []
    tail_words = word_count(NL.join(pending))
    if current is None:
        sections.append({"name": fallback, "words": tail_words})
    else:
        sections.append({"name": current, "words": tail_words})
    return sections

# trace: B4 diy-editorial-review stats（yaml 切节：顶层键作节名，节词数 = 该键子树字符串词数）
def yaml_sections(doc, fallback):
    if not isinstance(doc, dict):
        return [{"name": fallback, "words": word_count(NL.join(t for _p, t in walk_strings(doc, "")))}]
    sections = [{"name": str(key), "words": word_count(NL.join(t for _p, t in walk_strings(value, "")))}
                for key, value in doc.items()]
    return sections or [{"name": fallback, "words": 0}]

# trace: B4 diy-editorial-review stats（目标读取与切节；.md/纯文本 vs .yaml/.yml 分派）
def read_target(path, fallback):
    try:
        with io.open(path, "rb") as handle:
            raw = handle.read()
    except OSError as e:
        return None, None, v("MISSING_FILE", "", "目标文档无法读取：%s" % e)
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as e:
        return None, None, v("MISSING_FILE", "",
                             "目标文档无法按 UTF-8 解码（%s）：读不出来等同不在场" % e.reason)
    lines = len(text.splitlines())
    if path.lower().endswith(YAML_SUFFIXES):
        try:
            doc = load_yaml_text(text) or {}
        except yaml.YAMLError as e:
            return None, lines, v("UNPARSABLE_YAML", "", "目标 YAML 解析失败：%s" % e)
        return yaml_sections(doc, fallback), lines, None
    return md_sections(text, fallback), lines, None
