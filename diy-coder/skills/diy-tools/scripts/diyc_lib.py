# -*- coding: utf-8 -*-
"""diyc 共享层：实例解析 / YAML 原子 IO / 回执与渲染 / 产物索引（契约 §5）。

分工：本模块只提供机制，不含检查规则（diyc_check）与写回动作（diyc_writeback）；
CLI 定义与统一收口在 diyc.py。

- 实例解析语义沿 diy-help/scripts/help.py 的 resolve_output_dir（批次 1 加固版）：
  白名单 fullmatch 拒注入、配置损坏/形状异常降级默认 + warning、非法实例名 stderr + exit 1。
  唯一差异（契约 §3/§5 裁定）：仅 None 表示主线；显式空串按非法实例名拒绝（对齐 viewer
  R16-1 的 is None 严格语义），不复刻 help.py 的 falsy 回落——写回命令下空串常源于脚本
  未设变量，静默落到主线是高危失败模式；help.py 残留留后续批次。
- 原子写对齐 runner.py save_sprint 先例（同目录 tmp + os.replace，注释不保留）。
- Docs 是所有跨文档核对的唯一索引入口；story_covered 是 TDD 门（PENDING_UNCOVERED）
  与 reconcile 复用的唯一定义源（契约 §4.2）。
- baseline（已知遗留台账，D1-D4 用户裁定 2026-09-13）：{output_dir}/diyc-baseline.yaml，
  命中 (code, where) 降级 known、悬空条目 BASELINE_STALE、文件损坏/条目非法整份不生效；
  仅审计命令（check/trace/static）消费（写回拒绝被豁免会静默放行，属高危失败模式）；
  写入仅经 baseline_add（D3：仅用户裁定后调用，加载校验通过才追加）。
"""
# trace: S-6 AC-6.2 S-16 AC-16.1

import os

from diyc_lib_base import (
    AC_RE, BUG_RE, DEC_RE, DEFAULT_OUTPUT_DIR, EPIC_RE, FR_RE, INSTANCE_RE,
    NFR_RE, STORY_RE, TC_RE, TOKEN_RE, TOKEN_WHITELIST, args_output_dir,
    check_tokens, count_by, count_items, diyc_script_path, enum_check,
    id_sort, id_sort_key, is_int, load_yaml, load_yaml_safe, methods_path,
    next_record_id, normalize_keys, nonempty, now, project_name, read_config,
    require, resolve_output_dir, save_yaml_atomic, stamp, stamp_file, today,
    v, walk_strings, write_atomic
)
from diyc_lib_docs import DOC_FILES, Docs, _ac_ids, items  # noqa: E402
from diyc_lib_report import (
    AUDIT_COMMANDS, BASELINE_FILE, apply_baseline, baseline_add, emit, emit_via,
    load_baseline, receipt, receipt_base, read_sessions, run_tool, violation_line,
    warn_line,
)

# ---------------------------------------------------------------- 路径显示

def display_path(path, root) -> str:
    """回执 where 显示口径：正斜杠 + 相对 root；越界/跨盘回退绝对路径。"""
    try:
        rel = os.path.relpath(path, root)
    except ValueError:
        rel = os.path.abspath(path)
    if rel.startswith(".."):
        return os.path.abspath(path).replace("\\", "/")
    return rel.replace("\\", "/")


def rel_path(root, path) -> str:
    """相对路径（正斜杠归一·无越界回退）。"""
    return os.path.relpath(path, root).replace("\\", "/")


# ---------------------------------------------------------------- 文本工具

def short(text, limit=72) -> str:
    """文本压缩截断：空白折叠为单空格，超长截断加省略号。"""
    text = " ".join(str(text).split())
    return text if len(text) <= limit else text[:limit - 1] + "…"


def tail(text, limit=20) -> list:
    """取末尾非空行。"""
    lines = [ln for ln in (text or "").splitlines() if ln.strip()]
    return lines[-limit:]


# ---------------------------------------------------------------- 项目探测（e2e×author）

NODE_MANIFESTS = ("package.json",)
PY_MANIFESTS = ("pyproject.toml", "setup.py", "requirements.txt", "requirements-dev.txt",
                "requirements-test.txt", "Pipfile")
JAVA_MANIFESTS = ("pom.xml", "build.gradle", "build.gradle.kts")
TEST_FILE_SUFFIXES = (".spec.ts", ".spec.tsx", ".spec.js", ".spec.jsx", ".spec.py",
                      ".test.ts", ".test.tsx", ".test.js", ".test.jsx")


def builtin_framework(root):
    """内建测试链（无需第三方框架）：Cargo / Go / JVM 构建。"""
    table = (("Cargo.toml", "cargo test", "rust"),
             ("go.mod", "go test", "go"),
             ("pom.xml", "maven-surefire", "java"),
             ("build.gradle", "gradle test", "java"),
             ("build.gradle.kts", "gradle test", "java"))
    for rel, name, ptype in table:
        if os.path.isfile(os.path.join(root, rel)):
            return {"name": name, "detected_from": rel}, ptype
    return None, None


def detect_project_type(root):
    """project_type 判定（清单存在性，顺序即优先级）。返回 (type, 命中清单)。"""
    table = (("node", NODE_MANIFESTS), ("python", PY_MANIFESTS), ("rust", ("Cargo.toml",)),
             ("go", ("go.mod",)), ("java", JAVA_MANIFESTS), ("ruby", ("Gemfile",)),
             ("php", ("composer.json",)))
    for ptype, manifests in table:
        for rel in manifests:
            if os.path.isfile(os.path.join(root, rel)):
                return ptype, rel
    return "unknown", None


def is_test_file(name):
    """测试文件名判定（e2e/author 主群版；test_review 变体留本地）。"""
    lower = name.lower()
    if any(lower.endswith(s) for s in TEST_FILE_SUFFIXES):
        return True
    if lower.startswith("test_") and lower.endswith(".py"):
        return True
    if lower.endswith(("_test.py", "_test.go", "_test.rb")):
        return True
    return name.endswith(("Test.java", "Test.php"))
