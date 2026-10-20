# -*- coding: utf-8 -*-
"""diyc 共享层基件：时间/ID/YAML IO/配置解析/违规构造（契约 §5）。"""

import io
import os
import re
import sys
import tempfile
from datetime import date, datetime

import yaml

# 实例名白名单（与 help/viewer/runner/design 同源同值）：字母数字开头和结尾，中间可含 . _ -。
# 末字符禁点：Windows 目录名尾点被静默折叠（b. ≡ b），会破坏实例隔离；fullmatch 避免 $ 放行尾换行
INSTANCE_RE = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9_-])?")

DEFAULT_OUTPUT_DIR = "diy-output"

# ID 正则常量（契约 §5；trace 解析与各文档 ID 校验共用）。
# lookbehind 拒绝 alnum 前导：防止 NFR-1 中的 "FR-1"、XS-1 中的 "S-1" 被误当独立 ID
STORY_RE = re.compile(r"(?<![A-Za-z0-9])S-\d+")
AC_RE = re.compile(r"(?<![A-Za-z0-9])AC-\d+(?:\.\d+)*")
TC_RE = re.compile(r"(?<![A-Za-z0-9])TC-\d+(?:\.\d+)*")
FR_RE = re.compile(r"(?<![A-Za-z0-9])FR-\d+(?:\.\d+)*")
NFR_RE = re.compile(r"(?<![A-Za-z0-9])NFR-\d+")
DEC_RE = re.compile(r"(?<![A-Za-z0-9])D-\d+")
EPIC_RE = re.compile(r"(?<![A-Za-z0-9])E-\d+")
BUG_RE = re.compile(r"(?<![A-Za-z0-9])BUG-\d+")

# 未解析令牌检查（{...} 白名单外一律 TOKEN_UNRESOLVED；cis/wds 四技能共用）。
TOKEN_WHITELIST = ("{project-root}", "{output_dir}")
TOKEN_RE = re.compile(r"\{[A-Za-z0-9_\-]+\}")

# ---------------------------------------------------------------- 时间与 ID

def today() -> str:
    """"YYYY-MM-DD（本地时区）。"""
    return date.today().isoformat()


def stamp() -> str:
    """YYYY-MM-DD HH:MM（本地时区）。"""
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def now() -> str:
    """YYYY-MM-DD HH:MM:SS（本地时区）——created/updated 秒级真值（v4 批 3）。"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def stamp_file() -> str:
    """YYYYMMDD-HHMMSS（本地时区）——文件名安全时间戳（无空格冒号·可拼路径）。"""
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def id_sort_key(value):
    """排序键零件：字符串切成数字段/文字段的比较元组（数字感知；id_sort 与条目直排共用）。"""
    parts = re.split(r"(\d+)", str(value))
    return [(1, int(p)) if p.isdigit() else (0, p) for p in parts]


def id_sort(ids) -> list:
    """数字感知排序：S-2 < S-10，TC-5.1.2 < TC-5.1.10。"""
    return sorted(ids, key=id_sort_key)


def is_int(value):
    """整数判定（布尔不得充当整数：true 不是 1）。"""
    return isinstance(value, int) and not isinstance(value, bool)


def nonempty(value):
    """非空判定（逐型版）：None/空白串/空 list·dict·tuple → False；其余 True。
    空容器不得靠 str 化误判为有货（`str([])` = `"[]"`）。"""
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip() != ""
    if isinstance(value, (list, dict, tuple)):
        return len(value) > 0
    return True


def count_by(records, key, sub=None):
    """按 key 计数；非 dict / 空值跳过；值统一 str；sub 在场且值为 dict 时取子键。"""
    counts = {}
    for record in records:
        if not isinstance(record, dict):
            continue
        value = record.get(key)
        if sub is not None and isinstance(value, dict):
            value = value.get(sub)
        if nonempty(value):
            counts[str(value)] = counts.get(str(value), 0) + 1
    return counts


def count_items(records, key):
    """累加 records 各 dict 键 key 下列表长度之和；非 dict / 值非列表跳过。"""
    total = 0
    for record in records:
        if isinstance(record, dict) and isinstance(record.get(key), list):
            total += len(record[key])
    return total


def walk_strings(node, path):
    """递归产 (路径, 字符串值)：键只进路径不进文字——字数统计/标记扫描只碰值。
    根 path 由调用点自传（不关心定位时传 ''）。"""
    if isinstance(node, str):
        yield (path, node)
    elif isinstance(node, dict):
        for key, value in node.items():
            for item in walk_strings(value, "%s.%s" % (path, key)):
                yield item
    elif isinstance(node, list):
        for index, value in enumerate(node):
            for item in walk_strings(value, "%s[%d]" % (path, index)):
                yield item


def check_tokens(node, where):
    """未解析 `{...}` 令牌：白名单外一律 TOKEN_UNRESOLVED（沿用 B6 已批码）。"""
    violations = []
    for path, text in walk_strings(node, where):
        for token in TOKEN_RE.findall(text):
            if token in TOKEN_WHITELIST:
                continue
            violations.append(v("TOKEN_UNRESOLVED", path,
                                "未解析令牌 %s（白名单仅 %s）"
                                % (token, " / ".join(TOKEN_WHITELIST))))
    return violations


def diyc_script_path():
    """diyc.py 路径：与 diyc_lib 同目录（源码与安装布局同构）。"""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "diyc.py")


def methods_path(script_file, methods_file):
    """技能自带库文件路径：脚本目录的上一级（`scripts/` 的上一级），两种安装布局同构。

    `script_file` 传调用方 `__file__`（方法库在各技能目录，非 diyc_lib 目录）。
    """
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(script_file))),
                        methods_file)


def next_record_id(records, id_re, prefix):
    """下一个 `<prefix>-###`：现有最大序号 + 1（三位零填充）。空号不复用、不重号。"""
    max_no = 0
    for rec in records:
        if isinstance(rec, dict) and rec.get("id") is not None \
                and str(rec["id"]).strip() != "":
            m = id_re.fullmatch(str(rec["id"]).strip())
            if m:
                max_no = max(max_no, int(m.group(1)))
    return "%s-%03d" % (prefix, max_no + 1)

# ---------------------------------------------------------------- YAML IO

class DuplicateKeyError(yaml.YAMLError):
    """YAML 重复键（违规码 DUPLICATE_KEY；性质区分于解析失败 UNPARSABLE_YAML——重复键≠解析失败，
    底单 :364 ⑤）。继承 YAMLError：既有 except YAMLError 调用点零改动兼容（未接线处按解析失败
    处理、消息含键位）；需区分的调用点先 except DuplicateKeyError。"""

    def __init__(self, key, mark=None):
        self.key = key
        self.mark = mark
        loc = "（line %d）" % (mark.line + 1) if mark is not None else ""
        super().__init__("%r%s" % (key, loc))


class _DupKeySafeLoader(yaml.SafeLoader):
    """SafeLoader 变体：映射构造遇重复键抛 DuplicateKeyError（PyYAML 默认后值静默覆盖——
    实测丢数据的根因，R4=B 全量直连点统一走此加载器）。"""


def _construct_mapping_dup_check(loader, node, deep=False):
    # 只查本层字面键；`<<` merge 键本体跳过（合并键与显式键同名是合法覆盖，flatten 后并存
    # 若查会误报——先查后 flatten 即天然规避）
    seen = []
    for key_node, _ in node.value:
        if key_node.tag == "tag:yaml.org,2002:merge":
            continue
        key = loader.construct_object(key_node, deep=deep)
        if key in seen:
            raise DuplicateKeyError(key, key_node.start_mark)
        seen.append(key)
    return yaml.constructor.SafeConstructor.construct_mapping(loader, node, deep=deep)


_DupKeySafeLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping_dup_check)


def load_yaml_text(text):
    """解析 YAML 文本（含重复键检测）；空/纯注释 → None（同 safe_load 语义，调用方自行 or {}）。
    重复键 raise DuplicateKeyError；语法错 raise yaml.YAMLError。"""
    return yaml.load(text, Loader=_DupKeySafeLoader)


def load_yaml(path):
    """读取 YAML（直接返回数据·含重复键检测）；文件缺失 raise FileNotFoundError（调用方必须
    先处置）；解析错 raise yaml.YAMLError；重复键 raise DuplicateKeyError；空 → {}。"""
    with io.open(path, "r", encoding="utf-8") as f:
        return yaml.load(f, Loader=_DupKeySafeLoader) or {}


def normalize_keys(node):
    """YAML 1.1 布尔键归一：`no:`/`yes:` 被解析为 False/True 键——归回 'no'/'yes'，
    防编号键读到 false、写回污染产物（递归 dict/list；其余原样）。"""
    if isinstance(node, dict):
        out = {}
        for key, value in node.items():
            if isinstance(key, bool):
                key = "no" if key is False else "yes"
            out[key] = normalize_keys(value)
        return out
    if isinstance(node, list):
        return [normalize_keys(item) for item in node]
    return node


def load_yaml_checked(path):
    """读 YAML（含重复键检测+布尔键归一）→ (data, code, msg)。
    缺席 → (None, None, None)；空 → ({}, None, None)；正常 → (doc, None, None)；
    重复键 → (None, "DUPLICATE_KEY", 原因一行)；损坏/不可读 → (None, "UNPARSABLE_YAML", 原因)。"""
    if not os.path.isfile(path):
        return None, None, None
    try:
        with io.open(path, "r", encoding="utf-8") as f:
            return normalize_keys(yaml.load(f, Loader=_DupKeySafeLoader) or {}), None, None
    except DuplicateKeyError as e:
        return None, "DUPLICATE_KEY", str(e)
    except (yaml.YAMLError, OSError, UnicodeDecodeError) as e:
        return None, "UNPARSABLE_YAML", str(e)


def load_yaml_safe(path):
    """读 YAML（不抛版）：返回 (data, err)。缺席 → (None, None)；空文件 → ({}, None)；
    损坏/不可读/重复键 → (None, 原因一行)。载入即做布尔键归一（normalize_keys）。
    错误消息为裸原因——显示上下文由调用点自拼；需区分 DUPLICATE_KEY 的调用方改用
    load_yaml_checked（check 违规码接线面）。"""
    data, _code, msg = load_yaml_checked(path)
    if data is None and msg is None:
        return None, None
    return data, msg


def save_yaml_atomic(path, data) -> None:
    """写前建目录 + 同目录随机 tmp + os.replace 原子替换（并发安全·不撞名）。

    写回纪律（契约 §3）：全文 load → 就地改 → safe_dump(allow_unicode,
    sort_keys=False, default_flow_style=False)；注释不保留；换行强制 LF
    （跨平台输出一致·2026-10-16 组5 裁定 A）。
    失败（权限/路径被占用/磁盘满）清理 tmp 后原样抛出——不留残骸、不吞异常；
    顶层由 diyc.py main() 转 INTERNAL_ERROR 回执（V 复验 F-1）。
    """
    folder = os.path.dirname(os.path.abspath(path))
    if folder and not os.path.isdir(folder):
        os.makedirs(folder, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=folder, prefix=".diyc-", suffix=".tmp")
    os.close(fd)
    try:
        with io.open(tmp, "w", encoding="utf-8", newline="\n") as f:
            yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False,
                           default_flow_style=False)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise


def write_atomic(path, text) -> None:
    """写前建目录 + 同目录随机 tmp + flush/fsync + os.replace 原子替换
    （并发安全不撞名·断电不留半条文件·换行强制 LF）。
    失败清理 tmp 后原样抛出——不留残骸、不吞异常。"""
    folder = os.path.dirname(os.path.abspath(path))
    if folder and not os.path.isdir(folder):
        os.makedirs(folder, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=folder, prefix=".diyc-", suffix=".tmp")
    try:
        with io.open(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except BaseException:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise

# ---------------------------------------------------------------- 配置与实例解析

def _output_dir_from_cfg(cfg, warnings) -> str:
    """从配置取 output_dir；形状/类型/空值异常一律降级默认并记 warning（help.py 语义）。"""
    default = DEFAULT_OUTPUT_DIR
    paths = cfg.get("paths")
    if paths is None:
        return default
    if not isinstance(paths, dict):
        warnings.append("diy-coder.yaml: paths 形状异常（应为映射），降级默认 %s" % default)
        return default
    value = paths.get("output_dir", default)
    if not isinstance(value, str):
        warnings.append("diy-coder.yaml: output_dir 不是字符串，降级默认 %s" % default)
        return default
    if not value.strip():
        warnings.append("diy-coder.yaml: output_dir 为空值，降级默认 %s" % default)
        return default
    return value


def project_name(project_root):
    """产物 `project.name`：diy-coder.yaml 的 `project.name`；不可用 → 项目目录名 + warning。"""
    cfg, err = load_yaml_safe(os.path.join(project_root, "diy-coder.yaml"))
    if isinstance(cfg, dict):
        project = cfg.get("project")
        if isinstance(project, dict) and nonempty(project.get("name")):
            return str(project["name"]), None
    note = "diy-coder.yaml project.name 不可用（%s），回落项目目录名" % (err or "缺该键")
    return os.path.basename(os.path.abspath(project_root)), v("MISSING_FILE", "diy-coder.yaml", note)


def read_config(project_root) -> tuple:
    """读 diy-coder.yaml：返回 (cfg, warnings)。纯函数不写 stderr；缺失 → ({}, [])。"""
    cfg_path = os.path.join(project_root, "diy-coder.yaml")
    if not os.path.isfile(cfg_path):
        return {}, []
    warnings = []
    try:
        with io.open(cfg_path, "r", encoding="utf-8") as f:
            cfg = yaml.load(f, Loader=_DupKeySafeLoader)
    except yaml.YAMLError as e:
        return {}, ["diy-coder.yaml: %s" % e]
    if not isinstance(cfg, dict):
        return {}, warnings
    _output_dir_from_cfg(cfg, warnings)
    return cfg, warnings


def resolve_output_dir(project_root, instance) -> str:
    """解析本次运行唯一读写根：<project_root>/<paths.output_dir>[/<instance>]，normpath。

    仅 None（旗标缺席）表示主线；显式空串不回落主线，按非法实例名拒绝 → stderr 一行中文 +
    exit 1（viewer R16-1 严格语义；契约 §3/§5 裁定）。其余非法实例名同此处置。
    """
    cfg, warnings = read_config(project_root)
    for w in warnings:
        sys.stderr.write("WARN %s\n" % w)
    output_dir = _output_dir_from_cfg(cfg, [])
    if instance is not None:
        if not INSTANCE_RE.fullmatch(instance):
            sys.stderr.write("非法实例名: %s（字母数字开头和结尾，中间可含 . _ -）\n" % instance)
            sys.exit(1)
        output_dir = os.path.join(output_dir, instance)
    return os.path.normpath(os.path.join(project_root, output_dir))


def args_output_dir(args):
    """回执里的 output_dir 统一正斜杠（对齐 batch3-contract §3 的 where 口径）。

    与 resolve_output_dir 同名异物各司其职：本函数吃 CLI --output-dir 旗标（缺省回落
    <project_root>/diy-output），不读配置、无 instance 概念——analyze/reverse 回执面。
    """
    raw = args.output_dir or os.path.join(args.project_root, "diy-output")
    return os.path.normpath(raw).replace(os.sep, "/")

# ---------------------------------------------------------------- 违规构造

def v(code, where, msg) -> dict:
    """违规构造；where 统一正斜杠（契约 §3）。"""
    return {"code": code, "where": str(where).replace("\\", "/"), "msg": msg}


def enum_check(value, allowed, where, label, out):
    """枚举检查：非法 → ENUM_INVALID。"""
    if isinstance(value, str) and value.strip() in allowed:
        return value.strip()
    out.append(v("ENUM_INVALID", where, "%s 越界：%s（合法集 %s）"
                 % (label, value if nonempty(value) else "空", "|".join(allowed))))
    return None


def require(node, keys, where, out):
    """必填键非空检查。node 不是映射时只报一条。"""
    if not isinstance(node, dict):
        out.append(v("EMPTY_FIELD", where, "须为映射（键表 %s）" % " / ".join(keys)))
        return
    for key in keys:
        if not nonempty(node.get(key)):
            out.append(v("EMPTY_FIELD", "%s.%s" % (where, key), "必填键 %s 为空" % key))
