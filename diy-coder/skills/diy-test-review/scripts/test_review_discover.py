# -*- coding: utf-8 -*-
"""diy-test-review 扫描引擎：文件发现 + 语料采样 + 机械扫描 + pact/content 检查。"""
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import v  # noqa: E402

from test_review_lib import (  # noqa: E402
    ADD_INTERACTION_RE, ASSERTION_RE, C1_RE, C1_REASON_RE, C2_RE, C3_RES,
    COMMENT_MARKERS, CONTENT_IGNORE_PREFIX, EXCLUDE_DIRS, FFI_SAFE_MARKER,
    GENERATED_MARKERS, H1_RE, H5_MAX_LINES, H9_RE, KEY_PATTERNS, LLM_JUDGED_KEYS,
    MAESTRO_FLOW_SUFFIXES, MECHANICAL_KEYS, MERGE_CONFIG_RE, PACT_CONFIG_NAMES,
    PACT_FILE_SUFFIX, SAMPLE_CAP, TEST_BLOCK_RE, TEST_SUFFIXES,
    UNSUPPORTED_SUFFIXES, convention_status, read_text,
)
# ---------------------------------------------------------------- 文件发现

def is_maestro_flow(rel_path):
    name = os.path.basename(rel_path)
    if name.endswith(MAESTRO_FLOW_SUFFIXES):
        return True
    parts = rel_path.replace("\\", "/").split("/")
    return (name.endswith((".yaml", ".yml"))
            and any(p in ("maestro", ".maestro") for p in parts[:-1]))


def is_pact_config(rel_path):
    return os.path.basename(rel_path) in PACT_CONFIG_NAMES


def is_test_file(rel_path):
    name = os.path.basename(rel_path)
    if name.startswith("test_") and name.endswith(".py"):
        return True
    if any(name.endswith(suffix) for suffix in TEST_SUFFIXES):
        return True
    return is_maestro_flow(rel_path)


def is_unsupported_format(rel_path):
    return os.path.basename(rel_path).endswith(UNSUPPORTED_SUFFIXES)


def has_generated_marker(path):
    head = read_text(path)[:2000].lower()
    return any(marker.lower() in head for marker in GENERATED_MARKERS)


def has_code(text):
    """R-3：剥掉空行与注释行后是否还有内容（空文件判定，源 "No tests found"）。"""
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith(CONTENT_IGNORE_PREFIX):
            continue
        return True
    return False


def assertion_free(text):
    """R-3：文件内零断言 token（源 "No meaningful tests"）。宽口径，见 ASSERTION_RE。"""
    return not ASSERTION_RE.search(text)


def walk_files(base, exclude_abs=None):
    """递归目录下的全部文件；跳过排除目录与 resolved output_dir。"""
    for dirpath, dirnames, filenames in os.walk(base):
        for d in list(dirnames):
            if d in EXCLUDE_DIRS:
                dirnames.remove(d)
                continue
            if exclude_abs is not None and os.path.normcase(
                    os.path.abspath(os.path.join(dirpath, d))) == exclude_abs:
                dirnames.remove(d)
        for name in filenames:
            yield os.path.join(dirpath, name)


def classify_file(path, root):
    """→ (kind, rel)。kind ∈ test | empty | unsupported | generated | pact | other。

    `empty`（R-3）= 测试文件名下剥注释后无任何内容：没有可审的用例，匹配不到任何规则
    ⇒ 不评分（源 checklist "No tests found"）。
    """
    rel = os.path.relpath(path, root).replace("\\", "/")
    if is_pact_config(rel):
        return "pact", rel
    if has_generated_marker(path):
        return "generated", rel
    if is_test_file(rel):
        return ("test" if has_code(read_text(path)) else "empty"), rel
    if is_unsupported_format(rel):
        return "unsupported", rel
    return "other", rel


def discover_scope(args, root, out):
    """评审集发现。返回 (files, excluded, pact_configs, warnings)。

    --paths 给定时逐条判定（文件 → 分类；目录 → 递归）；缺席时按 suite 口径扫
    project-root（排除 output_dir / VCS / 依赖 / 构建目录）。两个 excluded 理由
    （源"文件不存在"与"解析不出"）在 diy 侧映射为 `out-of-scope`，详见 docstring。
    """
    warnings = []
    files, excluded, pacts = [], [], []
    seen = set()
    show_out = os.path.normcase(os.path.abspath(out))

    def take(path):
        kind, rel = classify_file(path, root)
        if kind == "test" and rel not in seen:
            seen.add(rel)
            files.append(rel)
        elif kind == "pact":
            if rel not in {p for p in pacts}:
                pacts.append(rel)
        elif kind in ("unsupported", "generated"):
            excluded.append({"path": rel, "reason": "格式不支持" if kind == "unsupported"
                             else "自动生成"})
        elif kind == "empty":
            # R-3：空测试文件匹配不到任何规则 ⇒ excluded 不评分（源 "No tests found"）
            if not any(e["path"] == rel for e in excluded):
                excluded.append({"path": rel, "reason": "超出范围"})
                warnings.append(v("EMPTY_FIELD", rel,
                                  "No tests found：空测试文件（无可审内容）→ 不评分"))
        elif kind == "other":
            excluded.append({"path": rel, "reason": "超出范围"})

    if args.paths:
        for raw in args.paths:
            path = raw if os.path.isabs(raw) else os.path.join(root, raw)
            path = os.path.abspath(path)
            if not os.path.exists(path):
                rel = os.path.relpath(path, root).replace("\\", "/")
                excluded.append({"path": rel, "reason": "超出范围"})
                warnings.append(v("MISSING_FILE", rel, "路径不存在：既不评审也不计入语料"))
                continue
            if os.path.isdir(path):
                for found in sorted(walk_files(path, show_out)):
                    take(found)
            else:
                take(path)
    else:
        for found in sorted(walk_files(root, show_out)):
            take(found)
    return files, excluded, pacts, warnings


def build_corpus(review_files, root, out):
    """convention baseline 语料：评审集之外的既有测试文件，上限 40，就近优先。"""
    review_abs = {os.path.normcase(os.path.abspath(os.path.join(root, f)))
                  for f in review_files}
    corpus = []
    for path in walk_files(root, os.path.normcase(os.path.abspath(out))):
        if os.path.normcase(os.path.abspath(path)) in review_abs:
            continue
        rel = os.path.relpath(path, root).replace("\\", "/")
        if is_test_file(rel):
            corpus.append(rel)

    def distance(rel):
        parts = set(os.path.dirname(rel).replace("\\", "/").split("/"))
        best = 0
        for reviewed in review_files:
            rparts = set(os.path.dirname(reviewed).replace("\\", "/").split("/"))
            best = max(best, len(parts ^ rparts))
        return best

    corpus.sort(key=lambda rel: (distance(rel) if review_files else 0, rel))
    return corpus, corpus[:SAMPLE_CAP]


def build_baseline(corpus, sampled, root):
    """5 机械键 {adopted, status}；2 判读键只标 judged_by: llm（裁定 3）。"""
    keys = {}
    for key in MECHANICAL_KEYS:
        patterns = KEY_PATTERNS[key]
        adopted = 0
        for rel in sampled:
            text = read_text(os.path.join(root, rel))
            if any(p.search(text) for p in patterns):
                adopted += 1
        keys[key] = {"adopted": adopted,
                     "status": convention_status(adopted, len(sampled))}
    for key in LLM_JUDGED_KEYS:
        keys[key] = {"judged_by": "llm"}
    return {"corpus_size": len(corpus), "sampled": len(sampled), "keys": keys,
            "baseline_unavailable": len(sampled) == 0}


def mechanical_scan(files, pacts, root):
    """机械集检出（裁定 6）：C1/C2/C3/H1/H5/H6/H7/H8/H9/L4。

    行级行报告命中行号；文件级行（FILE_LEVEL_ROWS）line 为 null。
    """
    found = []
    for rel in files:
        path = os.path.join(root, rel)
        text = read_text(path)
        lines = text.splitlines()
        maestro = is_maestro_flow(rel)
        for idx, line in enumerate(lines, 1):
            if C1_RE.search(line) and not _documented_reason(lines, idx):
                found.append({"row": "C1", "file": rel, "line": idx,
                              "note": "被禁用的用例：%s" % _short(line)})
            if C2_RE.search(line):
                found.append({"row": "C2", "file": rel, "line": idx,
                              "note": "聚焦标记会静默停用同文件其余用例：%s" % _short(line)})
            if any(rx.search(line) for rx in C3_RES):
                found.append({"row": "C3", "file": rel, "line": idx,
                              "note": "恒真断言无法失败：%s" % _short(line)})
            if H1_RE.search(line):
                found.append({"row": "H1", "file": rel, "line": idx,
                              "note": "裸计时器排序步骤：%s" % _short(line)})
            if maestro and H9_RE.search(line):
                found.append({"row": "H9", "file": rel, "line": idx,
                              "note": "flow 内联明文凭据（应走 ${ENV_VAR}）：%s" % _short(line)})
        if len(lines) > H5_MAX_LINES:
            found.append({"row": "H5", "file": rel, "line": None,
                          "note": "文件 %d 行，超过 %d 行上限" % (len(lines), H5_MAX_LINES)})
    found.extend(_pact_scan(pacts, root))
    return found


def _documented_reason(lines, idx):
    """C1 豁免：命中行或上一行有注释说明 / 行内 reason= （源"documented, still-true reason"）。"""
    for lineno in (idx, idx - 1):
        if 1 <= lineno <= len(lines):
            line = lines[lineno - 1]
            for marker in COMMENT_MARKERS:
                pos = line.find(marker)
                if pos >= 0 and line[pos + len(marker):].strip(" */\t") != "":
                    return True
            if C1_REASON_RE.search(line):
                return True
    return False


def _pact_scan(pacts, root):
    """pact vitest 配置行：H6（worker 并行）/ H7 与 L4（pool 隔离，按同对文件数分档）/ H8。

    R-4（源 step-03a §1b 违规发射规则末条）：配置经 `mergeConfig(` / `extends:` 组合时，
    三条必需设置可能落在不可跟随的基础配置里——literal 匹配只能得假阴性 ⇒ 不再冒充
    H6/H7，合一降为 L4 advisory（源逐字分类名 `pact-config-unverifiable`），给出两条
    出路（叶子配置内联 / `// tea:pact-ffi-safe` 标记）；带该标记即视为已验证，不报。
    H8 是显式击穿（本文件内的字面量），不受 mergeConfig 影响，照报。
    """
    found = []
    pacttest_count = 0
    for path in walk_files(root, None):
        if os.path.basename(path).endswith(PACT_FILE_SUFFIX):
            pacttest_count += 1
    for rel in pacts:
        text = read_text(os.path.join(root, rel))
        has_file_parallelism = re.search(r"\bfileParallelism\s*:\s*false\b", text)
        has_forks = (re.search(r"\bpool\s*:\s*['\"]forks['\"]", text)
                     and re.search(r"\bsingleFork\s*:\s*true\b", text))
        if MERGE_CONFIG_RE.search(text) and not (has_file_parallelism and has_forks):
            if FFI_SAFE_MARKER not in text:
                found.append({"row": "L4", "file": rel, "line": None,
                              "note": "pact-config-unverifiable：配置经 mergeConfig / "
                                      "extends 组合，三条必需设置的 literal 匹配不可验证"
                                      "（同对 .pacttest.ts %d 个）——在叶子配置内联 pool / "
                                      "singleFork / fileParallelism，或加 "
                                      "// %s 标记" % (pacttest_count, FFI_SAFE_MARKER)})
        else:
            if not has_file_parallelism:
                found.append({"row": "H6", "file": rel, "line": None,
                              "note": "配置缺 fileParallelism: false（并行 worker 争用共享 pact JSON）"})
            if not has_forks:
                row = "H7" if pacttest_count >= 2 else "L4"
                found.append({"row": row, "file": rel, "line": None,
                              "note": "配置缺 pool: 'forks' / singleFork: true"
                                      "（同对 .pacttest.ts %d 个）" % pacttest_count})
        if any(rx.search(text) for rx in (
                re.compile(r"\bsequence\s*:\s*\{[^}]*\bconcurrent\s*:\s*true"),
                re.compile(r"\bmaxConcurrency\s*:\s*([2-9]|\d{2,})"),
                re.compile(r"\bmaxWorkers\s*:\s*([2-9]|\d{2,})"),
                re.compile(r"\bisolate\s*:\s*false\b"))):
            found.append({"row": "H8", "file": rel, "line": None,
                          "note": "配置显式击穿序列化（concurrent / maxConcurrency / "
                                  "maxWorkers / isolate: false）"})
    return found


def _test_blocks(text):
    """逐个 `it(` / `test(` 块体（括号配平扫描）→ [(行号, 块体)]。"""
    blocks = []
    for match in TEST_BLOCK_RE.finditer(text):
        start, depth, i, quote = match.end() - 1, 0, match.end() - 1, None
        while i < len(text):
            char = text[i]
            if quote is not None:
                if char == "\\":
                    i += 2
                    continue
                if char == quote:
                    quote = None
            elif char in "\"'`":
                quote = char
            elif char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0:
                    break
            i += 1
        blocks.append((text.count("\n", 0, match.start()) + 1, text[start:i + 1]))
    return blocks


def _pact_interaction_warnings(files, root):
    """R-4（源 step-03a §1b）：单 `it()` 内含 >1 `addInteraction()` → advisory。

    该条**无 registry row**（源列在四个 registry 身份之外）⇒ 只出 warning、不给
    severity、不进账本，由 03 步写进 `recommendations` 散文（来源：Rust FFI 非确定性
    丢 interaction）。单块内计数，避免多 it 文件被整片误判。
    """
    warnings = []
    for rel in files:
        if not rel.endswith(PACT_FILE_SUFFIX):
            continue
        for line, body in _test_blocks(read_text(os.path.join(root, rel))):
            count = len(ADD_INTERACTION_RE.findall(body))
            if count > 1:
                warnings.append(v("SET_MISMATCH", "%s:%d" % (rel, line),
                                  "单 it() 内 %d 个 addInteraction()：Rust FFI 会非确定性"
                                  "丢 interaction——一 interaction 一 it()（注册表无此行，"
                                  "写进 recommendations 散文）" % count))
    return warnings


def _content_warnings(files, root):
    """R-3：极简测试文件（有内容但零断言，源 "No meaningful tests"）→ warning。

    空文件已在发现面归 excluded（本表只收有内容的）；判定为**提示**不是计分：命中文件的
    C4 条目（CRITICAL）由 03 步判定产出，分数随账本反映内容缺失。
    """
    warnings = []
    for rel in files:
        if assertion_free(read_text(os.path.join(root, rel))):
            warnings.append(v("EMPTY_FIELD", rel,
                              "No meaningful tests：文件内零断言——按 C4 成条目"
                              "（note 用该锚串），分数须反映内容缺失"))
    return warnings


def _short(text, limit=60):
    text = " ".join(str(text).split())
    return text if len(text) <= limit else text[:limit - 1] + "…"


def pact_config_paths(root, out, pacts):
    """pact vitest 配置发现：显式进面者优先，另扫 project-root（排除 output_dir 等）。"""
    found = list(pacts)
    for path in walk_files(root, os.path.normcase(os.path.abspath(out))):
        rel = os.path.relpath(path, root).replace("\\", "/")
        if is_pact_config(rel) and rel not in found:
            found.append(rel)
    return sorted(found)
