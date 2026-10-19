# -*- coding: utf-8 -*-
"""diy-spec 确定性引擎：spec-kernel.yaml 的骨架铸造（new）与校验（check）。

子命令：
  new    --slug S [--title T]：建一条记录骨架并 **铸造 `SK-###`**（三位零填充、取既有
         最大值 + 1，不重号不重用）；同 slug 已存在 → 拒绝并指出既有 `SK-xxx`（更新走
         记录就地编辑，不新建——「同一 slug = 同一记录」）。原子写。
  check  [--final] [--previous PATH] [--id SK-xxx]：五字段非空 / CAP 结构（intent +
         success 双非空、`CAP-N` 格式）/ CAP ID 记录内唯一 / slug 唯一 / companions 与
         sources 路径在场性（相对 project-root）/ artifacts 条目结构 / verdict 形状；
         **`--previous`**：按 slug 配对旧稿，旧稿 CAP 集合中「旧有新无且未标
         `retired: true`」→ `ID_UNSTABLE`（退役豁免同看两稿：旧稿该 CAP 标 retired，
         或新稿仍留该 id 且标 retired）；`--final` 附加：`status: 已定稿` + 零 `[假设]`
         + `verdict` 两段非空（自校验义务已履行）。exit 0 唯一放行。

分工裁定（任务书 §2.3）：spec-kernel 是新产物类型，不进 diyc.py check 的硬编码类型集；
本引擎沿用领域引擎形态，契约同构：exit 0 唯一放行 / `--json` 单行回执 /
`violations[{code, where, msg}]` + `counts`；写回命令回执另含 `updated`。违规码全部复用
batch3-contract §3 冻结集（**未新增码**）：`MISSING_FILE` / `UNPARSABLE_YAML` /
`DUPLICATE_ID` / `UNKNOWN_ID` / `ENUM_INVALID` / `EMPTY_FIELD` / `ASSUMPTION_PRESENT` /
`STATUS_MISMATCH` / `ID_UNSTABLE`。

事实裁定（B4 建议档归 W 项，回报第 5 项）：
  · #42「五字段非空」的判据 = `why` / `capabilities`（≥1 条且 intent + success 双非空）/
    `non_goals`（≥1 条，Spec Law 4）/ `success_signal` 逐字非空；`constraints` **键在场
    且为列表**，空列表放行——Spec Law 3 是品质判据（凑一条不淘汰设计的约束 = decoration，
    比空列表更坏），条数不设门。
  · #41 `retired` 条目的字段义务 = 退役条目的 `id` / `intent` / `success` **不失义务**
    （痕迹的价值在于「退役的是什么」）；`retired` 出现时须为布尔；退役条目仍计入 CAP ID
    唯一性与 `--previous` 在场判定。
  · #21 `--id` 缺席 → 校验全部记录（文件级：project / revisions / 记录 ID 唯一 / slug 唯一
    照查）；给出 → 记录内容面只门该条，ID 不在稿内报 `UNKNOWN_ID`。
  · #40 `--previous` 的比对范围与匹配键 = **按 `slug` 配对**（CAP-N 是记录内命名空间，
    跨记录并集比对无意义），逐记录比 CAP 集合；旧稿有、新稿整条 slug 消失 → 同判
    `ID_UNSTABLE`（整条记录的 CAP 一并丢失）。

禁手写实例解析：引擎不做 `--instance` / 白名单 / 目录推导；`--output-dir` 必填（每个子命令
各自接收），由调用方传入（SKILL.md 从 `diyc.py resolve` 取）。内容面（五字段 / CAP /
artifacts / verdict）由 LLM 直编 YAML；引擎只做骨架与校验——**`CAP-N` 由 LLM 铸造**、
引擎校验格式与唯一性（任务书 §2.4 铸造权分派）。
"""
# trace: B4 diy-spec 验收 #2（产物 schema + SK-### 稳定前缀）/#3（门禁零产出）/#4（CAP-N + retired + --previous）/12b（终门指向自带引擎）
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import display_path, emit_via, load_yaml_safe, nonempty, now, project_name, save_yaml_atomic, today, v  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from spec_kernel_checks import SK_RE, SPEC_FILE, check_previous, check_record  # noqa: E402

# trace: B4 diy-spec 验收 #2/#3（SK-### 由引擎铸造；同 slug 拒绝 = 零写入门禁）
def cmd_new(args):
    root = os.path.abspath(args.project_root)
    out = args.output_dir
    path = os.path.join(out, SPEC_FILE)
    show = display_path(path, root)
    violations, warnings, counts = [], [], {}
    if not nonempty(args.slug):
        violations.append(v("EMPTY_FIELD", "new --slug",
                            "slug 缺失（无头不可推 → 拒绝；交互式应先在会话里问一次）"))
    data, err = load_yaml_safe(path)
    if err is not None:
        violations.append(v("UNPARSABLE_YAML", show,
                            "YAML 解析失败，拒绝写入以免覆盖：%s" % err))
    elif data is not None and not isinstance(data, dict):
        violations.append(v("EMPTY_FIELD", show,
                            "顶层不是映射（须为 project + specs + revisions），拒绝写入"))
    elif nonempty(args.slug):
        if data is None:
            name, _w = project_name(root)
            if _w:
                warnings.append(_w)
            stamp = now()
            data = {"project": {"name": name, "created": stamp, "updated": stamp},
                    "specs": [], "revisions": []}
        existing = [r for r in (data.get("specs") or []) if isinstance(r, dict)]
        hit = [r for r in existing if str(r.get("slug")) == str(args.slug)]
        if hit:
            violations.append(v("DUPLICATE_ID", show + " specs[%s]" % args.slug,
                                "slug %s 已存在（%s）：同一 slug = 同一记录——更新走就地"
                                "编辑（保持该 id、CAP 保留、新 CAP 取下一个未用号），"
                                "或用另一个 slug 新建" % (args.slug, hit[0].get("id"))))
        else:
            numbers = [int(str(r["id"])[3:]) for r in existing
                       if nonempty(r.get("id")) and SK_RE.fullmatch(str(r["id"]))]
            sid = "SK-%03d" % (max(numbers) + 1 if numbers else 1)
            record = {"id": sid, "slug": str(args.slug),
                      "title": args.title if nonempty(args.title) else "",
                      "status": "草稿", "date": today(), "why": "",
                      "capabilities": [], "constraints": [], "non_goals": [],
                      "success_signal": "", "assumptions": [], "open_questions": [],
                      "companions": [], "sources": [], "artifacts": [],
                      "verdict": {"coherence": "",
                                  "preservation": {"dropped": [], "note": ""}}}
            data["specs"] = list(data.get("specs") or []) + [record]
            data["project"] = dict(data.get("project") or {})
            data["project"]["updated"] = now()
            if not nonempty(data["project"].get("created")):
                data["project"]["created"] = now()
            try:
                os.makedirs(out, exist_ok=True)
                save_yaml_atomic(path, data)
            except OSError as e:
                violations.append(v("MISSING_FILE", show, "写盘失败（零写入）：%s" % e))
            else:
                counts = {"specs": len(data["specs"]),
                          "capabilities": 0, "id": sid}
                counts["updated"] = data["project"]["updated"]
    payload = receipt("new", args, out, not violations, violations, warnings)
    payload["counts"] = counts
    if not violations:
        payload["updated"] = counts.pop("updated")
    emit_via(payload, args.json, human_new)
    return 0 if not violations else 1

def cmd_check(args):
    root = os.path.abspath(args.project_root)
    out = args.output_dir
    path = os.path.join(out, SPEC_FILE)
    show = display_path(path, root)
    violations, warnings = [], []
    counts = {"records": 0, "capabilities": 0, "retired": 0, "companions": 0,
              "sources": 0, "artifacts": 0}
    data, err = load_yaml_safe(path)
    if data is None and err is None:
        violations.append(v("MISSING_FILE", show,
                            "%s 不存在（先跑 new 建记录骨架）" % SPEC_FILE))
    elif err is not None:
        violations.append(v("UNPARSABLE_YAML", show, "YAML 解析失败：%s" % err))
    elif not isinstance(data, dict):
        violations.append(v("EMPTY_FIELD", show,
                            "顶层不是映射（须为 project + specs + revisions）"))
    else:
        project = data.get("project")
        if project is not None and not isinstance(project, dict):
            violations.append(v("EMPTY_FIELD", show + " project", "project 不是映射"))
        revisions = data.get("revisions")
        if revisions is not None and not isinstance(revisions, list):
            violations.append(v("EMPTY_FIELD", show + " revisions", "revisions 不是列表"))
        raw_records = data.get("specs")
        scope_slugs = None
        if raw_records is None:
            violations.append(v("EMPTY_FIELD", show + " specs",
                                "specs 缺失（集合形态；无记录写空列表）"))
        elif not isinstance(raw_records, list):
            violations.append(v("EMPTY_FIELD", show + " specs", "specs 不是列表"))
        else:
            counts["records"] = len(raw_records)
            seen_ids, seen_slugs = {}, {}
            for i, record in enumerate(raw_records):
                if not isinstance(record, dict):
                    continue
                rid, slug = record.get("id"), record.get("slug")
                if nonempty(rid):
                    if str(rid) in seen_ids:
                        violations.append(v("DUPLICATE_ID", "%s specs[%d].id" % (show, i),
                                            "记录 ID %s 重复（SK ID 稳定不重用）" % rid))
                    seen_ids[str(rid)] = i
                if nonempty(slug):
                    if str(slug) in seen_slugs:
                        violations.append(v("DUPLICATE_ID", "%s specs[%d].slug" % (show, i),
                                            "slug %s 重复（同一 slug = 同一记录，"
                                            "更新走就地编辑）" % slug))
                    seen_slugs[str(slug)] = i
            if args.id and str(args.id) not in seen_ids:
                violations.append(v("UNKNOWN_ID", show + " specs",
                                    "--id %s 在稿内不存在" % args.id))
            else:
                if args.id:
                    target = raw_records[seen_ids[str(args.id)]]
                    scope_slugs = {str(target.get("slug"))} \
                        if nonempty(target.get("slug")) else set()
                for i, record in enumerate(raw_records):
                    if args.id and (not isinstance(record, dict)
                                    or str(record.get("id")) != str(args.id)):
                        continue
                    part = check_record(i, record, args.final, root, show, violations)
                    for key, value in part.items():
                        counts[key] += value
            if args.final and not raw_records:
                violations.append(v("EMPTY_FIELD", show + " specs",
                                    "--final 要求至少 1 条记录"))
            if args.previous:
                check_previous(data, args.previous, root, show, violations, scope_slugs)
    payload = receipt("check", args, out, not violations, violations, warnings)
    payload["counts"] = counts
    emit_via(payload, args.json, human_check)
    return 0 if not violations else 1

def receipt(command, args, out, ok, violations, warnings):
    return {"ok": ok, "command": command, "project_root": args.project_root,
            "output_dir": os.path.normpath(out).replace("\\", "/"),
            "violations": violations, "warnings": warnings, "counts": {}}

def human_new(payload):
    if payload["ok"]:
        print("OK new：铸造 %s（记录 %d 条 · 文件 %s）"
              % (payload["counts"]["id"], payload["counts"]["specs"],
                 payload["output_dir"] + "/" + SPEC_FILE))
    else:
        for item in payload["violations"]:
            print("%s %s: %s" % (item["code"], item["where"], item["msg"]))
    for item in payload["warnings"]:
        print("警告 %s %s: %s" % (item["code"], item["where"], item["msg"]))
    print("汇总：违规 %d 条 · 警告 %d 条（exit %d）"
          % (len(payload["violations"]), len(payload["warnings"]),
             0 if payload["ok"] else 1))

def human_check(payload):
    counts = payload["counts"]
    if payload["ok"]:
        print("PASS：%s/%s 校验通过（记录 %d 条 · CAP %d 个 · 退役 %d 个）"
              % (payload["output_dir"], SPEC_FILE, counts["records"],
                 counts["capabilities"], counts["retired"]))
    else:
        for item in payload["violations"]:
            print("%s %s: %s" % (item["code"], item["where"], item["msg"]))
    for item in payload["warnings"]:
        print("警告 %s %s: %s" % (item["code"], item["where"], item["msg"]))
    print("汇总：违规 %d 条 · 警告 %d 条（exit %d）"
          % (len(payload["violations"]), len(payload["warnings"]),
             0 if payload["ok"] else 1))

def build_parser():
    ap = argparse.ArgumentParser(
        description="diy-spec 确定性引擎：spec-kernel.yaml 骨架铸造（new）与校验（check）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    n = sub.add_parser("new", help="建记录骨架并铸造 SK-###（同 slug 已存在 → 拒绝）")
    n.add_argument("--project-root", default=".", help="项目根（默认 .）")
    n.add_argument("--output-dir", required=True,
                   help="产物目录（必填；由调用方传入，引擎不做实例解析/目录推导）")
    n.add_argument("--slug", required=True,
                   help="记录唯一键（同一 slug = 同一记录；源带 slug 则继承）")
    n.add_argument("--title", default=None, help="标题（可后补）")
    n.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    n.set_defaults(func=cmd_new)

    c = sub.add_parser("check", help="校验 spec-kernel.yaml（五字段/CAP/路径；--final 附加定稿义务）")
    c.add_argument("--project-root", default=".", help="项目根（默认 .）")
    c.add_argument("--output-dir", required=True,
                   help="产物目录（必填；由调用方传入，引擎不做实例解析/目录推导）")
    c.add_argument("--final", action="store_true",
                   help="定稿校验：status: 已定稿 + 零 [假设] + verdict 两段非空")
    c.add_argument("--previous", default=None,
                   help="旧稿路径（改写既有记录前留档；按 slug 比对 CAP 集合）")
    c.add_argument("--id", default=None, help="只门一条记录（SK-xxx；文件级校验照查）")
    c.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    c.set_defaults(func=cmd_check)
    return ap

def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    args = build_parser().parse_args()
    sys.exit(args.func(args))

if __name__ == "__main__":
    main()
