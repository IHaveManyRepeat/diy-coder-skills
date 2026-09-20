# -*- coding: utf-8 -*-
"""diyc_writeback 写回命令测试（批次 3 / W3）。

覆盖（任务书 + batch3-contract.md §4.5-§4.9）：
- transition：八条合法边全部接受、待审查→已完成 与 待办→已完成 拒绝、已阻塞 必填 reason、
  已阻塞→待办 清 reason、已完成→进行中 清 augment（SS-012-04：重开即清旧 verdict）、
  --rounds 持久化 loop（终态补 outcome）、bump；
- green：evidence 写回 + test-plan 回填 + 双文件 bump、二次跑幂等（同 tc 替换不叠加）、
  状态/test_refs/test-plan 存在性/计数/空 red-green 逐一拒绝；
- done：三真源同批回填、空 test_refs 豁免、evidence 不完整/状态非待审查/故事不存在拒绝、rounds outcome；
- bug-add：序号铸造（既有 BUG-013 → BUG-014；无文件 → BUG-001 骨架）、--entry-file、
  枚举（source/class/subclass 对照）与必填拒绝、坏 JSON 拒绝、互斥参数拒绝；
- defer-add（2026-09-15 副作用纪律修订）：序号铸造（既有 DA-003 → DA-004；无文件 →
  DA-001 骨架）、四类 reason 全收、可选字段缺席不留空键、append 保留既有条目、
  枚举/必填/坏 JSON/互斥参数拒绝；
- reconcile：dry-run 零落盘 / --apply 落盘、add（缺覆盖→已阻塞+reason、story 已完成→已完成、
  已豁免 缺口视为覆盖）、remove 孤儿任务、changed 门重算（进行中→已阻塞、已阻塞→待办 清 reason）、
  待审查/已完成 不动、已完成 story 任务非已完成 只 warning 不伪造、test_refs 重推、新任务按 story 序插入、
  既有相对顺序保持、缺 stories/test-plan 拒绝。

依赖 W1 交付的 diyc_lib.py 与 tests/diyc_fixture.py（只读引用）；二者未落地时整文件跳过，
落地后自动激活（无需改动）。
"""
import argparse
import json
import sys
import unittest
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "skills" / "diy-tools" / "scripts"))
sys.path.insert(0, str(HERE))

try:
    import diyc_lib  # noqa: F401  （diyc_writeback 的运行时依赖）
    import diyc_writeback
    import diyc_fixture
    _READY = True
    _IMPORT_ERR = ""
except Exception as _e:  # W1 并行交付中：缺依赖时整文件跳过
    diyc_lib = None
    diyc_writeback = None
    diyc_fixture = None
    _READY = False
    _IMPORT_ERR = f"{_e.__class__.__name__}: {_e}"

NEEDS_W1 = unittest.skipUnless(_READY, f"等待 W1 交付 diyc_lib/diyc_fixture（{_IMPORT_ERR}）")


# ---- 产物形状工厂（薄委托 diyc_fixture，形状对齐 diy-output/*.yaml 实物） ----

def _story(sid, acs, status="待办"):
    return diyc_fixture.story(sid, [diyc_fixture.ac(a) for a in acs], status=status)


def _tc(tcid, ac, status="待办"):
    return diyc_fixture.tc(tcid, ac, status=status)


def _gap(ac, story, decision="待办"):
    return diyc_fixture.gap(ac, story, decision=decision)


def _task(sid, status="待办", refs=None, **kw):
    return diyc_fixture.task(sid, status, refs,
                             **{k: val for k, val in kw.items() if val is not None})


def _stories_doc(*stories):
    return diyc_fixture.doc_stories(list(stories))


def _tp_doc(*cases, gaps=()):
    return diyc_fixture.doc_test_plan(list(cases), gaps=list(gaps))


def _sprint_doc(*tasks):
    return diyc_fixture.doc_sprint(list(tasks))


class WritebackCase(unittest.TestCase):
    """共用夹具：临时项目根 + 产物读写 + args 构造（对齐 diyc.py 的 Namespace 契约）。"""

    def setUp(self):
        self.root = Path(diyc_fixture.make_root())
        self.out = Path(diyc_fixture.out_dir(str(self.root)))

    def tearDown(self):
        diyc_fixture.cleanup(str(self.root))

    def write(self, name, data):
        return diyc_fixture.write_doc(str(self.root), name, data)

    def read(self, name):
        with open(self.out / (name + ".yaml"), encoding="utf-8") as f:
            return yaml.safe_load(f)

    def args(self, command, **kw):
        base = dict(command=command, project_root=str(self.root), instance=None,
                    output_dir=str(self.out))
        base.update(kw)
        return argparse.Namespace(**base)


@NEEDS_W1
class TransitionTests(WritebackCase):

    def _sprint_one(self, status, **kw):
        self.write("sprint", _sprint_doc(_task("S-1", status, **kw)))

    def test_legal_edges_all_accepted(self):
        edges = [
            ("待办", "进行中"), ("待办", "已阻塞"),
            ("进行中", "已阻塞"), ("待审查", "已阻塞"),
            ("进行中", "待审查"), ("待审查", "进行中"),
            ("已阻塞", "待办"), ("已完成", "进行中"),
        ]
        for src, dst in edges:
            with self.subTest(edge=f"{src}→{dst}"):
                self._sprint_one(src, blocked_reason="旧原因" if src == "已阻塞" else None)
                res = diyc_writeback.run(self.args(
                    "transition", story="S-1", to=dst,
                    reason="阻塞原因" if dst == "已阻塞" else None, rounds=None))
                self.assertTrue(res["ok"], res)
                doc = self.read("sprint")
                self.assertEqual(doc["tasks"][0]["status"], dst)
                self.assertEqual(res["from"], src)
                self.assertEqual(res["to"], dst)
                self.assertEqual(doc["project"]["updated"], diyc_lib.today())

    def test_blocked_to_pending_clears_reason(self):
        self._sprint_one("已阻塞", blocked_reason="AC-1.1 无用例")
        res = diyc_writeback.run(self.args("transition", story="S-1", to="待办",
                                           reason=None, rounds=None))
        self.assertTrue(res["ok"], res)
        task = self.read("sprint")["tasks"][0]
        self.assertEqual(task["status"], "待办")
        self.assertNotIn("blocked_reason", task)

    def test_done_to_in_progress_clears_augment(self):
        # SS-012-04：重开即清旧 verdict，与 runner --reopen-failed 同语义
        # （冻结契约 §4.5 的「不清 augment」括号注已作废）
        self._sprint_one("已完成", augment="失败",
                         loop={"at": "2026-01-01", "rounds": 1, "outcome": "已完成"})
        res = diyc_writeback.run(self.args("transition", story="S-1", to="进行中",
                                           reason=None, rounds=None))
        self.assertTrue(res["ok"], res)
        task = self.read("sprint")["tasks"][0]
        self.assertEqual(task["status"], "进行中")
        self.assertNotIn("augment", task)

    def test_done_to_in_progress_without_augment_ok(self):
        # 缺席本就无事：重开不应凭空造键（未被补测过的任务）
        self._sprint_one("已完成")
        res = diyc_writeback.run(self.args("transition", story="S-1", to="进行中",
                                           reason=None, rounds=None))
        self.assertTrue(res["ok"], res)
        task = self.read("sprint")["tasks"][0]
        self.assertEqual(task["status"], "进行中")
        self.assertNotIn("augment", task)

    def test_rounds_persisted(self):
        self._sprint_one("待办")
        res = diyc_writeback.run(self.args("transition", story="S-1", to="进行中",
                                           reason=None, rounds=3))
        self.assertTrue(res["ok"], res)
        loop = self.read("sprint")["tasks"][0]["loop"]
        self.assertEqual(loop["rounds"], 3)
        self.assertEqual(loop["at"], diyc_lib.today())
        self.assertNotIn("outcome", loop)  # outcome 仅在终态出现

    def test_rounds_blocked_writes_outcome(self):
        self._sprint_one("进行中")
        res = diyc_writeback.run(self.args("transition", story="S-1", to="已阻塞",
                                           reason="缺用例", rounds=2))
        self.assertTrue(res["ok"], res)
        task = self.read("sprint")["tasks"][0]
        self.assertEqual(task["blocked_reason"], "缺用例")
        self.assertEqual(task["loop"],
                         {"at": diyc_lib.today(), "rounds": 2, "outcome": "已阻塞"})

    def test_review_to_done_rejected_with_done_hint(self):
        self._sprint_one("待审查")
        res = diyc_writeback.run(self.args("transition", story="S-1", to="已完成",
                                           reason=None, rounds=None))
        self.assertFalse(res["ok"])
        self.assertEqual(res["violations"][0]["code"], "ILLEGAL_TRANSITION")
        self.assertIn("diyc.py done", res["violations"][0]["msg"])
        self.assertEqual(self.read("sprint")["tasks"][0]["status"], "待审查")  # 零写入

    def test_pending_to_done_rejected(self):
        self._sprint_one("待办")
        res = diyc_writeback.run(self.args("transition", story="S-1", to="已完成",
                                           reason=None, rounds=None))
        self.assertFalse(res["ok"])
        self.assertEqual(res["violations"][0]["code"], "ILLEGAL_TRANSITION")

    def test_blocked_without_reason_rejected(self):
        self._sprint_one("待办")
        res = diyc_writeback.run(self.args("transition", story="S-1", to="已阻塞",
                                           reason="   ", rounds=None))
        self.assertFalse(res["ok"])
        self.assertEqual(res["violations"][0]["code"], "EMPTY_FIELD")
        self.assertEqual(self.read("sprint")["tasks"][0]["status"], "待办")

    def test_unknown_story_rejected(self):
        self._sprint_one("待办")
        res = diyc_writeback.run(self.args("transition", story="S-9", to="进行中",
                                           reason=None, rounds=None))
        self.assertFalse(res["ok"])
        self.assertEqual(res["violations"][0]["code"], "UNKNOWN_ID")

    def test_missing_sprint_rejected(self):
        res = diyc_writeback.run(self.args("transition", story="S-1", to="进行中",
                                           reason=None, rounds=None))
        self.assertFalse(res["ok"])
        self.assertEqual(res["violations"][0]["code"], "MISSING_FILE")


@NEEDS_W1
class GreenTests(WritebackCase):

    def setUp(self):
        super().setUp()
        self.write("stories", _stories_doc(_story("S-1", ["AC-1.1"])))
        self.write("test-plan", _tp_doc(_tc("TC-1.1.1", "AC-1.1"),
                                        _tc("TC-1.1.2", "AC-1.1")))
        self.write("sprint", _sprint_doc(_task("S-1", "进行中",
                                               ["TC-1.1.1", "TC-1.1.2"])))

    def _green(self, **kw):
        base = dict(story="S-1", tc=["TC-1.1.1"],
                    red=["unittest: FAILED"], green=["unittest: OK"])
        base.update(kw)
        return diyc_writeback.run(self.args("green", **base))

    def test_writes_evidence_and_backfills_test_plan(self):
        res = self._green()
        self.assertTrue(res["ok"], res)
        self.assertEqual(res["evidence_written"], ["TC-1.1.1"])
        self.assertEqual(res["test_plan_backfilled"], ["TC-1.1.1"])
        sprint = self.read("sprint")
        self.assertEqual(sprint["tasks"][0]["evidence"],
                         [{"tc": "TC-1.1.1", "red": "unittest: FAILED",
                           "green": "unittest: OK"}])
        self.assertEqual(sprint["project"]["updated"], diyc_lib.today())
        self.assertEqual(res["updated"], diyc_lib.today())
        tp = self.read("test-plan")
        statuses = {c["id"]: c["status"] for c in tp["test_cases"]}
        self.assertEqual(statuses["TC-1.1.1"], "通过")
        self.assertEqual(statuses["TC-1.1.2"], "待办")  # 未写入的用例不动
        self.assertEqual(tp["project"]["updated"], diyc_lib.today())

    def test_second_run_idempotent(self):
        self.assertTrue(self._green(green=["OK 二次"])["ok"])
        res = self._green(green=["OK 三次"])
        self.assertTrue(res["ok"], res)
        evidence = self.read("sprint")["tasks"][0]["evidence"]
        self.assertEqual(len(evidence), 1)  # 同 tc 替换，不叠加重复
        self.assertEqual(evidence[0]["green"], "OK 三次")

    def test_second_run_backfill_reports_only_new(self):
        self.assertTrue(self._green()["ok"])
        res = self._green()
        self.assertTrue(res["ok"], res)
        self.assertEqual(res["test_plan_backfilled"], [])  # 已是 通过 → 本次零回填

    def test_multi_tc_one_call(self):
        res = self._green(tc=["TC-1.1.2", "TC-1.1.1"], red=["r2", "r1"], green=["g2", "g1"])
        self.assertTrue(res["ok"], res)
        evidence = self.read("sprint")["tasks"][0]["evidence"]
        self.assertEqual([e["tc"] for e in evidence], ["TC-1.1.2", "TC-1.1.1"])
        self.assertEqual(res["test_plan_backfilled"], ["TC-1.1.2", "TC-1.1.1"])

    def test_non_in_progress_rejected(self):
        self.write("sprint", _sprint_doc(_task("S-1", "待办", ["TC-1.1.1"])))
        res = self._green()
        self.assertFalse(res["ok"])
        self.assertEqual(res["violations"][0]["code"], "STATUS_MISMATCH")

    def test_tc_not_in_test_refs_rejected(self):
        self.write("sprint", _sprint_doc(_task("S-1", "进行中", ["TC-1.1.1"])))
        res = self._green(tc=["TC-1.1.2"])
        self.assertFalse(res["ok"])
        self.assertEqual(res["violations"][0]["code"], "UNKNOWN_ID")
        self.assertIn("test_refs", res["violations"][0]["msg"])

    def test_tc_missing_in_test_plan_rejected(self):
        self.write("sprint", _sprint_doc(_task("S-1", "进行中", ["TC-9.9.9"])))
        res = self._green(tc=["TC-9.9.9"])
        self.assertFalse(res["ok"])
        self.assertEqual(res["violations"][0]["code"], "UNKNOWN_ID")
        self.assertIn("test-plan.yaml", res["violations"][0]["msg"])

    def test_count_mismatch_rejected(self):
        res = self._green(tc=["TC-1.1.1"], red=["r"], green=["g", "多余"])
        self.assertFalse(res["ok"])
        self.assertEqual(res["violations"][0]["code"], "SET_MISMATCH")

    def test_empty_red_rejected(self):
        res = self._green(red=["   "])
        self.assertFalse(res["ok"])
        self.assertEqual(res["violations"][0]["code"], "EMPTY_FIELD")
        self.assertIsNone(self.read("sprint")["tasks"][0].get("evidence"))  # 零写入

    def test_no_tc_rejected(self):
        res = self._green(tc=[], red=[], green=[])
        self.assertFalse(res["ok"])
        self.assertEqual(res["violations"][0]["code"], "EMPTY_FIELD")

    def test_duplicate_tc_in_one_call_rejected(self):
        res = self._green(tc=["TC-1.1.1", "TC-1.1.1"], red=["r1", "r2"], green=["g1", "g2"])
        self.assertFalse(res["ok"])
        self.assertEqual(res["violations"][0]["code"], "DUPLICATE_ID")


@NEEDS_W1
class DoneTests(WritebackCase):

    def setUp(self):
        super().setUp()
        self.write("stories", _stories_doc(_story("S-1", ["AC-1.1"]),
                                           _story("S-2", ["AC-2.1"])))
        self.write("test-plan", _tp_doc(_tc("TC-1.1.1", "AC-1.1"),
                                        _tc("TC-2.1.1", "AC-2.1")))
        self.write("sprint", _sprint_doc(_task(
            "S-1", "待审查", ["TC-1.1.1"],
            evidence=[{"tc": "TC-1.1.1", "red": "红记录", "green": "绿记录"}])))

    def test_backfills_three_sources(self):
        res = diyc_writeback.run(self.args("done", story="S-1", rounds=None))
        self.assertTrue(res["ok"], res)
        self.assertEqual(self.read("sprint")["tasks"][0]["status"], "已完成")
        self.assertEqual(self.read("stories")["stories"][0]["status"], "已完成")
        self.assertEqual(self.read("test-plan")["test_cases"][0]["status"], "通过")
        for name in ("sprint", "stories", "test-plan"):
            self.assertEqual(self.read(name)["project"]["updated"], diyc_lib.today(), name)
        self.assertEqual(res["backfilled"], {"stories": True, "test_plan": ["TC-1.1.1"]})
        self.assertEqual(res["updated"], diyc_lib.today())

    def test_empty_test_refs_story_exempt(self):
        self.write("sprint", _sprint_doc(_task("S-2", "待审查", [])))
        res = diyc_writeback.run(self.args("done", story="S-2", rounds=None))
        self.assertTrue(res["ok"], res)
        self.assertEqual(self.read("sprint")["tasks"][0]["status"], "已完成")
        self.assertEqual(self.read("stories")["stories"][1]["status"], "已完成")

    def test_evidence_green_blank_rejected(self):
        self.write("sprint", _sprint_doc(_task(
            "S-1", "待审查", ["TC-1.1.1"],
            evidence=[{"tc": "TC-1.1.1", "red": "r", "green": "  "}])))
        res = diyc_writeback.run(self.args("done", story="S-1", rounds=None))
        self.assertFalse(res["ok"])
        self.assertEqual(res["violations"][0]["code"], "EVIDENCE_MISSING")
        self.assertEqual(self.read("sprint")["tasks"][0]["status"], "待审查")  # 零写入

    def test_evidence_entry_missing_rejected(self):
        self.write("sprint", _sprint_doc(_task("S-1", "待审查", ["TC-1.1.1"], evidence=[])))
        res = diyc_writeback.run(self.args("done", story="S-1", rounds=None))
        self.assertFalse(res["ok"])
        self.assertEqual(res["violations"][0]["code"], "EVIDENCE_MISSING")

    def test_status_not_review_rejected(self):
        self.write("sprint", _sprint_doc(_task(
            "S-1", "进行中", ["TC-1.1.1"],
            evidence=[{"tc": "TC-1.1.1", "red": "r", "green": "g"}])))
        res = diyc_writeback.run(self.args("done", story="S-1", rounds=None))
        self.assertFalse(res["ok"])
        self.assertEqual(res["violations"][0]["code"], "STATUS_MISMATCH")

    def test_story_missing_in_stories_rejected(self):
        self.write("stories", _stories_doc(_story("S-2", ["AC-2.1"])))  # 无 S-1
        res = diyc_writeback.run(self.args("done", story="S-1", rounds=None))
        self.assertFalse(res["ok"])
        self.assertEqual(res["violations"][0]["code"], "UNKNOWN_ID")
        self.assertIn("stories.yaml", res["violations"][0]["msg"])

    def test_rounds_writes_done_outcome(self):
        res = diyc_writeback.run(self.args("done", story="S-1", rounds=1))
        self.assertTrue(res["ok"], res)
        loop = self.read("sprint")["tasks"][0]["loop"]
        self.assertEqual(loop, {"at": diyc_lib.today(), "rounds": 1, "outcome": "已完成"})

    def test_second_run_rejected(self):
        self.assertTrue(diyc_writeback.run(self.args("done", story="S-1", rounds=None))["ok"])
        res = diyc_writeback.run(self.args("done", story="S-1", rounds=None))
        self.assertFalse(res["ok"])
        self.assertEqual(res["violations"][0]["code"], "STATUS_MISMATCH")


@NEEDS_W1
class BugAddTests(WritebackCase):

    ENTRY = {
        "source": "开发", "story": "S-1", "class": "功能型", "subclass": "状态",
        "type": "类型", "symptom": "症状", "root_cause": "根因", "trigger": "触发",
        "fix": "修复", "prevention": "预防", "pattern": "模式",
    }

    def _add(self, entry=None, **kw):
        payload = dict(self.ENTRY if entry is None else entry)
        return diyc_writeback.run(self.args(
            "bug-add", entry=json.dumps(payload, ensure_ascii=False), entry_file=None, **kw))

    def test_sequence_minted_after_existing(self):
        bugs = [{"id": f"BUG-{i:03d}", "date": "2026-01-01", "source": "开发",
                 "story": "S-1", "class": "功能型", "subclass": "状态", "type": "t",
                 "symptom": "s", "root_cause": "r", "trigger": "g", "fix": "f",
                 "prevention": "p", "pattern": "pa"} for i in range(1, 14)]
        self.write("bug-log", {"project": diyc_fixture.project_meta(), "bugs": bugs})
        res = self._add()
        self.assertTrue(res["ok"], res)
        self.assertEqual(res["id"], "BUG-014")
        doc = self.read("bug-log")
        self.assertEqual(len(doc["bugs"]), 14)
        self.assertEqual(doc["bugs"][-1]["id"], "BUG-014")
        self.assertEqual(doc["bugs"][-1]["date"], diyc_lib.today())
        self.assertEqual(doc["project"]["updated"], diyc_lib.today())
        self.assertEqual(res["file"], "diy-output/bug-log.yaml")

    def test_missing_file_creates_skeleton(self):
        self.write("sprint", _sprint_doc(_task("S-1", "待办")))  # 供骨架取 project.name
        res = self._add()
        self.assertTrue(res["ok"], res)
        self.assertEqual(res["id"], "BUG-001")
        doc = self.read("bug-log")
        self.assertEqual(doc["bugs"][0]["id"], "BUG-001")
        self.assertEqual(doc["project"]["name"], "diy-coder-skill")  # 取自 sprint 的 project.name
        self.assertEqual(set(doc["project"]), {"name", "created", "updated"})

    def test_explicit_date_kept(self):
        res = self._add({**self.ENTRY, "date": "2026-02-02"})
        self.assertTrue(res["ok"], res)
        self.assertEqual(self.read("bug-log")["bugs"][0]["date"], "2026-02-02")

    def test_entry_file_input(self):
        path = self.root / "entry.json"
        path.write_text(json.dumps(self.ENTRY, ensure_ascii=False), encoding="utf-8")
        res = diyc_writeback.run(self.args("bug-add", entry=None, entry_file=str(path)))
        self.assertTrue(res["ok"], res)
        self.assertEqual(res["id"], "BUG-001")

    def test_bad_source_rejected(self):
        res = self._add({**self.ENTRY, "source": "guess"})
        self.assertFalse(res["ok"])
        self.assertEqual(res["violations"][0]["code"], "ENUM_INVALID")

    def test_subclass_class_mismatch_rejected(self):
        res = self._add({**self.ENTRY, "class": "非功能型", "subclass": "逻辑"})
        self.assertFalse(res["ok"])
        self.assertEqual(res["violations"][0]["code"], "ENUM_INVALID")

    def test_non_functional_subclass_accepted(self):
        res = self._add({**self.ENTRY, "class": "非功能型", "subclass": "可靠性"})
        self.assertTrue(res["ok"], res)

    def test_missing_required_field_rejected(self):
        entry = {k: v for k, v in self.ENTRY.items() if k != "fix"}
        res = self._add(entry)
        self.assertFalse(res["ok"])
        self.assertEqual(res["violations"][0]["code"], "EMPTY_FIELD")
        self.assertIn("fix", res["violations"][0]["msg"])

    def test_bad_json_rejected(self):
        res = diyc_writeback.run(self.args("bug-add", entry="{不是 json", entry_file=None))
        self.assertFalse(res["ok"])
        self.assertEqual(res["violations"][0]["code"], "ENTRY_INVALID")

    def test_both_entry_sources_rejected(self):
        res = diyc_writeback.run(self.args("bug-add", entry="{}", entry_file="x.json"))
        self.assertFalse(res["ok"])
        self.assertEqual(res["violations"][0]["code"], "SET_MISMATCH")


@NEEDS_W1
class DeferAddTests(WritebackCase):
    """defer-add（2026-09-15 副作用纪律修订）：保留确认类动作入队。"""

    ENTRY = {
        "skill": "diy-test-framework",
        "action": "合并 hook 到 .claude/settings.json",
        "command": "python scripts/merge-hook.py",
        "target": ".claude/settings.json",
        "reason": "用户配置",
    }

    def _add(self, entry=None, **kw):
        payload = dict(self.ENTRY if entry is None else entry)
        return diyc_writeback.run(self.args(
            "defer-add", entry=json.dumps(payload, ensure_ascii=False),
            entry_file=None, **kw))

    def test_sequence_minted_after_existing(self):
        actions = [{"id": f"DA-{i:03d}", "date": "2026-01-01", "skill": "s",
                    "action": "a", "reason": "仅人工可做", "status": "待办"}
                   for i in range(1, 4)]
        self.write("deferred-actions",
                   {"project": diyc_fixture.project_meta(), "actions": actions})
        res = self._add()
        self.assertTrue(res["ok"], res)
        self.assertEqual(res["id"], "DA-004")
        doc = self.read("deferred-actions")
        self.assertEqual(len(doc["actions"]), 4)
        self.assertEqual(doc["actions"][-1]["id"], "DA-004")
        self.assertEqual(doc["actions"][-1]["date"], diyc_lib.today())
        self.assertEqual(doc["actions"][-1]["status"], "待办")
        self.assertEqual(doc["project"]["updated"], diyc_lib.today())
        self.assertEqual(res["file"], "diy-output/deferred-actions.yaml")

    def test_missing_file_creates_skeleton(self):
        self.write("sprint", _sprint_doc(_task("S-1", "待办")))  # 供骨架取 project.name
        res = self._add()
        self.assertTrue(res["ok"], res)
        self.assertEqual(res["id"], "DA-001")
        doc = self.read("deferred-actions")
        self.assertEqual(doc["actions"][0]["id"], "DA-001")
        self.assertEqual(doc["project"]["name"], "diy-coder-skill")
        self.assertEqual(set(doc["project"]), {"name", "created", "updated"})

    def test_optional_fields_omitted_when_absent(self):
        entry = {k: v for k, v in self.ENTRY.items() if k not in ("command", "target")}
        res = self._add(entry)
        self.assertTrue(res["ok"], res)
        item = self.read("deferred-actions")["actions"][0]
        self.assertNotIn("command", item)
        self.assertNotIn("target", item)
        self.assertEqual(item["reason"], "用户配置")

    def test_append_keeps_existing_entries(self):
        first = self._add()
        self.assertTrue(first["ok"], first)
        second = self._add({**self.ENTRY, "reason": "仅人工可做", "action": "配置 API key"})
        self.assertTrue(second["ok"], second)
        doc = self.read("deferred-actions")
        self.assertEqual([a["id"] for a in doc["actions"]], ["DA-001", "DA-002"])
        self.assertEqual(doc["actions"][0]["reason"], "用户配置")  # 既有条目原样

    def test_all_four_reasons_accepted(self):
        for reason in ("用户配置", "破坏性操作", "越界改动", "仅人工可做"):
            with self.subTest(reason=reason):
                res = self._add({**self.ENTRY, "reason": reason})
                self.assertTrue(res["ok"], res)

    def test_bad_reason_rejected(self):
        res = self._add({**self.ENTRY, "reason": "whatever"})
        self.assertFalse(res["ok"])
        self.assertEqual(res["violations"][0]["code"], "ENUM_INVALID")

    def test_missing_required_field_rejected(self):
        entry = {k: v for k, v in self.ENTRY.items() if k != "action"}
        res = self._add(entry)
        self.assertFalse(res["ok"])
        self.assertEqual(res["violations"][0]["code"], "EMPTY_FIELD")
        self.assertIn("action", res["violations"][0]["msg"])

    def test_bad_json_rejected(self):
        res = diyc_writeback.run(self.args("defer-add", entry="{不是 json", entry_file=None))
        self.assertFalse(res["ok"])
        self.assertEqual(res["violations"][0]["code"], "ENTRY_INVALID")

    def test_both_entry_sources_rejected(self):
        res = diyc_writeback.run(self.args("defer-add", entry="{}", entry_file="x.json"))
        self.assertFalse(res["ok"])
        self.assertEqual(res["violations"][0]["code"], "SET_MISMATCH")


@NEEDS_W1
class ReconcileTests(WritebackCase):

    def test_dry_run_no_write(self):
        self.write("stories", _stories_doc(_story("S-1", ["AC-1.1"])))
        self.write("test-plan", _tp_doc(_tc("TC-1.1.1", "AC-1.1")))
        res = diyc_writeback.run(self.args("reconcile", apply=False))
        self.assertTrue(res["ok"], res)
        self.assertFalse(res["applied"])
        self.assertFalse((self.out / "sprint.yaml").exists())  # dry-run 零落盘
        self.assertEqual([t["story"] for t in res["actions"]["add"]], ["S-1"])
        self.assertEqual(res["actions"]["add"][0]["status"], "待办")
        self.assertEqual(res["actions"]["add"][0]["test_refs"], ["TC-1.1.1"])

    def test_apply_creates_draft_sprint(self):
        # 契约 §4.9 裁定：缺席（Create）→ 建骨架（name 取 stories 的 project.name）
        # + tasks 全量；status: 草稿，技能侧随后可改 已定稿
        self.write("stories", _stories_doc(_story("S-1", ["AC-1.1"])))
        self.write("test-plan", _tp_doc(_tc("TC-1.1.1", "AC-1.1")))
        res = diyc_writeback.run(self.args("reconcile", apply=True))
        self.assertTrue(res["ok"], res)
        self.assertTrue(res["applied"])
        doc = self.read("sprint")
        self.assertEqual(doc["project"]["name"], "diy-coder-skill")  # stories.yaml 的 project.name
        self.assertEqual(doc["project"]["status"], "草稿")
        self.assertEqual(doc["project"]["created"], diyc_lib.today())
        self.assertEqual(doc["project"]["updated"], diyc_lib.today())
        self.assertEqual(set(doc["project"]), {"name", "status", "created", "updated"})
        self.assertEqual(res["updated"], diyc_lib.today())
        self.assertEqual([t["story"] for t in doc["tasks"]], ["S-1"])

    def test_create_defaults_project_name(self):
        # 契约 §4.9：stories.yaml 无 project.name → 骨架缺省 "project"
        self.write("stories", {"project": {"status": "已定稿"},
                               "stories": [_story("S-1", ["AC-1.1"])]})
        self.write("test-plan", _tp_doc(_tc("TC-1.1.1", "AC-1.1")))
        res = diyc_writeback.run(self.args("reconcile", apply=True))
        self.assertTrue(res["ok"], res)
        self.assertEqual(self.read("sprint")["project"]["name"], "project")

    def test_apply_second_run_is_idempotent(self):
        # 幂等：二次 --apply 零动作、文件字节不变（不重写、不重复建任务）
        self.write("stories", _stories_doc(_story("S-1", ["AC-1.1"])))
        self.write("test-plan", _tp_doc(_tc("TC-1.1.1", "AC-1.1")))
        diyc_writeback.run(self.args("reconcile", apply=True))
        first = (self.out / "sprint.yaml").read_text(encoding="utf-8")
        res = diyc_writeback.run(self.args("reconcile", apply=True))
        self.assertTrue(res["ok"], res)
        self.assertEqual(res["actions"], {"add": [], "remove": [], "changed": []})
        self.assertEqual((self.out / "sprint.yaml").read_text(encoding="utf-8"), first)

    def test_refs_are_numeric_sorted(self):
        self.write("stories", _stories_doc(_story("S-2", ["AC-2.1"])))
        self.write("test-plan", _tp_doc(_tc("TC-2.1.2", "AC-2.1"), _tc("TC-2.1.10", "AC-2.1")))
        diyc_writeback.run(self.args("reconcile", apply=True))
        self.assertEqual(self.read("sprint")["tasks"][0]["test_refs"],
                         ["TC-2.1.2", "TC-2.1.10"])  # 数字感知（非字典序）

    def test_gap_pending_blocks_new_task(self):
        self.write("stories", _stories_doc(_story("S-1", ["AC-1.1"])))
        self.write("test-plan", _tp_doc(gaps=[_gap("AC-1.1", "S-1", decision="待办")]))
        res = diyc_writeback.run(self.args("reconcile", apply=True))
        self.assertTrue(res["ok"], res)
        task = self.read("sprint")["tasks"][0]
        self.assertEqual(task["status"], "已阻塞")
        self.assertIn("AC-1.1", task["blocked_reason"])
        self.assertIn("无用例（decision: 待办）", task["blocked_reason"])

    def test_waived_gap_stays_pending(self):
        self.write("stories", _stories_doc(_story("S-1", ["AC-1.1"])))
        self.write("test-plan", _tp_doc(gaps=[_gap("AC-1.1", "S-1", decision="已豁免")]))
        diyc_writeback.run(self.args("reconcile", apply=True))
        self.assertEqual(self.read("sprint")["tasks"][0]["status"], "待办")

    def test_done_story_new_task_done(self):
        self.write("stories", _stories_doc(_story("S-1", ["AC-1.1"], status="已完成")))
        self.write("test-plan", _tp_doc(_tc("TC-1.1.1", "AC-1.1", status="通过")))
        diyc_writeback.run(self.args("reconcile", apply=True))
        self.assertEqual(self.read("sprint")["tasks"][0]["status"], "已完成")

    def test_regates_in_progress_to_blocked(self):
        self.write("stories", _stories_doc(_story("S-1", ["AC-1.1"])))
        self.write("test-plan", _tp_doc(gaps=[_gap("AC-1.1", "S-1", decision="待办")]))
        self.write("sprint", _sprint_doc(_task("S-1", "进行中")))
        res = diyc_writeback.run(self.args("reconcile", apply=True))
        task = self.read("sprint")["tasks"][0]
        self.assertEqual(task["status"], "已阻塞")
        self.assertIn("AC-1.1", task["blocked_reason"])
        changed = {c["story"]: c["fields"] for c in res["actions"]["changed"]}
        self.assertEqual(changed["S-1"], ["status", "blocked_reason"])

    def test_recovers_blocked_to_pending(self):
        self.write("stories", _stories_doc(_story("S-1", ["AC-1.1"])))
        self.write("test-plan", _tp_doc(_tc("TC-1.1.1", "AC-1.1")))  # 覆盖已恢复
        self.write("sprint", _sprint_doc(
            _task("S-1", "已阻塞", blocked_reason="AC-1.1 无用例（decision: 待办）")))
        res = diyc_writeback.run(self.args("reconcile", apply=True))
        self.assertTrue(res["ok"], res)
        task = self.read("sprint")["tasks"][0]
        self.assertEqual(task["status"], "待办")
        self.assertNotIn("blocked_reason", task)

    def test_review_and_done_untouched(self):
        self.write("stories", _stories_doc(_story("S-1", ["AC-1.1"]),
                                           _story("S-2", ["AC-2.1"])))
        self.write("test-plan", _tp_doc(gaps=[_gap("AC-1.1", "S-1", decision="待办"),
                                              _gap("AC-2.1", "S-2", decision="待办")]))
        self.write("sprint", _sprint_doc(_task("S-1", "待审查"),
                                         _task("S-2", "已完成", note="已交付")))
        res = diyc_writeback.run(self.args("reconcile", apply=True))
        self.assertTrue(res["ok"], res)
        tasks = self.read("sprint")["tasks"]
        self.assertEqual([t["status"] for t in tasks], ["待审查", "已完成"])  # 审计产物不动
        self.assertEqual(res["actions"]["changed"], [])

    def test_done_story_with_non_done_task_warns_only(self):
        self.write("stories", _stories_doc(_story("S-1", ["AC-1.1"], status="已完成")))
        self.write("test-plan", _tp_doc(_tc("TC-1.1.1", "AC-1.1", status="通过")))
        self.write("sprint", _sprint_doc(_task("S-1", "待办", note="旧记录")))
        res = diyc_writeback.run(self.args("reconcile", apply=True))
        self.assertTrue(res["ok"], res)
        self.assertEqual(self.read("sprint")["tasks"][0]["status"], "待办")  # 不伪造交付
        self.assertTrue(any("已完成" in w for w in res["warnings"]), res["warnings"])

    def test_removes_orphan_task(self):
        self.write("stories", _stories_doc(_story("S-1", ["AC-1.1"])))
        self.write("test-plan", _tp_doc(_tc("TC-1.1.1", "AC-1.1")))
        self.write("sprint", _sprint_doc(_task("S-1", "待办", ["TC-1.1.1"]),
                                         _task("S-99", "已完成", note="孤儿")))
        res = diyc_writeback.run(self.args("reconcile", apply=True))
        self.assertEqual(res["actions"]["remove"], ["S-99"])
        self.assertEqual([t["story"] for t in self.read("sprint")["tasks"]], ["S-1"])

    def test_test_refs_recomputed_and_reported(self):
        self.write("stories", _stories_doc(_story("S-1", ["AC-1.1"])))
        self.write("test-plan", _tp_doc(_tc("TC-1.1.1", "AC-1.1"), _tc("TC-1.1.2", "AC-1.1")))
        self.write("sprint", _sprint_doc(_task("S-1", "待办", ["TC-1.1.2"])))
        res = diyc_writeback.run(self.args("reconcile", apply=True))
        changed = {c["story"]: c["fields"] for c in res["actions"]["changed"]}
        self.assertEqual(changed["S-1"], ["test_refs"])
        self.assertEqual(self.read("sprint")["tasks"][0]["test_refs"],
                         ["TC-1.1.1", "TC-1.1.2"])

    def test_new_tasks_inserted_by_story_order(self):
        self.write("stories", _stories_doc(_story("S-1", ["AC-1.1"]), _story("S-2", ["AC-2.1"]),
                                           _story("S-3", ["AC-3.1"])))
        self.write("test-plan", _tp_doc(_tc("TC-1.1.1", "AC-1.1"), _tc("TC-2.1.1", "AC-2.1"),
                                        _tc("TC-3.1.1", "AC-3.1")))
        self.write("sprint", _sprint_doc(_task("S-3", "待办", ["TC-3.1.1"])))
        diyc_writeback.run(self.args("reconcile", apply=True))
        self.assertEqual([t["story"] for t in self.read("sprint")["tasks"]],
                         ["S-1", "S-2", "S-3"])

    def test_existing_relative_order_preserved(self):
        # 既有顺序 S-3, S-1 与 story 顺序相反；新任务 S-2 插到 S-3 前，既有相对顺序不变
        self.write("stories", _stories_doc(_story("S-1", ["AC-1.1"]), _story("S-2", ["AC-2.1"]),
                                           _story("S-3", ["AC-3.1"])))
        self.write("test-plan", _tp_doc(_tc("TC-1.1.1", "AC-1.1"), _tc("TC-2.1.1", "AC-2.1"),
                                        _tc("TC-3.1.1", "AC-3.1")))
        self.write("sprint", _sprint_doc(_task("S-3", "待办", ["TC-3.1.1"]),
                                         _task("S-1", "待办", ["TC-1.1.1"])))
        diyc_writeback.run(self.args("reconcile", apply=True))
        self.assertEqual([t["story"] for t in self.read("sprint")["tasks"]],
                         ["S-2", "S-3", "S-1"])

    def test_missing_stories_rejected(self):
        res = diyc_writeback.run(self.args("reconcile", apply=False))
        self.assertFalse(res["ok"])
        self.assertEqual(res["violations"][0]["code"], "MISSING_FILE")

    def test_broken_test_plan_rejected(self):
        self.write("stories", _stories_doc(_story("S-1", ["AC-1.1"])))
        (self.out / "test-plan.yaml").write_text("test_cases: [oops\n", encoding="utf-8")
        res = diyc_writeback.run(self.args("reconcile", apply=True))
        self.assertFalse(res["ok"])
        self.assertEqual(res["violations"][0]["code"], "UNPARSABLE_YAML")

    def test_empty_stories_rejected(self):
        # 半写守卫：stories.yaml 存在但空 → 拒绝（否则全部任务会被当孤儿清除）
        self.write("stories", {})
        self.write("test-plan", _tp_doc())
        self.write("sprint", _sprint_doc(_task("S-1", "待办", note="既有")))
        res = diyc_writeback.run(self.args("reconcile", apply=True))
        self.assertFalse(res["ok"])
        self.assertEqual(res["violations"][0]["code"], "EMPTY_FIELD")
        self.assertEqual([t["story"] for t in self.read("sprint")["tasks"]], ["S-1"])  # 零写入

    def test_test_plan_without_cases_rejected(self):
        # 半写守卫：test_cases 键缺失（空文件/半写）→ 拒绝
        self.write("stories", _stories_doc(_story("S-1", ["AC-1.1"])))
        self.write("test-plan", {"project": diyc_fixture.project_meta()})
        res = diyc_writeback.run(self.args("reconcile", apply=True))
        self.assertFalse(res["ok"])
        self.assertEqual(res["violations"][0]["code"], "UNPARSABLE_YAML")


if __name__ == "__main__":
    unittest.main()
