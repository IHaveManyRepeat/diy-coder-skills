"""diy-wds-system 契约冒烟测试（B7b · W1）。

八类必备（任务书 §2.2 裁定 20）：门禁 / init / ID 铸号 / list / check / 跨技能门禁 /
回执键完整性 / 契约冒烟 + 本技能特有边界（token 派生自 design.yaml 的引用一致性、
组件 ID 的 26 前缀 / 6 分类 / 编号递增）。

夹具全落 tempfile；不读写仓库真实 diy-output/；不依赖 git 状态。
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent          # diy-coder/
SKILL = ROOT / "skills" / "diy-wds-system"
ENGINE = SKILL / "scripts" / "wds_system.py"
SKILL_MD = SKILL / "SKILL.md"
STEPS = SKILL / "steps"
PRODUCT = "wds-design-system.yaml"

# ── 冻结表（机械取数：源 step-08b:68–95 的 26 行箭头表 / :117–122 的 6 行分类表）──
PREFIXES = [
    "btn", "inp", "crd", "mdl", "drp", "chk", "rad", "tgl", "tab", "acc", "alt",
    "bdg", "avt", "icn", "img", "lnk", "txt", "hdg", "lst", "tbl", "frm", "cnt",
    "grd", "flx", "div", "spc",
]
CATEGORIES = ["Interactive", "Form", "Layout", "Content", "Feedback", "Navigation"]

# ── 母本 §1/§2/§3/§4/§5/§6 逐字（suite-texts.md；禁改写）──
M1 = ('实例解析（FR-4.5/D-9）由工具脚本执行：运行 `python "{project-root}/.claude/skills/'
      'diy-tools/scripts/diyc.py" resolve [--instance <name>] --json`，把回执里的 `output_dir` '
      '当作本次运行唯一的读写根目录。')
M2 = ('- **写作纪律。** 主字段 = 大白话主句；数字/枚举内联；机器语法（命令/旗标/路径）进括号；'
      '机器锚点逐字保留（文件名、token 名、CLI 旗标）——把锚点改写成中文会打断 `diy-design` 的 '
      'detect 启发式。schema 若定义 `plain`：一行写清该条目为什么存在，绝不写是什么（转述会漂移）；'
      '只写难懂的条目。若定义 `detail`：过程叙述——结论留在主字段。')
M3A = ('读 `{project-root}/diy-coder.yaml`；解析 `project.communication_language` / '
       '`project.document_output_language` / `paths.output_dir`。')
M3B = ('全程用 `communication_language` 对话；产物里的叙述文字用 `document_output_language` 写。'
       '机器锚点（ID、枚举值、文件名）逐字保留。')
M3C = ('缺省链：`paths.output_dir` 一律取 `diyc.py resolve` 回执（引擎缺省 `diy-output`，异常形状降级并 '
       'warning）；缺 `document_output_language` 落 `project.communication_language`；两者皆缺则跟随'
       '用户当前消息的语言，并在收尾一行说明。')
M3D = ('实例名只在本次激活参数出现 `--instance <name>` 时才传（无头侧入口 `runner.py --instance`；'
       '交互侧由用户在发起消息里给出同一旗标）；未传时回执的 `output_dir` 即主线平铺根。')
M4 = ('读取纪律：预载预算 = 本文件、上述配置与回执、`steps/` 下当前那一个文件——绝不批量预载；'
      '执行期读取以每个步骤开头的 `Read (input)` 行为唯一权威，**主文件不列举封闭清单**。')
M5 = ('渲染是静默旁路——只写调用命令，不新增「打开浏览器 / 报告路径等待查看 / 阻塞等待」交互点：'
      '`python "{project-root}/.claude/skills/diy-viewer/scripts/viewer.py" --project-root '
      '"{project-root}"`（resolved 实例时附 `--instance <name>`）。')
M6 = ('- **精准简练。** 写进产物的每条内容都要精准、简练：一条只讲一件事；不复述上游已写的信息'
      '（引用 ID）；不写没有信息量的套话。')

COMPONENT_KEYS = [
    "id", "name", "prefix", "category", "complexity", "status", "variants", "states",
    "styling", "behavior", "accessibility", "usage", "used_in", "token_refs", "version",
]


# ────────────────────────────── 夹具 ──────────────────────────────

def run(*args, cwd=None):
    p = subprocess.run(
        [sys.executable, str(ENGINE), *args],
        capture_output=True, text=True, encoding="utf-8", cwd=cwd,
    )
    return p.returncode, p.stdout, p.stderr


def receipt(out):
    """取 stdout 末行 JSON 回执。"""
    return json.loads(out.strip().splitlines()[-1])


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.out = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    # 上游门禁夹具：wds-scenarios.yaml（B7a 已交付）
    def seed_scenarios(self, status="已定稿", pages=("SC-01.P1",)):
        doc = {"project": {"name": "demo", "created": "2026-09-21",
                           "updated": "2026-09-21", "status": status},
               "scenarios": [{"id": "SC-01",
                              "pages": [{"id": p} for p in pages]}]}
        (self.out / "wds-scenarios.yaml").write_text(
            yaml.safe_dump(doc, allow_unicode=True, sort_keys=False), encoding="utf-8")

    def seed_design(self, color=None, spacing_scale=None):
        doc = {"project": {"name": "demo", "status": "已定稿"},
               "tokens": {
                   "color": color or {"bg": "#fff", "surface": "#eee", "text": "#111",
                                      "text_muted": "#666", "accent": "#06f",
                                      "accent_text": "#fff"},
                   "spacing": {"unit": "4px",
                               "scale": spacing_scale or [4, 6, 8, 12, 16, 24, 32, 48, 64]},
                   "typography": {"family_base": "Inter", "family_heading": "Inter",
                                  "scale": [12, 14, 16, 20, 24, 30, 36, 44]},
               }}
        (self.out / "design.yaml").write_text(
            yaml.safe_dump(doc, allow_unicode=True, sort_keys=False), encoding="utf-8")

    def base_args(self):
        return ["--project-root", str(self.out), "--output-dir", str(self.out)]

    def init_ok(self, *extra):
        rc, out, err = run("init", "--prefix", "btn", *extra, *self.base_args(), "--json")
        self.assertEqual(rc, 0, out + err)
        return receipt(out)

    def load(self):
        return yaml.safe_load((self.out / PRODUCT).read_text(encoding="utf-8"))

    def save(self, doc):
        (self.out / PRODUCT).write_text(
            yaml.safe_dump(doc, allow_unicode=True, sort_keys=False), encoding="utf-8")

    def full_component(self, cid="btn-001", prefix="btn", **over):
        rec = {"id": cid, "name": "Button", "prefix": prefix, "category": "Interactive",
               "complexity": "simple", "status": "在用", "variants": ["primary"],
               "states": [{"name": "默认", "signals": ["实心"]}], "styling": {"radius": "4px"},
               "behavior": {"interactions": ["click"]}, "accessibility": {"aria": "button"},
               "usage": {"when_to_use": "提交"}, "used_in": [], "token_refs": [],
               "version": {"created": "2026-09-21", "updated": "2026-09-21", "changes": 1}}
        rec.update(over)
        return rec


# ─────────────────── 1. 门禁（用法错误 / 空值 / 非法值 / 零产出） ───────────────────

class TestGate(Base):
    def test_missing_subcommand_is_usage_error(self):
        rc, out, err = run("--json")
        self.assertEqual(rc, 2)

    def test_missing_required_flag_is_usage_error(self):
        self.seed_scenarios()
        rc, out, err = run("init", *self.base_args(), "--json")
        self.assertEqual(rc, 2)

    def test_init_upstream_missing_is_zero_output(self):
        rc, out, _ = run("init", "--prefix", "btn", *self.base_args(), "--json")
        r = receipt(out)
        self.assertEqual(rc, 1)
        self.assertEqual(r["violations"][0]["code"], "MISSING_FILE")
        self.assertFalse((self.out / PRODUCT).exists())

    def test_init_upstream_not_finalized_is_zero_output(self):
        self.seed_scenarios(status="草稿")
        rc, out, _ = run("init", "--prefix", "btn", *self.base_args(), "--json")
        r = receipt(out)
        self.assertEqual(rc, 1)
        self.assertEqual(r["violations"][0]["code"], "STATUS_MISMATCH")
        self.assertFalse((self.out / PRODUCT).exists())

    def test_empty_prefix_is_empty_field(self):
        self.seed_scenarios()
        rc, out, _ = run("init", "--prefix", "", *self.base_args(), "--json")
        self.assertEqual(rc, 1)
        self.assertEqual(receipt(out)["violations"][0]["code"], "EMPTY_FIELD")

    def test_unknown_prefix_is_enum_invalid(self):
        self.seed_scenarios()
        rc, out, _ = run("init", "--prefix", "zzz", *self.base_args(), "--json")
        self.assertEqual(rc, 1)
        self.assertEqual(receipt(out)["violations"][0]["code"], "ENUM_INVALID")

    def test_illegal_mode_is_enum_invalid(self):
        self.seed_scenarios()
        rc, out, _ = run("init", "--prefix", "btn", "--mode", "maybe",
                         *self.base_args(), "--json")
        self.assertEqual(rc, 1)
        self.assertEqual(receipt(out)["violations"][0]["code"], "ENUM_INVALID")
        self.assertFalse((self.out / PRODUCT).exists())


# ────────────────────────────── 2. init ──────────────────────────────

class TestInit(Base):
    def test_init_mints_skeleton(self):
        self.seed_scenarios()
        r = self.init_ok()
        doc = self.load()
        self.assertEqual(doc["project"]["status"], "草稿")
        self.assertEqual(r["command"], "init")
        self.assertIn("updated", r)

    def test_default_mode_is_on(self):
        """裁定 17：设计系统默认开启。"""
        self.seed_scenarios()
        self.init_ok()
        self.assertEqual(self.load()["design_system_mode"], "on")

    def test_mode_off_is_allowed(self):
        self.seed_scenarios()
        self.init_ok("--mode", "off")
        self.assertEqual(self.load()["design_system_mode"], "off")

    def test_init_does_not_overwrite_existing(self):
        self.seed_scenarios()
        self.init_ok()
        doc = self.load()
        doc["components"][0]["name"] = "手改过"
        doc["components"][0]["id"] = "btn-007"
        self.save(doc)
        r = self.init_ok()
        self.assertTrue(r["warnings"])
        self.assertEqual(r["warnings"][0]["code"], "SET_MISMATCH")
        self.assertFalse(r["counts"]["created"])
        self.assertEqual(self.load()["components"][0]["id"], "btn-007")
        self.assertEqual(len(self.load()["components"]), 1)

    def test_init_is_the_only_writer(self):
        """list / show / check 三个只读子命令不写盘。"""
        self.seed_scenarios()
        self.init_ok()
        before = (self.out / PRODUCT).read_bytes()
        for cmd in ("list", "show", "check"):
            run(cmd, *self.base_args(), "--json")
        self.assertEqual((self.out / PRODUCT).read_bytes(), before)


# ─────────────────────── 3. ID 铸号（26 前缀 / 6 分类 / 递增） ───────────────────────

class TestIds(Base):
    def test_prefix_and_category_tables_frozen(self):
        """机械取数：源 step-08b 的前缀表 26 行 / 分类表 6 行。"""
        self.seed_scenarios()
        self.init_ok()
        doc = self.load()
        self.assertEqual([p["prefix"] for p in doc["prefixes"]], PREFIXES)
        self.assertEqual(doc["categories"], CATEGORIES)

    def test_first_component_gets_001(self):
        self.seed_scenarios()
        self.init_ok()
        self.assertEqual(self.load()["components"][0]["id"], "btn-001")

    def test_every_prefix_is_accepted_and_numbers_increment(self):
        self.seed_scenarios()
        self.init_ok()
        doc = self.load()
        for i, p in enumerate(PREFIXES):
            if p == "btn":                     # init 已铸 btn-001
                continue
            doc["components"].append(self.full_component(
                cid="%s-001" % p, prefix=p,
                category=doc["prefixes"][i]["category"]))
        self.save(doc)
        self.assertEqual(len(doc["components"]), 26)
        rc, out, _ = run("check", *self.base_args(), "--json")
        self.assertEqual(rc, 0, out)

    def test_gap_in_numbering_is_set_mismatch(self):
        self.seed_scenarios()
        self.init_ok()
        doc = self.load()
        doc["components"].append(self.full_component(cid="btn-003"))
        self.save(doc)
        rc, out, _ = run("check", *self.base_args(), "--json")
        self.assertEqual(rc, 1)
        self.assertIn("SET_MISMATCH", [v["code"] for v in receipt(out)["violations"]])

    def test_duplicate_id_is_duplicate_id(self):
        self.seed_scenarios()
        self.init_ok()
        doc = self.load()
        doc["components"].append(self.full_component())
        self.save(doc)
        rc, out, _ = run("check", *self.base_args(), "--json")
        self.assertEqual(rc, 1)
        self.assertIn("DUPLICATE_ID", [v["code"] for v in receipt(out)["violations"]])

    def test_prefix_not_in_table_is_enum_invalid(self):
        self.seed_scenarios()
        self.init_ok()
        doc = self.load()
        doc["components"][0]["prefix"] = "zzz"
        doc["components"][0]["id"] = "zzz-001"
        self.save(doc)
        rc, out, _ = run("check", *self.base_args(), "--json")
        self.assertEqual(rc, 1)
        self.assertIn("ENUM_INVALID", [v["code"] for v in receipt(out)["violations"]])

    def test_component_category_mismatch_with_prefix_table(self):
        self.seed_scenarios()
        self.init_ok()
        doc = self.load()
        doc["components"][0]["category"] = "Navigation"   # btn 属 Interactive
        self.save(doc)
        rc, out, _ = run("check", *self.base_args(), "--json")
        self.assertEqual(rc, 1)
        self.assertIn("SET_MISMATCH", [v["code"] for v in receipt(out)["violations"]])


# ────────────────────────────── 4. list ──────────────────────────────

class TestList(Base):
    def test_list_returns_six_fields_only(self):
        self.seed_scenarios()
        self.init_ok()
        rc, out, _ = run("list", *self.base_args(), "--json")
        r = receipt(out)
        self.assertEqual(rc, 0)
        self.assertEqual(len(r["items"]), 1)
        self.assertEqual(sorted(r["items"][0]),
                         sorted(["id", "name", "category", "prefix", "complexity", "status"]))

    def test_list_filter_prefix_misses(self):
        self.seed_scenarios()
        self.init_ok()
        rc, out, _ = run("list", "--prefix", "inp", *self.base_args(), "--json")
        self.assertEqual(receipt(out)["items"], [])

    def test_list_filter_category_hits(self):
        self.seed_scenarios()
        self.init_ok()
        rc, out, _ = run("list", "--category", "Interactive", *self.base_args(), "--json")
        self.assertEqual(len(receipt(out)["items"]), 1)

    def test_list_filter_status_hits(self):
        self.seed_scenarios()
        self.init_ok()
        rc, out, _ = run("list", "--status", "在用", *self.base_args(), "--json")
        self.assertEqual(len(receipt(out)["items"]), 1)

    def test_list_illegal_status_is_enum_invalid(self):
        self.seed_scenarios()
        self.init_ok()
        rc, out, _ = run("list", "--status", "bogus", *self.base_args(), "--json")
        self.assertEqual(rc, 1)
        self.assertEqual(receipt(out)["violations"][0]["code"], "ENUM_INVALID")

    def test_list_on_missing_product(self):
        self.seed_scenarios()
        rc, out, _ = run("list", *self.base_args(), "--json")
        self.assertEqual(rc, 1)
        self.assertEqual(receipt(out)["violations"][0]["code"], "MISSING_FILE")


# ────────────────────────────── 5. show ──────────────────────────────

class TestShow(Base):
    def test_show_full_document(self):
        self.seed_scenarios()
        self.init_ok()
        rc, out, _ = run("show", *self.base_args(), "--json")
        r = receipt(out)
        self.assertEqual(rc, 0)
        self.assertEqual(r["counts"]["components"], 1)

    def test_show_unknown_id(self):
        self.seed_scenarios()
        self.init_ok()
        rc, out, _ = run("show", "--id", "btn-099", *self.base_args(), "--json")
        self.assertEqual(rc, 1)
        self.assertEqual(receipt(out)["violations"][0]["code"], "UNKNOWN_ID")


# ────────────────────────────── 6. check ──────────────────────────────

class TestCheck(Base):
    def test_check_clean_draft_passes(self):
        self.seed_scenarios()
        self.init_ok()
        rc, out, _ = run("check", *self.base_args(), "--json")
        self.assertEqual(rc, 0, out)

    def test_final_requires_finalized_status(self):
        self.seed_scenarios()
        self.init_ok()
        doc = self.load()
        doc["components"][0] = self.full_component()
        self.save(doc)
        rc, out, _ = run("check", "--final", *self.base_args(), "--json")
        self.assertEqual(rc, 1)
        self.assertIn("STATUS_MISMATCH", [v["code"] for v in receipt(out)["violations"]])

    def test_final_passes_with_complete_component(self):
        self.seed_scenarios()
        self.init_ok()
        doc = self.load()
        doc["components"][0] = self.full_component()
        doc["project"]["status"] = "已定稿"
        self.save(doc)
        rc, out, _ = run("check", "--final", *self.base_args(), "--json")
        self.assertEqual(rc, 0, out)

    def test_final_detects_missing_component_key(self):
        self.seed_scenarios()
        self.init_ok()
        doc = self.load()
        rec = self.full_component()
        rec.pop("accessibility")
        doc["components"][0] = rec
        doc["project"]["status"] = "已定稿"
        self.save(doc)
        rc, out, _ = run("check", "--final", *self.base_args(), "--json")
        self.assertEqual(rc, 1)
        self.assertIn("EMPTY_FIELD", [v["code"] for v in receipt(out)["violations"]])

    def test_assumption_marker_is_detected(self):
        self.seed_scenarios()
        self.init_ok()
        doc = self.load()
        doc["components"][0] = self.full_component(name="[假设] Button")
        self.save(doc)
        rc, out, _ = run("check", *self.base_args(), "--json")
        self.assertEqual(rc, 1)
        self.assertIn("ASSUMPTION_PRESENT", [v["code"] for v in receipt(out)["violations"]])

    def test_unparsable_yaml_is_detected(self):
        self.seed_scenarios()
        (self.out / PRODUCT).write_text("project: [oops\n", encoding="utf-8")
        rc, out, _ = run("check", *self.base_args(), "--json")
        self.assertEqual(rc, 1)
        self.assertEqual(receipt(out)["violations"][0]["code"], "UNPARSABLE_YAML")


# ─────────────────── 7. 跨技能门禁（ID 链接入 wds-scenarios.yaml） ───────────────────

class TestCrossSkill(Base):
    def test_used_in_resolves_against_upstream_pages(self):
        self.seed_scenarios(pages=("SC-01.P1", "SC-01.P2"))
        self.init_ok()
        doc = self.load()
        doc["components"][0] = self.full_component(used_in=["SC-01.P2"])
        self.save(doc)
        rc, out, _ = run("check", *self.base_args(), "--json")
        self.assertEqual(rc, 0, out)

    def test_used_in_unknown_page_is_unknown_id(self):
        self.seed_scenarios()
        self.init_ok()
        doc = self.load()
        doc["components"][0] = self.full_component(used_in=["SC-09.P9"])
        self.save(doc)
        rc, out, _ = run("check", *self.base_args(), "--json")
        self.assertEqual(rc, 1)
        self.assertIn("UNKNOWN_ID", [v["code"] for v in receipt(out)["violations"]])

    def test_upstream_missing_blocks_check_too(self):
        self.seed_scenarios()
        self.init_ok()
        (self.out / "wds-scenarios.yaml").unlink()
        rc, out, _ = run("check", *self.base_args(), "--json")
        self.assertEqual(rc, 1)
        self.assertEqual(receipt(out)["violations"][0]["code"], "MISSING_FILE")


# ────────────── 8. 特有边界：token 派生自 design.yaml（裁定 5） ──────────────

class TestTokenDerivation(Base):
    def test_derived_mode_when_design_present(self):
        self.seed_scenarios()
        self.seed_design()
        self.init_ok()
        doc = self.load()
        self.assertEqual(doc["tokens"]["source"]["mode"], "派生")
        self.assertEqual(doc["tokens"]["source"]["file"], "design.yaml")
        self.assertEqual(doc["tokens"]["source"]["path"], "tokens")
        self.assertEqual(sorted(doc["tokens"]["namespaces"]["color"]),
                         ["accent", "accent_text", "bg", "surface", "text", "text_muted"])

    def test_standalone_mode_when_design_absent(self):
        self.seed_scenarios()
        r = self.init_ok()
        doc = self.load()
        self.assertEqual(doc["tokens"]["source"]["mode"], "独立")
        self.assertTrue([w for w in r["warnings"] if w["code"] == "MISSING_FILE"])

    def test_derived_tokens_are_names_only_never_values(self):
        """裁定 5：引用不复述——产物里不出现 design.yaml 的 token 值。"""
        self.seed_scenarios()
        self.seed_design(color={"bg": "#abcdef"})
        self.init_ok()
        self.assertNotIn("#abcdef", (self.out / PRODUCT).read_text(encoding="utf-8"))

    def test_spacing_vocabulary_is_the_single_normalized_set(self):
        self.seed_scenarios()
        self.seed_design()
        self.init_ok()
        sp = self.load()["tokens"]["namespaces"]["spacing"]
        self.assertEqual(sp, ["space-0", "space-3xs", "space-2xs", "space-xs", "space-sm",
                              "space-md", "space-lg", "space-xl", "space-2xl", "space-3xl"])

    def test_unresolvable_token_ref_is_violation(self):
        self.seed_scenarios()
        self.seed_design()
        self.init_ok()
        doc = self.load()
        doc["components"][0] = self.full_component(token_refs=["color.ghost"])
        self.save(doc)
        rc, out, _ = run("check", *self.base_args(), "--json")
        self.assertEqual(rc, 1)
        self.assertIn("TOKEN_UNRESOLVED", [v["code"] for v in receipt(out)["violations"]])

    def test_resolvable_token_ref_passes(self):
        self.seed_scenarios()
        self.seed_design()
        self.init_ok()
        doc = self.load()
        doc["components"][0] = self.full_component(
            token_refs=["color.accent", "spacing.space-md", "typography.family_base"])
        self.save(doc)
        rc, out, _ = run("check", *self.base_args(), "--json")
        self.assertEqual(rc, 0, out)

    def test_color_namespace_drift_from_design_is_detected(self):
        self.seed_scenarios()
        self.seed_design()
        self.init_ok()
        doc = self.load()
        doc["tokens"]["namespaces"]["color"].append("ghost")
        self.save(doc)
        rc, out, _ = run("check", *self.base_args(), "--json")
        self.assertEqual(rc, 1)
        self.assertIn("TOKEN_UNRESOLVED", [v["code"] for v in receipt(out)["violations"]])


# ───────── 9. 特有边界：重复检测的聚合段（可机械段） ─────────

class TestSimilarity(Base):
    def sim(self, *a):
        rc, out, err = run("similarity", *a, "--json")
        self.assertEqual(rc, 0, out + err)
        return receipt(out)["similarity"]

    def test_source_example_is_72_percent_level_3(self):
        """源 step-03:169–184 的示例：High/Medium/Medium/Medium = 0.72 → 72% → L3。"""
        s = self.sim("--visual", "high", "--functional", "medium",
                     "--behavioral", "medium", "--contextual", "medium")
        self.assertEqual(s["percentage"], 72)
        self.assertEqual(s["level_number"], 3)
        self.assertEqual(s["level"], "High Similarity")

    def test_all_high_is_100_level_1(self):
        s = self.sim("--visual", "high", "--functional", "high",
                     "--behavioral", "high", "--contextual", "high")
        self.assertEqual(s["percentage"], 100)
        self.assertEqual(s["level_number"], 1)

    def test_all_low_is_20_level_5(self):
        s = self.sim("--visual", "low", "--functional", "low",
                     "--behavioral", "low", "--contextual", "low")
        self.assertEqual(s["percentage"], 20)
        self.assertEqual(s["level_number"], 5)

    def test_level_2_boundary_80(self):
        s = self.sim("--visual", "high", "--functional", "high",
                     "--behavioral", "medium", "--contextual", "medium")
        self.assertEqual(s["percentage"], 84)
        self.assertEqual(s["level_number"], 2)

    def test_level_6_band_has_no_clean_sample_and_is_documented(self):
        """L6（<20）在 1.0/0.6/0.2 三值映射下取不到——源侧的非单调缺陷，登记不改。"""
        pcts = set()
        for a in ("high", "medium", "low"):
            for b in ("high", "medium", "low"):
                for c in ("high", "medium", "low"):
                    for d in ("high", "medium", "low"):
                        pcts.add(self.sim("--visual", a, "--functional", b,
                                          "--behavioral", c, "--contextual", d)["percentage"])
        self.assertEqual(min(pcts), 20)
        self.assertNotIn(19, pcts)

    def test_empty_grade_is_empty_field(self):
        rc, out, _ = run("similarity", "--visual", "", "--functional", "high",
                         "--behavioral", "high", "--contextual", "high", "--json")
        self.assertEqual(rc, 1)
        self.assertEqual(receipt(out)["violations"][0]["code"], "EMPTY_FIELD")

    def test_illegal_grade_is_enum_invalid(self):
        rc, out, _ = run("similarity", "--visual", "veryhigh", "--functional", "high",
                         "--behavioral", "high", "--contextual", "high", "--json")
        self.assertEqual(rc, 1)
        self.assertEqual(receipt(out)["violations"][0]["code"], "ENUM_INVALID")

    def test_similarity_writes_nothing(self):
        self.seed_scenarios()
        self.init_ok()
        before = (self.out / PRODUCT).read_bytes()
        self.sim("--visual", "high", "--functional", "medium",
                 "--behavioral", "medium", "--contextual", "medium")
        self.assertEqual((self.out / PRODUCT).read_bytes(), before)


# ────────────────────────── 10. 回执键完整性 ──────────────────────────

class TestReceipt(Base):
    COMMON = ["ok", "command", "project_root", "output_dir", "instance",
              "violations", "warnings", "counts"]

    def test_common_keys_on_every_subcommand(self):
        self.seed_scenarios()
        self.init_ok()
        for cmd in ("list", "show", "check"):
            rc, out, _ = run(cmd, *self.base_args(), "--json")
            r = receipt(out)
            for k in self.COMMON:
                self.assertIn(k, r, "%s 缺 %s" % (cmd, k))
        rc, out, _ = run("init", "--prefix", "btn", *self.base_args(), "--json")
        for k in self.COMMON:
            self.assertIn(k, receipt(out), "init 缺 %s" % k)

    def test_instance_is_null_but_present(self):
        self.seed_scenarios()
        r = self.init_ok()
        self.assertIsNone(r["instance"])
        self.assertIn("instance", r)

    def test_init_has_updated_readonly_does_not(self):
        self.seed_scenarios()
        r = self.init_ok()
        self.assertIn("updated", r)
        for cmd in ("list", "show", "check"):
            rc, out, _ = run(cmd, *self.base_args(), "--json")
            self.assertNotIn("updated", receipt(out), cmd)

    def test_warnings_share_shape_with_violations(self):
        self.seed_scenarios()
        r = self.init_ok()          # design.yaml 缺席 → warning
        self.assertTrue(r["warnings"])
        for w in r["warnings"]:
            self.assertEqual(sorted(w), ["code", "msg", "where"])


# ───────────────────────────── 11. 契约冒烟 ─────────────────────────────

class TestContract(unittest.TestCase):
    def test_skill_md_is_thin_and_has_four_sections(self):
        text = SKILL_MD.read_text(encoding="utf-8")
        lines = text.splitlines()
        self.assertLessEqual(len(lines), 90, "SKILL.md 超 90 行：%d" % len(lines))
        for sec in ("## 激活时", "## 工作流", "## 结构", "## 规则"):
            self.assertIn(sec, text)

    def test_mother_texts_verbatim(self):
        text = SKILL_MD.read_text(encoding="utf-8")
        for name, block in (("§1", M1), ("§2", M2), ("§3a", M3A), ("§3b", M3B),
                            ("§3c", M3C), ("§3d", M3D), ("§4", M4), ("§5", M5), ("§6", M6)):
            self.assertIn(block, text, "母本 %s 未逐字在场" % name)

    def test_final_gate_points_to_own_engine(self):
        text = SKILL_MD.read_text(encoding="utf-8")
        self.assertIn("wds_system.py", text)
        self.assertIn("check --final", text)

    def test_redline_no_wds_check_type(self):
        """红线：不得教模型调用 diyc.py check --type <WDS 型> --previous。"""
        text = SKILL_MD.read_text(encoding="utf-8")
        for bad in ("check --type wds", "check --type design-system",
                    "--type wds-design-system", "--type wds-system"):
            self.assertNotIn(bad, text)

    def test_frontmatter_five_fields(self):
        text = SKILL_MD.read_text(encoding="utf-8").split("---")[1]
        self.assertIn("phase: 2-wds-design", text)
        self.assertIn("precededBy: [diy-wds-scenarios]", text)
        self.assertIn("followedBy: []", text)
        self.assertIn("required: false", text)
        self.assertIn("line: wds", text)
        self.assertIn("outputs: wds-design-system.yaml", text)

    def test_steps_are_five_files_with_numbered_sections(self):
        files = sorted(p.name for p in STEPS.glob("*.md"))
        self.assertEqual(files, ["01-create.md", "02-import.md", "03-view.md",
                                 "04-edit.md", "05-finish.md"])
        total = 0
        for name in files:
            text = (STEPS / name).read_text(encoding="utf-8")
            self.assertRegex(text, r"^# Step \d+ — ", name)
            self.assertIn("**Read (input):**", text)
            self.assertIn("**Write (output):**", text)
            total += sum(1 for ln in text.splitlines() if ln.startswith("## 第 "))
        self.assertEqual(total, 23, "小节合计应为 23，实测 %d" % total)


if __name__ == "__main__":
    unittest.main()
