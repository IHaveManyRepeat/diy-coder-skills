# -*- coding: utf-8 -*-
"""diy-project-context 确定性引擎 e2e 测试（B1 批任务书 §7 / §2.5）。

覆盖：
- 用例 1：scan 在合成多部件夹具上识别 parts / stack / 既有文档 / 源码树（语言无关探测）
- 用例 2：scan 遇未知清单降级「存在但未解析」+ 结构化 warning，不崩溃
- 用例 3：scan 门禁（项目根不存在）→ exit 1 + 结构化拒绝 + 零产出
- 用例 4：check 合法产物 exit 0 唯一放行；非法各带对应违规码（MISSING_FILE / ENUM_INVALID /
          DUPLICATE_ID / EMPTY_FIELD / ASSUMPTION_PRESENT）
- 用例 5：rescan `--previous` 比对 PC-### 集合，旧有新无 → ID_UNSTABLE
- 用例 6：SKILL.md 契约冒烟（冻结实例句逐字 md5 + 终门句指向 context.py check --final）
- 附加：--output-dir 必填（用法错误 rc2）；--part 指名不存在 → UNKNOWN_ID

夹具全部落 tempdir 自建；不读写本仓库真实 diy-output；不依赖本机 git 状态。
运行：cd diy-coder && python -m unittest discover -s tests -p "test_context.py" -v
"""
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE = os.path.join(HERE, "..", "skills", "diy-project-context",
                      "scripts", "context.py")
SKILL_MD = os.path.join(HERE, "..", "skills", "diy-project-context", "SKILL.md")
NL = chr(10)

# 冻结文本校验值（batch4/frozen-texts.md §1：整句 233 字符，逐字复制）
INSTANCE_MD5 = "5445f98bc4d4821e6888b89406a97eac"
INSTANCE_ANCHOR = "Instance resolution (FR-4.5/D-9)"
# 冻结文本校验值（frozen-texts.md §2：纪律块单行 497 字符，逐字复制）
DISCIPLINE_MD5 = "f1b3b6fbb528f0cfab31f3196b3547ae"

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
    """用例 6：SKILL.md 契约冒烟（任务书 §2.1）。"""

    def read_skill(self):
        if not os.path.isfile(SKILL_MD):
            self.skipTest("SKILL.md 尚未交付")
        with io.open(SKILL_MD, encoding="utf-8") as f:
            return f.read()

    # trace: 任务书 §2.1（冻结实例句逐字；md5 口径同 frozen-texts §3 复现命令）
    def test_instance_sentence_is_frozen_verbatim(self):
        raw = self.read_skill()
        m = re.search(r"Instance resolution \(FR-4\.5/D-9\)[^\r\n]*", raw)
        self.assertTrue(m, "SKILL.md 缺实例解析样板句")
        frag = m.group(0)
        self.assertEqual(len(frag), 233, "实例句字符数偏离冻结文本（233）")
        self.assertEqual(hashlib.md5((frag + NL).encode("utf-8")).hexdigest(), INSTANCE_MD5,
                         "实例句与冻结文本不一致：%s" % frag)

    # trace: 任务书 §2.1（写作纪律块逐字；整块单行 497 字符）
    def test_writing_discipline_block_is_frozen_verbatim(self):
        raw = self.read_skill()
        m = re.search(r"^- \*\*Writing discipline\..*$", raw, re.MULTILINE)
        self.assertTrue(m, "SKILL.md 缺写作纪律块")
        frag = m.group(0)
        self.assertEqual(len(frag), 497, "纪律块字符数偏离冻结文本（497）")
        self.assertEqual(hashlib.md5((frag + NL).encode("utf-8")).hexdigest(),
                         DISCIPLINE_MD5, "纪律块与冻结文本不一致")

    # trace: 任务书 §2.1（终门句指向本技能领域引擎 check --final）
    def test_final_gate_points_to_engine(self):
        skill = self.read_skill()
        self.assertIn("context.py", skill, "终门句未指向领域引擎")
        self.assertIn("check --final", skill, "终门句缺 check --final")
        self.assertIn("--json", skill, "终门句缺 --json 回执")

    # trace: 任务书 §2.1（薄主文件 ≤90 行 + 四段结构 + 读取纪律 + 渲染静默）
    def test_main_file_is_thin_with_four_sections(self):
        raw = self.read_skill()
        self.assertLessEqual(len(raw.splitlines()), 90, "主文件须 ≤90 行")
        for head in ("## On Activation", "## Workflow", "## Schema", "## Rules"):
            self.assertIn(head, raw, "缺段：%s" % head)
        self.assertIn("never batch-load", raw, "缺读取纪律")
        self.assertIn("diy-viewer", raw, "缺渲染接线")


if __name__ == "__main__":
    unittest.main()
