# -*- coding: utf-8 -*-
"""diy-create-story 确定性引擎：目标 story 的情报采集（只读）+ story-context.yaml 校验。

子命令：
  collect  目标 story 的确定性采集（只读，绝不写文件）：
             1 门禁（源技能 step-1「确定目标故事」的门禁化）：stories.yaml 在场、可解析、
               project.status == 已定稿，且 --story 指向的 story 存在；不满足 → 零产出 exit 1
               + 结构化拒绝回执（violations 带码 + gate.route 给路由）。story 悬空时回执附
               suggestions（候选 story ID，供会话降级为用户选择）。
               sprint.yaml / test-plan.yaml / architecture.yaml 缺席不拒（源输入表 fallback
               语义：上游未生成则引用面为空，降级为 warning）。
             2 AC 清点：目标 story 的全部 acceptance_criteria（id/given/when/then/refs +
               可选 design_ref）+ epic（该 story 的 epic——回执字段，供记录的 epic 字段
               直接取用，会话不必手工回读 stories.yaml）——替换源 step-2「人工通读 epics
               分片提取故事基础」。
             3 TC 清点：test-plan.yaml 中 ac 属该 story AC 集的用例（id/ac/title/type/
               priority/technique/status）——源需人工核对，此处机械匹配。
             4 前序情报：stories.yaml 中编号最高且小于当前者（S-y, y < x）的 story 及其
               sprint 任务 note/evidence/loop/blocked_reason——替换源 step-2「扫描
               implementation_artifacts 找上一故事文件」。
             5 决策清单：architecture.yaml decisions[] 的 {id, title, status, affects} 摘要级
               ——替换源 step-3「通读架构文档提取护栏」的取材面（适用面判定留给会话）。
             6 git 情报：最近 5 次提交（hash/date/subject/files，每提交最多 20 个文件路径）
               ——替换源 step-2 的 git 分析；VCS 不可用 / 无提交 → NO_VCS warning 降级，不崩。
  check    校验 {output_dir}/story-context.yaml（SC-### 集合，形状对齐 bug-log.yaml）：
           schema / id 格式与唯一 / story 解析（stories.yaml）/ epic 与 story 一致 /
           ac_refs ⊆ 该 story 的 AC / tc_refs 解析（test-plan.yaml）且归属该 story /
           decisions 解析（architecture.yaml）/ files[].path 相对 project-root 且 更新 型
           存在 + current_state 非空 / 同一 story 仅一条记录（按 story 键原位重写）。
           --final 附加：status=已定稿、zero [假设]、files 非空、verify 非空、
           更新 型 preserve 非空、open_questions 空或逐条 [CLOSED] 显式闭合。
           上游缺席（stories 拒跑；test-plan/architecture 出 warning）时相关解析降级。

分工裁定（任务书 §2.2/§2.3/§3）：story-context 属新产物类型，不进 diyc.py check 的硬编码
类型集；本引擎契约同构（exit 0 唯一放行 / --json 单行回执 / violations[{code, where, msg}]
+ counts；where 正斜杠、相对 project-root）；--output-dir 必填，实例解析由 SKILL.md 委托
diyc.py resolve（引擎内不做）。--previous 不实现：记录按 story 键原位重写，SC ID 集合不会
收缩（任务书 §2.2 逐技能记账）。违规码复用 batch3-contract §3 冻结集；新增 NO_VCS（VCS 情报
不可用 / 无提交的降级专用，同 W5 diy-investigate 同名语义）。产物与 SC-### ID 由
diy-create-story 会话（LLM）创作，本引擎只校验格式与唯一性；两个子命令都不写盘。
"""
# trace: B2 diy-create-story 验收#3（前置门禁）/ #4（ID 链接入）/ #12（diyc 接线）
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import count_by, count_items, display_path, emit_via, items, load_yaml_safe, nonempty, v  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from story_context_checks import check_record  # noqa: E402
from story_context_collect import cmd_collect  # noqa: E402
from story_context_lib import ARCH_FILE, CONTEXT_FILE, STORIES_FILE, TEST_PLAN_FILE, base_payload, load_docs, missing_warning, story_map  # noqa: E402


def build_ctx(docs, root):
    return {
        "root": root,
        "has_stories": docs[STORIES_FILE]["present"] and docs[STORIES_FILE]["err"] is None,
        "has_test_plan": docs[TEST_PLAN_FILE]["present"] and docs[TEST_PLAN_FILE]["err"] is None,
        "has_arch": docs[ARCH_FILE]["present"] and docs[ARCH_FILE]["err"] is None,
        "stories": story_map(docs[STORIES_FILE]["data"]),
        "tcs": {str(tc["id"]): tc for tc in items(docs[TEST_PLAN_FILE]["data"], "test_cases")
                if isinstance(tc, dict) and nonempty(tc.get("id"))},
        "decisions": {str(d["id"]): d for d in items(docs[ARCH_FILE]["data"], "decisions")
                      if isinstance(d, dict) and nonempty(d.get("id"))},
    }

def cmd_check(args):
    root = os.path.abspath(args.project_root)
    out = os.path.abspath(args.output_dir)
    docs = load_docs(out)
    ctx = build_ctx(docs, root)
    path = os.path.join(out, CONTEXT_FILE)
    show = display_path(path, root)
    violations = []
    warnings = []
    records = []

    for name in (STORIES_FILE, TEST_PLAN_FILE, ARCH_FILE):
        if not docs[name]["present"]:
            warnings.append(missing_warning(
                out, name, "%s 缺席：相关引用解析降级（记录内逐条给出违规）" % name, root))

    data, err = load_yaml_safe(path)
    if data is None and err is None:
        violations.append(v("MISSING_FILE", show,
                            "%s 不存在（先完成一次 story 上下文包起草）" % CONTEXT_FILE))
    elif err is not None:
        violations.append(v("UNPARSABLE_YAML", show, "YAML 解析失败：%s" % err))
    elif not isinstance(data, dict):
        violations.append(v("EMPTY_FIELD", show, "顶层不是映射（须为 project + contexts）"))
    else:
        project = data.get("project")
        if project is not None and not isinstance(project, dict):
            violations.append(v("EMPTY_FIELD", show + " project", "project 不是映射"))
        revisions = data.get("revisions")
        if revisions is not None and not isinstance(revisions, list):
            violations.append(v("EMPTY_FIELD", show + " revisions", "revisions 不是列表"))
        raw_records = data.get("contexts")
        if raw_records is None:
            violations.append(v("EMPTY_FIELD", show + " contexts",
                                "contexts 缺失（集合形态；无记录写空列表）"))
        elif not isinstance(raw_records, list):
            violations.append(v("EMPTY_FIELD", show + " contexts", "contexts 不是列表"))
        else:
            records = [r for r in raw_records
                       if not (args.story and isinstance(r, dict)
                               and str(r.get("story")) != args.story)]
            if args.story and not records:
                violations.append(v("UNKNOWN_ID", show + " contexts",
                                    "--story %s 无对应记录" % args.story))
            for i, record in enumerate(records):
                violations += check_record(i, record, ctx, args.final, show)
            seen_ids = set()
            seen_stories = set()
            for i, record in enumerate(records):
                if not isinstance(record, dict):
                    continue
                rid = record.get("id")
                if nonempty(rid):
                    if str(rid) in seen_ids:
                        violations.append(v("DUPLICATE_ID", "%s.contexts[%d].id" % (show, i),
                                            "记录 ID %s 重复（SC ID 稳定不重用）" % rid))
                    seen_ids.add(str(rid))
                story = record.get("story")
                if nonempty(story):
                    if str(story) in seen_stories:
                        violations.append(v("DUPLICATE_ID", "%s.contexts[%d].story" % (show, i),
                                            "%s 已有一条记录；按 story 键原位更新，不新增记录" % story))
                    seen_stories.add(str(story))
            if args.final and not records:
                violations.append(v("EMPTY_FIELD", show + " contexts",
                                    "--final 要求至少 1 条记录"))

    counts = {
        "contexts": len(records),
        "by_status": count_by(records, "status"),
        "files": count_items(records, "files"),
        "acs": count_items(records, "ac_refs"),
        "tcs": count_items(records, "tc_refs"),
        "open_questions": count_items(records, "open_questions"),
    }
    ok = not violations
    payload = base_payload("check", args, out)
    payload["ok"] = ok
    payload["final"] = args.final
    payload["violations"] = violations
    payload["warnings"] = warnings
    payload["counts"] = counts
    emit_via(payload, args.json, human_check)
    return 0 if ok else 1

def human_check(payload):
    if payload["ok"]:
        print("PASS：%s 校验通过（contexts=%d）"
              % (payload["output_dir"] + "/" + CONTEXT_FILE, payload["counts"]["contexts"]))
        return
    print("FAIL：")
    for item in payload["violations"]:
        print("- %s %s: %s" % (item["code"], item["where"], item["msg"]))
    for item in payload["warnings"]:
        print("警告 %s %s: %s" % (item["code"], item["where"], item["msg"]))

def build_parser():
    ap = argparse.ArgumentParser(
        description="diy-create-story 确定性引擎：目标 story 情报采集（只读）+ "
                    "story-context.yaml 校验")
    sub = ap.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("collect", help="门禁 + AC/TC/前序/决策/git 采集（只读，不写盘）")
    c.add_argument("--story", required=True, help="目标 story ID（S-x）")
    c.add_argument("--project-root", default=".", help="项目根（默认 .）")
    c.add_argument("--output-dir", required=True,
                   help="产物目录（必填；由调用方传入，引擎不做实例解析/目录推导）")
    c.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    c.set_defaults(func=cmd_collect)

    k = sub.add_parser("check", help="校验 story-context.yaml（schema/引用/现场勘察；--final 附加定稿义务）")
    k.add_argument("--story", default=None, help="只校验该 story 的记录（可省 → 全量）")
    k.add_argument("--project-root", default=".", help="项目根（默认 .）")
    k.add_argument("--output-dir", required=True,
                   help="产物目录（必填；由调用方传入，引擎不做实例解析/目录推导）")
    k.add_argument("--final", action="store_true",
                   help="定稿校验：status 已落 final + verify/files/preserve 义务 + 零假设 + 未决清零")
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
