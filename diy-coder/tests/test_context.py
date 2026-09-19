# -*- coding: utf-8 -*-
"""diy-project-context 确定性引擎 e2e 测试（B1 批任务书 §7 / §2.5；中文化轮 B-23 同步）。

覆盖：
- 用例 1：scan 在合成多部件夹具上识别 parts / stack / 既有文档 / 源码树 / 关键目录回执（语言无关探测）
- 用例 2：scan 遇未知清单降级「存在但未解析」+ 结构化 warning，不崩溃
- 用例 3：scan 门禁（项目根不存在）→ exit 1 + 结构化拒绝 + 零产出
- 用例 4：check 合法产物 exit 0 唯一放行；非法各带对应违规码（MISSING_FILE / ENUM_INVALID /
          DUPLICATE_ID / EMPTY_FIELD / ASSUMPTION_PRESENT）
- 用例 5：rescan `--previous` 比对 PC-### 集合，旧有新无 → ID_UNSTABLE
- 用例 6：SKILL.md 契约冒烟（母本 §1–§6 中文定稿逐字 + 四段中文标题 + ≤93 行 + 终门句指向引擎）
- 用例 7：steps/ 形态（H1 中文步名 + Read/Write 两行英文锚 + 末段点名下一个）
- 附加：--output-dir 必填（用法错误 rc2）；--part 指名不存在 → UNKNOWN_ID

夹具全部落 tempdir 自建；不读写本仓库真实 diy-output；不依赖本机 git 状态。
运行：cd diy-coder && python -m unittest discover -s tests -p "test_context.py" -v
"""
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.join(HERE, "..", "skills", "diy-project-context")
ENGINE = os.path.join(SKILL_DIR, "scripts", "context.py")
SKILL_MD = os.path.join(SKILL_DIR, "SKILL.md")
STEPS_DIR = os.path.join(SKILL_DIR, "steps")
NL = chr(10)

# 套件级句式母本（suite-texts.md §1 / §2 / §3 / §4 / §5 / §6 中文定稿，逐字）
INSTANCE_ZH = ("实例解析（FR-4.5/D-9）由工具脚本执行：运行 "
               "`python \"{project-root}/.claude/skills/diy-tools/scripts/diyc.py\" "
               "resolve [--instance <name>] --json`，把回执里的 `output_dir` "
               "当作本次运行唯一的读写根目录。")
DISCIPLINE_ZH = ("- **写作纪律。** 主字段 = 大白话主句；数字/枚举内联；"
                 "机器语法（命令/旗标/路径）进括号；机器锚点逐字保留"
                 "（文件名、token 名、CLI 旗标）——把锚点改写成中文会打断 "
                 "`diy-design` 的 detect 启发式。schema 若定义 `plain`："
                 "一行写清该条目为什么存在，绝不写是什么（转述会漂移）；"
                 "只写难懂的条目。若定义 `detail`：过程叙述——结论留在主字段。")
RESOLVE_KEYS_ZH = ("解析 `project.communication_language` / "
                   "`project.document_output_language` / `paths.output_dir`")
READ_DISCIPLINE_ZH = ("读取纪律：预载预算 = 本文件、上述配置与回执、`steps/` 下当前那一个文件"
                      "——绝不批量预载；执行期读取以每个步骤开头的 `Read (input)` 行为唯一权威，"
                      "**主文件不列举封闭清单**。")
RENDER_SILENT_ZH = "渲染是静默旁路——只写调用命令"
PRECISE_ZH = ("- **精准简练。** 写进产物的每条内容都要精准、简练：一条只讲一件事；"
              "不复述上游已写的信息（引用 ID）；不写没有信息量的套话。")
# 英文原形（历史，批 4 冻结）——中文化后不得残留
INSTANCE_EN_MARK = "Instance resolution (FR-4.5/D-9)"
DISCIPLINE_EN_MARK = "- **Writing discipline."
STEPS = ("01-scan.md", "02-context.md", "03-rules.md", "04-finalize.md",
         "05-deep-dive.md")

PKG_JSON = ('{' + NL
            + '  "name": "web-client",' + NL
            + '  "private": true,' + NL
            + '  "dependencies": {"react": "^18.2.0", "react-dom": "^18.2.0"},' + NL
            + '  "devDependencies": {"vite": "^5.0.0", "vitest": "^1.6.0"}' + NL
            + '}' + NL)

GO_MOD = NL.join([
    "module example.com/api",
    "",
    "go 1.21",
    "",
    "require github.com/gin-gonic/gin v1.9.1",
]) + NL

PROJECT_CONTEXT_YAML = NL.join([
    "project:",
    "  name: mini",
    "  created: '2026-09-14'",
    "  updated: '2026-09-14'",
    "scan:",
    "  mode: 全量",
    "  level: 快速",
    "  date: '2026-09-14'",
    "  parts:",
    "  - name: client",
    "    type: 网页",
    "    path: client",
    "  - name: server",
    "    type: 后端",
    "    path: server",
    "stack:",
    "- part: client",
    "  language: TypeScript",
    "  framework: React",
    "  version: 18.2.0",
    "  notes: 前端部件",
    "- part: server",
    "  language: Go",
    "  framework: gin",
    "  version: 1.9.1",
    "  notes: 后端部件",
    "structure:",
    "  tree: mini/",
    "  key_dirs:",
    "  - path: client/src",
    "    purpose: 前端源码",
    "architecture:",
    "- part: client",
    "  summary: 组件化 SPA",
    "  key_points:",
    "  - 路由集中在 client/src/routes",
    "integration:",
    "- between: [client, server]",
    "  contract: REST /api/v1",
    "  notes: JSON over HTTPS",
    "rules:",
    "- id: PC-001",
    "  category: 语言",
    "  rule: 严格模式开启，禁 any",
    "  why: 类型回归靠 tsc --noEmit 拦截",
    "  where: client/tsconfig.json",
    "- id: PC-002",
    "  category: 工作流",
    "  rule: 提交前跑 npm test",
    "  why: 夹具规则",
    "  where: package.json scripts",
    "deep_dives: []",
    "revisions: []",
]) + NL


def run_engine(args):
    return subprocess.run([sys.executable, ENGINE] + args,
                          capture_output=True, text=True, encoding="utf-8")


class EngineCase(unittest.TestCase):
    """tmp 项目根 + diy-output 目录的公共夹具。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="ctx-")
        self.root = self.tmp.name
        self.out = os.path.join(self.root, "diy-output")
        os.makedirs(self.out, exist_ok=True)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, rel, content):
        path = os.path.join(self.root, rel)
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with io.open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    def scan(self, *extra):
        return run_engine(["scan", "--project-root", self.root,
                           "--output-dir", self.out, "--json"] + list(extra))

    def check(self, *extra):
        return run_engine(["check", "--project-root", self.root,
                           "--output-dir", self.out, "--json"] + list(extra))

    def ctx_path(self):
        return os.path.join(self.out, "project-context.yaml")


class ScanTests(EngineCase):

    # trace: 任务书 §7（scan 确定性：部件探测/分类/清单解析/既有文档/源码树）
    def test_scan_detects_multi_part_fixture(self):
        self.write("client/package.json", PKG_JSON)
        self.write("client/tsconfig.json", '{"compilerOptions": {"strict": true}}' + NL)
        self.write("client/README.md", "# client" + NL)
        self.write("client/src/main.ts", "export const a = 1" + NL)
        self.write("server/go.mod", GO_MOD)
        self.write("server/main.go", "package main" + NL)
        self.write("docs/architecture/overview.md", "# arch" + NL)
        self.write("README.md", "# mini" + NL)
        r = self.scan()
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        data = json.loads(r.stdout)
        self.assertTrue(data["ok"])
        self.assertEqual(data["repository_type"], "multi-part")
        names = [p["name"] for p in data["parts"]]
        self.assertEqual(sorted(names), ["client", "server"])
        types = {p["name"]: p["type"] for p in data["parts"]}
        self.assertEqual(types["client"], "网页")
        self.assertEqual(types["server"], "后端")
        langs = {s["part"]: s["language"] for s in data["stack"]}
        self.assertEqual(langs["client"], "TypeScript")
        self.assertEqual(langs["server"], "Go")
        frameworks = {s["part"]: s["framework"] for s in data["stack"]}
        self.assertEqual(frameworks["client"], "react")
        self.assertEqual(frameworks["server"], "gin")
        versions = {s["part"]: s["version"] for s in data["stack"]}
        self.assertEqual(versions["client"], "18.2.0")
        self.assertEqual(versions["server"], "1.21")  # go 指令版本
        self.assertIn("client", data["tree"])
        docs = [d["path"] for d in data["docs_found"]]
        self.assertIn("README.md", docs)
        self.assertIn("client/README.md", docs)
        self.assertIn("docs/architecture/overview.md", docs)
        self.assertEqual(data["counts"]["parts"], 2)

    # trace: 任务书 §7（单仓/工作区形态：packages/* 各自带清单才算部件，互不吞并）
    def test_scan_detects_monorepo_workspace(self):
        self.write("pnpm-workspace.yaml", "packages:" + NL + "- 'packages/*'" + NL)
        self.write("packages/core/package.json",
                   '{"name": "core", "main": "index.js"}' + NL)
        self.write("packages/cli/package.json",
                   '{"name": "cli", "bin": {"cli": "bin.js"}}' + NL)
        r = self.scan()
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        data = json.loads(r.stdout)
        self.assertEqual(data["repository_type"], "monorepo")
        self.assertEqual(sorted(p["name"] for p in data["parts"]), ["cli", "core"])
        types = {p["name"]: p["type"] for p in data["parts"]}
        self.assertEqual(types["cli"], "命令行")

    # trace: 任务书 §7（scan_level 三档：exhaustive 加 LOC，受上限约束）
    def test_scan_level_exhaustive_adds_loc(self):
        self.write("app/package.json", PKG_JSON)
        self.write("app/src/main.ts", "line1" + NL + "line2" + NL + "line3" + NL)
        quick = json.loads(self.scan().stdout)
        deep = json.loads(self.scan("--level", "深入").stdout)
        full = json.loads(self.scan("--level", "穷尽").stdout)
        self.assertEqual(quick["counts"]["files"], 0)
        self.assertEqual(deep["counts"]["files"], 1)
        self.assertEqual(deep["counts"]["loc"], 0)
        self.assertEqual(full["counts"]["loc"], 3)

    # trace: 任务书 硬规则 4（语言无关：未知清单降级「存在但未解析」，不崩不假设工具链）
    def test_scan_degrades_on_unknown_manifest(self):
        self.write("weird/Gemfile", 'source "https://rubygems.org"' + NL)
        self.write("weird/app.rb", "puts 1" + NL)
        self.write("weird/README.md", "# weird" + NL)
        r = self.scan()
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        self.assertNotIn("Traceback", r.stderr)
        data = json.loads(r.stdout)
        self.assertTrue(data["ok"])
        self.assertEqual([p["name"] for p in data["parts"]], ["weird"])
        self.assertEqual(data["parts"][0]["type"], "未知")
        codes = {w["code"] for w in data["warnings"]}
        self.assertIn("MANIFEST_UNPARSED", codes)
        self.assertTrue(all(w["where"] and w["msg"] for w in data["warnings"]))
        self.assertEqual(data["level"], "快速")

    # trace: 任务书 §2.5 用例 1（门禁拒绝路径 → 零产出 + 结构化理由）
    def test_scan_refuses_missing_project_root(self):
        ghost = os.path.join(self.root, "ghost")
        r = run_engine(["scan", "--project-root", ghost,
                        "--output-dir", self.out, "--json"])
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertNotIn("Traceback", r.stderr)
        data = json.loads(r.stdout)
        self.assertFalse(data["ok"])
        self.assertEqual(data["violations"][0]["code"], "MISSING_FILE")
        self.assertEqual(data["parts"], [])
        self.assertEqual(os.listdir(self.out), [], "拒绝路径不得写任何文件")

    # trace: A4④（CSV critical_directories 并入引擎：回执 critical_dirs 只报实际存在者）
    def test_scan_reports_critical_dirs_per_part(self):
        self.write("client/package.json", PKG_JSON)
        self.write("client/src/main.ts", "export const a = 1" + NL)
        self.write("client/app/entry.ts", "export const b = 2" + NL)
        self.write("server/go.mod", GO_MOD)          # 后端声明表里的目录一个都不存在
        r = self.scan()
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        data = json.loads(r.stdout)
        dirs = {e["part"]: e["dirs"] for e in data["critical_dirs"]}
        self.assertEqual(dirs["client"], ["client/src", "client/app"],
                         "网页部件应按 CSV 声明序报存在的关键目录")
        self.assertEqual(dirs["server"], [], "无命中 → 空列表，不猜")

    # trace: A4④（`--part` 收窄部件时 critical_dirs 同步收窄）
    def test_scan_critical_dirs_respect_part_filter(self):
        self.write("client/package.json", PKG_JSON)
        self.write("client/src/main.ts", "export const a = 1" + NL)
        self.write("server/go.mod", GO_MOD)
        data = json.loads(self.scan("--part", "client").stdout)
        self.assertEqual([e["part"] for e in data["critical_dirs"]], ["client"])

    # trace: 任务书 §7（--part 指名不存在 → 冻结码 UNKNOWN_ID，不静默）
    def test_scan_unknown_part_is_refused(self):
        self.write("client/package.json", PKG_JSON)
        r = self.scan("--part", "nope")
        self.assertEqual(r.returncode, 1, r.stdout)
        data = json.loads(r.stdout)
        self.assertEqual(data["violations"][0]["code"], "UNKNOWN_ID")

    # trace: 任务书 §7（scan 不写产物：扫描是只读证据）
    def test_scan_writes_nothing(self):
        self.write("client/package.json", PKG_JSON)
        r = self.scan("--level", "深入")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertFalse(os.path.exists(self.ctx_path()))
        self.assertEqual(os.listdir(self.out), [])

    # trace: 任务书 §2.3（--output-dir 必填：不做实例解析/目录推导）
    def test_output_dir_is_mandatory(self):
        r = run_engine(["scan", "--project-root", self.root, "--json"])
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        r2 = run_engine(["check", "--project-root", self.root, "--json"])
        self.assertEqual(r2.returncode, 2, r2.stdout + r2.stderr)


class CheckValidationTests(EngineCase):

    # trace: 任务书 §2.5 用例 3（合法产物 exit 0 唯一放行）
    def test_check_legal_artifact_passes(self):
        self.write("diy-output/project-context.yaml", PROJECT_CONTEXT_YAML)
        r = self.check("--final")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        data = json.loads(r.stdout)
        self.assertTrue(data["ok"])
        self.assertEqual(data["violations"], [])
        self.assertEqual(data["counts"]["rules"], 2)
        self.assertEqual(data["counts"]["parts"], 2)
        self.assertEqual(data["counts"]["rules_by_category"],
                         {"语言": 1, "工作流": 1})

    # trace: 任务书 §2.5 用例 3（各类违规各带冻结违规码）
    def test_check_reports_violation_codes(self):
        self.write("diy-output/project-context.yaml", PROJECT_CONTEXT_YAML)
        cases = [
            ("ENUM_INVALID",
             PROJECT_CONTEXT_YAML.replace("  mode: 全量", "  mode: full-scan")),
            ("ENUM_INVALID",
             PROJECT_CONTEXT_YAML.replace("  category: 语言", "  category: style")),
            ("DUPLICATE_ID",
             PROJECT_CONTEXT_YAML.replace("id: PC-002", "id: PC-001")),
            ("EMPTY_FIELD",
             PROJECT_CONTEXT_YAML.replace("  parts:" + NL + "  - name: client"
                                          + NL + "    type: 网页"
                                          + NL + "    path: client"
                                          + NL + "  - name: server"
                                          + NL + "    type: 后端"
                                          + NL + "    path: server" + NL, "  parts: []" + NL)),
            ("ASSUMPTION_PRESENT",
             PROJECT_CONTEXT_YAML.replace("rule: 提交前跑 npm test",
                                          "rule: 提交前跑 [假设] npm test")),
        ]
        for code, text in cases:
            self.write("diy-output/project-context.yaml", text)
            r = self.check("--final")
            self.assertEqual(r.returncode, 1, "%s: %s" % (code, r.stdout + r.stderr))
            data = json.loads(r.stdout)
            self.assertIn(code, {x["code"] for x in data["violations"]},
                          "%s 未报出：%s" % (code, r.stdout))
            self.assertTrue(all(x.get("where") and x.get("msg")
                                for x in data["violations"]), r.stdout)

    # trace: 任务书 §2.5 用例 2（缺文件 / 损坏 YAML → 结构化违规，不 Traceback）
    def test_check_missing_and_broken_file_are_structured(self):
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertNotIn("Traceback", r.stderr)
        self.assertEqual(json.loads(r.stdout)["violations"][0]["code"], "MISSING_FILE")
        self.write("diy-output/project-context.yaml", "scan: [" + NL)
        r2 = self.check()
        self.assertEqual(r2.returncode, 1)
        self.assertNotIn("Traceback", r2.stderr)
        self.assertEqual(json.loads(r2.stdout)["violations"][0]["code"], "UNPARSABLE_YAML")

    # trace: 任务书 §7（--final 附加义务：rules 非空且每条 rule/why/where 非空、stack 非空）
    def test_check_final_requires_rules_and_stack(self):
        no_rules = PROJECT_CONTEXT_YAML.split("rules:" + NL)[0] + "rules: []" + NL + "revisions: []" + NL
        self.write("diy-output/project-context.yaml", no_rules)
        r = self.check("--final")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("EMPTY_FIELD", {x["code"] for x in json.loads(r.stdout)["violations"]})
        self.assertEqual(self.check().returncode, 0, "起草期宽松：rules 为空合法")

        missing_why = PROJECT_CONTEXT_YAML.replace("  why: 夹具规则" + NL, "")
        self.write("diy-output/project-context.yaml", missing_why)
        r2 = self.check("--final")
        self.assertEqual(r2.returncode, 1, r2.stdout)
        self.assertIn("EMPTY_FIELD", {x["code"] for x in json.loads(r2.stdout)["violations"]})

    # trace: 任务书 §2.2（--previous：rescan 防丢规则，旧有新无 → ID_UNSTABLE）
    def test_check_previous_flags_dropped_rule(self):
        prev = os.path.join(self.out, "prev.yaml")
        # 旧稿多一条 PC-003（现稿丢失）——rescan 防丢规则的比对载荷
        dropped = PROJECT_CONTEXT_YAML.replace(
            "deep_dives: []" + NL,
            "- id: PC-003" + NL
            + "  category: 测试" + NL
            + "  rule: 旧稿规则" + NL
            + "  why: 旧稿" + NL
            + "  where: old/" + NL
            + "deep_dives: []" + NL)
        with io.open(prev, "w", encoding="utf-8") as f:
            f.write(dropped)
        self.write("diy-output/project-context.yaml", PROJECT_CONTEXT_YAML)
        r = self.check("--previous", prev)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        data = json.loads(r.stdout)
        self.assertIn("ID_UNSTABLE", {x["code"] for x in data["violations"]})
        self.assertIn("PC-003", r.stdout)
        # 旧稿不可读：结构化 warning，不静默、不阻断
        r2 = self.check("--previous", os.path.join(self.out, "nothere.yaml"))
        self.assertEqual(r2.returncode, 0, r2.stdout + r2.stderr)
        self.assertEqual(json.loads(r2.stdout)["warnings"][0]["code"], "MISSING_FILE")

    # trace: 任务书 §7（人读输出：每违规一行 CODE where: msg + 汇总行）
    def test_human_output_lines(self):
        self.write("diy-output/project-context.yaml", PROJECT_CONTEXT_YAML)
        r = run_engine(["check", "--final", "--project-root", self.root,
                        "--output-dir", self.out])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(r.stdout.strip())
        self.write("diy-output/project-context.yaml",
                   PROJECT_CONTEXT_YAML.replace("  mode: 全量", "  mode: bogus"))
        r2 = run_engine(["check", "--project-root", self.root, "--output-dir", self.out])
        self.assertEqual(r2.returncode, 1, r2.stdout)
        self.assertIn("ENUM_INVALID", r2.stdout)
        self.assertIn("FAIL", r2.stdout)


class SkillContractTests(unittest.TestCase):
    """用例 6：SKILL.md 契约冒烟（任务书 §2.1 / 中文化轮 B-23）。"""

    def read_skill(self):
        if not os.path.isfile(SKILL_MD):
            self.skipTest("SKILL.md 尚未交付")
        with io.open(SKILL_MD, encoding="utf-8", newline="") as f:
            return f.read().replace("\r\n", "\n")

    def read_step(self, name):
        with io.open(os.path.join(STEPS_DIR, name), encoding="utf-8", newline="") as f:
            return f.read().replace("\r\n", "\n")

    # trace: 母本 §1（实例解析句中文化定稿逐字）
    def test_instance_sentence_verbatim(self):
        skill = self.read_skill()
        self.assertIn(INSTANCE_ZH, skill, "SKILL.md 缺母本 §1 中文定稿（逐字）")
        self.assertNotIn(INSTANCE_EN_MARK, skill, "已转中文定稿，不得残留英文原形")

    # trace: 母本 §2（写作纪律块逐字，置 Rules 段末尾）
    def test_writing_discipline_block_at_rules_end(self):
        skill = self.read_skill()
        self.assertIn(DISCIPLINE_ZH, skill, "SKILL.md 缺母本 §2 中文定稿")
        self.assertNotIn(DISCIPLINE_EN_MARK, skill, "已转中文定稿，不得残留英文原形")
        self.assertEqual(DISCIPLINE_ZH, skill.rstrip(NL).splitlines()[-1],
                         "写作纪律块须置 Rules 段末尾")

    # trace: 母本 §3 / §4 / §5 / §6（中文化轮落地锚串）
    def test_mother_text_anchors(self):
        skill = self.read_skill()
        for label, frag in (("§3 配置解析键", RESOLVE_KEYS_ZH),
                            ("§4 读取纪律", READ_DISCIPLINE_ZH),
                            ("§5 渲染静默", RENDER_SILENT_ZH),
                            ("§6 精准简练", PRECISE_ZH)):
            self.assertIn(frag, skill, "SKILL.md 缺母本 %s 逐字文本" % label)

    # trace: 任务书 §2.1（终门句指向本技能领域引擎 check --final；实例解析委托 diyc.py）
    def test_final_gate_points_to_engine(self):
        skill = self.read_skill()
        self.assertIn("context.py", skill, "终门句未指向领域引擎")
        self.assertIn("check --final", skill, "终门句缺 check --final")
        self.assertIn("--json", skill, "终门句缺 --json 回执")
        self.assertIn("--output-dir", skill, "激活句/终门句须声明 --output-dir 必填")
        self.assertIn("diyc.py\" resolve", skill, "实例解析未委托 diyc.py resolve")

    # trace: 母本 §四 / 政策（四段中文标题 + ≤93 行预算 + description 中文注释 + 步名点名）
    def test_thin_main_file_structure(self):
        skill = self.read_skill()
        self.assertLessEqual(len(skill.splitlines()), 93, "薄主文件超出 93 行预算")
        self.assertIn("name: diy-project-context", skill)
        self.assertIn("outputs: project-context.yaml", skill)
        self.assertIn("# ↑ 中文：", skill, "description 缺中文注释")
        for section in ("## 激活时", "## 工作流", "## 结构", "## 规则"):
            self.assertIn(section, skill, "SKILL.md 缺四段：%s" % section)
        for name in STEPS:
            self.assertIn(name, skill, "工作流未点名 %s" % name)

    # trace: SS-024-13 / SS-024-08 / SS-024-09 / SS-024-06 / A4④ / SS-024-11（B-23 落点锁）
    def test_b23_landings(self):
        skill = self.read_skill()
        # Rule 1 的 .prev 具名例外（写面与 Rule 9 的临时快照不冲突）
        self.assertIn("project-context.yaml.prev", skill, "Rule 1 缺 .prev 具名例外")
        # 两条 check 命令都在细节文件里带全实参（SKILL.md 只指路、不重复命令）
        self.assertNotIn("check --previous {output_dir}", skill,
                         "命令出处应收敛到 steps/04-finalize.md")
        self.assertIn("steps/04-finalize.md", skill, "Rule 9 须指路 steps/04-finalize.md")
        finalize = self.read_step("04-finalize.md")
        for cmd in ("check --previous", "check --final"):
            line = [ln for ln in finalize.splitlines() if cmd in ln]
            self.assertTrue(line, "steps/04-finalize.md 缺 %s 命令行" % cmd)
            self.assertIn('--project-root "{project-root}"', line[0])
            self.assertIn('--output-dir "{output_dir}"', line[0])
        self.assertIn("exit 0", finalize, "Rewrite check 须在 exit 0 后才删 .prev")
        # 日期口径（A-7）：scan.date 一律写今天，不是首扫日
        scan = self.read_step("01-scan.md")
        self.assertIn("不是首扫日", scan, "steps/01-scan.md 缺 scan.date 口径")
        self.assertIn("critical_dirs", scan, "steps/01-scan.md 未接线 critical_dirs 回执")
        # A4④：critical_dirs 从回执取；A4③：不再指向源工作流的标注法
        context = self.read_step("02-context.md")
        self.assertIn("`critical_dirs`", context, "steps/02-context.md 未改「从回执取」")
        self.assertNotIn("annotates it", context, "steps/02-context.md 冗余从句未删")
        self.assertNotIn("source document (per-project-type", context, "文档映射表未删")
        # SS-024-11：deep-dive 的读面 = 回执 + 既有文件里的 structure
        deep = self.read_step("05-deep-dive.md")
        self.assertIn("既有的", deep, "steps/05-deep-dive.md 未改读面")
        self.assertNotIn("`structure` from step 1", deep, "steps/05-deep-dive.md 仍指 step 1 的 structure")

    # trace: 母本 §三（steps 形态：H1 中文步名 + Read/Write 英文锚 + 末段点名下一个）
    def test_steps_shape(self):
        for i, name in enumerate(STEPS, start=1):
            path = os.path.join(STEPS_DIR, name)
            self.assertTrue(os.path.isfile(path), "缺步骤文件 %s" % name)
            text = self.read_step(name)
            lines = text.splitlines()
            self.assertTrue(lines[0].startswith("# Step %d — " % i),
                            "%s 的 H1 须为 '# Step %d — <中文步名>'，实为 %r"
                            % (name, i, lines[0]))
            self.assertTrue(re.search(r"[一-鿿]", lines[0]),
                            "%s 的步名须含中文" % name)
            self.assertTrue(any(ln.startswith("**Read (input):**") for ln in lines),
                            "%s 缺 '**Read (input):**' 行" % name)
            self.assertTrue(any(ln.startswith("**Write (output):**") for ln in lines),
                            "%s 缺 '**Write (output):**' 行" % name)
            self.assertIn("## 播报与下一步", text, "%s 缺末段 '## 播报与下一步'" % name)
        # 线性链 + 深挖回接 + 末步声明
        for name, nxt in zip(STEPS[:3], STEPS[1:4]):
            self.assertIn(nxt, self.read_step(name), "%s 未点名下一个 %s" % (name, nxt))
        self.assertIn("05-deep-dive.md", self.read_step("01-scan.md"),
                      "steps/01-scan.md 须给深挖分支的改道")
        self.assertIn("04-finalize.md", self.read_step("05-deep-dive.md"),
                      "steps/05-deep-dive.md 须回接定稿步")
        self.assertIn("最后一个步骤文件", self.read_step("04-finalize.md"),
                      "steps/04-finalize.md 须声明本步是终局")


if __name__ == "__main__":
    unittest.main()
