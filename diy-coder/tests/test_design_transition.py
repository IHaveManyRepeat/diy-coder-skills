# -*- coding: utf-8 -*-
"""diy-design 引擎 transition 命令 + .prev 快照 / ID 稳定对账测试（C·3a 段1·W2）。

覆盖任务书 §4.2（transition 冻结契约：9 条合法边 + 非法边 + 错误码 + 原子写）·
§4.3（.prev 快照 + --previous ID 对账，失败分支 ID_UNSTABLE / MISSING_FILE / UNPARSABLE_YAML）。夹具为合成 design.yaml
+ 原型 HTML；一律走子进程调引擎（与 test_design.py 同法，验真回执而非函数返回值）。
"""
import datetime
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
DESIGN_PY = os.path.join(HERE, "..", "skills", "diy-design", "scripts", "design.py")
NL = chr(10)

GOOD_HTML = NL.join([
    "<!DOCTYPE html>",
    '<html lang="zh-CN">',
    "<head>",
    '<meta charset="utf-8">',
    "<title>待办列表</title>",
    "</head>",
    "<body>",
    "<h1>待办列表</h1>",
    "<button>新增</button>",
    "</body>",
    "</html>",
])

# 九条合法边（冻结表）；破坏性边（裁定 14 展开口径）= 任一条 → 已移除 与 已批准 → 结构稿中
LEGAL_EDGES = (
    ("未开始", "结构稿中"),
    ("结构稿中", "待验收"),
    ("结构稿中", "已移除"),
    ("待验收", "已批准"),
    ("待验收", "结构稿中"),
    ("待验收", "已移除"),
    ("已批准", "结构稿中"),
    ("已批准", "已移除"),
    ("已移除", "结构稿中"),
)
DESTRUCTIVE_EDGES = frozenset((("已批准", "结构稿中"), ("结构稿中", "已移除"),
                               ("待验收", "已移除"), ("已批准", "已移除")))

FOUR_STATES = NL.join([
    "  states:",
    "  - name: 悬停",
    "    signals: [图标, 动效]",
    "  - name: 空态",
    "    signals: [文字]",
    "  - name: 加载中",
    "    signals: [图标, 动效]",
    "  - name: 错误",
    "    signals: [图标, 文字]",
])


def design_text(status=None, with_prototype=True, with_states=True, removed_reason=None,
                page_id="P-1"):
    """合成 design.yaml：status=None 表示不写该键（旧稿形态）。"""
    lines = [
        "project:",
        "  name: mini",
        "  status: 草稿",
        "  updated: 2026-01-01",
        "direction: 瑞士编辑风——大字阶对比、留白节奏、单强调色",
        "frontend_framework: html",
        "tokens:",
        "  color:",
        "    bg: '#ffffff'",
        "    surface: '#f5f5f2'",
        "    text: '#1a1a1a'",
        "    text_muted: '#5a5a5a'",
        "    accent: '#0a5c8c'",
        "    accent_text: '#ffffff'",
        "  spacing:",
        "    unit: 4px",
        "    scale: [4px, 8px, 16px, 24px, 48px]",
        "  typography:",
        "    family_base: Inter",
        "    scale: [1rem, 1.25rem, 2rem]",
        "pages:",
        "- id: %s" % page_id,
        "  name: 待办列表",
        "  route: /todos",
    ]
    if status is not None:
        lines.append("  status: %s" % status)
    if removed_reason is not None:
        lines.append("  removed_reason: %s" % removed_reason)
    if with_states:
        lines.append(FOUR_STATES)
    if with_prototype:
        lines.append("  prototype: prototypes/P-1.html")
    lines.append("revisions: []")
    return NL.join(lines) + NL


def duplicate_page_text():
    """两个同 ID 页（ID 是唯一引用键，重复即拒）。"""
    return NL.join([
        "project: {name: mini, status: 草稿, updated: 2026-01-01}",
        "direction: 瑞士编辑风",
        "frontend_framework: html",
        "pages:",
        "- id: P-1",
        "  name: 甲",
        "  states:",
        "  - {name: 悬停, signals: [图标]}",
        "  prototype: prototypes/P-1.html",
        "- id: P-1",
        "  name: 乙",
        "  states:",
        "  - {name: 悬停, signals: [图标]}",
        "  prototype: prototypes/P-1.html",
    ]) + NL


def run_engine(args):
    return subprocess.run(
        [sys.executable, DESIGN_PY] + args,
        capture_output=True, text=True, encoding="utf-8",
    )


class TransitionCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, rel, content):
        path = os.path.join(self.root, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with io.open(path, "w", encoding="utf-8", newline="") as f:
            f.write(content)
        return path

    def write_design(self, **kwargs):
        self.design = self.write("diy-output/design.yaml", design_text(**kwargs))
        return self.design

    def write_prototype(self, rel="diy-output/prototypes/P-1.html", content=GOOD_HTML):
        return self.write(rel, content)

    def read(self, path):
        with io.open(path, "r", encoding="utf-8") as f:
            return f.read()

    def transition(self, to, page="P-1", reason=None, design=None, extra=()):
        args = ["transition", "--design", design or self.design, "--page", page, "--to", to]
        if reason is not None:
            args += ["--reason", reason]
        return run_engine(list(args) + list(extra) + ["--json"])

    def receipt(self, proc):
        return json.loads(proc.stdout)


class LegalEdgeTests(TransitionCase):
    # trace: C·3a §2.5（transition 9 条合法边冻结表）
    def test_all_nine_legal_edges_accepted(self):
        for src, dst in LEGAL_EDGES:
            with self.subTest(edge="%s→%s" % (src, dst)):
                self.write_prototype()
                reason = "废弃：被 v2 取代" if dst == "已移除" else None
                self.write_design(status=src,
                                  removed_reason="旧原因" if src == "已移除" else None)
                proc = self.transition(dst, reason=reason)
                self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
                data = self.receipt(proc)
                self.assertTrue(data["ok"], data)
                self.assertEqual(data["command"], "transition")
                self.assertEqual(data["page"], "P-1")
                self.assertEqual(data["from"], src)
                self.assertEqual(data["to"], dst)
                self.assertTrue(data["next_hint"])
                self.assertEqual(data["violations"], [])
                self.assertEqual(data["counts"]["revisions"],
                                 1 if (src, dst) in DESTRUCTIVE_EDGES else 0)
                written = self.read(self.design)
                self.assertIn("status: %s" % dst, written)
                if dst == "已移除":
                    self.assertIn("removed_reason: %s" % reason, written)
                # revisions 只在破坏性边追加
                if (src, dst) in DESTRUCTIVE_EDGES:
                    self.assertIn("revisions:", written)
                    self.assertIn("change: P-1", written)
                else:
                    self.assertIn("revisions: []", written)

    # trace: C·3a §5b #3b（待验收 → 已批准 = 用户批准（人裁），不是「进入实现」——
    #                    实现发生在 待验收 之前：diy-dev 目标是 结构稿中 页，审查通过后页仍留 待验收）
    def test_approval_edge_hint_is_user_approval_not_implementation(self):
        self.write_prototype()
        self.write_design(status="待验收")
        proc = self.transition("已批准")
        self.assertEqual(proc.returncode, 0, proc.stdout)
        hint = self.receipt(proc)["next_hint"]
        self.assertNotIn("进入实现", hint, "该边是用户批准，不得声称进入实现")
        self.assertIn("用户批准", hint)
        self.assertIn("无自动后续步", hint, "该边是人裁，无自动后续步")
        self.assertIn("待用户批准", hint, "审查通过后页仍留 待验收，只报待用户批准")

    # trace: C·3a §2.5（--reason 冻结：→ 已移除 必填）
    def test_removed_without_reason_rejected_and_zero_write(self):
        self.write_prototype()
        path = self.write_design(status="结构稿中")
        before = self.read(path)
        proc = self.transition("已移除")
        self.assertEqual(proc.returncode, 1, proc.stdout)
        data = self.receipt(proc)
        self.assertFalse(data["ok"])
        self.assertEqual([x["code"] for x in data["violations"]], ["EMPTY_FIELD"])
        self.assertEqual(self.read(path), before, "拒绝路径必须零写入")

    # trace: C·3a §2.3（project.updated 每次写回刷今天；from 缺省 = 未开始）
    def test_missing_status_field_is_treated_as_initial(self):
        self.write_prototype()
        self.write_design(status=None)
        proc = self.transition("结构稿中")
        self.assertEqual(proc.returncode, 0, proc.stdout)
        data = self.receipt(proc)
        self.assertEqual(data["from"], "未开始")
        self.assertEqual(data["updated"], datetime.date.today().isoformat())

    # trace: C·3a §2.3（removed_reason 仅 已移除 时写——恢复即清）
    def test_restore_from_removed_clears_reason(self):
        self.write_prototype()
        path = self.write_design(status="已移除", removed_reason="旧原因")
        proc = self.transition("结构稿中")
        self.assertEqual(proc.returncode, 0, proc.stdout)
        written = self.read(path)
        self.assertIn("status: 结构稿中", written)
        self.assertNotIn("removed_reason", written, "恢复后残留陈旧 removed_reason")


class IllegalEdgeTests(TransitionCase):
    # trace: C·3a §2.5（不在表内的边一律 ILLEGAL_TRANSITION，报错须教正确路径）
    def test_illegal_edges_rejected_with_teaching_message(self):
        cases = (("未开始", "已批准"), ("未开始", "待验收"), ("未开始", "已移除"),
                 ("结构稿中", "已批准"), ("待验收", "未开始"), ("已移除", "已批准"))
        for src, dst in cases:
            with self.subTest(edge="%s→%s" % (src, dst)):
                self.setUp()
                self.write_prototype()
                path = self.write_design(status=src)
                before = self.read(path)
                proc = self.transition(dst, reason="x")
                self.assertEqual(proc.returncode, 1, proc.stdout)
                data = self.receipt(proc)
                self.assertFalse(data["ok"])
                self.assertEqual(data["violations"][0]["code"], "ILLEGAL_TRANSITION")
                msg = data["violations"][0]["msg"]
                self.assertIn(src, msg)
                self.assertIn(dst, msg)
                self.assertIn("design.py transition 契约", msg, "报错未教正确路径")
                self.assertEqual(self.read(path), before, "非法边必须零写入")


class ErrorCodeTests(TransitionCase):
    # trace: C·3a §2.5（错误码复用 diyc 同名：UNKNOWN_ID / DUPLICATE_ID / GATE_FAILED）
    def test_unknown_page_id(self):
        self.write_prototype()
        self.write_design(status="未开始")
        proc = self.transition("结构稿中", page="P-9")
        self.assertEqual(proc.returncode, 1, proc.stdout)
        data = self.receipt(proc)
        self.assertEqual(data["violations"][0]["code"], "UNKNOWN_ID")
        self.assertEqual(data["page"], "P-9")

    def test_duplicate_page_ids(self):
        self.write_prototype()
        self.design = self.write("diy-output/design.yaml", duplicate_page_text())
        proc = self.transition("结构稿中")
        self.assertEqual(proc.returncode, 1, proc.stdout)
        data = self.receipt(proc)
        self.assertEqual(data["violations"][0]["code"], "DUPLICATE_ID")

    # trace: C·3a §2.3（pages[].id 契约与 validate 同口径：缺 ID / 非字符串 ID 给结构码，
    #                    不得退化成 DUPLICATE_ID: None 或 INTERNAL_ERROR(不可哈希)）
    def test_page_id_shape_problems_rejected_without_internal_error(self):
        self.write_prototype()
        self.design = self.write("diy-output/design.yaml",
                                 design_text(status="未开始").replace(
                                     "- id: P-1" + NL + "  name: 待办列表", "- name: 待办列表"))
        before = self.read(self.design)
        proc = self.transition("结构稿中")
        self.assertEqual(proc.returncode, 1, proc.stdout)
        data = self.receipt(proc)
        self.assertEqual([x["code"] for x in data["violations"]], ["EMPTY_FIELD"], proc.stdout)
        self.assertEqual(data["violations"][0]["where"], "design.yaml pages[0].id")
        self.assertEqual(self.read(self.design), before, "拒绝路径必须零写入")
        # id 为列表（不可哈希）：形状异常码 + 无 Traceback + 零写入
        self.design = self.write("diy-output/design.yaml",
                                 design_text(status="未开始", page_id="[P-1]"))
        before2 = self.read(self.design)
        proc2 = self.transition("结构稿中")
        self.assertEqual(proc2.returncode, 1, proc2.stdout)
        data2 = self.receipt(proc2)
        self.assertEqual([x["code"] for x in data2["violations"]], ["UNPARSABLE_YAML"],
                         proc2.stdout)
        self.assertNotIn("INTERNAL_ERROR", [x["code"] for x in data2["violations"]])
        self.assertNotIn("Traceback", proc2.stderr)
        self.assertEqual(self.read(self.design), before2, "拒绝路径必须零写入")

    def test_enum_invalid_status_value(self):
        self.write_prototype()
        self.write_design(status="草稿")
        proc = self.transition("结构稿中")
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertEqual(self.receipt(proc)["violations"][0]["code"], "ENUM_INVALID")

    def test_gate_failed_on_acceptance_edges(self):
        # 缺一态（四态不许省）与结构稿缺失两条分支各跑一次
        self.write_design(status="结构稿中", with_states=False)
        self.write_prototype()
        proc = self.transition("待验收")
        self.assertEqual(proc.returncode, 1, proc.stdout)
        data = self.receipt(proc)
        self.assertEqual(data["violations"][0]["code"], "GATE_FAILED")
        self.assertIn("错误", data["violations"][0]["msg"])
        # 待验收 → 已批准 同样走页级门：结构稿缺失
        self.write_design(status="待验收", with_prototype=False)
        proc2 = self.transition("已批准")
        self.assertEqual(proc2.returncode, 1, proc2.stdout)
        self.assertEqual(self.receipt(proc2)["violations"][0]["code"], "GATE_FAILED")

    def test_missing_and_unparsable_design(self):
        proc = self.transition("结构稿中", design=os.path.join(self.root, "nope.yaml"))
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(self.receipt(proc)["violations"][0]["code"], "MISSING_FILE")
        bad = self.write("diy-output/design.yaml", "pages: [1," + NL)
        self.design = bad
        proc2 = self.transition("结构稿中")
        self.assertEqual(proc2.returncode, 1)
        self.assertEqual(self.receipt(proc2)["violations"][0]["code"], "UNPARSABLE_YAML")
        self.assertNotIn("Traceback", proc2.stderr)

    def test_invalid_target_is_usage_error(self):
        self.write_prototype()
        self.write_design(status="未开始")
        proc = run_engine(["transition", "--design", self.design, "--page", "P-1",
                           "--to", "不存在态", "--json"])
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)


class ReceiptShapeTests(TransitionCase):
    # trace: C·3a §2.4（回执形状全家族统一：单行 JSON + 公共键 + 命令专有键）
    def test_receipt_shape_common_and_specific_keys(self):
        self.write_prototype()
        self.write_design(status="未开始")
        proc = self.transition("结构稿中")
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertEqual(len(proc.stdout.strip().splitlines()), 1, "回执必须是单行 JSON")
        data = self.receipt(proc)
        self.assertEqual(set(data), {"ok", "command", "violations", "warnings", "counts",
                                     "file", "page", "from", "to", "updated", "next_hint"})
        self.assertIsInstance(data["ok"], bool)
        self.assertIsInstance(data["violations"], list)
        self.assertIsInstance(data["warnings"], list)
        self.assertIsInstance(data["counts"], dict)
        self.assertIn("design.yaml", data["file"])

    # trace: C·3a §2.4（violations[] 为 {code, where, msg} 三键）
    def test_violation_shape_is_code_where_msg(self):
        self.write_prototype()
        self.write_design(status="未开始")
        proc = self.transition("已批准")
        self.assertEqual(proc.returncode, 1)
        for item in self.receipt(proc)["violations"]:
            self.assertEqual(set(item), {"code", "where", "msg"})
            self.assertNotIn("\\", item["where"], "where 须正斜杠")

    # trace: C·3a §4.7（人读态不等于 JSON 态）
    def test_human_mode_prints_no_json(self):
        self.write_prototype()
        self.write_design(status="未开始")
        proc = run_engine(["transition", "--design", self.design, "--page", "P-1",
                           "--to", "结构稿中"])
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertNotIn('{"ok"', proc.stdout)
        self.assertIn("P-1 未开始 → 结构稿中", proc.stdout)

    # trace: C·3a §2.5（已移除 的 warnings[] 给 stories.yaml 悬空 AC 清单）
    def test_removed_warns_dangling_design_refs(self):
        self.write_prototype()
        self.write("diy-output/stories.yaml", NL.join([
            "stories:",
            "- id: S-2",
            "  acceptance_criteria:",
            "  - id: AC-3",
            "    design_ref: P-1",
            "  - id: AC-4",
            "    design_ref: P-2",
        ]) + NL)
        self.write_design(status="待验收")
        proc = self.transition("已移除", reason="被 v2 首页取代")
        self.assertEqual(proc.returncode, 0, proc.stdout)
        data = self.receipt(proc)
        self.assertEqual(len(data["warnings"]), 1, data)
        self.assertIn("S-2", data["warnings"][0])
        self.assertIn("AC-3", data["warnings"][0])
        self.assertNotIn("AC-4", data["warnings"][0])
        self.assertIn("removed_reason: 被 v2 首页取代", self.read(self.design))


class PrevSnapshotTests(TransitionCase):
    # trace: C·3a §4.3（重写既有 design.yaml 前落 .prev；原子写不留残骸）
    def test_prev_snapshot_is_pre_write_content(self):
        self.write_prototype()
        path = self.write_design(status="未开始")
        with io.open(path, "rb") as f:
            before = f.read()
        proc = self.transition("结构稿中")
        self.assertEqual(proc.returncode, 0, proc.stdout)
        prev = path + ".prev"
        self.assertTrue(os.path.isfile(prev), "重写前未落 .prev 快照")
        with io.open(prev, "rb") as f:
            self.assertEqual(f.read(), before, ".prev 不是改写前的内容")
        self.assertFalse(os.path.exists(path + ".tmp"), "原子写残留 .tmp")
        self.assertFalse(os.path.exists(path + ".prev.tmp"), "快照写残留 .prev.tmp")

    # trace: C·3a §4.3（--previous 对账四条分支：稳定 / ID_UNSTABLE / MISSING_FILE / UNPARSABLE_YAML）
    def test_previous_reconciliation_branches(self):
        self.write_prototype()
        path = self.write_design(status="未开始")
        stale = self.write("diy-output/design.yaml.prev",
                           design_text(status="未开始", page_id="P-1"))
        # 分支一：ID 稳定 → exit 0
        proc = run_engine(["validate", "--design", path, "--previous", stale, "--json"])
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertTrue(self.receipt(proc)["ok"])
        # 分支二：新稿丢了 P-1（重编号为 P-7）→ ID_UNSTABLE
        self.write("diy-output/design.yaml", design_text(status="未开始", page_id="P-7"))
        proc2 = run_engine(["validate", "--design", path, "--previous", stale, "--json"])
        self.assertEqual(proc2.returncode, 1, proc2.stdout)
        data2 = self.receipt(proc2)
        self.assertEqual(data2["violations"][0]["code"], "ID_UNSTABLE")
        self.assertIn("P-1", data2["violations"][0]["msg"])
        # check 同口径（--previous 挂在 validate / check 两命令，同一实现）
        proc2b = run_engine(["check", "--design", path, "--previous", stale, "--json"])
        self.assertEqual([x["code"] for x in self.receipt(proc2b)["violations"]], ["ID_UNSTABLE"])
        # 分支三：快照不存在 → MISSING_FILE
        proc3 = run_engine(["validate", "--design", path, "--previous",
                            os.path.join(self.root, "nope.yaml"), "--json"])
        self.assertEqual(proc3.returncode, 1)
        self.assertEqual(self.receipt(proc3)["violations"][0]["code"], "MISSING_FILE")
        # 分支四：快照不可解析 → UNPARSABLE_YAML
        broken = self.write("diy-output/broken.prev", "pages: [1," + NL)
        proc4 = run_engine(["validate", "--design", path, "--previous", broken, "--json"])
        self.assertEqual(proc4.returncode, 1)
        self.assertEqual(self.receipt(proc4)["violations"][0]["code"], "UNPARSABLE_YAML")
        self.assertNotIn("Traceback", proc4.stderr)

    # trace: C·3a §4.3（transition 落快照 → 对账可闭环）
    def test_transition_snapshot_feeds_reconciliation(self):
        self.write_prototype()
        path = self.write_design(status="未开始")
        self.assertEqual(self.transition("结构稿中").returncode, 0)
        proc = run_engine(["validate", "--design", path, "--previous", path + ".prev", "--json"])
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertTrue(self.receipt(proc)["ok"])


if __name__ == "__main__":
    unittest.main()
