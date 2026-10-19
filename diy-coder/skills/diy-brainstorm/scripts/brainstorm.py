# -*- coding: utf-8 -*-
"""diy-brainstorm 确定性引擎：会话列举（list）/ 技术库加载与抽样（techniques）/
会话记录骨架铸造（init）/ brainstorm.yaml 校验（check [--final]）。

机制：会话记录是**内容型产物**（教练对话的结论落 `{output_dir}/brainstorm.yaml`），
内容面由会话（LLM）直接编辑 YAML；本引擎只做确定性的两件事——铸造骨架与机械校验。
技术库落技能目录根 `brain-methods.csv`（与 `scripts/` 平级，61 技术 / 10 类，中文原生），
路径按引擎自身位置推算（`Path(__file__).parent.parent`），两种安装布局（源码
`diy-coder/skills/` 与安装 `.claude/skills/`）下同构成立。

  list       列会话记录——只回 `id` / `topic` / `date` / `status` / `current_step` 五字段
             （源纪律：**只列名不读内容**，续接点由 `current_step` 承载）。产物缺席是新项目
             常态 → 空列表 + `ok: true`，不报错；产物损坏 → 结构化违规（列不出就列不出）。

  techniques 加载技术库：`--all` 全列 / `--category C` 按类筛选 / `--random N` 随机抽 N
             （跨类别优先，保证组合多样）/ 无参 = 随机 5 个候选。`--category` 合法值 =
             CSV 的 `category` 列（10 个中文类名，**取值语言随库**），非法值 → `ENUM_INVALID`
             + exit 1。四种技术选取模式（用户自选 / AI 推荐 / 随机 / 渐进流）都由这里取数。

  init       建会话记录骨架（`--topic` 必填 / `--goals` 可省）：铸造 `BS-###`（序号 = 现有
             最大 + 1，三位零填充，**不复用空号不重号**）、`status: 草稿` + `current_step: 1`，
             原子写（产物缺席则建文件；损坏 → 拒绝且零写入，绝不覆盖）。

  check      schema / `BS-###` 格式与唯一 / `status` 枚举 / `current_step` 枚举 1-5 且与
             `status` 同档（草稿→1；进行中→2-4；已完成→5，否则 `STATUS_MISMATCH`）/
             步骤锚点与内容一致（≥2 有 approach、≥3 有 techniques、=5 有 themes + priorities.top
             + actions——源纪律「无行动计划不得收尾」）/ 想法 `no` 连续不跳号（1..N）/
             `themes[].ideas`、`priorities` 三键与 `actions[].idea` 的引用必须落在本记录
             `ideas[].no` 内 / `techniques[].category` ∈ 库内类名。`--final` 附加：
             `status: 已完成` 且零 `[假设]`（定稿前清零，未决项落 `open_questions`）。
             `--id BS-xxx` 把记录级扫描收窄到一条（找不到 → `UNKNOWN_ID`）。
             exit 0 唯一放行。

分工裁定（任务书 §2.2 形 A）：brainstorm.yaml 属新产物类型，不进 diyc.py check 的硬编码
类型集；契约同构——exit 0 唯一放行 / `--json` 单行回执（`ensure_ascii=False`）/ 无 `--json`
走中文人读行（每违规一行 `CODE where: msg` + 汇总行）/ 回执共同键
{ok, command, project_root, output_dir, violations[{code, where, msg}], warnings, counts}，
写回命令（init）另含 `updated`；`where` 正斜杠、相对 project-root。`--output-dir` 必填、
无缺省；引擎不做实例解析 / 白名单 / 目录推导（实例解析由 SKILL.md 委托 `diyc.py resolve`）。
写回纪律：全文 load → 就地改 → 追加/合并 → `yaml.safe_dump(allow_unicode=True,
sort_keys=False, default_flow_style=False)` → 同目录临时文件 + `os.replace`（注释不保留）。

违规码：复用 batch3-contract §3 冻结集——本引擎用到 `MISSING_FILE` / `UNPARSABLE_YAML` /
`UNKNOWN_ID` / `ENUM_INVALID` / `EMPTY_FIELD` / `DUPLICATE_ID` / `SET_MISMATCH` /
`STATUS_MISMATCH` / `ASSUMPTION_PRESENT` 共 9 个，**零新增**。两处语义复用在此登记：
① `UNPARSABLE_YAML` 兼作技术库（CSV）解析失败码——冻结集里没有「非 YAML 文本不可解析」码，
   造新码不如复用最近义项（msg 内点名是 CSV）；
② `SET_MISMATCH` 承载「想法 `no` 非 1..N 连续」——该码的语义是集合与真值不符，正中此例。

`--previous` 不适用（任务书 §2.2 记账，W1 判 no）：本产物是追加式台账（`sessions[]` 只追加、
记录内序号 `no` 只在记录内递增），从无 ID 集合收缩面——不存在「旧有新无」可比对。
"""
# trace: 迁移计划 §二 验收 #2（产物 schema + BS-### 稳定 ID）/#3（门禁零产出退出）
#        /#4（ID 链接入：BS-### + 想法序号）/#12（领域引擎接线：a 实例委托 d/e 写权边界）
import argparse
import os
import sys


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from brainstorm_checks import cmd_check  # noqa: E402
from brainstorm_cmds import cmd_init, cmd_list, cmd_techniques  # noqa: E402

def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(
        description="diy-brainstorm 确定性引擎：会话列举（list）/ 技术库加载（techniques）"
                    "/ 记录骨架（init）/ brainstorm.yaml 校验（check）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(parser):
        parser.add_argument("--project-root", default=".",
                            help="项目根（默认 .）")
        parser.add_argument("--output-dir", required=True,
                            help="产物目录（必填；由调用方传入，引擎不做实例解析/目录推导）")
        parser.add_argument("--json", action="store_true", help="输出单行 JSON 回执")

    ls = sub.add_parser("list", help="列会话记录（只回 id/topic/date/status/current_step 五字段）")
    common(ls)
    ls.set_defaults(func=cmd_list)

    tp = sub.add_parser("techniques", help="技术库加载：--all / --category C / --random N（默认随机 5 个）")
    common(tp)
    group = tp.add_mutually_exclusive_group()
    group.add_argument("--all", action="store_true", help="全列技术库")
    group.add_argument("--category", default=None, help="按类筛选（类名取技术库的中文类名）")
    group.add_argument("--random", type=int, default=None, help="随机抽 N 条（跨类别优先）")
    tp.set_defaults(func=cmd_techniques)

    ini = sub.add_parser("init", help="建会话记录骨架（铸 BS-###，status: 草稿 + current_step: 1）")
    common(ini)
    ini.add_argument("--topic", required=True, help="会话议题（门禁：由会话询问收集，不代拟）")
    ini.add_argument("--goals", default=None, help="会话目标（可省，内容面可后补）")
    ini.set_defaults(func=cmd_init)

    ck = sub.add_parser("check", help="校验 brainstorm.yaml（schema/枚举/引用/锚点；--final 附加定稿义务）")
    common(ck)
    ck.add_argument("--final", action="store_true",
                    help="定稿校验：status: 已完成 + 零 [假设]")
    ck.add_argument("--id", default=None, help="只校验指定记录（BS-###）")
    ck.set_defaults(func=cmd_check)

    args = ap.parse_args()
    sys.exit(args.func(args))

if __name__ == "__main__":
    main()
