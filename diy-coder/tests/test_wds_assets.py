"""diy-wds-assets 冒烟测试（B7b / W2）。

夹具全部落 tempfile；不读写仓库真实 diy-output/；不依赖 git 状态。
覆盖：门禁 / init / ID 铸号 / list / show / check / prompts / 跨技能门禁 /
回执键完整性 / 契约冒烟 / 第 9 活动特有边界 / 资产落位与 viewer 缺口登记。
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

SKILLS = Path(__file__).resolve().parents[1] / "skills"
SKILL = SKILLS / "diy-wds-assets"
ENGINE = SKILL / "scripts" / "wds_assets.py"

ACTIVITY_DIRS = {
    "W": "wireframes",
    "P": "page-designs",
    "U": "ui-elements",
    "I": "icons",
    "M": "images",
    "V": "motion",
    "C": "content",
    "S": "presentation",
}
CODES = list(ACTIVITY_DIRS)
# AS-07 文案条目必须落的六段（`steps/07-content.md:10`；引擎 `--final` 核其在场）
CONTENT_KEYS = (
    "content_purpose",
    "trigger_map_context",
    "awareness_strategy",
    "action_filter",
    "empowerment_frame",
    "structural_order",
)


def run(args, cwd=None):
    # 引擎回执含中文 → 必须显式 utf-8（Windows 默认 GBK 会炸）
    proc = subprocess.run(
        [sys.executable, str(ENGINE), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=cwd,
    )
    payload = None
    if proc.stdout.strip():
        try:
            payload = json.loads(proc.stdout)
        except json.JSONDecodeError:
            payload = None
    return proc.returncode, payload, proc.stdout, proc.stderr


def run_bytes(args, cwd=None):
    """取**字节**回执（回执面契约的回归：不得只读源码 / 断言已解码串——真跑消费者才现形）。"""
    return subprocess.run([sys.executable, str(ENGINE), *args], capture_output=True, cwd=cwd)


def content_block(keys=CONTENT_KEYS):
    """AS-07 的六段内容块（夹具用；值的内容不参与机械核）。"""
    return {key: {"段": key} for key in keys}


def make_presentation_record(ident="AS-08.1", recipe="SD", principles=8, verdict="通过"):
    return {
        "id": ident,
        "recipe": recipe,
        "audience": "投资人",
        "format_card": "data/presentation-formats/sd-slides.md",
        "frames": [{"n": 1, "job": "persuade", "headline": "一句话", "notes": "备注"}],
        "assets": [{"path": "assets/presentation/deck.html", "format": "html"}],
        "review": {"principles": ["懂受众"] * principles, "verdict": verdict},
    }


def write_scenarios(root: Path, status="已定稿"):
    doc = {
        "project": {"name": "fixture", "created": "2026-09-21", "updated": "2026-09-21", "status": status},
        "scenarios": [
            {
                "id": "SC-01",
                "name": "Harriet 的第一次预约",
                "pages": [
                    {"id": "SC-01.P1", "name": "首页", "purpose": "让访客知道我们在做什么"},
                    {"id": "SC-01.P2", "name": "预约页", "purpose": "把访客变成预约"},
                ],
            }
        ],
        "revisions": [],
    }
    (root / "wds-scenarios.yaml").write_text(
        yaml.safe_dump(doc, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )


def write_design_system(root: Path):
    doc = {
        "project": {"name": "fixture", "created": "2026-09-21", "updated": "2026-09-21", "status": "已定稿"},
        "tokens": {"color": {"primary": "#2563EB"}, "spacing": {"md": "16px"}},
        "revisions": [],
    }
    (root / "wds-design-system.yaml").write_text(
        yaml.safe_dump(doc, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )


def make_item(activity_id: str, index: int, code: str, with_asset=True, verdict="通过"):
    item_id = f"{activity_id}.{index}"
    item = {
        "id": item_id,
        "name": f"资产 {item_id}",
        "pages": ["SC-01.P1"],
        "spec": "给访客看的第一屏",
        "variant": "L",
        "size": "1440x900",
        "token_ref": "color.primary",
        "prompt": "minimal, clean, whitespace, 1440x900, grayscale palette",
        "prompt_lang": "en",
        "assets": [],
        "review": {"checks": ["栅格一致", "导航一致", "字阶一致", "间距同阶"], "verdict": verdict},
    }
    if with_asset:
        item["assets"] = [
            {"path": f"assets/{ACTIVITY_DIRS[code]}/{item_id}.html", "format": "html"}
        ]
    return item


def fill_valid(root: Path):
    """把 init 出来的骨架填成一个可定稿的产物。

    AS-07 的条目带 `content` 六段——`--final` 机械核其在场（VA-03c），**夹具失真即为红**。
    """
    path = root / "wds-assets.yaml"
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    doc["stage"] = "收尾"
    for activity in doc["activities"]:
        code = activity["code"]
        if code == "S":
            activity["status"] = "已跳过"
            continue
        activity["status"] = "已评审"
        activity["scope"] = "all"
        activity["style"] = {"design": "minimal", "content": None, "format": None}
        activity["items"] = [make_item(activity["id"], 1, code), make_item(activity["id"], 2, code)]
        if code == "C":
            for item in activity["items"]:
                item["content"] = content_block()
    for activity in doc["activities"]:
        for item in activity.get("items") or []:
            doc["prompts"].append(
                {
                    "id": item["id"],
                    "activity": activity["id"],
                    "target": "外部生成服务",
                    "file": f"assets/{ACTIVITY_DIRS[activity['code']]}/prompts/{item['id']}.md",
                    "exported": True,
                }
            )
    doc["project"]["status"] = "已定稿"
    doc["stage"] = "收尾"
    path.write_text(yaml.safe_dump(doc, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return doc


def dump(root: Path, doc):
    (root / "wds-assets.yaml").write_text(
        yaml.safe_dump(doc, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )


class WdsAssetsTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.out = self.root / "diy-output"
        self.out.mkdir()

    def tearDown(self):
        self._tmp.cleanup()

    def init_ok(self):
        write_scenarios(self.out)
        code, payload, _, err = run(
            ["init", "--project-root", str(self.root), "--output-dir", str(self.out), "--json"]
        )
        self.assertEqual(code, 0, err)
        self.assertIsNotNone(payload)
        return payload

    # ---------------------------------------------------------------- 用法

    def test_no_subcommand_is_usage_error(self):
        code, payload, _, _ = run(["--json"])
        self.assertEqual(code, 2)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["violations"][0]["code"], "ENUM_INVALID")

    def test_unknown_subcommand_is_usage_error(self):
        code, _, _, _ = run(["frobnicate", "--json"])
        self.assertEqual(code, 2)

    # ------------------------------------------------------ 门禁与跨技能读

    def test_init_without_upstream_stops_with_zero_output(self):
        code, payload, _, _ = run(
            ["init", "--project-root", str(self.root), "--output-dir", str(self.out), "--json"]
        )
        self.assertEqual(code, 1)
        self.assertEqual(payload["violations"][0]["code"], "MISSING_FILE")
        self.assertFalse((self.out / "wds-assets.yaml").exists())

    def test_init_with_draft_upstream_stops(self):
        write_scenarios(self.out, status="草稿")
        code, payload, _, _ = run(
            ["init", "--project-root", str(self.root), "--output-dir", str(self.out), "--json"]
        )
        self.assertEqual(code, 1)
        self.assertEqual(payload["violations"][0]["code"], "STATUS_MISMATCH")
        self.assertFalse((self.out / "wds-assets.yaml").exists())

    def test_design_system_missing_degrades_to_warning(self):
        payload = self.init_ok()
        self.assertEqual(payload["warnings"][0]["code"], "MISSING_FILE")
        self.assertEqual(payload["violations"], [])

    def test_design_system_present_clears_warning(self):
        write_design_system(self.out)
        payload = self.init_ok()
        self.assertEqual(payload["warnings"], [])
        self.assertTrue(payload["counts"]["has_design_system"])

    # ------------------------------------------------------------ 骨架断言

    def test_init_writes_eight_activities_in_code_order(self):
        self.init_ok()
        doc = yaml.safe_load((self.out / "wds-assets.yaml").read_text(encoding="utf-8"))
        self.assertEqual(doc["project"]["status"], "草稿")
        self.assertEqual(doc["stage"], "线框")
        self.assertEqual([a["code"] for a in doc["activities"]], CODES)
        self.assertEqual([a["id"] for a in doc["activities"]], [f"AS-{i:02d}" for i in range(1, 9)])
        self.assertEqual(doc["prompts"], [])
        self.assertEqual(doc["presentation"], [])
        self.assertEqual(doc["revisions"], [])

    def test_repeated_init_does_not_clobber(self):
        self.init_ok()
        path = self.out / "wds-assets.yaml"
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        doc["activities"][0]["status"] = "进行中"
        doc["activities"][0]["items"] = [make_item("AS-01", 1, "W")]
        doc["revisions"].append({"date": "2026-09-21", "change": "AS-01.1", "reason": "先出了一版"})
        dump(self.out, doc)
        payload = self.init_ok()
        after = yaml.safe_load(path.read_text(encoding="utf-8"))
        self.assertEqual(after["activities"][0]["status"], "进行中")
        self.assertEqual(after["activities"][0]["items"][0]["id"], "AS-01.1")
        self.assertEqual(len(after["revisions"]), 1)
        self.assertFalse(payload["updated"])

    # ------------------------------------------------------------ list/show

    def test_list_returns_only_agreed_fields(self):
        self.init_ok()
        code, payload, _, _ = run(
            ["list", "--project-root", str(self.root), "--output-dir", str(self.out), "--json"]
        )
        self.assertEqual(code, 0)
        self.assertEqual(len(payload["activities"]), 8)
        row = payload["activities"][0]
        self.assertEqual(
            sorted(row.keys()), sorted(["id", "code", "name", "status", "items", "exported"])
        )

    def test_list_filters_by_status_and_rejects_unknown_value(self):
        self.init_ok()
        code, payload, _, _ = run(
            ["list", "--status", "已跳过", "--project-root", str(self.root), "--output-dir", str(self.out), "--json"]
        )
        self.assertEqual(code, 0)
        self.assertEqual(payload["activities"], [])
        code, payload, _, _ = run(
            ["list", "--status", "随便", "--project-root", str(self.root), "--output-dir", str(self.out), "--json"]
        )
        self.assertEqual(code, 1)
        self.assertEqual(payload["violations"][0]["code"], "ENUM_INVALID")

    def test_show_unknown_id(self):
        self.init_ok()
        code, payload, _, _ = run(
            ["show", "--id", "AS-99.1", "--project-root", str(self.root), "--output-dir", str(self.out), "--json"]
        )
        self.assertEqual(code, 1)
        self.assertEqual(payload["violations"][0]["code"], "UNKNOWN_ID")

    def test_show_whole_file_and_single_activity(self):
        self.init_ok()
        code, payload, _, _ = run(
            ["show", "--project-root", str(self.root), "--output-dir", str(self.out), "--json"]
        )
        self.assertEqual(code, 0)
        self.assertIn("activities", payload["doc"])
        code, payload, _, _ = run(
            ["show", "--id", "AS-01", "--project-root", str(self.root), "--output-dir", str(self.out), "--json"]
        )
        self.assertEqual(code, 0)
        self.assertEqual(payload["record"]["code"], "W")

    # --------------------------------------------------------------- check

    def test_skeleton_checks_clean_but_final_gate_blocks(self):
        self.init_ok()
        code, payload, _, _ = run(
            ["check", "--project-root", str(self.root), "--output-dir", str(self.out), "--json"]
        )
        self.assertEqual(code, 0, payload)
        self.assertEqual(payload["violations"], [])
        code, payload, _, _ = run(
            ["check", "--final", "--project-root", str(self.root), "--output-dir", str(self.out), "--json"]
        )
        self.assertEqual(code, 1)
        self.assertIn("STATUS_MISMATCH", {v["code"] for v in payload["violations"]})

    def test_check_receipt_reports_design_system_presence(self):
        """§4.1 连带：终门回执同 init 暴露 has_design_system（在场/缺席两态）。"""
        self.init_ok()
        code, payload, _, _ = run(
            ["check", "--project-root", str(self.root), "--output-dir", str(self.out), "--json"]
        )
        self.assertEqual(code, 0, payload)
        self.assertFalse(payload["counts"]["has_design_system"])
        write_design_system(self.out)
        code, payload, _, _ = run(
            ["check", "--project-root", str(self.root), "--output-dir", str(self.out), "--json"]
        )
        self.assertEqual(code, 0, payload)
        self.assertTrue(payload["counts"]["has_design_system"])

    def test_check_final_passes_on_complete_product(self):
        self.init_ok()
        fill_valid(self.out)
        code, payload, _, err = run(
            ["check", "--final", "--project-root", str(self.root), "--output-dir", str(self.out), "--json"]
        )
        self.assertEqual(code, 0, payload)
        self.assertEqual(payload["violations"], [])
        self.assertEqual(payload["counts"]["activities"], 8)
        self.assertEqual(payload["counts"]["skipped"], 1)

    def test_check_final_requires_all_items_evaluated(self):
        self.init_ok()
        doc = fill_valid(self.out)
        doc["activities"][1]["status"] = "进行中"
        dump(self.out, doc)
        code, payload, _, _ = run(
            ["check", "--final", "--project-root", str(self.root), "--output-dir", str(self.out), "--json"]
        )
        self.assertEqual(code, 1)
        self.assertIn("STATUS_MISMATCH", {v["code"] for v in payload["violations"]})

    def test_check_flags_asset_path_outside_activity_dir(self):
        self.init_ok()
        doc = fill_valid(self.out)
        doc["activities"][0]["items"][0]["assets"] = [{"path": "assets/icons/wrong.html", "format": "html"}]
        dump(self.out, doc)
        code, payload, _, _ = run(
            ["check", "--final", "--project-root", str(self.root), "--output-dir", str(self.out), "--json"]
        )
        self.assertEqual(code, 1)
        hit = [v for v in payload["violations"] if v["code"] == "SET_MISMATCH"]
        self.assertTrue(hit, payload["violations"])

    def test_check_flags_duplicate_and_mismatched_ids(self):
        self.init_ok()
        doc = fill_valid(self.out)
        doc["activities"][0]["items"][1]["id"] = "AS-01.1"
        dump(self.out, doc)
        code, payload, _, _ = run(
            ["check", "--final", "--project-root", str(self.root), "--output-dir", str(self.out), "--json"]
        )
        self.assertEqual(code, 1)
        self.assertIn("DUPLICATE_ID", {v["code"] for v in payload["violations"]})

        doc = fill_valid(self.out)
        doc["activities"][1]["items"][0]["id"] = "AS-01.7"
        dump(self.out, doc)
        code, payload, _, _ = run(
            ["check", "--final", "--project-root", str(self.root), "--output-dir", str(self.out), "--json"]
        )
        self.assertEqual(code, 1)
        self.assertIn("SET_MISMATCH", {v["code"] for v in payload["violations"]})

    def test_check_flags_orphan_prompt_and_empty_prompt(self):
        self.init_ok()
        doc = fill_valid(self.out)
        doc["prompts"].append(
            {"id": "AS-02.9", "activity": "AS-02", "target": "x", "file": "assets/page-designs/prompts/x.md", "exported": True}
        )
        doc["activities"][0]["items"][0]["prompt"] = "  "
        dump(self.out, doc)
        code, payload, _, _ = run(
            ["check", "--final", "--project-root", str(self.root), "--output-dir", str(self.out), "--json"]
        )
        self.assertEqual(code, 1)
        codes = {v["code"] for v in payload["violations"]}
        self.assertIn("SET_MISMATCH", codes)
        self.assertIn("EMPTY_FIELD", codes)

    def test_check_flags_assumption_and_unresolved_token(self):
        self.init_ok()
        doc = fill_valid(self.out)
        doc["activities"][0]["items"][0]["spec"] = "[假设] 也许首页要三块"
        # 夹具订正（裁定 16 ③ 判据反转）：`{some_token}` 这类**自创**占位符改判后天然放行
        # （已知漏检面）；判据现在抓的是**模板位残留**，故夹具改用骨架里的真模板位。
        doc["activities"][2]["items"][0]["spec"] = "文案里 {产品名} 这个模板位没填掉"
        dump(self.out, doc)
        code, payload, _, _ = run(
            ["check", "--final", "--project-root", str(self.root), "--output-dir", str(self.out), "--json"]
        )
        self.assertEqual(code, 1)
        codes = {v["code"] for v in payload["violations"]}
        self.assertIn("ASSUMPTION_PRESENT", codes)
        self.assertIn("TOKEN_UNRESOLVED", codes)

    def test_check_flags_bad_recipe_and_short_principles(self):
        self.init_ok()
        doc = fill_valid(self.out)
        doc["activities"][7]["status"] = "已评审"
        doc["presentation"] = [
            {
                "id": "AS-08.1",
                "recipe": "ZZ",
                "audience": "投资人",
                "format_card": "data/presentation-formats/pd-pitch.md",
                "frames": [{"n": 1, "job": "persuade", "headline": "一句话", "notes": "备注"}],
                "assets": [{"path": "assets/presentation/deck.html", "format": "html"}],
                "review": {"principles": ["懂受众"], "verdict": "通过"},
            }
        ]
        dump(self.out, doc)
        code, payload, _, _ = run(
            ["check", "--final", "--project-root", str(self.root), "--output-dir", str(self.out), "--json"]
        )
        self.assertEqual(code, 1)
        codes = {v["code"] for v in payload["violations"]}
        self.assertIn("ENUM_INVALID", codes)
        self.assertIn("SET_MISMATCH", codes)

    def test_check_final_requires_presentation_for_activity_eight(self):
        self.init_ok()
        doc = fill_valid(self.out)
        doc["activities"][7]["status"] = "已评审"
        doc["activities"][7]["items"] = [make_item("AS-08", 1, "S")]
        dump(self.out, doc)
        code, payload, _, _ = run(
            ["check", "--final", "--project-root", str(self.root), "--output-dir", str(self.out), "--json"]
        )
        self.assertEqual(code, 1)
        self.assertIn("MISSING_FILE", {v["code"] for v in payload["violations"]})

    # ------------------------------------------- 跨技能机械核（V2-01 回归）

    def test_check_resolves_item_pages_against_upstream(self):
        """`items[].pages[]` 须解析到上游页清单：形态不合 / 上游无此页都判违规。"""
        self.init_ok()
        doc = fill_valid(self.out)
        doc["activities"][0]["items"][0]["pages"] = ["NOT-A-PAGE-ID", "SC-99.P9"]
        dump(self.out, doc)
        code, payload, _, _ = run(
            ["check", "--project-root", str(self.root), "--output-dir", str(self.out), "--json"]
        )
        self.assertEqual(code, 1)
        hits = {(v["where"], v["code"]) for v in payload["violations"]}
        # 夹具上游只有 SC-01.P1 / SC-01.P2
        self.assertIn(("activities[0].items[0].pages[0]", "SET_MISMATCH"), hits)
        self.assertIn(("activities[0].items[0].pages[1]", "UNKNOWN_ID"), hits)

    def test_check_requires_same_upstream_gate_as_init(self):
        """上游缺席 / 未定稿 → 与 init 同门禁（不引入第二套判定）。"""
        self.init_ok()
        fill_valid(self.out)
        (self.out / "wds-scenarios.yaml").unlink()
        code, payload, _, _ = run(
            ["check", "--project-root", str(self.root), "--output-dir", str(self.out), "--json"]
        )
        self.assertEqual(code, 1)
        self.assertEqual(payload["violations"][0]["code"], "MISSING_FILE")

        write_scenarios(self.out, status="草稿")
        code, payload, _, _ = run(
            ["check", "--final", "--project-root", str(self.root), "--output-dir", str(self.out), "--json"]
        )
        self.assertEqual(code, 1)
        self.assertEqual(payload["violations"][0]["code"], "STATUS_MISMATCH")

    # ------------------------------------------------------------- prompts

    def test_prompts_lists_export_index_with_activity_filter(self):
        self.init_ok()
        fill_valid(self.out)
        code, payload, _, _ = run(
            ["prompts", "--project-root", str(self.root), "--output-dir", str(self.out), "--json"]
        )
        self.assertEqual(code, 0)
        self.assertEqual(payload["counts"]["prompts"], 14)
        self.assertEqual(payload["counts"]["exported"], 14)
        code, payload, _, _ = run(
            ["prompts", "--activity", "AS-03", "--project-root", str(self.root), "--output-dir", str(self.out), "--json"]
        )
        self.assertEqual(code, 0)
        self.assertEqual({p["activity"] for p in payload["prompts"]}, {"AS-03"})

    def test_prompts_rejects_unknown_activity(self):
        self.init_ok()
        code, payload, _, _ = run(
            ["prompts", "--activity", "AS-99", "--project-root", str(self.root), "--output-dir", str(self.out), "--json"]
        )
        self.assertEqual(code, 1)
        self.assertEqual(payload["violations"][0]["code"], "ENUM_INVALID")

    # -------------------------------------------------------- 回执键完整性

    def test_receipt_keys_across_subcommands(self):
        payload = self.init_ok()
        common = {"ok", "command", "project_root", "output_dir", "instance", "violations", "warnings", "counts"}
        self.assertTrue(common.issubset(payload.keys()), payload.keys())
        self.assertIsNone(payload["instance"])
        self.assertIn("updated", payload)
        for args in (
            ["list"],
            ["show"],
            ["check"],
            ["prompts"],
        ):
            code, payload, _, _ = run(
                [*args, "--project-root", str(self.root), "--output-dir", str(self.out), "--json"]
            )
            self.assertTrue(common.issubset(payload.keys()), (args, payload.keys()))
            self.assertIsNone(payload["instance"])
            self.assertNotIn("updated", payload)

    def test_missing_product_file_reports_missing_file(self):
        write_scenarios(self.out)
        code, payload, _, _ = run(
            ["list", "--project-root", str(self.root), "--output-dir", str(self.out), "--json"]
        )
        self.assertEqual(code, 1)
        self.assertEqual(payload["violations"][0]["code"], "MISSING_FILE")

    # ------------------------------------------------- 回执面契约（V3-02 / VA-01）

    def test_json_receipt_is_single_line_utf8_bytes(self):
        """VA-01：`--json` 回执须是**可 UTF-8 解码的单行**（本机 stdout 走 cp936 时曾吐 GBK 字节）。"""
        self.init_ok()
        proc = run_bytes(
            ["list", "--project-root", str(self.root), "--output-dir", str(self.out), "--json"]
        )
        self.assertEqual(proc.returncode, 0)
        text = proc.stdout.decode("utf-8")        # 不是 utf-8 在这里直接抛 UnicodeDecodeError
        self.assertEqual(len(text.strip().splitlines()), 1)
        self.assertEqual(text.count("\n"), 1)
        payload = json.loads(text)
        self.assertEqual(payload["project_root"], str(self.root))       # as-given，未 resolve
        self.assertEqual(payload["output_dir"], self.out.resolve().as_posix())

    def test_violation_schema_is_code_where_msg_and_relative_posix(self):
        """契约 §3：违规项逐字 `{code, where, msg}`；路径型 `where` = 相对 project-root + 正斜杠。"""
        write_scenarios(self.out)
        code, payload, _, _ = run(
            ["list", "--project-root", str(self.root), "--output-dir", str(self.out), "--json"]
        )
        self.assertEqual(code, 1)
        item = payload["violations"][0]
        self.assertEqual(sorted(item.keys()), ["code", "msg", "where"])
        self.assertEqual(item["where"], "diy-output/wds-assets.yaml")
        self.assertNotIn("\\", item["where"])

    def test_human_receipt_is_code_where_msg_plus_summary(self):
        write_scenarios(self.out)
        proc = run_bytes(["list", "--project-root", str(self.root), "--output-dir", str(self.out)])
        self.assertEqual(proc.returncode, 1)
        lines = proc.stdout.decode("utf-8").strip().splitlines()
        self.assertTrue(lines[0].startswith("MISSING_FILE diy-output/wds-assets.yaml: "), lines)
        self.assertNotIn("@", lines[0])
        self.assertEqual(lines[-1], "ok=False violations=1 warnings=0")

    # -------------------------------------------------- 只读子命令兜底（V3-03）

    def test_read_only_subcommands_fall_back_to_project_root_output_dir(self):
        """V3-03：只读子命令缺 `--output-dir` → 回落 `{project_root}/diy-output`（改前 rc=2）。"""
        self.init_ok()
        code, payload, _, err = run(["list", "--project-root", str(self.root), "--json"])
        self.assertEqual(code, 0, err)
        self.assertEqual(payload["counts"]["listed"], 8)
        self.assertEqual(payload["output_dir"], self.out.resolve().as_posix())

    def test_init_without_output_dir_is_still_usage_error(self):
        code, payload, _, _ = run(["init", "--project-root", str(self.root), "--json"])
        self.assertEqual(code, 2)
        self.assertEqual(payload["violations"][0]["code"], "ENUM_INVALID")

    # -------------------------------------------- 活动内递增核 / coverage（V3-04 / V2-02）

    def test_check_flags_non_continuous_item_sequence(self):
        """V3-04：活动内 `AS-<nn>.<m>` 须从 1 起连续递增（跳号夹具改前 rc=0）。"""
        self.init_ok()
        doc = fill_valid(self.out)
        doc["activities"][0]["items"][1]["id"] = "AS-01.3"
        dump(self.out, doc)
        code, payload, _, _ = run(
            ["check", "--final", "--project-root", str(self.root), "--output-dir", str(self.out), "--json"]
        )
        self.assertEqual(code, 1)
        hits = [v for v in payload["violations"] if v["where"] == "activities[0]"]
        self.assertEqual([v["code"] for v in hits if v["code"] == "SET_MISMATCH"], ["SET_MISMATCH"])
        self.assertIn("递增", hits[0]["msg"])

    def test_check_accepts_continuous_sequences(self):
        """对照：合法连续序号不产生活动级违规（不得误伤）。"""
        self.init_ok()
        fill_valid(self.out)
        code, payload, _, _ = run(
            ["check", "--final", "--project-root", str(self.root), "--output-dir", str(self.out), "--json"]
        )
        self.assertEqual(code, 0, payload)
        self.assertEqual([v for v in payload["violations"] if v["where"].startswith("activities")], [])

    def test_coverage_reports_unassigned_and_orphan(self):
        """V2-02：`check` 回执顶层给 `coverage`（形状取 `09-finish.md:23-25`）。"""
        self.init_ok()
        doc = fill_valid(self.out)
        doc["activities"][0]["items"][0]["pages"] = ["SC-01.P1", "SC-99.P9"]
        dump(self.out, doc)
        code, payload, _, _ = run(
            ["check", "--project-root", str(self.root), "--output-dir", str(self.out), "--json"]
        )
        self.assertEqual(code, 1)
        self.assertEqual(payload["coverage"]["unassigned"], ["SC-01.P2"])
        self.assertEqual(payload["coverage"]["orphan"], ["SC-99.P9"])

    def test_coverage_key_present_and_empty_when_fully_covered(self):
        """两列都空也须在场（空列表），否则模型取不到键。"""
        self.init_ok()
        doc = fill_valid(self.out)
        for activity in doc["activities"]:
            for item in activity.get("items") or []:
                item["pages"] = ["SC-01.P1", "SC-01.P2"]
        dump(self.out, doc)
        code, payload, _, _ = run(
            ["check", "--final", "--project-root", str(self.root), "--output-dir", str(self.out), "--json"]
        )
        self.assertEqual(code, 0, payload)
        self.assertEqual(payload["coverage"], {"unassigned": [], "orphan": []})

    # ------------------------------------------ ID 空间一致（N1 / N2 = 裁定 9 / 10）

    def test_show_reaches_presentation_and_prompts_id_space(self):
        """N1：`show --id` 须够到 `presentation[]` / `prompts[]`（改前 presentation 记录 rc=1）。"""
        self.init_ok()
        doc = fill_valid(self.out)
        doc["presentation"] = [make_presentation_record("AS-08.5")]
        dump(self.out, doc)
        code, payload, _, _ = run(
            ["show", "--id", "AS-08.5", "--project-root", str(self.root), "--output-dir", str(self.out), "--json"]
        )
        self.assertEqual(code, 0)
        self.assertEqual(payload["record"]["recipe"], "SD")
        code, payload, _, _ = run(
            ["show", "--id", "AS-01.2", "--project-root", str(self.root), "--output-dir", str(self.out), "--json"]
        )
        self.assertEqual(code, 0)
        self.assertEqual(payload["record"]["id"], "AS-01.2")

    def test_check_flags_presentation_id_form_and_duplicate(self):
        """N2：`presentation[].id` 形态 / 唯一性 / 与 AS-08 同源三核（改前零校验）。"""
        self.init_ok()
        doc = fill_valid(self.out)
        doc["activities"][7]["status"] = "已评审"
        doc["activities"][7]["items"] = [make_item("AS-08", 1, "S")]
        doc["presentation"] = [make_presentation_record("AS-07.1")]
        dump(self.out, doc)
        code, payload, _, _ = run(
            ["check", "--final", "--project-root", str(self.root), "--output-dir", str(self.out), "--json"]
        )
        self.assertEqual(code, 1)
        self.assertIn(("SET_MISMATCH", "presentation[0]"),
                      {(v["code"], v["where"]) for v in payload["violations"]})

        doc = fill_valid(self.out)
        doc["activities"][7]["status"] = "已评审"
        doc["activities"][7]["items"] = [make_item("AS-08", 1, "S")]
        doc["presentation"] = [make_presentation_record("AS-08.1"), make_presentation_record("AS-08.1")]
        dump(self.out, doc)
        code, payload, _, _ = run(
            ["check", "--final", "--project-root", str(self.root), "--output-dir", str(self.out), "--json"]
        )
        self.assertEqual(code, 1)
        dups = [v for v in payload["violations"] if v["where"] == "presentation[1]"]
        self.assertIn("重复", dups[0]["msg"])

    # ---------------------------------- 占位符判据反转（VA-02）/ 六段核（VA-03c）/ 逃逸（VA-07）

    def test_prompt_json_example_is_not_flagged(self):
        """VA-02 夹具 1：prompt 里的 JSON 示例不再误杀（改前 rc=1）。"""
        self.init_ok()
        doc = fill_valid(self.out)
        doc["activities"][0]["items"][0]["prompt"] = (
            '生成落地页 HTML，配置示例 {"breakpoint": "1440"}，占位 {page_name} 留空'
        )
        dump(self.out, doc)
        code, payload, _, _ = run(
            ["check", "--final", "--project-root", str(self.root), "--output-dir", str(self.out), "--json"]
        )
        self.assertEqual(code, 0, payload)
        self.assertEqual(payload["violations"], [])

    def test_prompt_template_slot_residue_is_flagged(self):
        """VA-02 夹具 2（防漏检）：模板位残留照抓——清单**解析自模板骨架**，非硬编码。"""
        self.init_ok()
        doc = fill_valid(self.out)
        doc["activities"][0]["items"][0]["prompt"] = "产品：{产品名}——{一句话定位}"
        dump(self.out, doc)
        code, payload, _, _ = run(
            ["check", "--final", "--project-root", str(self.root), "--output-dir", str(self.out), "--json"]
        )
        self.assertEqual(code, 1)
        hits = [v for v in payload["violations"] if v["code"] == "TOKEN_UNRESOLVED"]
        self.assertTrue(hits, payload["violations"])
        self.assertIn("wds-assets.yaml line ", hits[0]["where"])   # where 含文件段且正斜杠
        self.assertIn("占位符未填", hits[0]["msg"])

    def test_content_output_template_slot_residue_is_flagged(self):
        """V-A F-1（判据反转扩面）：第二模板 `content-output` 的模板位残留同样判 `TOKEN_UNRESOLVED`。"""
        self.init_ok()
        doc = fill_valid(self.out)
        doc["activities"][6]["items"][0]["content"]["content_purpose"] = "# 文案成稿 — {内容段名}"
        dump(self.out, doc)
        code, payload, _, _ = run(
            ["check", "--final", "--project-root", str(self.root), "--output-dir", str(self.out), "--json"]
        )
        self.assertEqual(code, 1)
        hits = [v for v in payload["violations"] if v["code"] == "TOKEN_UNRESOLVED"]
        self.assertTrue(hits, payload["violations"])
        self.assertIn("占位符未填", hits[0]["msg"])

    def test_project_root_and_output_dir_tokens_pass(self):
        """`{project-root}` / `{output_dir}` 天然不在模板位清单（`TOKEN_WHITELIST` 已删）。"""
        self.init_ok()
        doc = fill_valid(self.out)
        doc["activities"][0]["items"][0]["prompt"] = "跑 {project-root}/.claude 与 {output_dir}/assets"
        dump(self.out, doc)
        code, payload, _, _ = run(
            ["check", "--final", "--project-root", str(self.root), "--output-dir", str(self.out), "--json"]
        )
        self.assertEqual(code, 0, payload)

    def test_final_requires_as07_content_six_keys(self):
        """VA-03c：AS-07 条目缺 `content` 六段 → EMPTY_FIELD（改前 rc=0）。"""
        self.init_ok()
        doc = fill_valid(self.out)
        del doc["activities"][6]["items"][0]["content"]
        doc["activities"][6]["items"][1]["content"].pop("action_filter")
        dump(self.out, doc)
        code, payload, _, _ = run(
            ["check", "--final", "--project-root", str(self.root), "--output-dir", str(self.out), "--json"]
        )
        self.assertEqual(code, 1)
        wheres = {(v["code"], v["where"]) for v in payload["violations"]}
        self.assertIn(("EMPTY_FIELD", "activities[6].items[0].content"), wheres)
        self.assertIn(("EMPTY_FIELD", "activities[6].items[1].content"), wheres)

    def test_final_does_not_check_content_for_other_activities(self):
        """覆盖面纪律：只有 AS-07 要 `content`（其余活动的条目无此键不得判红）。"""
        self.init_ok()
        fill_valid(self.out)
        code, payload, _, _ = run(
            ["check", "--final", "--project-root", str(self.root), "--output-dir", str(self.out), "--json"]
        )
        self.assertEqual(code, 0, payload)

    def test_dotdot_paths_are_rejected(self):
        """VA-07：含 `..` 的资产 / 提示词路径逃逸被拒（改前 `assets/<活动>/../../x` rc=0）。"""
        self.init_ok()
        doc = fill_valid(self.out)
        doc["activities"][0]["items"][0]["assets"] = [
            {"path": "assets/wireframes/../../outside.html", "format": "html"}
        ]
        doc["prompts"][0]["file"] = "assets/wireframes/prompts/../../outside.md"
        dump(self.out, doc)
        code, payload, _, _ = run(
            ["check", "--final", "--project-root", str(self.root), "--output-dir", str(self.out), "--json"]
        )
        self.assertEqual(code, 1)
        hits = {(v["code"], v["where"]) for v in payload["violations"]}
        self.assertIn(("SET_MISMATCH", "activities[0].items[0].assets[0]"), hits)
        self.assertIn(("SET_MISMATCH", "prompts[0]"), hits)


class WdsAssetsDirectOutputTest(unittest.TestCase):
    """W8 产出模型修复的回归：直出产物 + 双向对表 + 提示词通道未回归（C·3a 段2）。"""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.out = self.root / "diy-output"
        self.out.mkdir()

    def tearDown(self):
        self._tmp.cleanup()

    # ------------------------------------------------- 偏移点：全树措辞归零

    def test_offset_wording_purged_across_skill_tree(self):
        """7+1 处偏移：「唯一生成通道」家族措辞在本技能树内归零（含引擎 docstring）。"""
        banned = ("唯一生成通道", "唯一的生成通道", "唯一的生成路径", "唯一的生成入口")
        for path in SKILL.rglob("*"):
            if path.suffix not in {".md", ".py", ".yaml"} or "__pycache__" in path.parts:
                continue
            body = path.read_text(encoding="utf-8")
            for phrase in banned:
                self.assertNotIn(phrase, body, f"{path}: {phrase}")

    def test_main_file_declares_direct_output(self):
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("产物由本技能直接产出", text)
        self.assertIn("照片类通道 + 用户可选项", text)
        # 英语 description 同步改写（不再是 prompts-only 口径）
        self.assertIn("produces the artifacts itself", text)

    def test_each_activity_declares_its_artifact_form(self):
        """8 活动的产出定义：各步写明直出形态与落点。"""
        expected = {
            "01-wireframes.md": ("直出 HTML", "assets/wireframes/"),
            "02-page-designs.md": ("直出 HTML", "assets/page-designs/"),
            "03-ui-elements.md": ("直出 HTML / CSS", "assets/ui-elements/"),
            "04-icons.md": ("直写 SVG", "assets/icons/"),
            "05-images.md": ("两路产出", "assets/images/"),
            "06-motion.md": ("直出 CSS / SVG 关键帧代码", "assets/motion/"),
            "07-content.md": ("成稿 `.md`", "assets/content/"),
            "08-presentation.md": ("直出 HTML 拼版", "assets/presentation/"),
        }
        for name, (marker, path_token) in expected.items():
            body = (SKILL / "steps" / name).read_text(encoding="utf-8")
            self.assertIn(marker, body, name)
            self.assertIn(path_token, body, name)
            self.assertIn("**Write (output):**", body, name)
            self.assertIn("导出", body, name)     # 提示词通道仍在场（可选项）

    def test_images_two_path_split(self):
        """M 图片两路：插画 / 示意 / 抽象直出 SVG；照片类走提示词通道。"""
        body = (SKILL / "steps" / "05-images.md").read_text(encoding="utf-8")
        self.assertIn("直出路", body)
        self.assertIn("提示词路", body)
        self.assertIn("photorealistic", body)
        self.assertIn("hyper-realistic", body)
        self.assertIn("矢量 = 文本", body)

    def test_browser_check_discipline_present_for_html_activities(self):
        """判据 ⑤：直出 HTML 后「浏览器实际打开核对」（规则 12）逐活动可执行。"""
        for name in (
            "01-wireframes.md",
            "02-page-designs.md",
            "03-ui-elements.md",
            "08-presentation.md",
        ):
            body = (SKILL / "steps" / name).read_text(encoding="utf-8")
            self.assertIn("浏览器实开核对", body, name)
            self.assertIn("playwright", body, name)
        motion = (SKILL / "steps" / "06-motion.md").read_text(encoding="utf-8")
        self.assertIn("浏览器里跑一遍", motion)
        self.assertIn("用浏览器实际打开核对", (SKILL / "SKILL.md").read_text(encoding="utf-8"))

    # --------------------------------------------------- 8 活动直出 + 双向核

    # (活动码 → 目录, 产物格式, 产物正文)：一张表覆盖 8 活动的直出形态
    ARTIFACTS = {
        "W": ("wireframes", "html", '<!doctype html><html lang="zh"><title>线框</title></html>'),
        "P": ("page-designs", "html", '<!doctype html><html lang="zh"><title>页面稿</title></html>'),
        "U": ("ui-elements", "css", ".btn-primary { color: #2563EB; }"),
        "I": ("icons", "svg", '<svg viewBox="0 0 24 24"><path d="M4 12h16"/></svg>'),
        "M": ("images", "svg", '<svg viewBox="0 0 16 9"><rect width="16" height="9"/></svg>'),
        "V": ("motion", "css", "@keyframes fade-in { from { opacity: 0 } }"),
        "C": ("content", "md", "# 首页文案成稿\n\n第一版正文。"),
        "S": ("presentation", "html", '<!doctype html><html lang="zh"><title>路演</title></html>'),
    }

    def init_direct(self):
        """按新模型填一份**带实体文件**的产物：8 活动直出，仅照片类走提示词。"""
        write_scenarios(self.out)
        code, payload, _, err = run(
            ["init", "--project-root", str(self.root), "--output-dir", str(self.out), "--json"]
        )
        self.assertEqual(code, 0, err)
        path = self.out / "wds-assets.yaml"
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        for activity in doc["activities"]:
            code_ = activity["code"]
            directory, fmt, body = self.ARTIFACTS[code_]
            activity["status"] = "已评审"
            activity["scope"] = "all"
            activity["style"] = {"design": "minimal", "content": None, "format": None}
            item = make_item(activity["id"], 1, code_, with_asset=False)
            rel = f"assets/{directory}/{item['id']}.{fmt}"
            target = self.out / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(body, encoding="utf-8")
            item["assets"] = [{"path": rel, "format": fmt}]
            activity["items"] = [item]
            if code_ == "C":
                item["content"] = content_block()
        record = make_presentation_record("AS-08.1")
        record["assets"] = [{"path": "assets/presentation/AS-08.1.html", "format": "html"}]
        doc["presentation"] = [record]
        # 照片类（M）走提示词通道：导出文件落在 assets/images/prompts/——双向核须排除该子目录
        prompt_file = self.out / "assets/images/prompts/AS-05.1.md"
        prompt_file.parent.mkdir(parents=True, exist_ok=True)
        prompt_file.write_text("# AS-05.1 照片提示词\nminimal, natural light\n", encoding="utf-8")
        doc["prompts"] = [
            {
                "id": "AS-05.1",
                "activity": "AS-05",
                "target": "外部图像服务",
                "file": "assets/images/prompts/AS-05.1.md",
                "exported": True,
            }
        ]
        doc["project"]["status"] = "已定稿"
        doc["stage"] = "收尾"
        dump(self.out, doc)
        return doc

    def reconcile(self):
        """资产双向对表（`prompts/` 子目录除外——它归提示词通道）。"""
        doc = yaml.safe_load((self.out / "wds-assets.yaml").read_text(encoding="utf-8"))
        declared: set[str] = set()
        for activity in doc["activities"]:
            for item in activity.get("items") or []:
                for asset in item.get("assets") or []:
                    declared.add(asset["path"])
        for record in doc.get("presentation") or []:
            for asset in record.get("assets") or []:
                declared.add(asset["path"])
        on_disk: set[str] = set()
        for activity_dir in (self.out / "assets").iterdir():
            if not activity_dir.is_dir():
                continue
            for path in activity_dir.rglob("*"):
                rel = path.relative_to(self.out).as_posix()
                if path.is_file() and "prompts" not in rel.split("/"):
                    on_disk.add(rel)
        return sorted(declared - on_disk), sorted(on_disk - declared)

    def test_direct_artifacts_pass_final_gate_and_reconcile_both_ways(self):
        self.init_direct()
        code, payload, _, _ = run(
            ["check", "--final", "--project-root", str(self.root), "--output-dir", str(self.out), "--json"]
        )
        self.assertEqual(code, 0, payload)
        self.assertEqual(payload["counts"]["items"], 8)
        forward, reverse = self.reconcile()
        self.assertEqual(forward, [])          # assets[] 每条都有实体文件
        self.assertEqual(reverse, [])          # 目录下每个产物都有条目（提示词包不算）

        # 负向对照 1：删一份实体文件 → 正向差集现形（这套对表不是「假机械核」）
        (self.out / "assets/icons/AS-04.1.svg").unlink()
        self.assertEqual(self.reconcile()[0], ["assets/icons/AS-04.1.svg"])

        # 负向对照 2：散一件无主产物 → 反向差集现形；提示词文件不误判为孤儿
        stray = self.out / "assets/wireframes/stray.html"
        stray.write_text("<html></html>", encoding="utf-8")
        self.assertEqual(self.reconcile()[1], ["assets/wireframes/stray.html"])

    def test_prompt_channel_exported_flip_not_regressed(self):
        """判据 ③：`prompts[].exported` 翻转机制与终门判定原样保留。"""
        self.init_direct()
        code, payload, _, _ = run(
            ["prompts", "--project-root", str(self.root), "--output-dir", str(self.out), "--json"]
        )
        self.assertEqual(code, 0, payload)
        self.assertEqual([p["id"] for p in payload["prompts"]], ["AS-05.1"])
        self.assertTrue(payload["prompts"][0]["exported"])

        doc = yaml.safe_load((self.out / "wds-assets.yaml").read_text(encoding="utf-8"))
        doc["prompts"][0]["exported"] = False
        dump(self.out, doc)
        code, payload, _, _ = run(
            ["check", "--final", "--project-root", str(self.root), "--output-dir", str(self.out), "--json"]
        )
        self.assertEqual(code, 1)
        hits = [v for v in payload["violations"] if v["where"] == "prompts[0]"]
        self.assertTrue(hits, payload["violations"])
        self.assertEqual(hits[0]["code"], "SET_MISMATCH")
        self.assertIn("已导出", hits[0]["msg"])


class WdsAssetsContractTest(unittest.TestCase):
    """契约冒烟：母本锚串 / 结构 / 数据资产 / 红线。"""

    def skill_text(self):
        return (SKILL / "SKILL.md").read_text(encoding="utf-8")

    def test_main_file_is_thin_with_four_sections(self):
        text = self.skill_text()
        self.assertLessEqual(len(text.splitlines()), 90)
        for section in ("## 激活时", "## 工作流", "## 结构", "## 规则"):
            self.assertIn(section, text)

    def test_suite_text_anchors_verbatim(self):
        text = self.skill_text()
        anchors = [
            '实例解析（FR-4.5/D-9）由工具脚本执行：运行 `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" resolve [--instance <name>] --json`，把回执里的 `output_dir` 当作本次运行唯一的读写根目录。',
            "读 `{project-root}/diy-coder.yaml`；解析 `project.communication_language` / `project.document_output_language` / `paths.output_dir`。",
            "全程用 `communication_language` 对话；产物里的叙述文字用 `document_output_language` 写。机器锚点（ID、枚举值、文件名）逐字保留。",
            "缺省链：`paths.output_dir` 一律取 `diyc.py resolve` 回执（引擎缺省 `diy-output`，异常形状降级并 warning）；缺 `document_output_language` 落 `project.communication_language`；两者皆缺则跟随用户当前消息的语言，并在收尾一行说明。",
            "实例名只在本次激活参数出现 `--instance <name>` 时才传（无头侧入口 `runner.py --instance`；交互侧由用户在发起消息里给出同一旗标）；未传时回执的 `output_dir` 即主线平铺根。",
            "读取纪律：预载预算 = 本文件、上述配置与回执、`steps/` 下当前那一个文件——绝不批量预载；执行期读取以每个步骤开头的 `Read (input)` 行为唯一权威，**主文件不列举封闭清单**。",
            '渲染是静默旁路——只写调用命令，不新增「打开浏览器 / 报告路径等待查看 / 阻塞等待」交互点：`python "{project-root}/.claude/skills/diy-viewer/scripts/viewer.py" --project-root "{project-root}"`（resolved 实例时附 `--instance <name>`）。',
            "- **精准简练。** 写进产物的每条内容都要精准、简练：一条只讲一件事；不复述上游已写的信息（引用 ID）；不写没有信息量的套话。",
            "- **写作纪律。** 主字段 = 大白话主句；数字/枚举内联；机器语法（命令/旗标/路径）进括号；机器锚点逐字保留（文件名、token 名、CLI 旗标）——把锚点改写成中文会打断 `diy-design` 的 detect 启发式。schema 若定义 `plain`：一行写清该条目为什么存在，绝不写是什么（转述会漂移）；只写难懂的条目。若定义 `detail`：过程叙述——结论留在主字段。",
        ]
        for anchor in anchors:
            self.assertIn(anchor, text, anchor[:40])

    def test_frontmatter_five_fields(self):
        head = self.skill_text().split("---")[1]
        self.assertIn("phase: 2-wds-design", head)
        self.assertIn("precededBy: [diy-wds-scenarios]", head)
        self.assertIn("followedBy: []", head)
        self.assertIn("required: false", head)
        self.assertIn("line: wds", head)
        self.assertIn("outputs: wds-assets.yaml", head)

    def test_terminal_gate_points_to_own_engine_only(self):
        text = self.skill_text()
        self.assertIn("wds_assets.py", text)
        self.assertIn("check --final", text)
        # 红线：不得教模型改用 diyc.py 的 WDS 型终门（禁止句本身可以出现）
        self.assertIn("不得改用 `diyc.py check --type`", text)

    def test_no_red_line_teaching_anywhere_in_skill_tree(self):
        # 只抓「教模型去调」的形态：`check --type <WDS 型>` / `--type <WDS 型> --previous`
        teaching = re.compile(r"check\s+--type\s+(wds|design-system|assets|evolution|analysis)", re.I)
        for path in SKILL.rglob("*.md"):
            body = path.read_text(encoding="utf-8")
            self.assertIsNone(
                teaching.search(body.replace("不得改用 `diyc.py check --type`", "")), str(path)
            )

    def test_step_files_and_section_counts(self):
        expected = {
            "01-wireframes.md": 5,
            "02-page-designs.md": 5,
            "03-ui-elements.md": 5,
            "04-icons.md": 5,
            "05-images.md": 6,
            "06-motion.md": 5,
            "07-content.md": 7,
            "08-presentation.md": 6,
            "09-finish.md": 4,
        }
        for name, count in expected.items():
            body = (SKILL / "steps" / name).read_text(encoding="utf-8")
            found = sum(1 for line in body.splitlines() if line.startswith("## 第 "))
            self.assertEqual(found, count, name)
            self.assertIn("**Read (input):**", body, name)
            self.assertIn("**Write (output):**", body, name)

    # ------------------------------------------- 第 9 活动：8 原则 / 7 配方

    def test_eight_principles_present_in_presentation_step(self):
        body = (SKILL / "steps" / "08-presentation.md").read_text(encoding="utf-8")
        for principle in (
            "懂受众",
            "视觉层级驱动注意力",
            "清晰优先于机巧",
            "每帧都有职责",
            "三秒规则",
            "留白构建焦点",
            "一致性即专业",
            "故事结构普适",
        ):
            self.assertIn(principle, body, principle)

    def test_seven_recipes_have_cards_and_prompt_texts(self):
        cards = {
            "SD": ("sd-slides.md", "Design a multi-slide presentation using Excalidraw frame-based layout."),
            "EX": ("ex-explainer.md", "engagement hooks at 0s, 3s, and every 15-30s"),
            "PD": ("pd-pitch.md", "problem → solution → traction → ask"),
            "CT": ("ct-talk.md", "Include speaker notes per slide"),
            "IN": ("in-infographic.md", "Choose the chart/diagram type that lets the data tell the story"),
            "VM": ("vm-concept-illustration.md", "Rube Goldberg machine, journey map, or creative-process diagram"),
            "CV": ("cv-concept-visual.md", "make the image the explanation"),
        }
        index = (SKILL / "data" / "presentation-formats" / "index.md").read_text(encoding="utf-8")
        for code, (filename, snippet) in cards.items():
            path = SKILL / "data" / "presentation-formats" / filename
            self.assertTrue(path.exists(), filename)
            body = path.read_text(encoding="utf-8")
            self.assertIn(snippet, body, code)
            self.assertIn(filename, index, code)
            self.assertIn(f"`{code}`", index, code)

    def test_presentation_step_binds_index_and_cards(self):
        body = (SKILL / "steps" / "08-presentation.md").read_text(encoding="utf-8")
        for code in ("SD", "EX", "PD", "CT", "IN", "VM", "CV"):
            self.assertIn(f"`{code}`", body)
        self.assertIn("一帧 = 一页", body)
        self.assertIn("Excalidraw", body)

    # ------------------------------------------------------ 数据资产与摘留

    def test_style_cards_kept_verbatim(self):
        design = sorted(p.stem for p in (SKILL / "data" / "styles" / "design-styles").glob("*.md"))
        content = sorted(p.stem for p in (SKILL / "data" / "styles" / "content-styles").glob("*.md"))
        self.assertEqual(
            design, ["brutalist", "corporate", "editorial", "minimal", "organic", "playful"]
        )
        self.assertEqual(
            content,
            [
                "3d-render",
                "comic-book",
                "flat-design",
                "hyper-realistic",
                "illustration",
                "isometric",
                "line-art",
                "pencil-sketch",
                "photorealistic",
                "watercolor",
            ],
        )
        body = (SKILL / "data" / "styles" / "design-styles" / "minimal.md").read_text(encoding="utf-8")
        self.assertIn("`minimal, clean, whitespace, simple, uncluttered, modern, restrained, elegant simplicity`", body)

    def test_three_non_service_assets_retained(self):
        iteration = (SKILL / "data" / "iteration-refinement.md").read_text(encoding="utf-8")
        self.assertIn("第一拍", iteration)
        self.assertIn("第三拍", iteration)
        flags = (SKILL / "data" / "stop-red-flags.md").read_text(encoding="utf-8")
        for name in ("过早优化", "过度工程", "分析瘫痪", "工具崇拜"):
            self.assertIn(name, flags)
        skeleton = (SKILL / "templates" / "prompt-export.template.md").read_text(encoding="utf-8")
        self.assertIn("=== 生成指令 ===", skeleton)
        # 去服务绑定：额度 / 站点地址这类「用它生成」的指令不得残留（出处注记里点名是允许的）
        for banned in ("stitch.withgoogle.com", "350 standard", "200 pro"):
            self.assertNotIn(banned, skeleton)
        self.assertIn("去 **Stitch** 服务绑定", skeleton)

    def test_content_template_keeps_six_models(self):
        body = (SKILL / "templates" / "content-output.template.md").read_text(encoding="utf-8")
        for model in ("Trigger Map", "Action Mapping", "Badass Users", "Golden Circle"):
            self.assertIn(model, body)
        # Alpha Feedback 段裁（模板正文不得再有该节；出处注记里点名是允许的）
        self.assertNotIn("**Alpha Feedback:**", body)
        self.assertIn("Alpha 声明", body)

    def test_schema_template_present(self):
        body = (SKILL / "templates" / "wds-assets.schema.yaml").read_text(encoding="utf-8")
        for key in ("activities:", "prompts:", "presentation:", "revisions:"):
            self.assertIn(key, body)

    # ------------------------------------------- 资产落位与 viewer 缺口登记

    def test_asset_subdir_convention_and_viewer_gap_registered(self):
        text = self.skill_text()
        self.assertIn("assets/<活动>/", text)
        self.assertIn("viewer.py", text)
        self.assertIn("渲染不到", text)
        finish = (SKILL / "steps" / "09-finish.md").read_text(encoding="utf-8")
        self.assertIn("assets/<活动>/prompts/", finish)
        self.assertIn("渲染不到", finish)

    def test_no_external_service_claims(self):
        text = self.skill_text()
        self.assertIn("不接任何外部服务", text)
        for path in SKILL.rglob("*.md"):
            body = path.read_text(encoding="utf-8")
            for banned in ("npx @wds", "figma-mcp-server", "stitch.withgoogle.com"):
                self.assertNotIn(banned, body, str(path))


if __name__ == "__main__":
    unittest.main()
