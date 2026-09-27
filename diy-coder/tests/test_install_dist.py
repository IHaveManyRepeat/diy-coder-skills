# -*- coding: utf-8 -*-
"""install.py 分发完整性验收（C·5 欠账）。

夹具策略（裁定 14）：把源技能树**冻结**成临时副本，`python <冻结源>/install.py <临时目标根>`
装到 tempfile 后断言安装侧产物——零副作用、可重复。**绝不读工作区 `.claude/skills/`**：那会把
sync 纪律混进测试面（改了源还没 sync 时误红），分发面与同步纪律必须分开。

冻结的两个理由：
  ① W1–W6 并行施工**实时改源**（实测 `diy-wds-assets/scripts/wds_assets.py` 在我两次安装之间
     被改过）——直接拿源树当期望值，会把并发写误判成「分发不一致」；
  ② 探针（`__pycache__` / `diy-` 前缀外的目录）只能植在副本上，不能写进真实源树。

覆盖：技能计数与逐目录 SKILL.md · 子目录递归（三层路径）· `__pycache__` 排除 · 非 `diy-`
目录不分发 · 仓库根 runner/exp-sync 落 diy-tools/scripts/ · 逐文件内容一致 · 幂等（含
rmtree 分支）· diy-coder.yaml 仅首次创建。

运行：cd diy-coder && python -m unittest discover -s tests -p "test_install_dist.py" -v
trace: 任务书 §7.2（裁定 14）；被测面 install.py:26-53。
"""
import atexit
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                       # diy-coder/
SKILLS_SRC = os.path.join(ROOT, "skills")
INSTALLED_REL = os.path.join(".claude", "skills")
TOOLS = ("runner.py", "exp-sync.py")               # 仓库根 → 安装侧 diy-tools/scripts/（:37-41）
# 现役技能数（B7b 收口后 49）：新增/删除技能时同步更新——install.py 漏拷即红
EXPECTED_SKILL_COUNT = 49
# 植进冻结副本的探针：源侧不该被分发的三类路径（install.py:28-29 / :34）
PROBES = {
    "skills/diy-viewer/scripts/__pycache__/probe.pyc": "",        # :34 ignore_patterns("__pycache__")
    "skills/__pycache__/probe.pyc": "",
    "skills/not-a-skill/keep.md": "# 非 diy- 前缀目录：:28-29 不得分发\n",
}


def run_install(dst_root, frozen_root):
    """跑 `<冻结源>/install.py <目标根>`，返回 CompletedProcess（utf-8 解码回执）。"""
    return subprocess.run([sys.executable, os.path.join(frozen_root, "install.py"), dst_root],
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


def md5(path):
    with open(path, "rb") as fh:
        return hashlib.md5(fh.read()).hexdigest()


def read_text(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def write_text(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def diy_dirs(root):
    """某目录下的 `diy-*` 子目录名。"""
    return sorted(n for n in os.listdir(root)
                  if n.startswith("diy-") and os.path.isdir(os.path.join(root, n)))


def snapshot(root, skip_dirs=()):
    """{相对路径（正斜杠）→ md5}；`skip_dirs` 命名的目录整棵跳过（源树的 `__pycache__`）。"""
    out = {}
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for name in files:
            path = os.path.join(dirpath, name)
            out[os.path.relpath(path, root).replace(os.sep, "/")] = md5(path)
    return out


def sizes(root):
    """{相对路径 → 字节数}：只 stat 不读内容（Windows 上新建文件的首次读取代价高，约 17ms/个）。"""
    out = {}
    for dirpath, _, files in os.walk(root):
        for name in files:
            path = os.path.join(dirpath, name)
            out[os.path.relpath(path, root).replace(os.sep, "/")] = os.path.getsize(path)
    return out


def _expected_tree(src_snapshot):
    """安装侧应有全体 = 源技能树（`diy-*` 目录、排除 `__pycache__`）+ 仓库根两工具的落位副本。"""
    exp = {rel: h for rel, h in src_snapshot.items() if rel.split("/")[0].startswith("diy-")}
    for tool in TOOLS:
        exp["diy-tools/scripts/" + tool] = md5(os.path.join(ROOT, tool))
    return exp


def _freeze_source(attempts=3):
    """源技能树 → 临时副本，返回 (副本根, 期望安装树)。

    建副本前后各读一次源指纹，不一致说明窗口期内有人改源（W1–W6 并行施工），重来；
    连 `attempts` 次都被打断才判红——那时报「源在动」，而不是「分发不一致」。指纹不含
    `__pycache__`（别的窗口跑测试会实时生成 .pyc）；副本则**含** `__pycache__`，供 :34 忽略面测试。
    """
    for _ in range(attempts):
        before = snapshot(SKILLS_SRC, skip_dirs=("__pycache__",))
        root = tempfile.mkdtemp(prefix="diy-install-src-")
        shutil.copytree(SKILLS_SRC, os.path.join(root, "skills"))
        for name in ("install.py", "diy-coder.yaml") + TOOLS:
            shutil.copyfile(os.path.join(ROOT, name), os.path.join(root, name))
        if snapshot(SKILLS_SRC, skip_dirs=("__pycache__",)) == before:
            atexit.register(shutil.rmtree, root, ignore_errors=True)
            return root, _expected_tree(before)
        shutil.rmtree(root, ignore_errors=True)
    raise AssertionError("源技能树在 %d 次冻结窗口内均被并发改动（W1–W6 并行施工中），"
                         "无法判定分发一致性" % attempts)


_FROZEN = None


def frozen_source():
    """(冻结源根, 期望安装树)；同进程只冻结一次（副本含探针）。"""
    global _FROZEN
    if _FROZEN is None:
        root, expected = _freeze_source()
        for rel, text in PROBES.items():
            write_text(os.path.join(root, *rel.split("/")), text)
        _FROZEN = (root, expected)
    return _FROZEN


class InstallDistributionTests(unittest.TestCase):
    """一次安装（装到临时目标根）→ 多条只读断言。"""

    @classmethod
    def setUpClass(cls):
        cls.frozen_root, cls.expected = frozen_source()
        cls.tmp = tempfile.TemporaryDirectory()
        cls.dst = os.path.join(cls.tmp.name, "proj")     # 故意不存在：顺带验 makedirs（:25）
        cls.proc = run_install(cls.dst, cls.frozen_root)
        cls.skills_dir = os.path.join(cls.dst, INSTALLED_REL)
        cls.got = snapshot(cls.skills_dir) if os.path.isdir(cls.skills_dir) else {}

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_install_returns_zero_and_reports_count(self):
        self.assertEqual(self.proc.returncode, 0,
                         "install.py 非零退出：\n%s\n%s" % (self.proc.stdout, self.proc.stderr))
        self.assertIn("已安装 %d 个 skill" % EXPECTED_SKILL_COUNT, self.proc.stdout,
                      "install.py 回执的技能数与预期不符：\n%s" % self.proc.stdout)

    def test_all_diy_skills_installed_with_skill_md(self):
        self.assertTrue(os.path.isdir(self.skills_dir),
                        "安装侧 .claude/skills 不存在：\n%s\n%s"
                        % (self.proc.stdout, self.proc.stderr))
        want = diy_dirs(os.path.join(self.frozen_root, "skills"))
        self.assertEqual(want, diy_dirs(SKILLS_SRC), "冻结副本与真实源的技能目录已不同步")
        got = sorted(n for n in os.listdir(self.skills_dir)
                     if os.path.isdir(os.path.join(self.skills_dir, n)))
        self.assertEqual(got, want,
                         "安装侧技能目录与源不一致：漏拷 %s；多拷 %s"
                         % (sorted(set(want) - set(got)), sorted(set(got) - set(want))))
        self.assertEqual(len(got), EXPECTED_SKILL_COUNT,
                         "技能数变了：实测 %d，常量 %d——新增/删除技能时更新常量"
                         % (len(got), EXPECTED_SKILL_COUNT))
        missing = [n for n in got if not os.path.isfile(os.path.join(self.skills_dir, n, "SKILL.md"))]
        self.assertEqual(missing, [], "以下技能装了目录却缺 SKILL.md：%s" % missing)

    def test_tree_matches_source_file_by_file(self):
        """逐文件（含子目录递归）内容一致：缺失 / 多出 / 内容不同 三分类报差异。"""
        self.assertGreater(len(self.expected), EXPECTED_SKILL_COUNT,
                           "预期集合异常小（%d）——源树扫描失灵，本断言在空转" % len(self.expected))
        missing = sorted(set(self.expected) - set(self.got))
        extra = sorted(set(self.got) - set(self.expected))
        differ = sorted(k for k in set(self.expected) & set(self.got)
                        if self.expected[k] != self.got[k])
        self.assertEqual((missing, extra, differ), ([], [], []),
                         "安装侧与源逐文件不一致：缺失 %s；多出 %s；内容不同 %s"
                         % (missing[:5], extra[:5], differ[:5]))

    def test_deep_nested_dirs_are_copied(self):
        """三层及更深路径（copytree 递归面）——B7b 新增的 data/presentation-formats/ 是最新用例。"""
        deep = ("diy-wds-assets/data/styles/design-styles/brutalist.md",
                "diy-wds-assets/data/styles/design-styles/editorial.md",
                "diy-wds-assets/data/presentation-formats/index.md",
                "diy-wds-assets/data/presentation-formats/sd-slides.md",
                "diy-wds-assets/steps/08-presentation.md")
        for rel in deep:
            src = os.path.join(self.frozen_root, "skills", *rel.split("/"))
            self.assertTrue(os.path.isfile(src), "冻结源缺 %s（源树已变，先核用例）" % rel)
            dst = os.path.join(self.skills_dir, *rel.split("/"))
            self.assertTrue(os.path.isfile(dst), "深层路径未递归拷入：%s" % rel)
            self.assertEqual(md5(dst), md5(src), "深层文件内容不一致：%s" % rel)

    def test_pycache_and_non_diy_not_distributed(self):
        leaked = [p for p in sorted(PROBES)          # 跳过 "skills/" 前缀 → 安装侧对应路径
                  if os.path.exists(os.path.join(self.skills_dir, *p.split("/")[1:]))]
        self.assertEqual(leaked, [], "不应分发的探针路径出现在安装侧：%s" % leaked)
        leaked_dirs = [os.path.relpath(dp, self.skills_dir).replace(os.sep, "/")
                       for dp, _, _ in os.walk(self.skills_dir)
                       if os.path.basename(dp) == "__pycache__"]
        self.assertEqual(leaked_dirs, [],
                         "__pycache__ 被分发（:34 ignore_patterns 失效）：%s" % leaked_dirs[:5])
        pyc = sorted(k for k in self.got if k.endswith(".pyc"))
        self.assertEqual(pyc, [], "安装侧有 .pyc 残留：%s" % pyc[:5])

    def test_repo_root_tools_land_in_diy_tools_scripts(self):
        for tool in TOOLS:
            dst = os.path.join(self.skills_dir, "diy-tools", "scripts", tool)
            self.assertTrue(os.path.isfile(dst),
                            "install.py:37-41 未把 %s 分发进 .claude/skills/diy-tools/scripts/" % tool)
            self.assertEqual(md5(dst), md5(os.path.join(self.frozen_root, tool)),
                             "%s 的内容与源不一致" % tool)
            self.assertFalse(os.path.exists(os.path.join(self.dst, tool)),
                             "%s 落到了目标根，应在 diy-tools/scripts/ 下" % tool)

    def test_config_created_at_target_root(self):
        cfg = os.path.join(self.dst, "diy-coder.yaml")
        self.assertTrue(os.path.isfile(cfg), "首次安装未创建 diy-coder.yaml（:44-47）")
        with open(cfg, "rb") as fh:
            got = fh.read()
        with open(os.path.join(self.frozen_root, "diy-coder.yaml"), "rb") as fh:
            self.assertEqual(got, fh.read(), "首次创建的 diy-coder.yaml 与源不逐字一致")


class RepeatInstallTests(unittest.TestCase):
    """幂等 + rmtree 分支 + 既有配置不被覆盖（自建临时目标根）。"""

    def test_second_install_is_idempotent_and_drops_stale(self):
        frozen_root, _expected = frozen_source()
        with tempfile.TemporaryDirectory() as tmp:
            dst = os.path.join(tmp, "proj")
            os.makedirs(dst)
            sentinel = "project:\n  name: 项目自有配置（安装不得覆盖）\n"
            cfg = os.path.join(dst, "diy-coder.yaml")
            write_text(cfg, sentinel)

            first = run_install(dst, frozen_root)
            self.assertEqual(first.returncode, 0, "首次安装失败：\n%s\n%s"
                             % (first.stdout, first.stderr))
            self.assertEqual(read_text(cfg), sentinel, "install.py:45-49 覆盖了既有 diy-coder.yaml")
            skills_dir = os.path.join(dst, INSTALLED_REL)
            self.assertTrue(os.path.isdir(os.path.join(skills_dir, "diy-viewer", "scripts")),
                            "首次安装未铺出技能树，后续断言无意义")
            before = sizes(skills_dir)

            # 植入陈旧残留：第二次安装必须整目录重铺（rmtree :31-32），而非原地叠加
            write_text(os.path.join(skills_dir, "diy-viewer", "scripts", "stale_probe.py"), "x = 1\n")
            write_text(os.path.join(skills_dir, "diy-tools", "scripts", "__pycache__", "stale.pyc"), "")

            second = run_install(dst, frozen_root)
            self.assertEqual(second.returncode, 0,
                             "第二次安装失败（rmtree 失效时 copytree 会因目录已存在报错）：\n%s\n%s"
                             % (second.stdout, second.stderr))
            for rel in ("diy-viewer/scripts/stale_probe.py", "diy-tools/scripts/__pycache__"):
                self.assertFalse(os.path.exists(os.path.join(skills_dir, *rel.split("/"))),
                                 "陈旧残留仍在（%s）——第二次安装未整目录重铺" % rel)
            self.assertEqual(sizes(skills_dir), before, "两次安装结果不一致（幂等性破）")
            self.assertEqual(read_text(cfg), sentinel, "第二次安装覆盖了既有 diy-coder.yaml")


class DefaultTargetTests(unittest.TestCase):
    """无参形态：目标 = 源根的父目录（install.py:21）。

    C·11 收口后裁定补测（V-C 偏离 ① / L3）——原 8 用例只测显式目标根；无参分支的语义是
    「装到源树所在仓库」，直跑冻结源（其根在系统临时目录下）会往共享 /tmp 拉屎，故本用例
    自建 `<tmp>/diy-coder/` 一层：无参目标 = 该临时根，随 TemporaryDirectory 自动清理。
    """

    def test_no_arg_installs_into_parent_of_source_root(self):
        frozen_root, _expected = frozen_source()
        with tempfile.TemporaryDirectory() as tmp:
            src_root = os.path.join(tmp, "diy-coder")
            shutil.copytree(frozen_root, src_root)
            proc = subprocess.run([sys.executable, os.path.join(src_root, "install.py")],
                                  capture_output=True, text=True, encoding="utf-8", errors="replace")
            self.assertEqual(proc.returncode, 0,
                             "无参安装失败：\n%s\n%s" % (proc.stdout, proc.stderr))
            self.assertIn("已安装 %d 个 skill" % EXPECTED_SKILL_COUNT, proc.stdout,
                          "无参回执的技能数不符：\n%s" % proc.stdout)
            skills_dir = os.path.join(tmp, INSTALLED_REL)
            self.assertTrue(os.path.isdir(skills_dir),
                            "无参目标不是「源根的父目录」（install.py:21）：%s 未创建" % skills_dir)
            got = sorted(n for n in os.listdir(skills_dir)
                         if n.startswith("diy-") and os.path.isdir(os.path.join(skills_dir, n)))
            self.assertEqual(len(got), EXPECTED_SKILL_COUNT,
                             "无参安装技能数 %d ≠ %d" % (len(got), EXPECTED_SKILL_COUNT))
            self.assertEqual(os.path.exists(os.path.join(src_root, ".claude")), False,
                             "安装写进了源根自身（应只写目标根 = 源根父目录）")
            cfg = os.path.join(tmp, "diy-coder.yaml")
            self.assertTrue(os.path.isfile(cfg), "无参安装未在目标根创建 diy-coder.yaml")


class SmokeTargetTests(unittest.TestCase):
    """C·5 余项①（收口后裁定）：冒烟对象 = **安装侧**。

    原实现 `smoke(src)` 验源树——源好而安装侧坏（分发级失败）时仍拿 rc=0 绿回执，
    检验对象错位。本用例的鉴别力：改前把安装侧 skills 目录传给 smoke，内部按
    `<参数>/skills/diy-viewer/...` 拼接必然找不到 → 首个断言即红。
    """

    def test_smoke_verifies_installed_side(self):
        import importlib.util
        frozen_root, _expected = frozen_source()
        spec = importlib.util.spec_from_file_location(
            "frozen_install_mod", os.path.join(frozen_root, "install.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        with tempfile.TemporaryDirectory() as tmp:
            dst = os.path.join(tmp, "proj")
            proc = run_install(dst, frozen_root)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            skills_dir = os.path.join(dst, INSTALLED_REL)
            self.assertTrue(mod.smoke(skills_dir), "正常安装侧应冒烟通过")
            shutil.rmtree(os.path.join(skills_dir, "diy-viewer"))
            self.assertFalse(mod.smoke(skills_dir),
                             "安装侧缺 diy-viewer 时冒烟须红——证冒烟验的是安装侧")


if __name__ == "__main__":
    unittest.main()
