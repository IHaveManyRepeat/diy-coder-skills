# -*- coding: utf-8 -*-
"""diy-bmb-builder 确定性引擎 e2e 测试（技能工厂：造 / 改 / 评）。

覆盖（任务书 §2.5 W1 清单 ①–⑩ + 两条补口）：
- 用例 1：门禁面——check/prepass 目标不存在 → exit 1 + MISSING_FILE 且零产出；
           steps/01-intent.md 载三条门禁句（无意图零产出 / 输入过薄停并问 / MISSING_FILE 拒绝）
- 用例 2：scaffold 合法 → exit 0 + 目录结构断言（SKILL.md + steps/ + files_created）
- 用例 3：scaffold 名字非法 → NAME_ILLEGAL；目标已存在 → FILE_CONFLICT；
           --to-source 与 --dest 互斥 → exit 2（用法错误）
- 用例 4：回执键完整性（七共同键 / warnings 与 violations 同形 / 人读态 CODE where: msg + 汇总行）
- 用例 5：契约冒烟（SKILL.md 母本 §1 中文定稿逐字 + 终门句指向本引擎 + 零 YAML 声明句 +
           四段中文标题 ≤90 行 + check --final 自证 exit 0）
- 用例 6：prepass 两套——metrics（token 计数与废话 grep）；integrity（根级编号前缀阶段名判违规）
- 用例 7：mlog 追加的原子性与 ack 形状（{ok,file,n,appended} 恒一行 JSON + 只追加）
- 用例 8：落点断言（默认 --dest 算出 {project-root}/.claude/skills + --force 硬护栏拒绝已建技能名）
- 用例 9：template 两级语义（残留 {if-} → exit 3；残留 {token} → tokens_remaining 不算失败）
- 用例 10：未解析 {…} 令牌 → TOKEN_UNRESOLVED（{project-root} 是唯一例外，按 --project-root 自解析）
- 用例 11：scan 机械面（禁绝对路径 / 禁 ../ 越界 / 脚本合规）
- 用例 12：render 从 findings.json 落 skill-analysis-report.{md,html}（脚本渲染，非手写）

夹具全部落 tempdir 自建；不读写本仓库真实 diy-output；不依赖本机 git 状态；不真调模型。
运行：cd diy-coder && python -m unittest discover -s tests -p "test_bmb_builder.py" -v
"""
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.abspath(os.path.join(HERE, "..", "skills", "diy-bmb-builder"))
ENGINE = os.path.join(SKILL_DIR, "scripts", "bmb_builder.py")
SKILL_MD = os.path.join(SKILL_DIR, "SKILL.md")
STEPS_DIR = os.path.join(SKILL_DIR, "steps")
NL = "\n"

# 母本 §1 实例解析句 · 中文定稿（逐字；契约冒烟断言锚串）
INSTANCE_ZH = ('实例解析（FR-4.5/D-9）由工具脚本执行：运行 '
               '`python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" resolve '
               '[--instance <name>] --json`，把回执里的 `output_dir` 当作本次运行唯一的读写根目录。')
# 母本 §4 读取纪律（逐字）
READ_ZH = ('读取纪律：预载预算 = 本文件、上述配置与回执、`steps/` 下当前那一个文件——绝不批量预载；'
           '执行期读取以每个步骤开头的 `Read (input)` 行为唯一权威，**主文件不列举封闭清单**。')
# 母本 §6 精准简练（逐字）
PRECISE_ZH = ('- **精准简练。** 写进产物的每条内容都要精准、简练：一条只讲一件事；'
              '不复述上游已写的信息（引用 ID）；不写没有信息量的套话。')
# 母本 §3 配置解析锚串（与 test_suite_texts.py 的 ANCHOR_RESOLVE_KEYS 同值同形）
CONFIG_ZH = ("解析 `project.communication_language` / "
             "`project.document_output_language` / `paths.output_dir`")

COMMON_KEYS = ("ok", "command", "project_root", "output_dir",
               "violations", "warnings", "counts")


def run_engine(args, cwd=None):
    if not os.path.isfile(ENGINE):
        raise AssertionError("引擎文件不存在：%s" % ENGINE)
    proc = subprocess.run([sys.executable, ENGINE] + args,
                          capture_output=True, text=True, encoding="utf-8", cwd=cwd)
    if proc.stdout is None or proc.stderr is None:
        raise AssertionError("引擎输出非 UTF-8（stderr 被非 UTF-8 字节污染？%r）" % (args,))
    return proc


def read(path):
    with io.open(path, encoding="utf-8") as fh:
        return fh.read()


def write(path, text):
    parent = os.path.dirname(path)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent)
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


class EngineCase(unittest.TestCase):
    """tmp 项目根（含 .claude/skills 与 diy-output）的公共夹具。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="bmb-builder-")
        self.root = self.tmp.name
        self.out = os.path.join(self.root, "diy-output")
        self.skills = os.path.join(self.root, ".claude", "skills")
        os.makedirs(self.out)
        os.makedirs(self.skills)

    def tearDown(self):
        self.tmp.cleanup()

    def common(self, *extra):
        return ["--project-root", self.root, "--output-dir", self.out] + list(extra)

    def scaffold(self, name, *extra):
        return run_engine(["scaffold", "--name", name, "--json"] + self.common(*extra))

    def payload(self, proc):
        self.assertEqual(proc.returncode in (0, 1, 3), True,
                         "非预期退出码 %d（stderr=%s）" % (proc.returncode, proc.stderr))
        return json.loads(proc.stdout.strip().splitlines()[-1])


class GateTests(EngineCase):
    """用例 1：门禁面（零产出退出 + 路由句在场）。"""

    def test_missing_target_is_refused_with_zero_output(self):
        ghost = os.path.join(self.root, "ghost-skill")
        before = sorted(os.listdir(self.root))
        for args in (["check", "--target", ghost, "--json"],
                     ["prepass", "--target", ghost, "--json"],
                     ["scan", "--target", ghost, "--json"]):
            proc = run_engine(args + self.common())
            self.assertEqual(proc.returncode, 1, "%s 应拒绝" % args[0])
            data = json.loads(proc.stdout)
            self.assertFalse(data["ok"])
            self.assertEqual(data["violations"][0]["code"], "MISSING_FILE",
                             "%s 的拒绝码" % args[0])
        self.assertEqual(sorted(os.listdir(self.root)), before, "拒绝路径须零产出")
        self.assertFalse(os.path.exists(ghost), "拒绝路径不得代建目标目录")

    def test_intent_gate_sentences_present(self):
        text = read(os.path.join(STEPS_DIR, "01-intent.md"))
        for anchor in ("零产出", "停并问", "MISSING_FILE",
                       "module-plan.yaml", "build_order", "已定稿"):
            self.assertIn(anchor, text, "01-intent.md 缺门禁/入口锚串 %r" % anchor)


class ScaffoldTests(EngineCase):
    """用例 2 / 3：脚手架成功路径、名字非法、目标已存在、旗标互斥。"""

    def test_scaffold_creates_skill_tree(self):
        proc = self.scaffold("demo-skill")
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        data = self.payload(proc)
        self.assertTrue(data["ok"])
        skill_md = os.path.join(self.skills, "demo-skill", "SKILL.md")
        self.assertTrue(os.path.isfile(skill_md), "SKILL.md 未落盘")
        self.assertTrue(os.path.isdir(os.path.join(self.skills, "demo-skill", "steps")),
                        "steps/ 未 stub")
        self.assertIn("files_created", data, "scaffold 回执须含 files_created")
        self.assertTrue(any("demo-skill" in f for f in data["files_created"]))
        body = read(skill_md)
        for section in ("## 激活时", "## 工作流", "## 结构", "## 规则"):
            self.assertIn(section, body, "起手 SKILL.md 缺 %r" % section)
        self.assertIn("name: demo-skill", body)
        self.assertIn(INSTANCE_ZH, body, "起手 SKILL.md 须带母本 §1 定稿句")

    def test_bad_name_and_existing_target(self):
        proc = self.scaffold("Demo Skill")
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(self.payload(proc)["violations"][0]["code"], "NAME_ILLEGAL")

        self.assertEqual(self.scaffold("demo-skill").returncode, 0)
        again = self.scaffold("demo-skill")
        self.assertEqual(again.returncode, 1, "重复建同名须拒绝")
        self.assertEqual(self.payload(again)["violations"][0]["code"], "FILE_CONFLICT")

    def test_source_and_dest_are_mutually_exclusive(self):
        proc = self.scaffold("demo-skill", "--dest", self.skills, "--to-source")
        self.assertEqual(proc.returncode, 2, "同给 --dest 与 --to-source 属用法错误")


class ReceiptTests(EngineCase):
    """用例 4：回执共同键 + warnings 同形 + 人读态。"""

    def test_receipt_keys_and_shapes(self):
        self.scaffold("demo-skill")
        target = os.path.join(self.skills, "demo-skill")
        proc = run_engine(["check", "--target", target, "--json"] + self.common())
        data = json.loads(proc.stdout)
        for key in COMMON_KEYS:
            self.assertIn(key, data, "回执缺共同键 %r" % key)
        for key in ("violations", "warnings"):
            for item in data[key]:
                self.assertEqual(set(item.keys()), {"code", "where", "msg"},
                                 "%s 条目形状须为 {code,where,msg}" % key)
        self.assertEqual(data["command"], "check")
        self.assertEqual(data["project_root"], self.root)
        self.assertTrue(data["output_dir"].endswith("diy-output"))
        self.assertEqual(proc.stdout.strip().count(NL), 0, "--json 须单行")
        self.assertNotIn("\\", data["output_dir"], "回执路径用正斜杠")

    def test_human_receipt_lines(self):
        self.scaffold("demo-skill")
        bad = os.path.join(self.skills, "demo-skill")
        write(os.path.join(bad, "SKILL.md"), "# 无四段的 SKILL" + NL)
        proc = run_engine(["check", "--target", bad] + self.common())
        self.assertEqual(proc.returncode, 1)
        lines = proc.stdout.strip().splitlines()
        self.assertTrue(any(" " in ln and ":" in ln for ln in lines[:-1]),
                        "人读态每条违规一行 `CODE where: msg`")
        self.assertTrue(lines[-1].startswith("汇总"), "末行须为汇总行")


class ContractSmokeTests(unittest.TestCase):
    """用例 5：SKILL.md / steps 契约冒烟（母本逐字 + 终门句 + 零 YAML 声明）。"""

    def test_skill_md_contract(self):
        text = read(SKILL_MD)
        self.assertIn(INSTANCE_ZH, text, "缺母本 §1 中文定稿逐字句")
        self.assertIn(CONFIG_ZH, text, "缺母本 §3 配置解析逐字块")
        self.assertIn(READ_ZH, text, "缺母本 §4 读取纪律逐字句")
        self.assertIn(PRECISE_ZH, text, "缺母本 §6 精准简练逐字块")
        self.assertIn("- **写作纪律。**", text, "缺母本 §2 写作纪律块")
        self.assertIn("scripts/bmb_builder.py", text, "终门句须指向本引擎")
        self.assertIn("零 YAML", text, "缺零 YAML 产物声明句")
        for section in ("## 激活时", "## 工作流", "## 结构", "## 规则"):
            self.assertIn(section, text, "缺四段之一 %r" % section)
        self.assertLessEqual(len(text.splitlines()), 90, "SKILL.md 须 ≤90 行")
        for field in ("name:", "description:", "phase:", "precededBy:", "followedBy:",
                      "required:", "line:", "outputs:"):
            self.assertIn(field, text, "frontmatter 缺字段 %r" % field)

    def test_final_gate_passes_on_own_skill_dir(self):
        proc = run_engine(["check", "--target", SKILL_DIR, "--final", "--json",
                           "--project-root", SKILL_DIR, "--output-dir", SKILL_DIR])
        self.assertEqual(proc.returncode, 0,
                         "本技能须过自己的终门：%s" % proc.stdout)
        data = json.loads(proc.stdout)
        self.assertTrue(data["ok"])
        self.assertEqual(data["counts"]["steps"], 5, "steps 文件数应为 5")


class PrepassTests(EngineCase):
    """用例 6：prepass 两套（metrics 计量 / integrity 判违规）。"""

    def _skill_with(self, body_extra="", root_files=None):
        name = "probe-skill"
        self.scaffold(name)
        target = os.path.join(self.skills, name)
        write(os.path.join(target, "SKILL.md"), read(os.path.join(target, "SKILL.md")) + body_extra)
        for rel, content in (root_files or {}).items():
            write(os.path.join(target, rel), content)
        write(os.path.join(target, "steps", "01-first.md"),
              "# Step 1 — 第一步" + NL + NL + "**Read (input):** x" + NL +
              "**Write (output):** y" + NL + NL + "Make sure to open the floor." + NL)
        return target

    def test_metrics_counts_and_waste(self):
        target = self._skill_with()
        proc = run_engine(["prepass", "--target", target, "--set", "metrics", "--json"]
                          + self.common())
        self.assertEqual(proc.returncode, 0, "metrics 面不判违规：%s" % proc.stdout)
        data = json.loads(proc.stdout)
        metrics = data["metrics"]
        self.assertGreaterEqual(metrics["counts"]["files"], 2)
        self.assertGreater(metrics["counts"]["tokens"], 0)
        methods = {f["method"] for f in metrics["files"]}
        self.assertTrue(methods <= {"tiktoken", "fallback"}, "计数方法须二选一")
        labels = [w["label"] for f in metrics["files"] for w in f["waste"]]
        self.assertTrue(any("make sure" in lb.lower() for lb in labels),
                        "废话模式 grep 须命中：%s" % labels)

    def test_integrity_flags_numbered_stage_at_root(self):
        target = self._skill_with(root_files={"01-stage.md": "# 阶段一" + NL})
        proc = run_engine(["prepass", "--target", target, "--set", "integrity", "--json"]
                          + self.common())
        self.assertEqual(proc.returncode, 1, "根级编号前缀阶段文件须判违规")
        data = json.loads(proc.stdout)
        codes = {item["code"] for item in data["violations"]}
        self.assertIn("NAME_ILLEGAL", codes)
        self.assertTrue(all(item["where"].find("\\") < 0 for item in data["violations"]))


class MlogTests(EngineCase):
    """用例 7：mlog 追加的原子性与 ack 形状。"""

    def test_append_only_and_ack(self):
        logs = os.path.join(self.out, "build-logs")
        args = ["mlog", "--dir", logs, "--file", "demo-skill.md", "--json"]
        init = run_engine(["mlog", "--dir", logs, "init", "--file", "demo-skill.md",
                           "--subject", "demo-skill 构建", "--json"] + self.common())
        self.assertEqual(init.returncode, 0, init.stderr + init.stdout)
        ack = json.loads(init.stdout.strip())
        self.assertEqual(ack["appended"], False)
        self.assertEqual(ack["n"], 0)

        first = run_engine(["mlog", "--dir", logs, "append", "--file", "demo-skill.md",
                            "--type", "decision", "--text", "先写最小版本", "--json"]
                           + self.common())
        self.assertEqual(first.returncode, 0)
        ack1 = json.loads(first.stdout.strip())
        self.assertEqual(ack1["appended"], True)
        self.assertEqual(ack1["n"], 1)
        self.assertTrue(ack1["file"].endswith("build-logs/demo-skill.md"), ack1["file"])
        body_before = read(os.path.join(logs, "demo-skill.md"))

        second = run_engine(["mlog", "--dir", logs, "append", "--file", "demo-skill.md",
                             "--type", "gap", "--text", "缺真专家知识", "--json"] + self.common())
        ack2 = json.loads(second.stdout.strip())
        self.assertEqual(ack2["n"], 2)
        body_after = read(os.path.join(logs, "demo-skill.md"))
        self.assertTrue(body_after.startswith(body_before.rstrip(NL)),
                        "只追加：既有内容须是前缀")

        done = run_engine(["mlog", "--dir", logs, "set-complete", "--file", "demo-skill.md",
                           "--json"] + self.common())
        self.assertEqual(done.returncode, 0)
        self.assertIn("complete", read(os.path.join(logs, "demo-skill.md")))

        missing = run_engine(["mlog", "--dir", logs, "append", "--file", "ghost.md",
                              "--type", "note", "--text", "x", "--json"] + self.common())
        self.assertEqual(missing.returncode, 1)
        self.assertEqual(json.loads(missing.stdout)["violations"][0]["code"], "MISSING_FILE")

        bad_type = run_engine(["mlog", "--dir", logs, "append", "--file", "demo-skill.md",
                               "--type", "闲聊", "--text", "x", "--json"] + self.common())
        self.assertEqual(bad_type.returncode, 1)
        self.assertEqual(json.loads(bad_type.stdout)["violations"][0]["code"], "ENUM_INVALID")

    def test_file_name_is_pure_name_only(self):
        """`--file` 只收纯文件名：越界/占位/空白名一律 NAME_ILLEGAL，且零写入（V 修复 1）。"""
        logs = os.path.join(self.out, "build-logs")
        escaped = os.path.join(self.out, "escaped.md")
        for name in ("../../escaped.md", "sub/other.md", "sub\\other.md", ".", "..", "   "):
            proc = run_engine(["mlog", "--dir", logs, "init", "--file", name,
                               "--subject", "越界试探", "--json"] + self.common())
            self.assertEqual(proc.returncode, 1, "`--file %r` 须拒绝" % name)
            data = json.loads(proc.stdout)
            self.assertEqual(data["violations"][0]["code"], "NAME_ILLEGAL",
                             "`--file %r` 的拒绝码" % name)
            self.assertEqual(data["violations"][0]["where"], "--file")
            self.assertIn("file", data, "被拒路径也须回 file 键（与 W3 的 mlog 同形）")
            self.assertIn("action", data, "被拒路径也须回 action 键")
        self.assertFalse(os.path.exists(escaped), "越界路径不得落盘")
        self.assertFalse(os.path.exists(os.path.join(self.out, "sub")), "不得代建越界父目录")
        self.assertFalse(os.path.exists(os.path.join(logs, "escaped.md")), "零写入")


class CodeRegistryTests(unittest.TestCase):
    """修复 2：`INTERNAL_ERROR` 须在模块 docstring 的新增码清单里登记（§2.2 硬要求）。"""

    def test_internal_error_is_declared(self):
        text = read(ENGINE)
        docstring = text.split('"""')[1]
        self.assertIn("INTERNAL_ERROR", docstring, "模块 docstring 须登记 INTERNAL_ERROR")
        self.assertIn("未预期异常", docstring, "登记须说明它是什么面")
        self.assertIn("batch3-contract §3 冻结集", docstring, "登记须说明它与冻结集的关系")


class DestinationTests(EngineCase):
    """用例 8：落点（默认 dest 由 --project-root 算出）+ --force 硬护栏。"""

    def test_default_dest_is_install_face(self):
        proc = self.scaffold("落点技能")
        self.assertEqual(proc.returncode, 1, "非 hyphen-case 名拒绝")
        proc = self.scaffold("dest-probe")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue(os.path.isfile(os.path.join(self.skills, "dest-probe", "SKILL.md")),
                        "默认落 {project-root}/.claude/skills/<name>/")

    def test_force_guardrail_refuses_built_skill_name(self):
        proc = run_engine(["scaffold", "--name", "diy-dev", "--force", "--json"]
                          + self.common())
        self.assertEqual(proc.returncode, 1, "--force 也须拒绝已建技能名")
        self.assertEqual(self.payload(proc)["violations"][0]["code"], "FILE_CONFLICT")

    def test_force_rebuilds_ordinary_target(self):
        self.scaffold("ordinary-skill")
        target = os.path.join(self.skills, "ordinary-skill")
        write(os.path.join(target, "STALE.md"), "旧内容" + NL)
        proc = run_engine(["scaffold", "--name", "ordinary-skill", "--force", "--json"]
                          + self.common())
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        self.assertFalse(os.path.exists(os.path.join(target, "STALE.md")), "重建须清场")
        self.assertTrue(os.path.isfile(os.path.join(target, "SKILL.md")))


class TemplateTests(EngineCase):
    """用例 9：template 两级语义（残留 {if-} 硬失败 / 残留 {token} 交人判断）。"""

    def test_leftover_if_marker_is_hard_failure(self):
        src = os.path.join(self.root, "broken.md")
        write(src, "{if-a}甲{/if-b}" + NL)
        proc = run_engine(["template", "--src", src, "--dest",
                           os.path.join(self.root, "out.md"), "--json"] + self.common())
        self.assertEqual(proc.returncode, 3, "残留 {if-} → exit 3")
        self.assertFalse(os.path.exists(os.path.join(self.root, "out.md")), "硬失败须零产出")

    def test_conditional_and_variable_substitution(self):
        src = os.path.join(self.root, "tpl.md")
        dest = os.path.join(self.root, "rendered.md")
        write(src, "{if-rich}富版{/if-rich}{if-lean}精简版{/if-lean}" + NL +
              "名 = {skill-name}" + NL + "根 = {project-root}" + NL)
        proc = run_engine(["template", "--src", src, "--dest", dest,
                           "--set", "skill-name=demo-skill", "--true", "lean", "--json"]
                          + self.common())
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        data = self.payload(proc)
        self.assertIn("tokens_remaining", data, "template 回执须含 tokens_remaining")
        self.assertIn("{project-root}", data["tokens_remaining"])
        body = read(dest)
        self.assertNotIn("富版", body)
        self.assertIn("精简版", body)
        self.assertIn("名 = demo-skill", body)


class TokenTests(EngineCase):
    """用例 10：未解析 {…} 令牌拒绝；{project-root} 是唯一例外。"""

    def test_unresolved_token_rejected(self):
        proc = run_engine(["check", "--target", "{output_dir}/skills/demo", "--json"]
                          + self.common())
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(json.loads(proc.stdout)["violations"][0]["code"], "TOKEN_UNRESOLVED")

    def test_project_root_token_is_resolved(self):
        dest = os.path.join("{project-root}", ".claude", "skills")
        proc = run_engine(["scaffold", "--name", "token-probe", "--dest", dest, "--json"]
                          + self.common())
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        self.assertTrue(os.path.isfile(os.path.join(self.skills, "token-probe", "SKILL.md")))
        self.assertFalse(os.path.isdir(os.path.join(self.root, "{project-root}")),
                         "不得造出字面 {project-root} 目录")


class ScanTests(EngineCase):
    """用例 11：scan 机械面（路径形态 + 脚本合规）。"""

    def test_scan_flags_absolute_and_escape(self):
        self.scaffold("scan-probe")
        target = os.path.join(self.skills, "scan-probe")
        write(os.path.join(target, "steps", "01-go.md"),
              "# Step 1 — 走" + NL + NL + "**Read (input):** ../outside.md" + NL +
              "**Write (output):** C:/abs/path.md" + NL)
        proc = run_engine(["scan", "--target", target, "--check", "path-standards", "--json"]
                          + self.common())
        self.assertEqual(proc.returncode, 1)
        data = json.loads(proc.stdout)
        self.assertIn("scan", data)
        msgs = " ".join(item["msg"] for item in data["violations"])
        self.assertIn("绝对路径", msgs)
        self.assertIn("..", msgs)

    def test_scan_scripts_conventions(self):
        self.scaffold("script-probe")
        target = os.path.join(self.skills, "script-probe")
        write(os.path.join(target, "scripts", "bad.py"), "print('no header')" + NL)
        proc = run_engine(["scan", "--target", target, "--check", "scripts", "--json"]
                          + self.common())
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(json.loads(proc.stdout)["violations"][0]["code"], "EMPTY_FIELD")


class RenderTests(EngineCase):
    """用例 12：render 由脚本落 md/html（不得手写 HTML）。"""

    def test_render_writes_report_pair(self):
        run_dir = os.path.join(self.root, "analysis-run")
        findings = {
            "schema_version": 2,
            "subject": "skills/demo-skill",
            "generated": "2026-09-21",
            "verdict": "一句话总评",
            "grade": "good",
            "summary": "两句话叙述。",
            "findings": [
                {"id": "leanness-1", "lens": "leanness", "severity": "high",
                 "title": "仪式段", "location": "SKILL.md:20",
                 "evidence": "观察到", "recommendation": "删掉"},
            ],
        }
        write(os.path.join(run_dir, "findings.json"), json.dumps(findings, ensure_ascii=False))
        proc = run_engine(["render", "--dir", run_dir, "--json"] + self.common())
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        html = read(os.path.join(run_dir, "skill-analysis-report.html"))
        md = read(os.path.join(run_dir, "skill-analysis-report.md"))
        self.assertIn("leanness-1", html)
        self.assertIn("一句话总评", md)
        self.assertIn("Schema: 2", md)
        self.assertNotIn("{{", html, "不得残留未替换的模板标记")

    def test_render_refuses_malformed_findings(self):
        run_dir = os.path.join(self.root, "bad-run")
        write(os.path.join(run_dir, "findings.json"), "{不是 JSON")
        proc = run_engine(["render", "--dir", run_dir, "--json"] + self.common())
        self.assertEqual(proc.returncode, 1)
        self.assertFalse(os.path.exists(os.path.join(run_dir, "skill-analysis-report.html")))


if __name__ == "__main__":
    unittest.main()
