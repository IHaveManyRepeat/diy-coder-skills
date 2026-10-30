# -*- coding: utf-8 -*-
"""diy-teach-me-testing 领域引擎：跨会话学习进度的生成（init）/ 仪表盘与校验（status）/
单一写通道（update）/ 门禁校验（check [--final]）。

机制：技能结构（7 节课程 id/名称/时长/先修/学习路径/角色适配）是**定义态**，落技能内静态资产
`curriculum.yaml`；学员进度是**运行态**，落 `{output_dir}/learning-progress.yaml`。两者用整数
session id（1-7）对齐，禁混为一文件。引擎负责全部机械判定：

  init    读 curriculum.yaml 建进度（7 节全未开始）+ 建 `{output_dir}/notes/` 目录；
          进度文件已存在且**可用** → 拒绝（ALREADY_EXISTS）并指引 resume（不覆盖）；
          已存在但**不可用**（解析失败 / 顶层非映射 / 缺 sessions 列表）→ 不带 `--recover`
          仍拒绝（同一判据的违规码）并把 `--recover` 指成唯一出路，带 `--recover` 则先把原
          文件逐字节备份为 `learning-progress.yaml.corrupt-<YYYYmmdd-HHMMSS>.bak`（shutil.copy2），
          再重建 7 节骨架——丢的只是台账断点，损坏件与笔记 md 都留在盘上。`--role` 可省
          （省略 → learner.role: null）；无论是否省略，`learner.assessed` 一律 null——
          画像采集归 02-assess（update --learner），init 不得置位。

  status  读进度 + 校验（与 check 同源）+ 输出仪表盘数据（每节状态 / 下一个推荐 / 完成度），
          并直出 `entry_step`——即 SKILL.md 里跨会话重入分流表的判定结果（进度文件不存在 →
          steps/01-init.md；进度文件不可用（损坏）→ steps/01-init.md（走 `init --recover`）；
          learner.assessed 为空 → steps/02-assess.md；sessions_completed < 7
          → steps/03-hub.md；7 节齐但 summary.generated 为假 → steps/05-completion.md；
          summary.generated 为真 → steps/03-hub.md）。分流表是唯一入口，判定输入就是本回执。

  update  唯一写通道，三形态互斥（--session / --learner / --summary 三者取一）：
            --session N [--status S] [--score S] [--notes P] [--topics N]
              幂等 upsert：以 session id 为键，重复完成不重复计数（sessions_completed 由
              status 计数得出）。重做（已完成的节再次完成）→ score/日期以最新为准
              + 追加一条 revisions（{date, change: "session N 重做", reason: "重做"}）；
              notes md 由技能侧覆盖同名文件，引擎只记路径。
            --learner [--role R] [--experience S] [--goals G] [--pain-points P]
              写 learner 区块并置 assessed = 当日（02-assess 专线）。
            --summary --path P
              置 summary = {generated: true, path: completion-summary.md, date: 当日}
              （05-completion 专线；P 须解析到 {output_dir}/completion-summary.md 且文件在场，
              且 7 节已修满）。
          任一形态落盘后一律按三式重算派生字段；**写前跑一遍与 check 同源的校验**
          （写通道与门禁同源：引擎不写一份会被 check 判违规的进度）。

  check   schema / session id 集合与 curriculum 一致（整数 1-7）/ 派生字段与真值一致
          （基准 = 三式：sessions_completed = status==已完成 计数、
          completion_percentage = floor(completed*100/7 + 0.5)、next_recommended = 最小未完成
          id，全完成 → null）/ score 范围与状态（0-100 整数、非已完成恒 null、session 7
          恒 null）/ session 7 完成判据（status==已完成 → topics_explored >=
          curriculum.sessions[7].min_topics）/ notes 路径口径（相对、正斜杠、归属 notes/、
          命名 notes/session-<NN>.md、文件在场；已完成节必填）/ learner 自洽（assessed
          非空 → role 与 experience 不得为空）/ summary 自洽 / --final 三条件（7 节全已完成
          且 summary.generated 为真 且 summary.path 文件在场）。exit 0 唯一放行。

派生字段（sessions_completed / completion_percentage / next_recommended）**只由本引擎写**；
LLM 手写与真值不符 → SET_MISMATCH。命令面互斥组由 argparse 强制；旗标组合错误（如 --score 配
--learner）走用法错误 exit 2。

违规码：复用冻结集——本引擎用到 MISSING_FILE / UNPARSABLE_YAML /
UNKNOWN_ID / ENUM_INVALID / EMPTY_FIELD / STATUS_MISMATCH / SET_MISMATCH / TOOL_ERROR 共 8 个。
**新增 1 码：`ALREADY_EXISTS`**（init 面：进度文件已存在 → 拒绝并指引 resume；冻结集里没有
「目标已存在」语义的码，DUPLICATE_ID 只指 ID 重复，复用会误导读回执的人）。
--previous 不适用：进度按 curriculum 固定 session 键幂等 upsert，无 ID 集合收缩面。

规格偏离（须主 agent 仲裁，2 条）：

① update --session 在 §7 冻结签名 `[--score S] [--notes P] [--status S]` 之外**增补可选旗标
`[--topics N]`**。理由：§7 的运行态 schema 要求 session 7 以 `topics_explored >= min_topics`
作为完成判据、且该字段「仅 session 7 非空」，但冻结命令面没有任何通道能写它——不加此旗标则
session 7 永远无法经引擎完成，7/7 结业门与 check --final 三条件均不可达（单一写通道纪律又禁止
LLM 手写 YAML）。增补是**纯加性**的：冻结签名中的三个旗标语义一字未动，仅多一个可选入口
（已追认）。

② init 在 §7 冻结签名 `[--role R]` 之外**增补可选旗标 `[--recover]`**（V 能力清点 T-6，乙类：
功能性缺陷）。理由：损坏的进度文件让每条命令都只能报错——`status` / `update` / `check` 读不动
它，`init` 又因「已存在」一律拒绝，而单一写通道纪律禁止 LLM 手改 YAML ⇒ **损坏即死锁，需人工
干预且无步骤承载**（「检测 + 自动备份 + 提供 fresh start」）。
该旗标把恢复收归引擎：备份（逐字节副本）→ 重建，人只发命令、不碰 YAML。**纯加性**：不带
`--recover` 时逐字保持原行为（文件可用 → ALREADY_EXISTS 拒绝），且文件可用时带 `--recover`
同样拒绝——「进度文件已存在 → 强制 resume」纪律一字未松。

回执契约对齐 B1/B2/B3 既有先例：共同键 {ok, command, project_root, output_dir, violations
[{code,where,msg}], warnings, counts}；写命令（init / update）另含 `updated`（bump 后日期）；
where 一律正斜杠、相对 project-root，无位置时用命令形态字符串；人读态每条违规一行
`CODE where: msg` + 末尾汇总行；--json 单行（ensure_ascii=False）；--output-dir 必填
（argparse required，无默认值）；引擎不做实例解析/白名单/目录推导（实例解析由 SKILL.md 委托
diyc.py resolve）。写回纪律：全文 load → 就地改 → yaml.safe_dump(allow_unicode=True,
sort_keys=False, default_flow_style=False) → 同目录临时文件 + os.replace（注释不保留）。
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from progress_init import cmd_init, cmd_status  # noqa: E402
from progress_update import cmd_check, cmd_update  # noqa: E402

# ---------------------------------------------------------------- 命令行面

# trace: 命令行面（--output-dir 必填；update 三形态互斥）
def build_parser():
    ap = argparse.ArgumentParser(
        description="diy-teach-me-testing 领域引擎：学习进度生成（init）/ 仪表盘与校验（status）"
                    "/ 单一写通道（update）/ 门禁校验（check --final）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    i = sub.add_parser("init", help="建 {output_dir}/learning-progress.yaml（7 节全未开始）"
                                    "+ notes/ 目录；已存在 → 拒绝并指引 resume"
                                    "（不可用的损坏件走 --recover：先备份再重建）")
    i.add_argument("--role", default=None,
                   help="学员角色（可省；省略 → learner.role: null。assessed 一律 null）")
    i.add_argument("--recover", action="store_true",
                   help="损坏件恢复通道：进度文件不可用（解析失败 / 顶层非映射 / 缺 sessions "
                        "列表）时先把原文件备份为 learning-progress.yaml.corrupt-"
                        "<YYYYmmdd-HHMMSS>.bak 再重建 7 节骨架；不带本旗标只报错指路，"
                        "文件可用时带本旗标也一律拒绝（走 resume）")
    i.add_argument("--project-root", default=".", help="项目根（默认 .）")
    i.add_argument("--output-dir", required=True,
                   help="产物目录（必填；由调用方传入，引擎不做实例解析/目录推导）")
    i.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    i.set_defaults(func=cmd_init)

    s = sub.add_parser("status", help="读进度 + 校验（与 check 同源）+ 仪表盘 + 分流 entry_step")
    s.add_argument("--project-root", default=".", help="项目根（默认 .）")
    s.add_argument("--output-dir", required=True, help="产物目录（必填）")
    s.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    s.set_defaults(func=cmd_status)

    u = sub.add_parser("update", help="唯一写通道：--session / --learner / --summary 三形态互斥")
    form = u.add_mutually_exclusive_group(required=True)
    form.add_argument("--session", type=int, default=None, help="session id（整数 1-7）")
    form.add_argument("--learner", action="store_true", help="写 learner 区块（画像采集专线）")
    form.add_argument("--summary", action="store_true", help="置 summary.generated（结业专线）")
    u.add_argument("--status", default=None,
                   help="session 形态：目标状态（未开始|进行中|已完成）")
    u.add_argument("--score", type=int, default=None,
                   help="session 形态：quiz 分 0-100（仅 --status 已完成；session 7 无 quiz）")
    u.add_argument("--notes", default=None,
                   help="session 形态：笔记路径，固定命名 notes/session-<NN>.md（文件须在场）")
    u.add_argument("--topics", type=int, default=None,
                   help="session 形态：探索主题数（仅 session 7；完成判据 >= min_topics）")
    u.add_argument("--role", default=None, help="learner 形态：角色（QA|开发|组长|负责人）")
    u.add_argument("--experience", default=None,
                   help="learner 形态：经验等级（learning_paths 的键）")
    u.add_argument("--goals", action="append", default=None,
                   help="learner 形态：学习目标（可重复）")
    u.add_argument("--pain-points", action="append", default=None,
                   help="learner 形态：当前痛点（可重复）")
    u.add_argument("--path", default=None, help="summary 形态：结业摘要路径（completion-summary.md）")
    u.add_argument("--project-root", default=".", help="项目根（默认 .）")
    u.add_argument("--output-dir", required=True, help="产物目录（必填）")
    u.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    u.set_defaults(func=cmd_update)

    k = sub.add_parser("check", help="进度文件校验（schema/派生三式/score/topics/notes/learner）；"
                                     "--final 附加 7 节齐 + 摘要置位 + 摘要文件在场")
    k.add_argument("--final", action="store_true",
                   help="结业门校验：sessions_completed == 7 且 summary.generated == true"
                        " 且 summary.path 文件在场")
    k.add_argument("--project-root", default=".", help="项目根（默认 .）")
    k.add_argument("--output-dir", required=True, help="产物目录（必填）")
    k.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    k.set_defaults(func=cmd_check)
    return ap

# trace: 旗标组合纪律（形态专属旗标配错形态 → 用法错误 exit 2）
def check_flag_forms(parser, args):
    session_flags = ("status", "score", "notes", "topics")
    learner_flags = ("role", "experience", "goals", "pain_points")

    def given(names):
        return [name for name in names if getattr(args, name) is not None]

    if args.learner:
        bad = given(session_flags + ("path",))
        if bad:
            parser.error("--learner 形态不接 --%s" % " --".join(bad))
        return
    if args.summary:
        bad = given(session_flags + learner_flags)
        if bad:
            parser.error("--summary 形态不接 --%s" % " --".join(bad))
        if args.path is None:
            parser.error("--summary 形态须给 --path（completion-summary.md）")
        return
    bad = given(learner_flags + ("path",))
    if bad:
        parser.error("--session 形态不接 --%s" % " --".join(bad))
    if not given(session_flags):
        parser.error("--session 形态须至少给 --status / --score / --notes / --topics 之一")

# trace: 入口（stdout/stderr 固定 UTF-8；退出码由子命令返回）
def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    parser = build_parser()
    args = parser.parse_args()
    if args.cmd == "update":
        check_flag_forms(parser, args)
    sys.exit(args.func(args))

if __name__ == "__main__":
    main()
