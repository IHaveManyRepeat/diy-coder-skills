# -*- coding: utf-8 -*-
"""diy-investigate 确定性引擎：证据现场采集（collect）+ investigation.yaml 校验（check）。

collect（只读，绝不写文件、绝不下结论）：
  1 VCS 情报（源 Outcome 2 证据类目 + Outcome 4 git log 首扫）：git 可用且根目录在仓库内时取
    `git log` 近期提交（--since 限范围）与涉及文件；git 缺席/非仓库/命令失败 → NO_VCS warning
    降级（结构情报不受影响，不崩）。
  2 目标区域（--area）文件清单：文件直取 / 目录递归取文本类扩展名，逐文件计行数——行数是
    「>10K tokens 须委派子代理返 JSON」的成本依据；清单即源纪律「错误串 grep 候选面」（grep
    由会话执行，引擎不做结论）。
  3 结构候选面：同名族并行实现（源 Outcome 4 glob the affected directory for parallel
    implementations）+ 测试文件（test_<stem> / <stem>_test / <stem>.test / <stem>.spec 约定）。
  回执 {ok, vcs, files, candidates, warnings, counts}；超扫描上限 → SCAN_TRUNCATED warning。

check（IV-### 集合，形状对齐 bug-log.yaml）：schema / 枚举（record status / mode / grade /
availability / hypothesis status / confidence / backlog priority / backlog status / input
kind）/ IV+EV+H ID 格式
与记录内唯一 / evidence 三态齐全（grade + availability）/ hypotheses 生命周期完整性（status
非「待验证」⇒ resolution 非空——「假设永不删除，只更新状态 + 追加 Resolution」的机械化）/
stronghold 在场（evidence_light=false 时；源纪律「据点先行」）/ evidence_light=true ⇒
missing_evidence 非空（源纪律「缺失证据也是发现」）/ follow_ups 与 side_findings 追加块
（note 必填；side_findings 承接源 Side Findings——切向观察，非当前线程，与 evidence/backlog
语义区分；字段可选）。--final 附加：project.status 已定稿、conclusion 文本 + confidence、
handoff_brief 非空、timeline 非空、零 [假设]。exit 0 唯一放行。

分工裁定（任务书 §2.2/§7）：investigation 属新产物类型，不进 diyc.py check 硬编码类型集；
契约同构（exit 0 唯一放行 / --json 单行回执 / violations[{code, where, msg}] + counts；where
正斜杠、相对 project-root；--output-dir 必填、不做实例解析）。--previous 不实现（案件追加式，
resume 同 slug 原位更新，ID 集合只增不减）。无跨文档机械核对面（anytime 入口，不引用上游产物
ID），不委派 diyc；实例解析仍委托 `diyc.py resolve`（SKILL.md 激活句）。违规码复用
batch3-contract §3 冻结集，不新增；新增 warning 码 NO_VCS / SCAN_TRUNCATED。产物与 IV-/EV-/H-
ID 由会话（LLM）创作，本引擎只校验格式与唯一性。
"""
# trace: 迁移计划 §二 验收 #3（门禁形态：anytime 入口无上游门禁，拒绝路径=MISSING_FILE）
# trace: 迁移计划 §二 验收 #12（diyc 接线 a 实例委托 / b 终门 / c 记账不实现 / e 写权边界）
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from investigation_checks import cmd_check  # noqa: E402
from investigation_collect import cmd_collect  # noqa: E402

def build_parser():
    ap = argparse.ArgumentParser(
        description="diy-investigate 确定性引擎：证据现场采集（collect）+ "
                    "investigation.yaml 校验（check）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("collect", help="证据现场采集：VCS 情报 + 区域文件清单 + 候选面（只读）")
    p.add_argument("--area", default=None,
                   help="目标区域（文件或目录；结构情报的锚点）")
    p.add_argument("--since", default=None,
                   help="git log 起始（如 '2026-09-01' 或 '3 days ago'）")
    p.add_argument("--project-root", default=".", help="项目根（默认 .）")
    p.add_argument("--output-dir", required=True,
                   help="产物目录（必填；由调用方传入，引擎不做实例解析/目录推导）")
    p.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    p.set_defaults(func=cmd_collect)

    k = sub.add_parser("check", help="校验 investigation.yaml（schema/枚举/ID/证据纪律）")
    k.add_argument("--id", default=None, help="只校验指定案件（IV-xxx）")
    k.add_argument("--project-root", default=".", help="项目根（默认 .）")
    k.add_argument("--output-dir", required=True,
                   help="产物目录（必填；由调用方传入，引擎不做实例解析/目录推导）")
    k.add_argument("--final", action="store_true",
                   help="定稿校验：project.status 已定稿 + conclusion/handoff_brief/timeline + 零假设")
    k.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    k.set_defaults(func=cmd_check)
    return ap

def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    args = build_parser().parse_args()
    sys.exit(args.func(args))

if __name__ == "__main__":
    main()
