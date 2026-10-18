# -*- coding: utf-8 -*-
"""diy-test-framework 确定性引擎：栈探测（detect）+ 模板渲染落盘（scaffold）+ 台账与 CI 三方对齐校验（check）。

子命令
------
detect   语言无关的栈探测（只读）。清单表（`LANG_MANIFESTS`）判语言与包管理器；移动指示器
         （`.maestro/` / `maestro/` / `app.json` / `Podfile` / `android/app/build.gradle` /
         `*.xcodeproj` / `*.xcworkspace` / `pubspec.yaml` / package.json 的 react-native|expo 依赖）
         **优先判定** 移动端（否则 RN/Expo 工程会被误判为前端）；前后端并存 → 全栈；
         既有框架配置 → `existing.framework`；CI 平台（.github/workflows/*.yml / .gitlab-ci.yml /
         Jenkinsfile / azure-pipelines.yml / .harness/pipeline.yaml / .circleci/config.yml）→
         `existing.ci`；`suggested` = 选型建议（框架 / 平台 / 脚手架 profile）；`templates` 给出
         模板覆盖面（移动端面**无模板覆盖**，据任务书 §5 裁定 5 与 §12.11：HALT + 登记）；
         `git` = 仓库事实（`.git` 在场 / origin 远端名；源 ci/step-01 §1「Git repository required」）；
         `context` = 架构文档与 auth 线索（源 fw/step-01 §2「Check for architecture docs /
         Note auth requirements」）——只报事实，不做推断。
         清单全不命中 → `ok: false` + `MISSING_FILE`（门禁拒绝，零产出）；清单在场但不可解析 →
         `MANIFEST_UNPARSABLE` warning 降级（对齐 e2e.py 先例），探测继续。
scaffold --plan <plan.json>  按 plan 渲染技能内模板写入项目——**只写 plan 声明的路径、只写新增
         文件，不做任何形式的 merge，绝不删除或覆盖任何既有文件**。
         预检零写入：plan 可解析 + 字段齐全（缺席 MISSING_FILE / 不可解析 UNPARSABLE_YAML /
         字段非法 ENTRY_INVALID）+ 每个 `files[].template` 命中技能内实际模板（不命中 MISSING_FILE）
         + 所选模板的占位符取值完备（未取值 EMPTY_FIELD）+ 每个 path 过形态校验（相对、正斜杠、
         无 `.` `..` 段 → ENUM_INVALID，对齐 correct-course `path:` 口径），全部通过才写第一个字节。
         写入阶段逐文件判定三分支：目标不存在 → 原子写（同目录临时文件 + os.replace）；
         目标存在且内容 == 同模板同 plan 的渲染结果（逐字节）→ skip（幂等重入，崩溃后重入同样成立）；
         目标存在且内容不同 → 冲突 → 删除本次已写文件（回滚，删除失败不静默：warning + 残留清单）
         → 整条拒绝 exit 1（`FILE_CONFLICT`，回执列出冲突 path）。
         回执 `pending_commands` = plan `substitutions` 里 INSTALL_CMD / BROWSER_INSTALL /
         LINT_CMD / TEST_CMD 的非空取值（**命令执行归步骤层，本引擎保持纯文件操作**）。
         模板渲染协议：模板首行指令 `# placeholders: A B`（或 `// placeholders:`）声明占位符集，
         该行渲染时剥除；正文出现的 `{{NAME}}` 集须与该声明相等，取值来自 plan `substitutions`；
         渲染 = 逐字节复制 + 占位符替换，不注入时间戳/随机/环境值（同模板同 plan → 同字节）。
check [--final]  台账 schema / 枚举 / files[].path 形态 / 生成文件存在性 / `ci_alignment`（**重扫
         不采信台账**：现场从 test-plan.yaml + CI 文件重算 阻断 命令覆盖与阈值注入，与台账
         `static_check_alignment` 比对，漏 阻断 条目或 `in_ci` 不符 → `CI_MISALIGNED`；
         台账 order 不在 static_checks → `UNKNOWN_ID`；test-plan 缺席 / static_checks 字段缺席 /
         列表为空 → 同一处置：跳过对齐判定 + warning，不阻塞；mode=框架 或 platform=none →
         不适用，后者记 warning）/ **生成物脚本块注入扫描**（现场扫 CI 文件的 `run:` / `script:` /
         `command:` / `sh` 块，块内出现不可信上下文直接插值 → `UNSAFE_INJECTION`；注释行不参与，
         comment 内的示例不算违规）/ `checks` 中 失败 条目 note 非空。
         `--final` 附加：zero `[假设]`、framework 非空、mode=两者|CI 时 ci 段完整
         （platform ∈ 五平台、file 在场、stages / gates / static_check_alignment 齐）、
         `ci.gates` 拉满 P0/P1 双 `100%`（2026-09-15 用户裁定，源为 P1≥95%）。

违规码
------
复用 batch3-contract §3 冻结集：`MISSING_FILE` `UNPARSABLE_YAML` `DUPLICATE_ID` `UNKNOWN_ID`
`ENUM_INVALID` `EMPTY_FIELD` `ENTRY_INVALID` `ASSUMPTION_PRESENT`。
新增（本引擎专用，已在回报中登记）：
  - `FILE_CONFLICT`   scaffold 目标已存在且内容不同（不覆盖既有文件）→ 回滚 + 整条拒绝。
  - `CI_MISALIGNED`   CI 三方对齐失败：阻断 工具命令未出现在 CI 文件、台账 `in_ci` 与现场
                      重算不符、台账漏 阻断 条目、或 CI 文件缺台账 `ci.gates` 阈值字面量。
  - `UNSAFE_INJECTION` 生成物脚本块内直接插值不可信上下文（`${{ inputs.* }}` /
                      `${{ github.event.* }}` / `${{ github.head_ref }}` / `${{ parameters.* }}` /
                      Harness `<+input>` / `<+trigger.*>` / `<+pipeline.variables.*>`）——源
                      steps-v/step-01 §2a 的 FAIL 项；inputs 只能是 DATA 不能是 COMMAND。
沿用先例扩展码：`MANIFEST_UNPARSABLE`（detect 专用降级，B2 diy-e2e-tests 首创同码）。
warning 专用扩展码：`TEMPLATE_UNSUPPORTED`（detect 专用：栈已识别但 `templates/` 未覆盖，
面 = 移动端；告警随门禁 HALT 一起给出，不单列违规）。

分工裁定（任务书 §2.3 / §5）：test-framework.yaml 是新产物类型，不进 diyc.py check 的硬编码
类型集；本引擎沿用领域引擎形态（同 checkpoint.py / e2e.py）。实例解析委托 SKILL.md 侧的
`diyc.py resolve`；本引擎不做 --instance / 白名单 / 目录推导，`--output-dir` 必填。
产物与产物 ID（TF-###）由 LLM 会话铸造，本引擎只校验格式与唯一性。
"""
# trace: B3 diy-test-framework 验收 #3（前置门禁零产出退出）/#4（ID 链接入）/#12（领域引擎接线）
# trace: S-2 AC-2.2 CI 三方对齐（correct-course path: 口径 + test-plan static_checks 链）
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import count_by, count_items, display_path, load_yaml_safe, nonempty, v  # noqa: E402

from test_framework_checks import check_record, scan_ci_injection  # noqa: E402
from test_framework_detect import cmd_detect  # noqa: E402
from test_framework_lib import (  # noqa: E402
    BACKEND_PROFILES, BROWSER_PROFILES, CI_PLATFORMS, CI_TEMPLATES, PLACEHOLDER_RE,
    TF_FILE, TEMPLATES_DIR, emit, out_dir, parse_template, render_template,
    template_abs,
)
from test_framework_scaffold import cmd_scaffold  # noqa: E402


def cmd_check(args):
    root = os.path.abspath(args.project_root)
    out = out_dir(args)
    path = os.path.join(out, TF_FILE)
    show = display_path(path, root)
    violations, warnings, records = [], [], []
    data, err = load_yaml_safe(path)
    if data is None and err is None:
        violations.append(v("MISSING_FILE", show, "%s 不存在（先完成一次测试基建会话）" % TF_FILE))
    elif err is not None:
        violations.append(v("UNPARSABLE_YAML", show, "YAML 解析失败：%s" % err))
    elif not isinstance(data, dict):
        violations.append(v("EMPTY_FIELD", show, "顶层不是映射（须为 project + setups）"))
    else:
        project = data.get("project")
        if project is not None and not isinstance(project, dict):
            violations.append(v("EMPTY_FIELD", show + " project", "project 不是映射"))
        if data.get("revisions") is not None and not isinstance(data.get("revisions"), list):
            violations.append(v("EMPTY_FIELD", show + " revisions", "revisions 不是列表"))
        raw = data.get("setups")
        if raw is None:
            violations.append(v("EMPTY_FIELD", show + " setups", "setups 缺失（无记录写空列表）"))
        elif not isinstance(raw, list):
            violations.append(v("EMPTY_FIELD", show + " setups", "setups 不是列表"))
        else:
            records = raw
            seen = set()
            for i, record in enumerate(records):
                violations += check_record(root, out, i, record, args.final, show, warnings)
                if isinstance(record, dict) and nonempty(record.get("id")):
                    rid = str(record["id"])
                    if rid in seen:
                        violations.append(v("DUPLICATE_ID", "%s.setups[%d].id" % (show, i),
                                            "记录 ID %s 重复（TF ID 稳定不重用）" % rid))
                    seen.add(rid)
            if args.final and not records:
                violations.append(v("EMPTY_FIELD", show + " setups", "--final 要求至少 1 条记录"))
    counts = {"setups": len(records), "by_mode": count_by(records, "mode"),
              "by_status": count_by(records, "status"),
              "by_platform": count_by(records, "ci", "platform"),
              "files": count_items(records, "files"), "checks": count_items(records, "checks"),
              "deferred": count_items(records, "deferred")}
    ok = not violations
    payload = {"ok": ok, "command": "check", "project_root": args.project_root,
               "output_dir": os.path.normpath(out).replace("\\", "/"), "final": args.final,
               "violations": violations, "warnings": warnings, "counts": counts}
    emit(payload, args.json, human_check)
    return 0 if ok else 1


def human_check(payload):
    if payload["ok"]:
        print("PASS：%s 校验通过（setups=%d）" % (TF_FILE, payload["counts"]["setups"]))
        return
    print("FAIL：")
    for item in payload["violations"]:
        print("- %s %s: %s" % (item["code"], item["where"], item["msg"]))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(
        description="diy-test-framework 确定性引擎：栈探测（detect）+ 模板渲染落盘（scaffold）"
                    "+ 台账与 CI 三方对齐校验（check）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("detect", help="栈/语言/包管理器/既有框架/CI 平台探测（只读；无清单 → 拒绝）")
    d.add_argument("--project-root", default=".", help="项目根（默认 .）")
    d.add_argument("--output-dir", required=True,
                   help="产物目录（必填；由调用方传入，引擎不做实例解析/目录推导）")
    d.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    d.set_defaults(func=cmd_detect)

    s = sub.add_parser("scaffold", help="按 plan 渲染模板写项目（只写新文件；冲突即回滚 + 整条拒绝）")
    s.add_argument("--plan", required=True, help="plan JSON 路径（相对 project-root 或绝对路径）")
    s.add_argument("--project-root", default=".", help="项目根（默认 .）")
    s.add_argument("--output-dir", required=True,
                   help="产物目录（必填；由调用方传入，引擎不做实例解析/目录推导）")
    s.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    s.set_defaults(func=cmd_scaffold)

    c = sub.add_parser("check", help="校验 test-framework.yaml（schema/枚举/路径/CI 三方对齐）")
    c.add_argument("--project-root", default=".", help="项目根（默认 .）")
    c.add_argument("--output-dir", required=True,
                   help="产物目录（必填；由调用方传入，引擎不做实例解析/目录推导）")
    c.add_argument("--final", action="store_true",
                   help="定稿校验：zero [假设] + framework 非空 + ci 段完整 + 阈值拉满 100%")
    c.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    c.set_defaults(func=cmd_check)

    args = ap.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
