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
    """把 init 出来的骨架填成一个可定稿的产物。"""
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
        doc["activities"][2]["items"][0]["spec"] = "引用 {some_token} 的未知令牌"
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
