# -*- coding: utf-8 -*-
"""diy-test-gate 确定性引擎入口：覆盖率矩阵 join + 单一门决策校验（跨文档核对委派 diyc）。

子命令：
  collect  质量门的确定性采集（只读，零写盘）：
             0 前置门禁（任务书 §4）：stories.yaml / test-plan.yaml（须 project.status:
               已定稿）/ prd.yaml 三件套在场且可解析；`--story S-x` 给出时须在 stories.yaml
               可解析；AC 集为空 → 拒绝。任一项不满足 → 零产出 exit 1 + 结构化拒绝
               （violations + gate.route 给路由）。
             1 矩阵 join：AC（stories）× TC（test-plan）× 证据台账（sprint 任务
               test_refs / evidence）。覆盖判定表逐 TC（任务书 §4）：
               ① status: 失败 → blocker 不计（失败胜，即使同 TC 留有 green 记录）；
               ② status: 通过 且有 evidence（该 story 任务的台账条目 red/green 均非空；
                  test_refs 只用于查台账归属）→ 已验证；
               ③ status: 通过 但无台账 → 已验证 + warning。**本引擎分不出这条「通过」
                  是谁写的**（diy-e2e-tests / diy-augment 追加用例不写 evidence 属合法，
                  其余来源应经 diyc green 写回）——warning 带上 technique 供人工核对，
                  替读者摊事实、不替读者下结论；
               ④ 待办 → 不计。
               AC coverage 五值：无 TC / 全未验证 → NONE；全验证且 type 全 单元 →
               UNIT-ONLY；全 集成 → INTEGRATION-ONLY；全验证且含 端到端 或 ≥2 类
               type → FULL；部分验证 → PARTIAL。
             2 priority 推导：prd.yaml FR priority（必须→P0 / 应该→P1 / 可选→P2），
               一 AC 多 FR 取最高；无 FR refs → P2 + warning。
             3 统计：totals / 三线（p0 / p1 / p2）/ by_level / by_tc / by_story + 缺口清单
               （kind：none | partial | blocker | heuristic | accepted_gap |
               test_plan_pending）。5 类盲区启发式按 AC 文本关键词 + 已验证 TC 的层级 /
               技术给**候选**（口径按可读数据面收窄，**不读源码**），最终判定留在
               steps/03-matrix-gaps.md。
             3b 证据时效（G-1）：台账 red/green 里的最新时间戳、`mutation-report.yaml`
               各 run 的 date，超过 EVIDENCE_TTL_DAYS（7）天 → `EVIDENCE_STALE` warning；
               处置（重跑 / 用户确认 + `gate.basis` 注明）留在 steps/03 与 steps/05。
             3c 跨层重复覆盖候选（G-2）：同一 AC 下「同一 technique + 同一 kill_target」
               在 ≥2 个 type 层级各有用例 → `coverage.duplicates`（可接受重叠 / 跨层冗余的
               判定与合并建议留在 steps/03 → `gate.recommendations`）。
             4 软指标六项（soft_metrics，任务书 §4 口径，带 分子 / 分母 / algorithm）。
             5 NFR 证据面（nfr_inputs）：四域 + 阈值载体实测（prd / architecture /
               test-plan 三处候选源均无结构化阈值载体）+ prd NFR 条目参考面 + 合规五标准
               静态清单（G-3，第五个走查维度）+ 跨域风险合成的两条规则（G-4）——两者都是
               **走查纪律的输入面**，判定与落点（`findings` / `recommendations`）在 steps/04，
               校验在 check。
             6 mutation 面：读 {output_dir}/mutation-report.yaml，缺席 → score=null +
               warning（日常口径；`--final` 时必须，见 check 面 MISSING_FILE）；
               在场 → 取全部 run 的 score 最小值（保守口径）。
             7 跨文档核对委托（任务书 §2.3）：子进程 `diyc.py check --type test-plan
               --final --json`——rc 0|1 均为正常回执，其 violations 进 diyc.violations
               （计入本技能判定，不当失败吞掉）；diyc 缺席 / rc=2 / 回执不可解析 →
               TOOL_MISSING / TOOL_ERROR 结构化降级，不崩。
  check    校验 {output_dir}/test-gate.yaml（TG-### 集合）：schema / 枚举 / 记录 ID 唯一 /
           引用解析（产物自身的 AC / TC / S 存在性——test-gate 不在 diyc 类型集内，本引擎
           自实现，不与 diyc 已覆盖规则重复；跨文档一致性仍委派 diyc）/ totals 与 by_level
           重算 / 门决策自洽（重算硬判据 actual；overlay：合成 且 confidence≠高 →
           至少 CONCERNS；NFR 域 CONCERNS 或软判据失败 → 至少 CONCERNS；任一硬判据
           失败 → 必须 FAIL；全部 通过 无域 CONCERNS 无 overlay → 才可 PASS）/ waiver 8 键
           契约（安全域 FAIL 不可豁免）/ 阈值 source 强制记出处；--final 附加：
           status 已落 已定稿、basis 非空、hard / soft 两组判据齐、零 [假设]、
           合规五标准逐条记账（G-3：行形态 + 聚合 FAIL>PARTIAL>PASS 重算）、跨域合成
           候选的落点（G-4：命中而 findings / recommendations 无 `<域>×<域>` 行即违例）；
           mutation-report 缺席日常只记 warning、`--final` 时判 MISSING_FILE
           （迁移计划 §十三:459「缺席日常 n/a、--final 时必须」）。
    check 只重算「同记录内可机械重算」的量（判据 actual、totals、by_level、overall_risk、
    非功能致命、P0 未覆盖、变异得分）——不重跑 collect 的覆盖判定表（那是
    collect 与 steps/03 LLM 复核的职责），避免二份实现。
    本引擎不写盘：产物由会话（LLM）按 Schema 段创作，引擎只采集与校验。

模块切分对齐 `diy-tools` 先例：本文件 = 入口 + collect 面；`gate_lib.py` = 常量 / 索引 /
diyc 委派 / mutation 面；`gate_check.py` = check 面（懒加载）。违规码全表见 `gate_lib.py`
模块 docstring（W2 建设期 6 码：DECISION_INCONSISTENT / CRITERION_STALE /
WAIVER_INCOMPLETE / WAIVER_INAPPLICABLE / THRESHOLD_UNSOURCED / UNKNOWN_THRESHOLD_PASS；
能力补齐轮 4 码：EVIDENCE_STALE / COMPLIANCE_UNRECORDED /
COMPLIANCE_AGGREGATE_MISMATCH / CROSS_DOMAIN_UNRECORDED）。
"""
# trace: 迁移计划 §二 验收 #3（前置门禁零产出退出）/#4（ID 链接入）/#12（diyc 接线）
# trace: 任务书 §4 W2（门禁 / collect 判定表与软指标）/ §2.2 引擎契约
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gate_collect import cmd_collect  # noqa: E402


# ---------------------------------------------------------------- check（懒加载）

def cmd_check(args):
    """check 子命令：懒加载 gate_check（模块缺失与 argparse 用法错误同级处理，rc=2）。"""
    try:
        import gate_check
    except ImportError as err:
        print("gate_check.py 缺失或不可导入：%s" % err, file=sys.stderr)
        return 2
    return gate_check.cmd_check(args)


# ---------------------------------------------------------------- 输出

def human_collect(payload):
    if payload["ok"]:
        print("PASS：矩阵 %d 行（覆盖 %s%%），缺口 %d 条，重复覆盖候选 %d 条"
              "（时效告警 %d），diyc 违规 %d 条"
              % (payload["counts"]["items"],
                 payload["coverage"]["totals"]["pct"],
                 payload["counts"]["gaps"],
                 payload["counts"].get("duplicates", 0),
                 payload["counts"].get("stale_evidence", 0),
                 payload["counts"].get("diyc_violations", 0)))
        for item in payload["warnings"]:
            print("- WARN %s %s: %s" % (item["code"], item["where"], item["msg"]))
        return
    print("FAIL：")
    for item in payload["violations"]:
        print("- %s %s: %s" % (item["code"], item["where"], item["msg"]))
    if payload["gate"].get("route"):
        print("路由：%s" % payload["gate"]["route"])


def build_parser():
    ap = argparse.ArgumentParser(
        description="diy-test-gate 确定性引擎：覆盖率矩阵 join + 单一门决策校验"
                    "（跨文档核对委派 diyc）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("collect",
                       help="前置门禁 + 矩阵 join + 软指标 + NFR / mutation 证据面（只读）")
    c.add_argument("--scope", default="story", help="门范围（唯一合法值 story）")
    c.add_argument("--story", default=None, help="限定单个 story（S-x；缺省扫全部）")
    c.add_argument("--project-root", default=".", help="项目根（默认 .）")
    c.add_argument("--output-dir", required=True,
                   help="产物目录（必填；由调用方传入，引擎不做实例解析/目录推导）")
    c.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    c.set_defaults(func=cmd_collect)

    k = sub.add_parser("check",
                       help="校验 test-gate.yaml（schema/枚举/门决策自洽/waiver 契约；"
                            "--final 附加定稿义务）")
    k.add_argument("--project-root", default=".", help="项目根（默认 .）")
    k.add_argument("--output-dir", required=True,
                   help="产物目录（必填；由调用方传入，引擎不做实例解析/目录推导）")
    k.add_argument("--final", action="store_true",
                   help="定稿校验：status 已落 已定稿 + basis 非空 + 两组判据齐 + 零假设")
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
