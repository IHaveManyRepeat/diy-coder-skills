# -*- coding: utf-8 -*-
"""diy-brainstorm 确定性引擎：会话列举（list）/ 技术库加载与抽样（techniques）/
会话记录骨架铸造（init）/ brainstorm.yaml 校验（check [--final][--previous]）/ 开工快照（snapshot）。

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
             + actions——源纪律「无行动计划不得收尾」）/ **三级稳定 ID**（想法
             `BI-###` / 主题聚类 `BT-###` / 行动计划 `BA-###`，三位零填充）形态与**文件内按前缀
             全局唯一**（重复 → `DUPLICATE_ID`；空号合法——稳定 ID 不重编号，故不设连续约束）/
             `ideas[].no` 不得与 id 并存 / `themes[].ideas`、`priorities` 三键与
             `actions[].idea` 的引用必须落在本记录 `ideas[].id` 内 / `techniques[].category`
             ∈ 库内类名。`--final` 附加：`status: 已完成` 且零 `[假设]`（定稿前清零，未决项落
             `open_questions`）。`--id BS-xxx` 把记录级扫描收窄到一条（找不到 → `UNKNOWN_ID`）。
             `--previous` 版本对账：比对
             `{output_dir}/brainstorm.yaml.prev`，三失败分支 = `ID_UNSTABLE`（旧稿有、新稿无的
             会话记录 / 记录内想法·主题聚类·行动计划标识）/ `MISSING_FILE`（.prev 缺失）/
             `UNPARSABLE_YAML`（.prev 不可解析）；某级从无 id 迁到有 id 的那一轮（迁移轮）跳过
             该级比对，首拍 / 迁移不误报。exit 0 唯一放行。

  snapshot   每轮开工拍快照（逐字节原子复制）：`{output_dir}/brainstorm.yaml` → 同目录 `.prev`。
             产物缺席 → `ok` 放行不拍（新项目常态）；产物损坏 → 拒绝且零写入；
             `.prev` 在场**不覆盖**——先对账（同 `--previous` 三失败分支），不过 exit 1 零写入，
             过才覆盖为本轮基线；首拍（.prev 缺席）直拍。

分工裁定：brainstorm.yaml 属新产物类型，不进 diyc.py check 的硬编码
类型集；契约同构——exit 0 唯一放行 / `--json` 单行回执（`ensure_ascii=False`）/ 无 `--json`
走中文人读行（每违规一行 `CODE where: msg` + 汇总行）/ 回执共同键
{ok, command, project_root, output_dir, violations[{code, where, msg}], warnings, counts}，
写回命令（init、snapshot）另含命令级附加键（`updated` / `prev`）；`where` 正斜杠、相对 project-root。`--output-dir` 必填、
无缺省；引擎不做实例解析 / 白名单 / 目录推导（实例解析由 SKILL.md 委托 `diyc.py resolve`）。
写回纪律：全文 load → 就地改 → 追加/合并 → `yaml.safe_dump(allow_unicode=True,
sort_keys=False, default_flow_style=False)` → 同目录临时文件 + `os.replace`（注释不保留）。

违规码：复用冻结集——本引擎在用 `MISSING_FILE` / `UNPARSABLE_YAML` /
`UNKNOWN_ID` / `ENUM_INVALID` / `EMPTY_FIELD` / `DUPLICATE_ID` / `STATUS_MISMATCH` /
`ASSUMPTION_PRESENT` 共 8 个（冻结九码里的 `SET_MISMATCH` 随 `ideas[].no` 退场不再触发——
稳定 ID 不重编号，空号合法，「连续不跳号」约束随之作废），**冻结九码一字不动**；技能级新增码
1 个：**`ID_UNSTABLE`（--previous 对账：旧稿有、新稿无的稳定标识）**——按 bmb-module
「冻结 9 + 技能级新增码」先例在此登记。补登 **`TOOL_ERROR`**（工具层写盘失败通用码，两处
抛出点：init 写盘失败 `brainstorm_cmds.py:159`、snapshot 写盘失败 `brainstorm.py:128`——
只补文档登记，代码早已抛出）。语义复用在此登记：
① `UNPARSABLE_YAML` 兼作技术库（CSV）解析失败码——冻结集里没有「非 YAML 文本不可解析」码，
   造新码不如复用最近义项（msg 内点名是 CSV）；
② `ENUM_INVALID` 兼作「`ideas[].no` 与 id 并存」——冻结集里没有「废字段残留」码，最近义项是
   字段取值/形态不合法。

`--previous` 判 **yes**：
`BI-###` / `BT-###` / `BA-###` 未来成为 prd 的外部引用锚，素材单元丢失即跨文件断链（下游
`UNKNOWN_ID` 只能发现、不能恢复，prd 里也没有素材原文）——必须有 `.prev` 完整快照兜底。每轮
开工 `snapshot` 拍 `.prev`（在场不覆盖、先对账后拍）；`check [--final] --previous` 走三失败
分支；迁移轮按级跳过比对；`revisions`（改因留痕）与 `.prev`（兜底快照）两机制并存、不互替。
"""
# trace: 产物 schema + BS-### 稳定 ID；门禁零产出退出
#        /#4（ID 链接入：BS-### + 想法序号）/#12（领域引擎接线：a 实例委托 d/e 写权边界）
import argparse
import io
import os
import sys


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import display_path, read_sessions, receipt_base, v  # noqa: E402

from brainstorm_checks import check_previous, cmd_check, load_previous  # noqa: E402
from brainstorm_cmds import cmd_init, cmd_list, cmd_techniques  # noqa: E402
from brainstorm_lib import BRAINSTORM_FILE, emit  # noqa: E402

def cmd_snapshot(args):
    """每轮开工拍 `.prev`：产物缺席 → 放行不拍；`.prev` 在场先对账，不过零写入（不覆盖）。"""
    root = os.path.abspath(args.project_root)
    out = os.path.abspath(args.output_dir)
    path = os.path.join(out, BRAINSTORM_FILE)
    prev = path + ".prev"
    show = display_path(path, root)
    prev_show = display_path(prev, root)
    payload = receipt_base("snapshot", args, out)
    records, violations, warnings = read_sessions(path, show)
    if records is None and not violations:
        payload["ok"] = True
        payload["counts"] = {"sessions": 0, "snapshot": 0}
        return emit(payload, args.json, "PASS：产物缺席，无可拍摄（init 后再拍）")
    if violations:
        payload["violations"] = violations  # 损坏 / 顶层非映射 → 拒绝拍摄且零写入
        payload["warnings"] = warnings
        return emit(payload, args.json)
    existed = os.path.isfile(prev)
    if existed:
        prev_doc, prev_violations = load_previous(prev, root)
        if prev_doc is None:
            payload["violations"] = prev_violations
            return emit(payload, args.json)
        lost = check_previous(prev_doc, records, show, prev_show)
        if lost:
            payload["violations"] = lost  # 在场不覆盖：对账不过 exit 1，.prev 原样
            return emit(payload, args.json)
    try:
        with io.open(path, "rb") as fh:
            content = fh.read()
        with io.open(prev + ".tmp", "wb") as fh:
            fh.write(content)
        os.replace(prev + ".tmp", prev)
    except OSError as e:
        try:
            os.remove(prev + ".tmp")
        except OSError:
            pass
        payload["violations"] = [v("TOOL_ERROR", prev_show, "快照写盘失败：%s" % e)]
        return emit(payload, args.json)
    payload["ok"] = True
    payload["prev"] = prev_show
    payload["counts"] = {"sessions": len(records), "snapshot": 1}
    return emit(payload, args.json,
                "PASS：已拍快照 %s（%s）" % (prev_show, "对账通过后覆盖" if existed else "首拍"))

def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(
        description="diy-brainstorm 确定性引擎：会话列举（list）/ 技术库加载（techniques）"
                    "/ 记录骨架（init）/ brainstorm.yaml 校验（check）/ 开工快照（snapshot）")
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
    ck.add_argument("--previous", action="store_true",
                    help="版本对账（缺省比对 {output_dir}/brainstorm.yaml.prev）：旧有新无 → ID_UNSTABLE"
                         " / 快照缺失 → MISSING_FILE / 不可解析 → UNPARSABLE_YAML；"
                         "想法/主题/行动三级标识的迁移轮跳过比对")
    ck.set_defaults(func=cmd_check)

    sn = sub.add_parser("snapshot", help="每轮开工拍 .prev 快照（在场先对账，不过不覆盖）")
    common(sn)
    sn.set_defaults(func=cmd_snapshot)

    args = ap.parse_args()
    sys.exit(args.func(args))

if __name__ == "__main__":
    main()
