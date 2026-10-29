# -*- coding: utf-8 -*-
"""diy-bmb-builder 确定性引擎：技能树脚手架 + 模板机 + 预扫 + 结构扫描 + 过程日志 + 终门 + 报告渲染。

机制（技能工厂的 Build / Edit / Analyze 三意图共用这一个引擎）——

  scaffold  建技能目录骨架：`--name N` 归一到 hyphen-case（≤64），SKILL.md 从内置模板起手
            （四段中文标题 + 冻结句），按 `--dirs` stub 子目录。
            落点：默认 `{project-root}/.claude/skills/`（安装面，落此即用）；`--to-source` 落
            套件源树（进 git 分发），该层缺席 → MISSING_FILE
            拒绝且**不代建父目录**；`--to-source` 与 `--dest` 互斥（同给 = 用法错误 exit 2）。
            目标已存在 → FILE_CONFLICT 拒绝；`--force` 才允许 rmtree 重建。
            **--force 硬护栏**：目标名命中 `diy-coder/skills/` 下已建技能名、或命中本套件
            禁改面（根脚本 / `diy-output` / `docs` / `diy-coder`）→ 即使 --force 也拒绝
            （FILE_CONFLICT）。护栏名单由**引擎自身位置**（`<套件根>/diy-coder/skills`）与
            静态名单合成，故与 --project-root 指到哪无关。
            回执另含 `files_created`（正斜杠、相对 project-root）。

  template  模板机：`{if-X}...{/if-X}` 条件块由内向外展开（X ∈ `--true` 则为真、否则整块删），
            再按 `--set k=v` 替换 `{k}`。两级失败语义照源：**残留 `{if-}` 标记 = exit 3 硬失败**
            （括号写错，发出去会把标记原样 ship）且零产出；**残留 `{token}` = 不算失败**，
            列进回执 `tokens_remaining` 交人判断（`{project-root}` 这类运行时 token 是合法的）。

  prepass   两套源预扫合并成一个子命令，`--set metrics|integrity|all`（默认 all），
            输出统一成**一份** JSON 回执：
              metrics  逐文件 token 计数（tiktoken，缺席时 chars//4 并标 method）、行数、
                       废话模式 grep（"make sure to"/"don't forget"/"it is important" 及
                       中文对应「务必/别忘了/重要的是」）、回指模式（"as described above" /
                       「如上所述」）、编号前缀文件名标记。**只出数、不判违规**。
              integrity 数字前缀阶段文件名散在技能根 → 违规（阶段文件须落 `steps/`）；
                       `## On Exit` / `## 退出时` 段 → 违规（diy 无 exit hook，永不执行）；
                       残留模板标记 → 违规；必备四段中文标题缺失 → 违规；`steps/` 编号缺口
                       与 SKILL.md 引用的步骤文件缺席 → 违规；语言直白度反模式（"you should"/
                       "please"/"handle appropriately"/"when ready" 及中文对应）→ **warning**。

  scan      机械面：`--check all|path-standards|scripts`（默认 all）。
            path-standards：`.md` 里的绝对路径 / `../` 越界 / `./<目录>/` 跨目录引用（围栏内豁免）。
            scripts：`scripts/*.py` 的套件合规——`# -*- coding: utf-8 -*-` 头、中文模块 docstring、
            `sys.stdout.reconfigure(encoding="utf-8")`、至少一处 `# trace:`；`input(` 判违规
            （无头态阻塞）。缺 argparse / 缺 `sys.exit` 记 warning。

  mlog      过程日志（memlog 的 diy 落点）：`--dir D` + 三动作 init / append / set-complete。
            **文件名由调用方经 `--file NAME` 显式给**（不靠 --dir 反推）；`init` 收 `--subject S`。
            `--file` **只收纯文件名**：含路径分隔符（`/` 或反斜杠）、`.`/`..`、空白名 → NAME_ILLEGAL
            （写面不许越出 `--dir`，否则边界形同虚设）。
            只追加、不重写历史；读改写走临时文件 + fsync + `os.replace`（崩不半写）。
            回执恒为一行 JSON，含共同键 + `{file, n, appended}` 三附加键（人读态与 --json 无关）。

  check     产物技能终门。基础项（中途可跑）：SKILL.md 在场；四段中文标题齐备；锚串逐字在场；frontmatter 六字段（phase/precededBy/followedBy/
            required/line/outputs）+ name/description 齐备且形态合法；**自足性**——技能根相对
            引用（`steps/` `references/` `scripts/` `assets/`）必须落在技能目录内，越界引用
            （`../`）判内容依赖违规。`--final` 附加结构终门：SKILL.md ≤90 行、`steps/` 至少
            一个步骤文件、每步 H1 `# Step N — <中文步名>` + `**Read (input):**`/`**Write (output):**`
            行 + 步号连续 + 每步结尾点名下一个要读的文件（末步声明不再读）。
            **自足性豁免清单**（内容面判据，非字面「禁一切跨目录引用」）：`{project-root}` 令牌
            路径（diyc.py 调用、diy-coder.yaml、viewer 调用）、
            `{output_dir}` 产物路径、`path:<relative>` 引用式路径——三者一律豁免。

  render    由脚本把 `findings.json` 渲染成 `skill-analysis-report.md` + `.html`（十二件
            报告集里的最后两件）。**绝不手写 HTML**；findings.json 形状不对或主体仍是占位
            则拒绝渲染（零产出）。

违规码：复用冻结集（MISSING_FILE / UNPARSABLE_YAML / EMPTY_FIELD /
ENUM_INVALID / SET_MISMATCH）；新增码中本引擎用到 NAME_ILLEGAL（名字/文件名形态非法；
`mlog --file` 只收纯文件名——含路径分隔符、`.`/`..`、空白名一律拒绝，否则 `--dir` 的边界形同虚设）、
FILE_CONFLICT（目标已存在 / 破坏性护栏 / 内容依赖越界）、TOKEN_UNRESOLVED（未解析 `{...}` 令牌
与残留模板标记）；未用到 UNKNOWN_ID / ID_UNSTABLE（本技能无 ID 集合面，`--previous` 判 no）。
另有一个**套件既有码** `INTERNAL_ERROR`：不在冻结清单内，非新造——沿用 `diyc.py`
顶层兜底先例（未预期异常转回执，不让异常裸奔、不静默吞错），故在此登记。
回执共同键 {ok, command, project_root, output_dir, violations[{code,where,msg}], warnings[], counts}；
warnings 与 violations 同形；where 正斜杠、相对 project-root；exit 0 唯一放行，1 = 违规/被拒绝，
2 = 用法错误（argparse），3 = template 残留 `{if-}` 标记。`--output-dir` 全部子命令必填
（引擎不读 diy-coder.yaml，不设默认）；`--project-root` 默认 `.`。路径参数里的 `{...}` 令牌
一律拒绝（TOKEN_UNRESOLVED）——**唯一例外 `{project-root}`**，由引擎按 `--project-root` 自解析。
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))

from bmb_builder_check import cmd_check, cmd_mlog  # noqa: E402
from bmb_builder_lib import DEFAULT_DIRS, ENTRY_TYPES  # noqa: E402
from bmb_builder_render import cmd_render  # noqa: E402
from bmb_builder_scaffold import cmd_scaffold, cmd_template, parse_set  # noqa: E402
from bmb_builder_scan import cmd_prepass, cmd_scan  # noqa: E402
from diyc_lib import v  # noqa: E402


# ---------------------------------------------------------------- 命令行面

# trace: diy-bmb-builder 命令行面（子命令 + 旗标；--output-dir 全部必填，引擎不读配置）
def build_parser():
    ap = argparse.ArgumentParser(
        description="diy-bmb-builder 确定性引擎：技能树脚手架（scaffold）/ 模板机（template）/"
                    "预扫（prepass）/ 结构扫描（scan）/ 过程日志（mlog）/ 产物终门（check）/"
                    "报告渲染（render）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def add_common(parser):
        parser.add_argument("--project-root", default=".", help="项目根（默认 .）")
        parser.add_argument("--output-dir", required=True,
                            help="本次运行的产物目录（必填；由调用方经 diyc.py resolve 传入，"
                                 "引擎不读 diy-coder.yaml）")
        parser.add_argument("--json", action="store_true", help="输出单行 JSON 回执")

    s = sub.add_parser("scaffold", help="建技能目录骨架（默认落 {project-root}/.claude/skills/）")
    s.add_argument("--name", required=True, help="技能名（须已是 hyphen-case，≤64 字符）")
    s.add_argument("--dirs", default=DEFAULT_DIRS,
                   help="要 stub 的子目录，逗号分隔（默认 steps；可选 references,scripts,assets）")
    s.add_argument("--dest", help="落点父目录（默认 {project-root}/.claude/skills）")
    s.add_argument("--to-source", action="store_true",
                   help="落套件源 {project-root}/diy-coder/skills（与 --dest 互斥）")
    s.add_argument("--force", action="store_true",
                   help="目标已存在时清场重建（硬护栏：已建技能名与禁改面即使 --force 也拒绝）")
    add_common(s)
    s.set_defaults(func=cmd_scaffold)

    t = sub.add_parser("template", help="模板机（{if-X} 条件块 + {var} 替换；残留 {if-} 硬失败）")
    t.add_argument("--src", required=True, help="模板文件")
    t.add_argument("--dest", required=True, help="输出文件")
    t.add_argument("--set", action="append", type=parse_set, metavar="k=v",
                   help="变量替换（可重复）")
    t.add_argument("--true", action="append", metavar="X",
                   help="条件名视为真（可重复；未给的 {if-X} 整块删）")
    add_common(t)
    t.set_defaults(func=cmd_template)

    p = sub.add_parser("prepass", help="预扫（metrics 计量 / integrity 结构；两套合一）")
    p.add_argument("--target", required=True, help="技能目录")
    p.add_argument("--set", action="append", choices=("metrics", "integrity", "all"),
                   help="跑哪一套（可重复；默认 all）")
    p.add_argument("--out", help="另存 JSON 回执到该文件（调用方显式给的落点）")
    add_common(p)
    p.set_defaults(func=cmd_prepass)

    c = sub.add_parser("scan", help="机械面扫描（路径形态 / 脚本合规）")
    c.add_argument("--target", required=True, help="技能目录")
    c.add_argument("--check", choices=("all", "path-standards", "scripts"), default="all",
                   help="扫描面（默认 all；--lens 一词留给五透镜，不用作本旗标）")
    c.add_argument("--out", help="另存 JSON 回执到该文件")
    add_common(c)
    c.set_defaults(func=cmd_scan)

    m = sub.add_parser("mlog", help="过程日志（只追加；恒发一行 JSON ack）")
    m.add_argument("--dir", required=True, help="日志目录（W1 = {output_dir}/build-logs）")
    m.add_argument("--file", required=True, help="日志文件名（调用方显式给，如 <skill-name>.md）")
    m.add_argument("action", choices=("init", "append", "set-complete"), help="动作")
    m.add_argument("--subject", help="init 的标题")
    m.add_argument("--type", help="append 的条目类型（%s）" % "|".join(ENTRY_TYPES))
    m.add_argument("--text", help="append 的条目内容")
    add_common(m)
    m.set_defaults(func=cmd_mlog)

    k = sub.add_parser("check", help="产物技能终门（结构 / 母本逐字 / 自足 / 六字段）")
    k.add_argument("--target", required=True, help="技能目录")
    k.add_argument("--final", action="store_true",
                   help="结构终门：另加 SKILL.md ≤90 行 + steps 形态与步尾点名")
    add_common(k)
    k.set_defaults(func=cmd_check)

    r = sub.add_parser("render", help="由 findings.json 渲染报告 md/html（禁手写 HTML）")
    r.add_argument("--dir", required=True, help="分析运行目录（含 findings.json）")
    add_common(r)
    r.set_defaults(func=cmd_render)
    return ap


# trace: diy-bmb-builder 旗标互斥校验（--to-source 与 --dest 同给 = 用法错误 exit 2）
def validate_args(args):
    if args.cmd == "scaffold" and args.to_source and args.dest:
        return "--to-source 与 --dest 互斥：落套件源就不要再给 --dest"
    return None


# trace: diy-bmb-builder 入口（stdout/stderr 固定 UTF-8；未预期异常转 INTERNAL_ERROR，不静默）
def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    parser = build_parser()
    args = parser.parse_args()
    problem = validate_args(args)
    if problem:
        parser.error(problem)
    try:
        return args.func(args)
    except Exception as e:  # 未预期异常：报回执 + stderr 诊断，不裸奔
        sys.stderr.write("诊断：内部错误 %s：%s\n" % (type(e).__name__, e))
        payload = {
            "ok": False, "command": args.cmd, "project_root": args.project_root,
            "output_dir": os.path.normpath(os.path.abspath(args.output_dir)).replace("\\", "/"),
            "violations": [v("INTERNAL_ERROR", args.cmd, "%s: %s" % (type(e).__name__, e))],
            "warnings": [], "counts": {},
        }
        print(json.dumps(payload, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    sys.exit(main())
