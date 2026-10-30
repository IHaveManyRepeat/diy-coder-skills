# -*- coding: utf-8 -*-
"""diy-editorial-review 确定性引擎：目标文档结构统计（stats）+ editorial-review.yaml 校验（check）。

机制：本技能对同一份文稿跑两个透镜——结构透镜（删减 / 重组 / 简化的建议）与文风透镜
（沟通障碍的三列修订建议），一次评审出一份 findings 台账（editorial-review.yaml 的
reviews[]）。两透镜（结构 + 文风）把两件机械活留给了人：

  stats   目标文档结构统计（section count / word count / …）：
            .md / 纯文本 → `#` 是**文档标题**（不计词、不切节），节由行首 `##` / `###` 切
                            （`####` 及更深不算），标题文本作节名；第一节之前若有正文，
                            归一个以文件名为名的节；无 `##`/`###` → 整文档一个节、节名取文件名；
            .yaml / .yml  → 按顶层键切节（键名作节名），节词数 = 该键子树全部字符串的词数；
            词数口径（唯一一处定义，findings 的 impact_words 同此）：中文字符按 1 词计
            （中文无空格分词），西文按 `[A-Za-z0-9_]+` 分词计；标题行不计入所在节词数。
            目标不存在 → MISSING_FILE；全文 < 3 词 → EMPTY_FIELD；无法按 UTF-8 解码 → MISSING_FILE（文档读不出来，等同不在场）。
            同时校验本次评审的 `--lens`（结构|文风，可重复；缺省两透镜全跑）与
            `--reader-type`（人类|LLM，缺省 人类）——越界即 ENUM_INVALID，**在动手前**拒绝；
            回执原样给出 `lenses` / `reader_type`，记录侧照抄、不凭记忆重打。

  check   校验 {output_dir}/editorial-review.yaml（本技能产出的 findings 台账）。基础校验：
          YAML 可解析（异常转 UNPARSABLE_YAML）；顶层 project{name,created,updated} +
          reviews[] + revisions[] 缺项；reviews[].id 形态 ER-###（三位数字）且全局唯一
          （DUPLICATE_ID / ENUM_INVALID）；target 的**基准**（project-root 相对 + 正斜杠 +
          无 `path:` 前缀，越界即 ENUM_INVALID）与**在场性**（相对 project-root 解析，
          不存在 → MISSING_FILE）；date 非空；status ∈ 草稿|已定稿；lenses 非空、取值
          结构|文风、不重复；**lenses 与两槽一致性**（跑了哪个透镜 → 对应槽在场；槽在场而
          lenses 未声明同判）→ SET_MISMATCH；reader_type ∈ 人类|LLM；open_questions 为列表。
          structure 槽：model 五值枚举（教程线性 / 参考 MECE / 解释抽象到具体 /
          任务式 meta-first / 战略金字塔）；findings[].no 记录内序号自 1 起连续、不重复
          （**取值兼容 YAML 1.1 的裸键 `no`**——PyYAML 把 `no:` 解析成布尔 `False`，
          记录侧照 schema 写裸 `no` 即可，引擎两形同读）
          （跳号 SET_MISMATCH、重号 DUPLICATE_ID、非正整数 ENUM_INVALID）；
          category 六值枚举 CUT|MERGE|MOVE|CONDENSE|QUESTION|PRESERVE；target 章节名 /
          rationale 非空；impact_words 为整数（PRESERVE 的代价记负数，允许负值）；
          estimated_reduction_words 为整数、meets_length_target ∈ 是|否|未设目标。
          prose 槽：findings[].no 同规；original / revised / changes 非空；locations 为列表。
          --final 附加：status 已落 `已定稿`（否则 STATUS_MISMATCH）、记录内零 `[假设]`
          字面量（ASSUMPTION_PRESENT）、estimated_reduction_words 与 findings 的
          impact_words 之和一致（两者都填时；PRESERVE 的负值参与求和 → SET_MISMATCH）。
          `--id ER-xxx` 只校该条记录；给的 ID 不在场 → UNKNOWN_ID。
          **`--previous` 判 no**（追加式台账：reviews[] 只追加、无 ID 集合收缩面），不实现。

规则来源：违规码全部复用冻结集——本引擎用到 MISSING_FILE /
UNPARSABLE_YAML / DUPLICATE_ID / UNKNOWN_ID / ENUM_INVALID / EMPTY_FIELD /
ASSUMPTION_PRESENT / SET_MISMATCH / STATUS_MISMATCH 共 9 个，**无新增码**。回执契约对齐
既有先例：exit 0 唯一放行 / --json 单行 JSON（ensure_ascii=False）/ 共同键
{ok, command, project_root, output_dir, violations[{code,where,msg}], warnings, counts}；
where 一律正斜杠、相对 project-root；人读态每条违规一行 `CODE where: msg` + 末尾汇总行；
--output-dir 必填（argparse required，无默认值）。分工裁定：本引擎不做实例解析、不做白名单、
不推导目录（实例解析由 SKILL.md 委托 diyc.py resolve）；两个子命令都**只读**——stats 只读
目标文档、check 只读台账，都不写任何文件（台账由技能侧编辑，终门走 check --final）。
"""
import argparse
import os
import sys


sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import display_path, emit_via, items, load_yaml_safe, v, violation_line  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from editorial_review_checks import check_review, check_top_level, review_counts  # noqa: E402
from editorial_review_text import LENSES, READER_TYPES, REVIEW_FILE, YAML_SUFFIXES, read_target  # noqa: E402

# trace: stats（--lens / --reader-type 越界判定：非法值 ENUM_INVALID）
def check_scope_flags(lens_args, reader_type):
    violations = []
    lenses = []
    for value in lens_args or []:
        if str(value) not in LENSES:
            violations.append(v("ENUM_INVALID", "--lens",
                                "透镜越界：%s（合法集 结构|文风）" % value))
        elif str(value) not in lenses:
            lenses.append(str(value))
    if reader_type not in READER_TYPES:
        violations.append(v("ENUM_INVALID", "--reader-type",
                            "reader_type 越界：%s（合法集 人类|LLM）" % reader_type))
    if not violations and not lenses:
        lenses = list(LENSES)
    return [name for name in LENSES if name in lenses], violations

# trace: stats 子命令（结构地图 + 门禁；只读，exit 0 唯一放行）
def cmd_stats(args):
    root = os.path.abspath(args.project_root)
    out = os.path.abspath(args.output_dir)
    path = os.path.abspath(args.target if os.path.isabs(args.target)
                           else os.path.join(root, args.target))
    show = display_path(path, root)
    lenses, violations = check_scope_flags(args.lens, args.reader_type)
    target = {"path": show, "kind": "yaml" if path.lower().endswith(YAML_SUFFIXES) else "md",
              "lines": 0, "sections": [], "total_words": 0}
    if not violations:
        if not os.path.isfile(path):
            violations.append(v("MISSING_FILE", show,
                                "目标文档不存在：--target 须指向一份 md/yaml 文档"))
        else:
            sections, lines, err = read_target(path, os.path.basename(path))
            if err is not None:
                violations.append(v(err["code"], show, err["msg"]))
            else:
                target["lines"] = lines
                target["sections"] = sections
                target["total_words"] = sum(section["words"] for section in sections)
                if target["total_words"] < 3:
                    violations.append(v("EMPTY_FIELD", show,
                                        "内容不足 3 词（实为 %d 词）：不足以评审，" "词数门槛" % target["total_words"]))
    payload = {
        "ok": not violations,
        "command": "stats",
        "project_root": args.project_root,
        "output_dir": os.path.normpath(out).replace("\\", "/"),
        "violations": violations,
        "warnings": [],
        "counts": {"sections": len(target["sections"]),
                   "words": target["total_words"], "lines": target["lines"]},
        "lenses": lenses,
        "reader_type": args.reader_type,
        "target": target,
    }
    emit_via(payload, args.json, human_stats)
    return 0 if payload["ok"] else 1

# trace: stats 人读态（结构地图 + 末尾汇总行）
def human_stats(payload):
    target = payload["target"]
    if payload["violations"]:
        print("拒绝：目标 %s" % target["path"])
    else:
        print("目标：%s（%s · %d 行 · %d 词）· 透镜 %s · reader_type %s"
              % (target["path"], target["kind"], target["lines"], target["total_words"],
                 "+".join(payload["lenses"]), payload["reader_type"]))
        for section in target["sections"]:
            print("- %s（%d 词）" % (section["name"], section["words"]))
    for item in payload["violations"]:
        print(violation_line(item))
    counts = payload["counts"]
    print("汇总：节 %d · 词 %d · 行 %d · 违规 %d 条（exit %d）"
          % (counts["sections"], counts["words"], counts["lines"],
             len(payload["violations"]), 0 if payload["ok"] else 1))

# trace: check 子命令（台账校验；exit 0 唯一放行）
def cmd_check(args):
    root = os.path.abspath(args.project_root)
    out = os.path.abspath(args.output_dir)
    path = os.path.join(out, REVIEW_FILE)
    show = display_path(path, root)
    violations = []
    checked = []
    data, err = load_yaml_safe(path)
    if data is None and err is None:
        violations.append(v("MISSING_FILE", show,
                            "%s 不存在（先跑一次文稿评审产出 findings 台账）" % REVIEW_FILE))
    elif err is not None:
        violations.append(v("UNPARSABLE_YAML", show, "YAML 解析失败：%s" % err))
    elif not isinstance(data, dict):
        violations.append(v("EMPTY_FIELD", show,
                            "顶层不是映射（须为 project + reviews + revisions）"))
    else:
        violations += check_top_level(data, show)
        reviews = items(data, "reviews")
        seen_ids = set()
        for i, review in enumerate(reviews):
            rid = review.get("id") if isinstance(review, dict) else None
            if args.id and str(rid) != args.id:
                continue
            checked.append(review)
            violations += check_review(i, review, show, root, args.final, seen_ids)
        if args.id and not checked:
            violations.append(v("UNKNOWN_ID", show + ".reviews",
                                "台账里没有 id: %s 的记录" % args.id))
    counts = review_counts(checked)
    payload = {
        "ok": not violations,
        "command": "check",
        "project_root": args.project_root,
        "output_dir": os.path.normpath(out).replace("\\", "/"),
        "final": args.final,
        "violations": violations,
        "warnings": [],
        "counts": counts,
    }
    emit_via(payload, args.json, human_check)
    return 0 if payload["ok"] else 1

# trace: check 人读态（每条违规一行 `CODE where: msg` + 末尾汇总行）
def human_check(payload):
    counts = payload["counts"]
    if payload["ok"]:
        print("PASS：%s 校验通过（review %d · 结构 findings %d · 文风 findings %d）"
              % (payload["output_dir"] + "/" + REVIEW_FILE, counts["reviews"],
                 counts["structure_findings"], counts["prose_findings"]))
    else:
        for item in payload["violations"]:
            print(violation_line(item))
    print("汇总：违规 %d 条 · 警告 %d 条（exit %d）"
          % (len(payload["violations"]), len(payload["warnings"]),
             0 if payload["ok"] else 1))

# trace: 命令行面（--output-dir 必填；引擎不做实例解析/目录推导）
def build_parser():
    ap = argparse.ArgumentParser(
        description="diy-editorial-review 确定性引擎：目标文档结构统计（stats）+ "
                    "editorial-review.yaml 校验（check）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("stats", help="文档结构地图（章节 / 顶层键 + 各节词数）+ 透镜与 "
                                     "reader_type 门禁（只读）")
    s.add_argument("--target", required=True,
                   help="被评审文档（md/yaml；相对路径按 project-root 解析）")
    s.add_argument("--lens", action="append", default=None,
                   help="本次评审的透镜：结构 / 文风（可重复；缺省两透镜全跑）")
    s.add_argument("--reader-type", default="人类",
                   help="读者档：人类（缺省）| LLM")
    s.add_argument("--project-root", default=".", help="项目根（默认 .）")
    s.add_argument("--output-dir", required=True,
                   help="产物目录（必填；由调用方传入，引擎不做实例解析/目录推导）")
    s.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    s.set_defaults(func=cmd_stats)

    k = sub.add_parser("check", help="校验 editorial-review.yaml（schema/枚举/一透镜一槽/"
                                     "序号连续；--final 附加定稿义务）")
    k.add_argument("--project-root", default=".", help="项目根（默认 .）")
    k.add_argument("--output-dir", required=True,
                   help="产物目录（必填；由调用方传入，引擎不做实例解析/目录推导）")
    k.add_argument("--final", action="store_true",
                   help="定稿校验：status 已定稿 + 零 [假设] + 削减估计与 findings 一致")
    k.add_argument("--id", default=None, help="只校该条记录（ER-###）；给出的 ID 不在场 → UNKNOWN_ID")
    k.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    k.set_defaults(func=cmd_check)
    return ap

# trace: 入口（stdout/stderr 固定 UTF-8；退出码由子命令返回）
def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    args = build_parser().parse_args()
    sys.exit(args.func(args))

if __name__ == "__main__":
    main()
