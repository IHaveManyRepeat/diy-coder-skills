# -*- coding: utf-8 -*-
"""diy-cis-method 确定性引擎：会话列举（list）/ 单条详情（show）/ 方法库加载（methods）/
会话记录骨架铸造（init）/ cis-method.yaml 校验（check [--final]）。

机制：本技能是**四分支创意方法引导器**（创新策略 / 问题求解 / 设计思维 / 叙事），
四条分支各有固定的源步骤序列（9 / 9 / 7 / 10 步）。产物 `{output_dir}/cis-method.yaml`
是**单 YAML 集合、内容型产物**——每步的成品内容由会话（LLM）直接编辑 YAML 写回
（`deliverable.<键>` + `open_questions`，并推进 `current_step` / `status`），本引擎只做
确定性的两件事——**铸造骨架**与**机械校验**。分工写死（任务书 §2.2）：`id` / `method` /
`date` 由 `init` 铸造后不再由 LLM 改；五个子命令里**只有 `init` 写盘**，`check` 只校验不写。

方法库落技能目录根 `cis-methods.csv`（与 `scripts/` 平级，四源合一的 115 条 / 23 类，
中文原生），路径按引擎自身位置推算（`Path(__file__).parent.parent`），两种安装布局
（源码 `diy-coder/skills/` 与安装 `.claude/skills/`）下同构成立。

  list    列会话记录——只回 `id` / `method` / `topic` / `date` / `status` / `current_step`
          六字段（源纪律：**只列不读正文**，续接锚点是 `current_step`）。产物缺席是新项目
          常态 → 空列表 + `ok: true`，不报错；产物损坏 → 结构化违规。

  show    单条记录全文（`--id CM-###`）；不在集合内 → `UNKNOWN_ID`。

  methods 加载方法库（对应 `diy-brainstorm` 的 `techniques` 命令）：默认只给**该分支工作流
          实际接入的类别**（可达集，裁定 5(e) 保真照搬源侧），`--all` 给该 `method` 的
          全部条目（**不跨分支**——语义是「含源侧未接入工作流的条目」，不是「全库 115 条」），
          `--category C` 在结果集上按类过滤（`C` 须是该 `method` 的合法类名，否则
          `ENUM_INVALID`），`--random N` 从**默认结果集**抽 N 条、`N` 超界 → 全给 + warning
          （不报错）。`--method` 必填（缺席 → `EMPTY_FIELD`；`init` 侧的缺席另由 argparse
          `required` 判为用法错误 exit 2——两处口径不同，见任务书 §2.6 ①/⑧）。

  init    建会话记录骨架（`--method` / `--topic` 必填）：铸造 `CM-###`（序号 = 现有最大 + 1，
          三位零填充，**不复用空号不重号**）、`status: 草稿` + `current_step: 1`，
          全文 load → 就地改 → 原子写（产物缺席则建文件；损坏 → 拒绝且零写入，绝不覆盖）。

  check   schema / `CM-###` 格式与唯一 / `method` 枚举 / `topic` / `date` /
          `current_step` 越界与同档（`草稿`=1；`进行中`=2..末步-1；`已完成`=末步）/
          `deliverable` 空而 `status ≠ 草稿` / **分支必填键**（下表）/ 多余键（warning）/
          `open_questions` / 未解析 `{...}` 令牌。`--final` 附加：`status: 已完成` 且零 `[假设]`。
          `--id CM-xxx` 把记录级扫描收窄到一条（找不到 → `UNKNOWN_ID`）。exit 0 唯一放行。

分支必填键表（内表 `STEP_KEYS`，共 **34 键**）：每分支 = 该分支**每个源 step 的第一个
「非注入」`<template-output>` 键**（源侧两形态：一键一标签 / 逗号分隔多键，多键按逗号切分后
取首键）。**注入项 = `date` / `user_name` / `agent_role` / `agent_name` 四项，一律不入表**。
创新策略 9 + 问题求解 9 + 设计思维 7 + 叙事 9 = 34——叙事第 10 步的唯一标签是
`agent_role, agent_name, user_name, date`（四个全是注入项）→ **该步无实键**。
`check` 按**进度**校验（`current_step` 已走到的步其首键必须已落），`--final` 时
`status: 已完成` 已把 `current_step` 顶到末步 → 等价于「分支必填键集齐全」。
**不校验全部 122 个模板键**（源侧模板键表是建议结构，非封闭集）：多余键只给 warning。
问题求解分支的源侧第 9 步 `optional="true"` → `已完成` 时 `current_step ∈ {8, 9}`
**显式放行**（本批唯一的分支内例外，不得推广到其他分支）。

可达集映射（内表 `REACHABLE_CATEGORIES`，裁定 5(e)）：默认集 = 源侧工作流实际引用的类
（保真照搬）——创新策略 25 / 问题求解 30 / 设计思维 15；**叙事分支为源侧缺陷修复后**
（Step 2 改由引擎按类呈现全部条目）默认集 = `--all` = **25**。类名逐字取 §0 裁定 5(d)
的 23 个冻结中文名（`CATEGORY_ENUM`），与 `cis-methods.csv` 的 `category` 值同词
（库行校验会逐行核对，跨工位漂移在此暴露）。

违规码：复用 batch3-contract §3 冻结集——本引擎用到 `MISSING_FILE` / `UNPARSABLE_YAML` /
`EMPTY_FIELD` / `ENUM_INVALID` / `UNKNOWN_ID` / `DUPLICATE_ID` / `STATUS_MISMATCH` /
`ASSUMPTION_PRESENT` 共 8 个；**唯一新增码 = `TOKEN_UNRESOLVED`**（**不在**冻结集内，
也不在「已批扩展」两项内）——承载 §0 裁定 8 的「白名单外的任何 `{...}` 令牌一律拒绝」
（白名单仅 `{project-root}`（唯一例外）与 `{output_dir}`（源 `{output_folder}` 的 diy 替换））。
两处语义复用在此登记：
① `UNPARSABLE_YAML` 兼作方法库（CSV）解析失败码——冻结集里没有「非 YAML 文本不可解析」码，
   造新码不如复用最近义项（msg 内点名是 CSV；承 `diy-brainstorm/scripts/brainstorm.py` 先例）；
② `ENUM_INVALID` 兼作 `--random` 超界与非可达类名的 warning 码（同族先例同款用法）。

`--previous` 判 **no**（裁定 10）：`sessions[]` 只追加、`CM-###` 顺序递增，从无 ID 集合
收缩面——不存在「旧有新无」可比对；改既有记录往 `revisions` 追加而不重编号。

契约（承 batch3-contract §3 / 任务书 §2.2）：exit 0 唯一放行 / 1 = 违规或被拒绝 /
2 = 用法错误（argparse 默认）/ **本批无 exit 3**；`--json` → 单行回执（`ensure_ascii=False`），
无 `--json` → 中文人读行（每违规一行 `CODE where: msg` + 汇总行）；回执共同键
`{ok, command, project_root, output_dir, instance, violations, warnings, counts}`
（`instance` 恒 `null` 但**键在位**，`warnings` 与 `violations` 同形），`where` 正斜杠、
相对 project-root；**写盘命令（`init`）回执另含 `updated`**，只读子命令不含。
`--project-root`（默认 `.`）全部子命令都收；`--output-dir` **写盘子命令必填**（不设默认、
**不得**私读 `diy-coder.yaml` 当默认），只读子命令可省（其 `output_dir` 回执取值 = 调用方
从 `diyc.py resolve` 回执拿到的值；省了则回执为 `null`，需读产物的子命令明确报缺而不静默按空处理）。
**`--instance` 一律不做**（裁定 9）：实例由 SKILL.md 委托 `diyc.py resolve` 解析后以
`--output-dir` 形式传入，签名表内不出现它。
写回纪律：全文 load → 就地改 → `yaml.safe_dump(allow_unicode=True, sort_keys=False,
default_flow_style=False)` → 同目录临时文件 + `os.replace`（注释不保留；复用
`diyc_lib.save_yaml_atomic` 的同款实现——不另造一份语义不同的）。
"""
# trace: 迁移计划 §二 验收 #2（产物 schema + CM-### 稳定 ID）/#3（议题非空门禁）
#        /#4（ID 链：唯一性 + 顺序性 + 不进主链）/#12（领域引擎接线：b 终门 / e 写权边界）
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
# 探针 re-export：test_cis_method getattr(TOKEN_WHITELIST/STEP_KEYS/REACHABLE_CATEGORIES/CATEGORY_ENUM)
from diyc_lib import TOKEN_WHITELIST  # noqa: E402,F401

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cis_method_checks import cmd_check  # noqa: E402
from cis_method_cmds import cmd_init, cmd_list, cmd_methods, cmd_show  # noqa: E402
from cis_method_lib import CATEGORY_ENUM, REACHABLE_CATEGORIES, STEP_KEYS  # noqa: E402

# ---------------------------------------------------------------- CLI

def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(
        description="diy-cis-method 确定性引擎：会话列举（list）/ 单条详情（show）/ 方法库加载"
                    "（methods）/ 记录骨架（init）/ cis-method.yaml 校验（check）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(parser, output_required=False):
        parser.add_argument("--project-root", default=".",
                            help="项目根（默认 .）")
        parser.add_argument("--output-dir", required=output_required, default=None,
                            help="产物目录（写盘子命令必填；只读子命令可省，取值由 "
                                 "`diyc.py resolve` 回执给）")
        parser.add_argument("--json", action="store_true", help="输出单行 JSON 回执")

    ls = sub.add_parser("list", help="列会话记录（只回 id/method/topic/date/status/current_step）")
    common(ls)
    ls.add_argument("--method", default=None, help="按分支过滤（四条分支之一）")
    ls.set_defaults(func=cmd_list)

    sh = sub.add_parser("show", help="单条记录全文（--id CM-###）")
    common(sh)
    sh.add_argument("--id", required=True, help="记录 ID（CM-###）")
    sh.set_defaults(func=cmd_show)

    mt = sub.add_parser("methods", help="方法库加载：默认分支可达集 / --all / --category C "
                                        "/ --random N")
    common(mt)
    mt.add_argument("--method", default=None, help="分支（必填：创新策略|问题求解|设计思维|叙事）")
    mt.add_argument("--category", default=None, help="按类过滤（类名取库内冻结中文类名）")
    group = mt.add_mutually_exclusive_group()
    group.add_argument("--all", action="store_true",
                       help="该分支全部条目（不跨分支；含源侧未接入工作流的条目）")
    group.add_argument("--random", type=int, default=None, help="从默认结果集随机抽 N 条")
    mt.set_defaults(func=cmd_methods)

    ini = sub.add_parser("init", help="建会话记录骨架（铸 CM-###，status: 草稿 + current_step: 1）")
    common(ini, output_required=True)
    ini.add_argument("--method", required=True,
                     help="分支（必填：创新策略|问题求解|设计思维|叙事）")
    ini.add_argument("--topic", required=True, help="议题（门禁：由会话询问收集，不代拟）")
    ini.set_defaults(func=cmd_init)

    ck = sub.add_parser("check", help="校验 cis-method.yaml（schema/枚举/键表/令牌；"
                                      "--final 附加定稿义务）")
    common(ck)
    ck.add_argument("--final", action="store_true",
                    help="定稿校验：status: 已完成 + 分支必填键齐全 + 零 [假设]")
    ck.add_argument("--id", default=None, help="只校验指定记录（CM-###）")
    ck.set_defaults(func=cmd_check)

    args = ap.parse_args()
    sys.exit(args.func(args))

if __name__ == "__main__":
    main()
