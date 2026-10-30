# -*- coding: utf-8 -*-
"""diy-design 确定性引擎：前端需求检测 + 易用性自检 + schema 校验 + 页状态迁移。

子命令（回执 = 全家族统一形状，单行 JSON：{ok, command, violations[{code, where, msg}],
warnings[], counts{}, file}；退出码 0 成功 / 1 拒绝 / 2 用法错误）：
  detect      扫 prd.yaml FR statement → has_frontend（命中词 ∩ ¬机器锚词，启发式；
              普通动词不构成否决，机器锚词按词边界锚定；LLM 在 SKILL.md 层保留语义复核权）
  validate    design.yaml 结构契约：direction 非空、token 三类、每页四交互状态、原型存在、
              pages[].id 非空字符串与 status 枚举/removed_reason、open_questions 结构与终门、
              token_scope 形状；
              --previous <旧稿> 追加 ID 稳定对账（ID_UNSTABLE / MISSING_FILE / UNPARSABLE_YAML）
  check       design.yaml + 原型自检（判据面 = 回执 violations[].code）：易用性 contrast /
              color-only-signal / semantic-html · 无障碍 a11y-touch-target / a11y-keyboard /
              a11y-focus-order / a11y-reduced-motion ·
              设计系统 ds-token-color / ds-token-font-size / ds-token-spacing
  audit       扫 src 实现源码的 one-off 色值/字号（hex 按语法位置判定：只判声明值/内联 style
              等真实色值位，var() fallback 与选择器/注释不算）；token_scope 内的路径跳过
  transition  页状态迁移写回（9 条合法边冻结；重写 design.yaml 前落 .prev 快照；
              → 已移除 必填 --reason；破坏性边追加 revisions[]）

写回纪律（transition）：原样载入 → 就地改 → safe_dump(allow_unicode, sort_keys=False)
→ 同目录 .tmp + os.replace 原子替换；校验不过零写入。实例解析由 SKILL.md 层委托 `diyc.py resolve` 完成。
"""
# trace: S-14 AC-14.1 AC-14.2 AC-14.3 TC-14.1.1 TC-14.2.1 TC-14.3.1
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import load_yaml, resolve_output_dir, v  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from design_audit import cmd_audit  # noqa: E402
from design_checks import cmd_check, cmd_validate  # noqa: E402
from design_lib import PAGE_STATUSES, emit, norm_path, receipt  # noqa: E402
from design_transition import LEGAL_EDGES, cmd_transition  # noqa: E402

HIT_WORDS = ("页面", "界面", "登录", "表单", "图表", "看板", "仪表盘",
             "导航栏", "弹窗", "轮播", "输入框", "按钮", "列表页", "详情页")
# 机器锚词否决（finding determinism-1 修复）：只有工具链/文档语境的机器锚词能否决命中——
# 文件名扩展名（prd.yaml）、技能名前缀（diy-）、技术术语（html/token/skill）与套件组件名
# （viewer），按词边界锚定。普通动词（生成/渲染/产出…）不再构成否决：它们出现在真实 UI
# 需求句中是常态（如「系统应生成订单详情页」，靠 viewer/diy- 等锚词而非动词排除）。
MACHINE_VETO_RE = re.compile(
    r"(?<![a-z0-9])(?:yaml|html|tokens?|skills?|viewers?)(?![a-z0-9])|diy-[a-z0-9]",
    re.IGNORECASE)

# ---------------------------------------------------------------- detect

def cmd_detect(args):  # trace: S-14 AC-14.2 TC-14.2.1 前端需求启发式（命中词+机器锚词否决），skip 判定证据
    output_dir = resolve_output_dir(args.project_root, args.instance)
    prd_path = os.path.join(output_dir, "prd.yaml")
    rel = norm_path(prd_path)
    if not os.path.isfile(prd_path):
        return emit(receipt("detect", False, file=rel,
                            violations=[v("MISSING_FILE", rel,
                                          "%s 不存在——先运行 diy-prd 生成该产物" % rel)],
                            counts={"requirements": 0, "hits": 0}), args.json)
    prd = load_yaml(prd_path)
    hits = []
    total = 0
    for group in prd.get("features", []) or []:
        for fr in group.get("requirements", []) or []:
            total += 1
            text = str(fr.get("statement", ""))
            if any(w in text for w in HIT_WORDS) and not MACHINE_VETO_RE.search(text):
                hits.append({"fr": fr.get("id"), "text": text[:80]})
    skip_reason = None if hits else \
        "PRD 未检测到面向用户的界面需求（启发式：命中词零命中或机器锚词否决）；LLM 可语义复核否决"
    result = receipt("detect", True, file=rel, violations=[],
                     counts={"requirements": total, "hits": len(hits)},
                     has_frontend=bool(hits), hits=hits, skip_reason=skip_reason)
    line = ("检测到前端需求：%s" % json.dumps(hits, ensure_ascii=False)
            if hits else "SKIP：%s" % skip_reason)
    return emit(result, args.json, [line])

# ---------------------------------------------------------------- CLI

def build_parser():
    ap = argparse.ArgumentParser(description="diy-design 检测/自检/校验/迁移引擎")
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("detect", help="检测 PRD 前端需求")
    d.add_argument("--project-root", default=".")
    d.add_argument("--instance", default=None)
    d.add_argument("--json", action="store_true")
    d.set_defaults(func=cmd_detect)
    for name, helptext, handler in (
            ("check", "易用性 / 无障碍 / 设计系统自检（判据 = 回执 violations[].code）",
             cmd_check),
            ("validate", "design.yaml 结构契约校验", cmd_validate)):
        p = sub.add_parser(name, help=helptext)
        p.add_argument("--design", required=True)
        p.add_argument("--previous", default=None,
                       help="旧稿快照（如 design.yaml.prev）：追加 ID 稳定对账")
        p.add_argument("--json", action="store_true")
        p.set_defaults(func=handler)
    a = sub.add_parser("audit", help="one-off 色值/字号审计（token 单一源）")
    a.add_argument("--design", required=True)
    a.add_argument("--src", required=True)
    a.add_argument("--json", action="store_true")
    a.set_defaults(func=cmd_audit)
    t = sub.add_parser("transition", help="页状态迁移写回（9 条合法边）")
    t.add_argument("--design", required=True)
    t.add_argument("--page", required=True)
    t.add_argument("--to", required=True, choices=list(PAGE_STATUSES))
    t.add_argument("--reason", default=None)
    t.add_argument("--json", action="store_true")
    t.set_defaults(func=cmd_transition)
    return ap

def main():  # trace: S-14 AC-14.1 子命令路由（utf-8 输出确定性）
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    args = build_parser().parse_args()
    try:
        return args.func(args)
    except Exception as e:  # 顶层兜底（照 diyc.py）：未预期异常也出回执，绝不空 stdout 静默失败
        result = receipt(args.cmd, False, file=getattr(args, "design", None),
                         violations=[v("INTERNAL_ERROR", getattr(args, "design", None) or args.cmd,
                                       "未预期内部异常：%s: %s（操作可能部分完成，请核对现场后重试）"
                                       % (type(e).__name__, e))])
        return emit(result, getattr(args, "json", False))

if __name__ == "__main__":
    sys.exit(main())
