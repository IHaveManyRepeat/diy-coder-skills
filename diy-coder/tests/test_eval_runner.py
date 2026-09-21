# -*- coding: utf-8 -*-
"""diy-eval-runner 确定性引擎测试（B5 批 W3，任务书 §2.5 W3 清单 ①–⑦）。

覆盖（任务书 §2.5 W3 七项 + 降级/隔离面）：
- 用例 ①：门禁——target 缺席 / 无 SKILL.md / 找不到 cases / `--mode` 非法
          / `load_signal` 子串式，全部拒绝 + 零产出
- 用例 ②：`run --mode baseline` 在**假 adapter**（不真调模型）下产出 run 目录结构
          （公共根三件 + `<config>/<case-id>/` 五件 + `--runs>1` 下钻 `run-N/`），
          并断言 baseline 语义（`skill` 侧已 stage、`bare` 侧什么都没 stage）、
          零 YAML 主产物、`state_prefix` 已前置、回执键完整（warnings 与 violations 同形）
- 用例 ③：trigger 的 `--queries` 形状（`queries/q{idx}-r{run}/` + `triggers-result.json`）
          与**只认 `tool_use`**（init 事件 + 文本提及都出现技能名 → 不算触发）
- 用例 ④：aggregate 的 mean / n-1 标准差 / delta 公式 + `--self-test`
- 用例 ⑤：`check --run-dir D` 终门——合法 run 放行；计数与实际目录不符 → SET_MISMATCH；
          quality 模式缺 `grading.json` → MISSING_FILE（补齐后放行）
- 用例 ⑥：SKILL.md 契约冒烟（母本 §1/§2/§3/§4/§6 逐字 + 四段 + 六字段 + ≤90 行 +
          「永不删除、覆盖、轮转」声明 + §5 不适用的理由句 + 四对边界句 + 两条反自欺硬规则）
- 用例 ⑦：未解析 `{...}` 令牌 → `TOKEN_UNRESOLVED`（`{project-root}` 由引擎自解析）
- 用例 ⑧：`mlog`（与 W1 同构：`--dir` + `--file` + 恒发一行 ack `{ok, file, n, appended}`）
- 用例 ⑨：两条降级路径——`invocation` 解析为空 → 只 stage + 结果记 `skipped`；
          命令不在 PATH（白名单未覆盖）→ 跳过该 mode + warning，都不崩、都不入队
- 用例 ⑩：清场环境的隔离契约（从零构建、不继承宿主；auth 变量仅在宿主非空时传）

夹具全部落 tempdir 自建；不读写本仓库真实 diy-output；不依赖本机 git 状态；**不真调模型**
（假 adapter 是本地脚本，只回放 JSONL transcript）。
运行：cd diy-coder && python -m unittest discover -s tests -p "test_eval_runner.py" -v
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.join(HERE, "..", "skills", "diy-eval-runner")
ENGINE = os.path.join(SKILL_DIR, "scripts", "eval_runner.py")
SKILL_MD = os.path.join(SKILL_DIR, "SKILL.md")
NL = chr(10)

# 套件级句式母本（suite-texts.md §1 / §2 / §3 / §4 / §6 中文定稿，逐字）
INSTANCE_ZH = ("实例解析（FR-4.5/D-9）由工具脚本执行：运行 "
               "`python \"{project-root}/.claude/skills/diy-tools/scripts/diyc.py\" "
               "resolve [--instance <name>] --json`，把回执里的 `output_dir` "
               "当作本次运行唯一的读写根目录。")
RESOLVE_KEYS_ZH = ("解析 `project.communication_language` / "
                   "`project.document_output_language` / `paths.output_dir`")
READ_DISCIPLINE_ZH = ("读取纪律：预载预算 = 本文件、上述配置与回执、`steps/` 下当前那一个文件"
                      "——绝不批量预载；执行期读取以每个步骤开头的 `Read (input)` 行为唯一权威，"
                      "**主文件不列举封闭清单**。")
DISCIPLINE_ZH = ("- **写作纪律。** 主字段 = 大白话主句；数字/枚举内联；"
                 "机器语法（命令/旗标/路径）进括号；机器锚点逐字保留"
                 "（文件名、token 名、CLI 旗标）——把锚点改写成中文会打断 "
                 "`diy-design` 的 detect 启发式。schema 若定义 `plain`："
                 "一行写清该条目为什么存在，绝不写是什么（转述会漂移）；"
                 "只写难懂的条目。若定义 `detail`：过程叙述——结论留在主字段。")
PRECISE_ZH = ("- **精准简练。** 写进产物的每条内容都要精准、简练：一条只讲一件事；"
              "不复述上游已写的信息（引用 ID）；不写没有信息量的套话。")

SKILL_FIXTURE = NL.join([
    "---",
    "name: diy-foo",
    "description: '假技能——评测夹具，不参与任何真实调用。'",
    "---",
    "",
    "# diy-foo",
    "",
    "夹具技能。",
]) + NL

CASES = [{
    "id": "create-1",
    "input": "给 InsuLens 写一份 brief，笔记在 evals/files/memo.md",
    "rubric": ["brief.md 存在且字数在 250-1500 之间"],
    "state_prefix": "[技能已走完发现阶段；第 4 轮用户被问及干系人，回答：]",
    "files": [],
}]

QUERIES = [
    {"query": "TRIGGER 请评测我的技能", "should_trigger": True},
    {"query": "SUBSTR_ONLY 只是提了一下它的名字", "should_trigger": False},
]

# 假 adapter：不调任何模型，按 prompt 关键字回放 JSONL transcript。
# init 事件列出全部发现的技能名（= 子串匹配的陷阱）；纯文本提及同样出现技能名。
FAKE_ADAPTER = NL.join([
    "# -*- coding: utf-8 -*-",
    '"""假 adapter 夹具：只回放 JSONL transcript，不调模型。"""',
    "import glob",
    "import json",
    "import os",
    "import sys",
    "",
    "",
    "sys.stdout.reconfigure(encoding=\"utf-8\")",
    "",
    "",
    "def emit(obj):",
    "    sys.stdout.write(json.dumps(obj, ensure_ascii=False) + chr(10))",
    "    sys.stdout.flush()",
    "",
    "",
    "argv = sys.argv[1:]",
    'prompt = argv[argv.index("-p") + 1] if "-p" in argv else " ".join(argv)',
    'skills = sorted(glob.glob(os.path.join(os.getcwd(), ".claude", "skills", "*-trig-*")))',
    'names = [os.path.basename(p) for p in skills] or ["<无合成技能>"]',
    "",
    'emit({"type": "system", "subtype": "init", "skills": names})',
    "for name in names:",
    '    emit({"type": "text", "text": "discovered skill: " + name})',
    "",
    'if "TRIGGER" in prompt and skills:',
    "    emit({\"type\": \"assistant\", \"message\": {\"content\": [",
    '        {"type": "tool_use", "name": "Skill",',
    '         "input": {"skill": names[0]}}],',
    '        "usage": {"input_tokens": 7, "output_tokens": 3}}})',
    "else:",
    "    emit({\"type\": \"assistant\", \"message\": {\"content\": [",
    '        {"type": "text", "text": "已完成"}],',
    '        "usage": {"input_tokens": 11, "output_tokens": 5}}})',
    "",
    'emit({"type": "result", "usage": {"input_tokens": 11, "output_tokens": 5},',
    '      "env_keys": sorted(os.environ.keys()), "cwd": os.getcwd()})',
]) + NL


def _write(path, text):
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


class Base(unittest.TestCase):
    """tmp 项目根 + 假技能 + 假 adapter 的公共夹具。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="evalrunner-")
        self.root = self.tmp.name
        self.proj = os.path.join(self.root, "proj")
        self.out = os.path.join(self.proj, "diy-output")
        self.skill = os.path.join(self.proj, "skills", "diy-foo")
        _write(os.path.join(self.skill, "SKILL.md"), SKILL_FIXTURE)
        _write(os.path.join(self.skill, "evals", "cases.json"),
               json.dumps(CASES, ensure_ascii=False))
        self.fake = os.path.join(self.root, "fake_adapter.py")
        _write(self.fake, FAKE_ADAPTER)
        self.adapter = os.path.join(self.root, "adapter.json")
        _write(self.adapter, json.dumps({
            "invocation": [sys.executable, self.fake, "-p", "{prompt}"],
            "auth_env": "ANTHROPIC_API_KEY",
        }, ensure_ascii=False))
        os.makedirs(self.out, exist_ok=True)

    def tearDown(self):
        self.tmp.cleanup()

    def engine(self, args, extra_env=None):
        env = dict(os.environ)
        env.pop("ANTHROPIC_API_KEY", None)
        if extra_env:
            env.update(extra_env)
        return subprocess.run([sys.executable, ENGINE] + args,
                              capture_output=True, text=True, encoding="utf-8",
                              cwd=self.root, env=env)

    def receipt(self, result):
        return json.loads(result.stdout)

    def run_dirs(self):
        base = os.path.join(self.out, "eval-runs")
        if not os.path.isdir(base):
            return []
        return [os.path.join(base, d) for d in sorted(os.listdir(base))
                if os.path.isdir(os.path.join(base, d))]

    def only_run(self):
        dirs = self.run_dirs()
        self.assertEqual(len(dirs), 1, "期望恰好一个 run 目录，实得 %s" % dirs)
        return dirs[0]

    def codes(self, payload):
        return {x["code"] for x in payload["violations"]}


class GateTests(Base):
    """用例 ①：门禁（拒绝 + 零产出）。"""

    def test_missing_skill_and_skill_md(self):
        missing = os.path.join(self.proj, "skills", "diy-nope")
        r = self.engine(["run", "--skill", missing, "--output-dir", self.out,
                         "--project-root", self.proj, "--json"])
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("MISSING_FILE", self.codes(self.receipt(r)))
        bare = os.path.join(self.proj, "skills", "diy-bare")
        os.makedirs(bare, exist_ok=True)
        r = self.engine(["run", "--skill", bare, "--output-dir", self.out,
                         "--project-root", self.proj, "--json"])
        self.assertEqual(r.returncode, 1)
        self.assertIn("SKILL.md", self.receipt(r)["violations"][0]["msg"])
        self.assertEqual(self.run_dirs(), [], "门禁拒绝必须零产出")

    def test_no_cases_file_means_no_invention(self):
        empty = os.path.join(self.proj, "skills", "diy-empty")
        _write(os.path.join(empty, "SKILL.md"), SKILL_FIXTURE)
        r = self.engine(["run", "--skill", empty, "--mode", "quality",
                         "--output-dir", self.out, "--project-root", self.proj, "--json"])
        self.assertEqual(r.returncode, 1)
        payload = self.receipt(r)
        self.assertIn("MISSING_FILE", self.codes(payload))
        self.assertIn("不发明用例", payload["violations"][0]["msg"])
        self.assertEqual(self.run_dirs(), [])

    def test_bad_mode_and_substring_load_signal(self):
        r = self.engine(["run", "--skill", self.skill, "--mode", "bogus",
                         "--output-dir", self.out, "--project-root", self.proj, "--json"])
        self.assertEqual(r.returncode, 1)
        self.assertIn("ENUM_INVALID", self.codes(self.receipt(r)))

        bad = os.path.join(self.root, "adapter-substr.json")
        _write(bad, json.dumps({
            "invocation": [sys.executable, self.fake, "-p", "{prompt}"],
            "load_signal": {"type": "string", "pattern": "diy-foo"},
        }, ensure_ascii=False))
        r = self.engine(["run", "--skill", self.skill, "--mode", "trigger",
                         "--queries", self._queries_file(), "--adapter", bad,
                         "--output-dir", self.out, "--project-root", self.proj, "--json"])
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        payload = self.receipt(r)
        self.assertIn("ENUM_INVALID", self.codes(payload))
        self.assertIn("子串", payload["violations"][0]["msg"])
        self.assertEqual(self.run_dirs(), [])

    def _queries_file(self):
        path = os.path.join(self.root, "queries.json")
        _write(path, json.dumps(QUERIES, ensure_ascii=False))
        return path


class RunModeTests(Base):
    """用例 ②：baseline 真跑（假 adapter）+ run 目录结构 + 回执键。"""

    def _run(self, extra=None):
        args = ["run", "--skill", self.skill, "--mode", "baseline",
                "--adapter", self.adapter, "--runs", "2", "--label", "evals",
                "--output-dir", self.out, "--project-root", self.proj, "--json"]
        return self.engine(args + (extra or []))

    def test_baseline_run_dir_shape(self):
        r = self._run()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        payload = self.receipt(r)
        run_dir = self.only_run()
        self.assertEqual(payload["run_dir"].replace("\\", "/"),
                         os.path.normpath(run_dir).replace("\\", "/"))

        # 公共根三件
        for name in ("run.json", "execution-summary.json", ".memlog.md"):
            self.assertTrue(os.path.isfile(os.path.join(run_dir, name)), name)
        run_json = json.loads(_read(os.path.join(run_dir, "run.json")))
        for key in ("run_id", "skill_path", "mode", "configs", "runs_per_case",
                    "adapter", "started_at", "case_count"):
            self.assertIn(key, run_json, key)
        self.assertEqual(run_json["configs"], ["skill", "bare"])
        self.assertEqual(run_json["case_count"], 1)

        # `<config>/<case-id>/run-N/` 五件
        for config in ("skill", "bare"):
            for run_idx in (1, 2):
                cdir = os.path.join(run_dir, config, "create-1", "run-%d" % run_idx)
                for name in ("prompt.txt", "case.json", "transcript.jsonl", "timing.json"):
                    self.assertTrue(os.path.isfile(os.path.join(cdir, name)),
                                    "%s/%s" % (config, name))
                self.assertTrue(os.path.isdir(os.path.join(cdir, "cwd")))
                prompt = _read(os.path.join(cdir, "prompt.txt"))
                self.assertTrue(prompt.startswith(CASES[0]["state_prefix"]),
                                "state_prefix 必须前置：%r" % prompt[:40])
                self.assertIn(CASES[0]["input"], prompt)

        # baseline 语义：skill 侧 stage 了技能、bare 侧什么都没 stage
        staged = os.path.join(run_dir, "skill", "create-1", "run-1",
                              "cwd", ".claude", "skills", "diy-foo", "SKILL.md")
        self.assertTrue(os.path.isfile(staged), "skill 配置必须 stage 被测技能")
        self.assertFalse(os.path.exists(os.path.join(
            run_dir, "bare", "create-1", "run-1", "cwd", ".claude")),
            "bare 配置不得 stage 任何技能")

        # 零 YAML 主产物
        yamls = []
        for dirpath, _dirs, files in os.walk(run_dir):
            yamls += [f for f in files if f.endswith((".yaml", ".yml"))]
        self.assertEqual(yamls, [], "run 目录零 YAML 主产物")

        # 回执键完整（warnings 与 violations 同形）
        for key in ("ok", "command", "project_root", "output_dir",
                    "violations", "warnings", "counts"):
            self.assertIn(key, payload, key)
        self.assertEqual(payload["violations"], [])
        for item in payload["warnings"]:
            self.assertEqual(set(item), {"code", "where", "msg"})
        self.assertEqual(payload["counts"]["executed"], 4)
        self.assertEqual(payload["counts"]["skipped"], 0)
        summary = json.loads(_read(os.path.join(run_dir, "execution-summary.json")))
        self.assertEqual(summary["total"], 4)
        self.assertEqual(len(summary["results"]), 4)

    def test_variant_and_combined_modes(self):
        stripped = os.path.join(self.proj, "skills", "diy-foo-min")
        _write(os.path.join(stripped, "SKILL.md"), SKILL_FIXTURE)
        r = self.engine(["run", "--skill", self.skill, "--mode", "variant",
                         "--variant-path", stripped, "--adapter", self.adapter,
                         "--output-dir", self.out, "--project-root", self.proj, "--json"])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        run_dir = self.only_run()
        run_json = json.loads(_read(os.path.join(run_dir, "run.json")))
        self.assertEqual(run_json["configs"], ["skill", "variant"])
        self.assertEqual(run_json["variant_path"].replace("\\", "/"),
                         os.path.normpath(stripped).replace("\\", "/"))
        for config in ("skill", "variant"):
            self.assertTrue(os.path.isfile(os.path.join(
                run_dir, config, "create-1", "transcript.jsonl")), config)
        r = self.engine(["check", "--run-dir", run_dir,
                         "--project-root", self.proj, "--json"])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

        # variant 模式缺 --variant-path → 用法错误（exit 2），零产出
        r = self.engine(["run", "--skill", self.skill, "--mode", "variant",
                         "--output-dir", self.out, "--project-root", self.proj, "--json"])
        self.assertEqual(r.returncode, 2)


class TriggerTests(Base):
    """用例 ③：trigger 形状 + 只认 `tool_use`。"""

    def test_trigger_only_tool_use_counts(self):
        queries = os.path.join(self.root, "queries.json")
        _write(queries, json.dumps(QUERIES, ensure_ascii=False))
        r = self.engine(["run", "--skill", self.skill, "--mode", "trigger",
                         "--queries", queries, "--adapter", self.adapter,
                         "--runs", "2", "--output-dir", self.out,
                         "--project-root", self.proj, "--json"])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        run_dir = self.only_run()

        result_path = os.path.join(run_dir, "triggers-result.json")
        self.assertTrue(os.path.isfile(result_path))
        data = json.loads(_read(result_path))
        self.assertEqual(data["detection"], "tool_use")
        by_query = {x["query"]: x for x in data["results"]}
        hit = by_query["TRIGGER 请评测我的技能"]
        miss = by_query["SUBSTR_ONLY 只是提了一下它的名字"]
        self.assertEqual(hit["trigger_rate"], 1.0)
        self.assertTrue(hit["pass"])
        self.assertEqual(miss["triggers"], 0,
                         "init 事件与纯文本提及都不算触发（禁整篇子串匹配）")
        self.assertEqual(miss["trigger_rate"], 0.0)
        self.assertTrue(miss["pass"], "该触发而没触发才算失败；不该触发的静默即为通过")

        # queries/q{idx}-r{run}/ 形状：含合成技能与 .home，且无 <config>/<case-id>/ 层
        for idx, run_idx in ((0, 1), (0, 2), (1, 1), (1, 2)):
            qdir = os.path.join(run_dir, "queries", "q%03d-r%d" % (idx, run_idx))
            self.assertTrue(os.path.isdir(qdir), qdir)
            self.assertTrue(os.path.isdir(os.path.join(qdir, ".home")))
            self.assertTrue(os.path.isfile(os.path.join(qdir, "transcript.jsonl")))
            skills = [d for d in os.listdir(os.path.join(qdir, ".claude", "skills"))
                      if d.startswith("diy-foo-trig-")]
            self.assertEqual(len(skills), 1, "合成技能唯一名后缀")
        for config in ("skill", "bare", "variant"):
            self.assertFalse(os.path.isdir(os.path.join(run_dir, config)),
                             "trigger 模式不得有 <config>/<case-id>/ 层")

        # 同一问句的多次重复共用一个合成技能名 → 终门能在每个 q{i}-r{j}/ 里找到它
        r = self.engine(["check", "--run-dir", run_dir,
                         "--project-root", self.proj, "--json"])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


class AggregateTests(Base):
    """用例 ④：aggregate 公式（mean / n-1 标准差 / delta）+ `--self-test`。"""

    def _fixture_run(self):
        run_dir = os.path.join(self.out, "eval-runs", "20260101-000000-fx")
        _write(os.path.join(run_dir, "run.json"), json.dumps({
            "run_id": "20260101-000000-fx", "skill_path": "x", "mode": ["baseline"],
            "configs": ["skill", "bare"], "runs_per_case": 3, "adapter": "fx",
            "started_at": "2026-01-01T00:00:00Z", "case_count": 1,
        }, ensure_ascii=False))
        for config, values in (("skill", (13.0, 15.0, 17.0)), ("bare", (10.0, 12.0, 14.0))):
            for i, val in enumerate(values, 1):
                _write(os.path.join(run_dir, config, "c1", "run-%d" % i, "timing.json"),
                       json.dumps({"case_id": "c1", "config": config, "status": "ok",
                                   "elapsed_s": val, "total_tokens": int(val * 10)},
                                  ensure_ascii=False))
        return run_dir

    def test_aggregate_formula_and_delta(self):
        run_dir = self._fixture_run()
        r = self.engine(["aggregate", "--run-dir", run_dir,
                         "--project-root", self.proj, "--json"])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        payload = self.receipt(r)
        skill = payload["configs"]["skill"]["metrics"]["elapsed_s"]
        self.assertEqual(skill["n"], 3)
        self.assertAlmostEqual(skill["mean"], 15.0)
        self.assertAlmostEqual(skill["stddev"], 2.0)   # n-1 贝塞尔校正
        self.assertEqual((skill["min"], skill["max"]), (13.0, 17.0))
        delta = payload["delta"]["elapsed_s"]
        self.assertAlmostEqual(delta["delta"], 3.0)    # 被测 skill − 基准 bare
        self.assertAlmostEqual(delta["delta_pct"], 25.0)
        self.assertEqual(payload["against"], "bare")
        self.assertEqual(payload["subject"], "skill")

    def test_self_test_and_default_against_fallback(self):
        r = self.engine(["aggregate", "--self-test", "--json"])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        payload = self.receipt(r)
        self.assertEqual(payload["self_test"], "passed")
        self.assertIn("stddev_n_minus_1", payload["checked"])

        run_dir = self._fixture_run()
        variant = os.path.join(run_dir, "variant")
        for i, val in enumerate((20.0, 22.0, 24.0), 1):
            _write(os.path.join(variant, "c1", "run-%d" % i, "timing.json"),
                   json.dumps({"case_id": "c1", "config": "variant", "status": "ok",
                               "elapsed_s": val}, ensure_ascii=False))
        _write(os.path.join(run_dir, "run.json"), json.dumps({
            "run_id": "20260701-000000-fx", "skill_path": "x", "mode": ["variant"],
            "configs": ["skill", "variant"], "runs_per_case": 3, "adapter": "fx",
            "started_at": "2026-07-01T00:00:00Z", "case_count": 1,
        }, ensure_ascii=False))
        os.remove(os.path.join(run_dir, "bare", "c1", "run-1", "timing.json"))
        r = self.engine(["aggregate", "--run-dir", run_dir,
                         "--against", "nope", "--json"])
        self.assertEqual(r.returncode, 1)
        self.assertIn("UNKNOWN_ID", self.codes(self.receipt(r)))


class CheckTests(Base):
    """用例 ⑤：`check --run-dir D` 终门。"""

    def _baseline_run(self):
        r = self.engine(["run", "--skill", self.skill, "--mode", "baseline",
                         "--adapter", self.adapter, "--output-dir", self.out,
                         "--project-root", self.proj, "--json"])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return self.only_run()

    def test_check_passes_on_valid_run_and_catches_drift(self):
        run_dir = self._baseline_run()
        r = self.engine(["check", "--run-dir", run_dir,
                         "--project-root", self.proj, "--json"])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        payload = self.receipt(r)
        self.assertTrue(payload["ok"])
        self.assertIn("run_dirs", payload["counts"])

        summary_path = os.path.join(run_dir, "execution-summary.json")
        summary = json.loads(_read(summary_path))
        summary["total"] += 1
        _write(summary_path, json.dumps(summary, ensure_ascii=False, indent=2))
        r = self.engine(["check", "--run-dir", run_dir,
                         "--project-root", self.proj, "--json"])
        self.assertEqual(r.returncode, 1)
        self.assertIn("SET_MISMATCH", self.codes(self.receipt(r)))

    def test_check_requires_grading_for_quality(self):
        r = self.engine(["run", "--skill", self.skill, "--mode", "quality",
                         "--adapter", self.adapter, "--output-dir", self.out,
                         "--project-root", self.proj, "--json"])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        run_dir = self.only_run()
        r = self.engine(["check", "--run-dir", run_dir,
                         "--project-root", self.proj, "--json"])
        self.assertEqual(r.returncode, 1, "quality 模式缺 grading.json 不得放行")
        self.assertIn("MISSING_FILE", self.codes(self.receipt(r)))

        case_dir = os.path.join(run_dir, "skill", "create-1")
        _write(os.path.join(case_dir, "grading.json"), json.dumps({
            "case_id": "create-1",
            "expectations": [{"text": "brief.md 存在且字数在 250-1500 之间",
                              "passed": True, "evidence": "cwd/brief.md，487 词"}],
            "summary": {"passed": 1, "failed": 0, "total": 1, "pass_rate": 1.0},
            "rubric_feedback": {"weak": [], "uncovered": [],
                                "overall": "No suggestions; the rubric looks discriminating."},
        }, ensure_ascii=False))
        r = self.engine(["check", "--run-dir", run_dir,
                         "--project-root", self.proj, "--json"])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_check_missing_run_dir(self):
        r = self.engine(["check", "--run-dir", os.path.join(self.out, "eval-runs", "nope"),
                         "--project-root", self.proj, "--json"])
        self.assertEqual(r.returncode, 1)
        self.assertIn("MISSING_FILE", self.codes(self.receipt(r)))


class DegradeTests(Base):
    """用例 ⑨：两条降级路径（skip + warning，不崩、不入队）。"""

    def test_no_invocation_stages_only(self):
        r = self.engine(["run", "--skill", self.skill, "--mode", "baseline",
                         "--output-dir", self.out, "--project-root", self.proj, "--json"])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        payload = self.receipt(r)
        run_dir = self.only_run()
        self.assertEqual(payload["counts"]["skipped"], 2)
        self.assertEqual(payload["counts"]["executed"], 0)
        self.assertTrue(payload["warnings"], "降级不得静默")
        self.assertIn("ADAPTER_MISSING", {x["code"] for x in payload["warnings"]})
        # 只 stage：prompt / case / cwd 在场，transcript 不在场
        case_dir = os.path.join(run_dir, "skill", "create-1")
        self.assertTrue(os.path.isfile(os.path.join(case_dir, "prompt.txt")))
        self.assertTrue(os.path.isdir(os.path.join(case_dir, "cwd")))
        self.assertFalse(os.path.exists(os.path.join(case_dir, "transcript.jsonl")))
        r = self.engine(["check", "--run-dir", run_dir,
                         "--project-root", self.proj, "--json"])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_unresolvable_command_skips_mode(self):
        r = self.engine(["run", "--skill", self.skill, "--mode", "baseline",
                         "--invocation", "diy-no-such-cmd-xyz", "{prompt}",
                         "--output-dir", self.out, "--project-root", self.proj, "--json"])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        payload = self.receipt(r)
        run_dir = self.only_run()
        self.assertIn("MODE_SKIPPED", {x["code"] for x in payload["warnings"]})
        self.assertIn("白名单", payload["warnings"][0]["msg"])
        summary = json.loads(_read(os.path.join(run_dir, "execution-summary.json")))
        self.assertEqual([m["mode"] for m in summary["skipped_modes"]], ["baseline"])
        self.assertEqual(payload["counts"]["executed"], 0)


class IsolationTests(Base):
    """用例 ⑩：清场环境契约（从零构建、不继承宿主；auth 仅宿主非空才传）。"""

    def _transcripts(self):
        run_dir = self.only_run()
        out = []
        for dirpath, _dirs, files in os.walk(run_dir):
            if "transcript.jsonl" in files:
                out.append(os.path.join(dirpath, "transcript.jsonl"))
        return out

    def test_env_is_built_from_scratch(self):
        env = {"EVAL_RUNNER_HOST_SECRET": "leak", "ANTHROPIC_API_KEY": ""}
        r = self.engine(["run", "--skill", self.skill, "--mode", "baseline",
                         "--adapter", self.adapter, "--output-dir", self.out,
                         "--project-root", self.proj, "--json"], extra_env=env)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        seen = set()
        for path in self._transcripts():
            for line in _read(path).splitlines():
                evt = json.loads(line)
                if "env_keys" in evt:
                    seen |= set(evt["env_keys"])
                    self.assertNotIn("EVAL_RUNNER_HOST_SECRET", evt["env_keys"],
                                     "宿主变量不得泄漏进清场环境")
                    self.assertNotIn("ANTHROPIC_API_KEY", evt["env_keys"],
                                     "auth 变量在宿主为空串时不得传（会毁掉运行时凭据回落）")
        self.assertTrue(seen, "未取到假 adapter 回报的环境键")
        self.assertTrue({"PATH", "HOME", "CLAUDE_CONFIG_DIR"} <= seen, seen)

    def test_auth_env_forwarded_when_non_empty(self):
        env = {"ANTHROPIC_API_KEY": "sk-fixture"}
        r = self.engine(["run", "--skill", self.skill, "--mode", "quality",
                         "--adapter", self.adapter, "--output-dir", self.out,
                         "--project-root", self.proj, "--json"], extra_env=env)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        seen = set()
        for path in self._transcripts():
            for line in _read(path).splitlines():
                evt = json.loads(line)
                if "env_keys" in evt:
                    seen |= set(evt["env_keys"])
        self.assertIn("ANTHROPIC_API_KEY", seen)


class MlogTests(Base):
    """用例 ⑧：`mlog`（与 W1 逐字同构的接口面）。"""

    def test_mlog_ack_and_append_only(self):
        memlog_dir = os.path.join(self.proj, "build-logs")
        r = self.engine(["mlog", "--dir", memlog_dir, "init",
                         "--file", ".memlog.md", "--subject", "run-x",
                         "--output-dir", self.out])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        ack = json.loads(r.stdout.strip().splitlines()[-1])
        # 恒发一行 JSON ack：共同键 + 命令级附加键（与 W1 的 mlog 同构）
        self.assertTrue({"ok", "file", "n", "appended"} <= set(ack), ack)
        self.assertTrue({"command", "project_root", "violations", "warnings", "counts"} <= set(ack))
        self.assertEqual(ack["command"], "mlog")
        self.assertTrue(ack["ok"])
        self.assertEqual(ack["n"], 0)
        self.assertFalse(ack["appended"])
        self.assertTrue(ack["file"].endswith(".memlog.md"))

        r = self.engine(["mlog", "--dir", memlog_dir, "append",
                         "--file", ".memlog.md", "--type", "decision",
                         "--text", "选 baseline 先跑", "--output-dir", self.out])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        ack = json.loads(r.stdout.strip().splitlines()[-1])
        self.assertEqual(ack["n"], 1)
        self.assertTrue(ack["appended"])
        body = _read(os.path.join(memlog_dir, ".memlog.md"))
        self.assertIn("- (decision) 选 baseline 先跑", body)

        r = self.engine(["mlog", "--dir", memlog_dir, "set-complete",
                         "--file", ".memlog.md", "--output-dir", self.out])
        ack = json.loads(r.stdout.strip().splitlines()[-1])
        self.assertEqual(ack["n"], 1)
        self.assertFalse(ack["appended"])
        self.assertIn("status: complete", _read(os.path.join(memlog_dir, ".memlog.md")))

        # 只追加：重复 init 拒绝、类型越界拒绝、条目永不改写
        r = self.engine(["mlog", "--dir", memlog_dir, "init", "--file", ".memlog.md",
                         "--output-dir", self.out, "--json"])
        self.assertEqual(r.returncode, 1)
        self.assertIn("FILE_CONFLICT", self.codes(json.loads(r.stdout)))
        r = self.engine(["mlog", "--dir", memlog_dir, "append", "--file", ".memlog.md",
                         "--type", "bogus", "--text", "x", "--output-dir", self.out, "--json"])
        self.assertEqual(r.returncode, 1)
        self.assertIn("ENUM_INVALID", self.codes(json.loads(r.stdout)))
        r = self.engine(["mlog", "--dir", memlog_dir, "append", "--file", ".memlog.md",
                         "--type", "note", "--text", "   ", "--output-dir", self.out, "--json"])
        self.assertEqual(r.returncode, 1)
        self.assertIn("EMPTY_FIELD", self.codes(json.loads(r.stdout)))
        # --file 只收文件名（不许用路径冒充）
        r = self.engine(["mlog", "--dir", memlog_dir, "init", "--file", "sub/.memlog.md",
                         "--output-dir", self.out, "--json"])
        self.assertEqual(r.returncode, 1)
        self.assertIn("NAME_ILLEGAL", self.codes(json.loads(r.stdout)))
        # 三次被拒的操作都不许碰到既有 memlog：条目仍只有一条、状态仍是 complete
        after = _read(os.path.join(memlog_dir, ".memlog.md"))
        self.assertEqual(after.count("- ("), 1)
        self.assertIn("status: complete", after)
        self.assertFalse(os.path.exists(os.path.join(memlog_dir, "sub")),
                         "被拒的 --file 不得造出目录")

    def test_run_writes_memlog_at_run_root(self):
        r = self.engine(["run", "--skill", self.skill, "--mode", "quality",
                         "--adapter", self.adapter, "--output-dir", self.out,
                         "--project-root", self.proj, "--json"])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        text = _read(os.path.join(self.only_run(), ".memlog.md"))
        self.assertTrue(text.startswith("---"), text[:20])
        self.assertIn("subject:", text)
        self.assertIn("- (event)", text)


class TokenTests(Base):
    """用例 ⑦：未解析 `{...}` 令牌 → `TOKEN_UNRESOLVED`。"""

    def test_unresolved_token_rejected(self):
        r = self.engine(["run", "--skill", "{some-token}/diy-foo",
                         "--output-dir", self.out, "--project-root", self.proj, "--json"])
        self.assertEqual(r.returncode, 1)
        payload = self.receipt(r)
        self.assertIn("TOKEN_UNRESOLVED", self.codes(payload))
        self.assertEqual(self.run_dirs(), [], "拒绝必须零产出")

        r = self.engine(["check", "--run-dir", "{output_dir}/eval-runs/x",
                         "--project-root", self.proj, "--json"])
        self.assertEqual(r.returncode, 1)
        self.assertIn("TOKEN_UNRESOLVED", self.codes(self.receipt(r)))

    def test_project_root_token_resolved(self):
        r = self.engine(["run", "--skill", "{project-root}/skills/diy-foo",
                         "--mode", "baseline", "--adapter", self.adapter,
                         "--output-dir", self.out, "--project-root", self.proj, "--json"])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        run_json = json.loads(_read(os.path.join(self.only_run(), "run.json")))
        self.assertNotIn("{project-root}", run_json["skill_path"])
        self.assertTrue(os.path.isfile(os.path.join(run_json["skill_path"], "SKILL.md")))


class ContractTests(Base):
    """用例 ⑥：SKILL.md 契约冒烟 + 引擎码登记面。"""

    def test_skill_md_contract(self):
        text = _read(SKILL_MD)
        for anchor in (INSTANCE_ZH, RESOLVE_KEYS_ZH, READ_DISCIPLINE_ZH,
                       DISCIPLINE_ZH, PRECISE_ZH):
            self.assertIn(anchor, text, "母本定稿缺失：%s" % anchor[:24])
        for heading in ("## 激活时", "## 工作流", "## 结构", "## 规则"):
            self.assertIn(heading, text, heading)
        for field in ("name:", "description:", "phase:", "precededBy:",
                      "followedBy:", "required:", "line:", "outputs:"):
            self.assertIn(NL + field, text, field)
        self.assertLessEqual(len(text.splitlines()), 90, "薄主文件 ≤90 行")

        # 两条反自欺硬规则必须在场
        for phrase in ("tool_use", "子串", "不给部分分", "举证责任", "反向"):
            self.assertIn(phrase, text, phrase)
        # run 目录「永不删除、覆盖、轮转」
        self.assertIn("永不删除、覆盖、轮转", text)
        # 零 YAML + 母本 §5 不适用的理由
        self.assertIn("零 YAML", text)
        self.assertIn("§5 不适用", text)
        # 终门 = check --run-dir（无 --final）
        self.assertIn("check --run-dir", text)
        self.assertNotIn("--final", text, "run 目录追加式，无定稿态")
        # 四对边界声明
        for peer in ("diy-test-review", "diy-test-gate", "diy-review", "runner.py"):
            self.assertIn(peer, text, peer)
        # 降级：不入队
        self.assertIn("不入队", text)
        # 令牌纪律
        self.assertIn("TOKEN_UNRESOLVED", text)

    def test_skill_dir_shape_and_engine_codes(self):
        self.assertTrue(os.path.isfile(ENGINE))
        steps = sorted(os.listdir(os.path.join(SKILL_DIR, "steps")))
        self.assertEqual(steps, ["01-scope.md", "02-run.md", "03-report.md"])
        refs = sorted(os.listdir(os.path.join(SKILL_DIR, "references")))
        self.assertEqual(refs, ["description-optimization.md", "eval-format.md",
                                "grader.md", "platform-adapter.md",
                                "self-improvement.md"])
        src = _read(ENGINE)
        for code in ("TOKEN_UNRESOLVED", "UNPARSABLE_JSON", "MODE_SKIPPED",
                     "ADAPTER_MISSING", "AGAINST_FALLBACK", "INCOMPLETE_RUN"):
            self.assertIn(code, src, "引擎 docstring 未登记 %s" % code)

    def test_steps_point_to_next_file(self):
        for name, nxt in (("01-scope.md", "./02-run.md"),
                          ("02-run.md", "./03-report.md")):
            text = _read(os.path.join(SKILL_DIR, "steps", name))
            self.assertIn("Read (input)", text, name)
            self.assertIn("Write (output)", text, name)
            self.assertIn(nxt, text, "%s 必须点名下一个要读的文件" % name)


if __name__ == "__main__":
    unittest.main()
