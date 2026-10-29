# -*- coding: utf-8 -*-
"""diy-checkpoint-preview 确定性引擎：变更候选定位（前置门禁）+ checkpoint.yaml 校验。

子命令：
  target  4 层级联定位被审变更，确定性部分不留给 LLM：
            1 显式 --ref（commit / range / 分支；PR 引用须先解析为本地 ref）
            2 {output_dir}/sprint.yaml 中 status: 待审查 的任务
            3 git 工作区改动 → HEAD 提交
            4 四者皆无 → 零产出 exit 1 + 结构化拒绝回执（含路由）
          只读检测，绝不写文件。环境健壮性：目录非 git 仓库 / 无提交 / 无 diff
          一律返回空候选 + 结构化原因，不崩溃。
          裸提交候选附意图判定：提交信息 subject < 10 词 →
          inferred: true + 原因；工作区改动 / range 无单一提交信息 → null + 原因。
  check   校验 {output_dir}/checkpoint.yaml（顶层 project + checkpoints 集合，形状对齐
          bug-log.yaml）：schema / 枚举 / story 引用可解析 / change_type 出现时非空；
          --final 附加定稿义务（checkpoints 非空、concern 非空、decision 已定且非 讨论、
          status 已落 已定稿、next 非空、零 [假设]）。exit 0 唯一放行。

分工裁定：checkpoint 属新产物类型，不进 diyc.py check 的硬编码类型集；
本引擎沿用领域引擎形态（同 design.py 分工），契约同构：exit 0 唯一放行 / --json 单行回执 /
violations[{code, where, msg}] + counts。违规码复用冻结集，
新增 NO_TARGET（门禁拒绝专用）。

禁手写实例解析：引擎不做 --instance / 白名单 / 目录推导；--output-dir 必填，
由调用方传入（SKILL.md 从 diyc.py resolve 取）。产物与产物 ID 由 diy-checkpoint-preview
会话（LLM）创作——CK-0nn 由 LLM 铸造、本引擎只校验格式与唯一性。
"""
# trace: 前置门禁零产出退出 + ID 链接入 + 领域引擎接线
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import count_items, display_path, load_yaml_safe, nonempty, v  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from checkpoint_checks import check_record, count_by  # noqa: E402
from checkpoint_target import CK_FILE, MODES, cmd_target, load_story_index  # noqa: E402,F401  # MODES=re-export（test_checkpoint engine_modes 直读）

def cmd_check(args):
    root = os.path.abspath(args.project_root)
    out = args.output_dir
    path = os.path.join(out, CK_FILE)
    show = display_path(path, root)
    violations = []
    warnings = []
    records = []

    data, err = load_yaml_safe(path)
    if data is None and err is None:
        violations.append(v("MISSING_FILE", show,
                            "%s 不存在（先完成一次 checkpoint 起草）" % CK_FILE))
    elif err is not None:
        violations.append(v("UNPARSABLE_YAML", show, "YAML 解析失败：%s" % err))
    elif not isinstance(data, dict):
        violations.append(v("EMPTY_FIELD", show, "顶层不是映射（须为 project + checkpoints）"))
    else:
        # project 形状为 {name, created, updated}，状态挂记录级（不要求 project.status）
        project = data.get("project")
        if project is not None and not isinstance(project, dict):
            violations.append(v("EMPTY_FIELD", show + " project", "project 不是映射"))
        revisions = data.get("revisions")
        if revisions is not None and not isinstance(revisions, list):
            violations.append(v("EMPTY_FIELD", show + " revisions", "revisions 不是列表"))
        raw_records = data.get("checkpoints")
        if raw_records is None:
            violations.append(v("EMPTY_FIELD", show + " checkpoints",
                                "checkpoints 缺失（集合形态；无记录写空列表）"))
        elif not isinstance(raw_records, list):
            violations.append(v("EMPTY_FIELD", show + " checkpoints", "checkpoints 不是列表"))
        else:
            records = raw_records
            story_ids, index_warnings = load_story_index(out)
            warnings += index_warnings
            seen = set()
            for i, record in enumerate(records):
                violations += check_record(i, record, args.final, story_ids, show)
                if isinstance(record, dict) and nonempty(record.get("id")):
                    rid = str(record["id"])
                    if rid in seen:
                        violations.append(v("DUPLICATE_ID", "%s.checkpoints[%d].id" % (show, i),
                                            "记录 ID %s 重复（CK ID 稳定不重用）" % rid))
                    seen.add(rid)
            if args.final and not records:
                violations.append(v("EMPTY_FIELD", show + " checkpoints",
                                    "--final 要求至少 1 条记录"))

    counts = {
        "checkpoints": len(records),
        "by_decision": count_by(records, "decision"),
        "by_status": count_by(records, "status"),
        "by_source": count_by(records, "target"),
        "concerns": count_items(records, "concerns"),
        "risks": count_items(records, "risks"),
        "observations": count_items(records, "observations"),
    }
    ok = not violations
    payload = {
        "ok": ok,
        "command": "check",
        "project_root": args.project_root,
        "output_dir": os.path.normpath(out).replace("\\", "/"),
        "final": args.final,
        "violations": violations,
        "warnings": warnings,
        "counts": counts,
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        if ok:
            print("PASS：%s 校验通过（checkpoints=%d）" % (show, len(records)))
        else:
            print("FAIL：")
            for item in violations:
                print("- %s %s: %s" % (item["code"], item["where"], item["msg"]))
    return 0 if ok else 1

def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(
        description="diy-checkpoint-preview 确定性引擎：变更候选定位（门禁）+ checkpoint.yaml 校验")
    sub = ap.add_subparsers(dest="cmd", required=True)

    t = sub.add_parser("target", help="4 层级联定位被审变更（显式 ref → 冲刺任务待审查态 → Git 提交）")
    t.add_argument("--project-root", default=".", help="项目根（默认 .）")
    t.add_argument("--output-dir", required=True,
                   help="产物目录（必填；由调用方传入，引擎不做实例解析/目录推导）")
    t.add_argument("--ref", default=None, help="显式变更锚点（commit / range / 分支）")
    t.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    t.set_defaults(func=cmd_target)

    c = sub.add_parser("check", help="校验 checkpoint.yaml（schema/枚举/引用；--final 附加定稿义务）")
    c.add_argument("--project-root", default=".", help="项目根（默认 .）")
    c.add_argument("--output-dir", required=True,
                   help="产物目录（必填；由调用方传入，引擎不做实例解析/目录推导）")
    c.add_argument("--final", action="store_true", help="定稿校验：decision 已定 + status 已落 已定稿 + 零假设")
    c.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    c.set_defaults(func=cmd_check)

    args = ap.parse_args()
    sys.exit(args.func(args))

if __name__ == "__main__":
    main()
