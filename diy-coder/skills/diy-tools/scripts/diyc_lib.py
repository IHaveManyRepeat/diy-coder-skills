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
"""
# trace: S-6 AC-6.2 S-16 AC-16.1

import io
import json
import os
import re
import sys
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

# 文档名 → 文件名（契约 §6 形状以 diy-output 实物为准）
DOC_FILES = {
    "prd": "prd.yaml",
    "architecture": "architecture.yaml",
    "openapi": "openapi.yaml",
    "epics": "epics.yaml",
    "stories": "stories.yaml",
    "test-plan": "test-plan.yaml",
    "sprint": "sprint.yaml",
    "design": "design.yaml",
    "bug-log": "bug-log.yaml",
}


# ---------------------------------------------------------------- 时间与 ID

def today() -> str:
    """"YYYY-MM-DD（本地时区）。"""
    return date.today().isoformat()


def stamp() -> str:
    """YYYY-MM-DD HH:MM（本地时区）。"""
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def _id_sort_key(value):
    parts = re.split(r"(\d+)", str(value))
    return [(1, int(p)) if p.isdigit() else (0, p) for p in parts]


def id_sort(ids) -> list:
    """数字感知排序：S-2 < S-10，TC-5.1.2 < TC-5.1.10。"""
    return sorted(ids, key=_id_sort_key)


# ---------------------------------------------------------------- YAML IO

def load_yaml(path):
    """读取 YAML；缺失/空 → {}；解析错 raise yaml.YAMLError（调用方决定处置）。"""
    if not os.path.isfile(path):
        return {}
    with io.open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def safe_load_yaml(path):
    """不抛版本：返回 (data, err)。缺失/空 → ({}, None)；解析错 → (None, 错误一行中文)。"""
    if not os.path.isfile(path):
        return {}, None
    try:
        with io.open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        return None, "YAML 解析失败: %s" % e
    return (data if data is not None else {}), None


def save_yaml_atomic(path, data) -> None:
    """同目录 tmp + os.replace 原子替换（对齐 runner.save_sprint 先例）。

    写回纪律（契约 §3）：全文 load → 就地改 → safe_dump(allow_unicode,
    sort_keys=False, default_flow_style=False)；注释不保留。
    """
    tmp = path + ".tmp"
    with io.open(tmp, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False,
                       default_flow_style=False)
    os.replace(tmp, path)


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


def read_config(project_root) -> tuple:
    """读 diy-coder.yaml：返回 (cfg, warnings)。纯函数不写 stderr；缺失 → ({}, [])。"""
    cfg_path = os.path.join(project_root, "diy-coder.yaml")
    if not os.path.isfile(cfg_path):
        return {}, []
    warnings = []
    try:
        with io.open(cfg_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
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


# ---------------------------------------------------------------- 违规与回执

def v(code, where, msg) -> dict:
    """违规构造；where 统一正斜杠（契约 §3）。"""
    return {"code": code, "where": str(where).replace("\\", "/"), "msg": msg}


def receipt(command, ok, **fields) -> dict:
    """回执基础构造；公共键（project_root/output_dir/instance/violations/warnings/counts）
    由 diyc.py 收口补齐（契约 §2）。"""
    r = {"ok": bool(ok), "command": command}
    r.update(fields)
    return r


def _summary_line(result) -> str:
    n = len(result.get("violations") or [])
    m = len(result.get("warnings") or [])
    if result.get("ok"):
        base = "diyc %s：通过" % result.get("command", "?")
    else:
        base = "diyc %s：%d 项违规（exit 1）" % (result.get("command", "?"), n)
    if m:
        base += "，%d 项警告" % m
    return base


def emit(result, as_json, human_lines_fn=None) -> int:
    """打印回执并返回 exit code（ok → 0 否则 1）。

    - as_json：单行 JSON（ensure_ascii=False）。
    - 人类态：human_lines_fn(result) 提供附加信息行（可选，如 output_dir / 层清单），
      emit 之后统一渲染违规行 `CODE where: msg`、WARN 行与汇总行。
    """
    if as_json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        lines = list(human_lines_fn(result) or []) if human_lines_fn is not None else []
        lines += ["%s %s: %s" % (x.get("code"), x.get("where"), x.get("msg"))
                  for x in result.get("violations") or []]
        lines += ["WARN %s" % w for w in result.get("warnings") or []]
        lines.append(_summary_line(result))
        for line in lines:
            print(line)
    return 0 if result.get("ok") else 1


# ---------------------------------------------------------------- 产物索引

def _list_of_dicts(container, key) -> list:
    if not isinstance(container, dict):
        return []
    items = container.get(key)
    if not isinstance(items, list):
        return []
    return [i for i in items if isinstance(i, dict)]


def _ac_ids(tc_entry) -> list:
    """TC 条目的 ac 字段：str 或 list 均接受（形状以产物为准，容错读）。"""
    ac = tc_entry.get("ac")
    if isinstance(ac, str):
        return [ac]
    if isinstance(ac, list):
        return [a for a in ac if isinstance(a, str)]
    return []


class Docs:
    """产物索引层：全部跨文档核对的唯一入口（契约 §5）。解析失败经 yaml_err 可见。"""

    def __init__(self, project_root, output_dir):
        self.project_root = project_root
        self.output_dir = output_dir
        self._cache = {}
        self._errs = {}

    # -- 原始文档 ----------------------------------------------------------

    def doc(self, name):
        """name: prd/architecture/openapi/epics/stories/test-plan/sprint/design/bug-log。

        缺失 → None；解析失败/顶层非映射 → None（错误见 yaml_err）；空文件 → {}。
        """
        if name in self._cache:
            return self._cache[name]
        fname = DOC_FILES[name]
        path = os.path.join(self.output_dir, fname)
        data = None
        if os.path.isfile(path):
            try:
                with io.open(path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
            except yaml.YAMLError as e:
                self._errs[name] = "YAML 解析失败: %s" % e
            else:
                if data is None:
                    data = {}
                elif not isinstance(data, dict):
                    self._errs[name] = "顶层不是映射（实际 %s）" % type(data).__name__
                    data = None
        self._cache[name] = data
        return data

    def yaml_err(self, name):
        """该文档的解析错误一行中文；无错 → None。"""
        self.doc(name)
        return self._errs.get(name)

    # -- 索引 --------------------------------------------------------------

    def stories(self) -> dict:
        """S-x → story 条目。"""
        d = self.doc("stories") or {}
        return {s["id"]: s for s in _list_of_dicts(d, "stories")
                if isinstance(s.get("id"), str)}

    def acs(self) -> dict:
        """AC-x.y → ac 条目（注入 _story）。"""
        out = {}
        for sid, s in self.stories().items():
            for a in _list_of_dicts(s, "acceptance_criteria"):
                if isinstance(a.get("id"), str):
                    entry = dict(a)
                    entry["_story"] = sid
                    out[a["id"]] = entry
        return out

    def tcs(self) -> dict:
        """TC-x.y.z → tc 条目（注入 _story，经 ac 反查；解析不到为 None）。"""
        d = self.doc("test-plan") or {}
        acs = self.acs()
        out = {}
        for t in _list_of_dicts(d, "test_cases"):
            if not isinstance(t.get("id"), str):
                continue
            entry = dict(t)
            story = None
            for ac_id in _ac_ids(t):
                hit = acs.get(ac_id)
                if hit is not None:
                    story = hit.get("_story")
                    break
            entry["_story"] = story
            out[t["id"]] = entry
        return out

    def gaps(self) -> dict:
        """AC → coverage_gaps 条目（同一 AC 多条取首条）。"""
        d = self.doc("test-plan") or {}
        out = {}
        for g in _list_of_dicts(d, "coverage_gaps"):
            ac = g.get("ac")
            if isinstance(ac, list):
                ac = ac[0] if ac else None
            if isinstance(ac, str) and ac not in out:
                out[ac] = g
        return out

    def frs(self) -> dict:
        """FR-x.y → requirement（注入 _feature）。"""
        d = self.doc("prd") or {}
        out = {}
        for f in _list_of_dicts(d, "features"):
            for r in _list_of_dicts(f, "requirements"):
                if isinstance(r.get("id"), str):
                    entry = dict(r)
                    entry["_feature"] = f.get("id")
                    out[r["id"]] = entry
        return out

    def nfrs(self) -> dict:
        """NFR-x → 条目。"""
        d = self.doc("prd") or {}
        return {n["id"]: n for n in _list_of_dicts(d, "nfrs")
                if isinstance(n.get("id"), str)}

    def decisions(self) -> dict:
        """D-x → 架构决策条目。"""
        d = self.doc("architecture") or {}
        return {x["id"]: x for x in _list_of_dicts(d, "decisions")
                if isinstance(x.get("id"), str)}

    def epics(self) -> dict:
        """E-x → epic 条目。"""
        d = self.doc("epics") or {}
        return {x["id"]: x for x in _list_of_dicts(d, "epics")
                if isinstance(x.get("id"), str)}

    def tasks(self) -> dict:
        """S-x → sprint 任务条目。"""
        d = self.doc("sprint") or {}
        return {t["story"]: t for t in _list_of_dicts(d, "tasks")
                if isinstance(t.get("story"), str)}

    # -- 派生（TDD 门唯一入口） --------------------------------------------

    def tcs_for_story(self, story) -> list:
        """该 story 全部 AC 绑定的 TC id（数字感知排序）。"""
        acs = self.acs()
        wanted = {a_id for a_id, a in acs.items() if a.get("_story") == story}
        bound = [t_id for t_id, t in self.tcs().items()
                 if wanted.intersection(_ac_ids(t))]
        return id_sort(bound)

    def story_covered(self, story) -> tuple:
        """(covered, 缺覆盖 AC 列表)——TDD 门（PENDING_UNCOVERED）与 reconcile 唯一定义源。

        缺覆盖 AC = 无任何 TC 绑定，且（无 coverage_gaps 条目 或 decision == pending）；
        gap decision 为 waived / accept-gap → 豁免。story 不存在视为无缺覆盖
        （存在性由调用方单独校验）。
        """
        entry = self.stories().get(story)
        if not entry:
            return True, []
        tcs = self.tcs()
        bound_acs = set()
        for t in tcs.values():
            bound_acs.update(_ac_ids(t))
        gaps = self.gaps()
        missing = []
        for a in _list_of_dicts(entry, "acceptance_criteria"):
            ac_id = a.get("id")
            if not isinstance(ac_id, str):
                continue
            if ac_id in bound_acs:
                continue
            g = gaps.get(ac_id)
            if isinstance(g, dict) and g.get("decision") in ("waived", "accept-gap"):
                continue
            missing.append(ac_id)
        return (not missing), missing
