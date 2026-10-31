# -*- coding: utf-8 -*-
"""bmb-builder Edit 通道正文规范检查：四类禁入零在场（引用句 + 检查脚本门）。

以后改 diy 技能一律走 builder 的 Edit 意图；正文写完（落盘后）跑本脚本核对四类禁入
零在场，exit 0 才算过。宿主无关的独立命令（不绑 hook——hook 绑宿主，脚本随查随跑）：

  python "{project-root}/.claude/skills/diy-bmb-builder/scripts/check_body_rules.py" \\
      --target <技能目录> [--json] [--project-root P] [--output-dir D]

四类禁入（正文规范清单，细节与逐条正则以 PATTERNS 为准）：
  ①源路径锚  ②拍板引语  ③任务批名词  ④迁移决策记录

词表口径＝单源（2026-10-31 用户裁·词表下沉）：PATTERNS/EXEMPT 下沉
diyc_body_rules.py（diy-tools 共享底座·diyc* 前缀跨技能 import 豁免在案），
安装面 guard 与本脚本同引，改词只改彼处。公共表自身落 skills/ 扫描面内，
禁入 token 一律以 chr() 码点运行时拼装、源文件不含字面（构造避开，非 EXEMPT）。

违规码：复用 MISSING_FILE（目标缺席）；新增 BODY_RULE（正文命中四类禁入词一条记一条，
豁免键除外）。回执共同键 {ok, command, project_root, output_dir, violations, warnings,
counts}；exit 0 唯一放行，1 = 有命中或目标不存在，2 = 用法错误（argparse）。
"""

import argparse
import io
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))

from diyc_lib import v  # noqa: E402
from diyc_body_rules import EXEMPT, PATTERNS  # noqa: E402  词表单源（diy-tools 共享底座）

EXTS = (".py", ".md", ".yaml", ".csv")


# trace: diy-bmb-builder 正文扫描（walk 目标技能树；rel 口径对齐 guard＝技能名/相对路径）
def iter_files(target):
    for dirpath, dirnames, filenames in os.walk(target):
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        for name in filenames:
            if name.endswith(EXTS):
                yield os.path.join(dirpath, name)


# trace: diy-bmb-builder 单技能正文检查（命中逐条 BODY_RULE；豁免键过滤）
def cmd_check_body(args):
    payload = {
        "ok": False, "command": "check-body", "project_root": args.project_root,
        "output_dir": os.path.normpath(os.path.abspath(args.output_dir)).replace("\\", "/"),
        "violations": [], "warnings": [], "counts": {"hits": 0},
    }
    target = os.path.abspath(args.target)
    if not os.path.isdir(target):
        payload["violations"].append(v("MISSING_FILE", args.target, "技能目录不存在"))
        return _finish(payload, args)
    skill_name = os.path.basename(os.path.normpath(target))
    hits = []
    for path in iter_files(target):
        rel = skill_name + "/" + os.path.relpath(path, target).replace(os.sep, "/")
        try:
            text = io.open(path, encoding="utf-8").read()
        except (UnicodeDecodeError, OSError):
            continue
        for label, pattern in PATTERNS:
            for match in pattern.finditer(text):
                anchor = match.group(0)
                if (rel, anchor) in EXEMPT:
                    continue
                hits.append(v("BODY_RULE", rel, "命中「%s」：%r" % (label, anchor)))
    payload["violations"] = hits
    payload["counts"] = {"hits": len(hits)}
    return _finish(payload, args)


# trace: diy-bmb-builder 回执收尾（ok 由 violations 决定；--json 单行 / 人读行）
def _finish(payload, args):
    payload["ok"] = not payload["violations"]
    if args.json:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        for item in payload["violations"]:
            print("%s %s: %s" % (item["code"], item["where"], item["msg"]))
        print("汇总：违规 %d 条 · 命中 %d（exit %d）"
              % (len(payload["violations"]), payload["counts"]["hits"],
                 0 if payload["ok"] else 1))
    return 0 if payload["ok"] else 1


# trace: diy-bmb-builder 命令行面（--target 必给；--json 单行回执）
def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(
        description="bmb-builder Edit 通道正文规范检查：四类禁入零在场门")
    ap.add_argument("--target", required=True, help="技能目录")
    ap.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    ap.add_argument("--project-root", default=".", help="项目根（默认 .）")
    ap.add_argument("--output-dir", default=".", help="本次运行的产物目录（回执口径）")
    args = ap.parse_args()
    try:
        return cmd_check_body(args)
    except Exception as e:  # 未预期异常：不静默、不裸奔（对齐引擎 INTERNAL_ERROR 口径）
        sys.stderr.write("诊断：内部错误 %s：%s\n" % (type(e).__name__, e))
        print(json.dumps({
            "ok": False, "command": "check-body",
            "project_root": args.project_root,
            "output_dir": os.path.normpath(os.path.abspath(args.output_dir)).replace("\\", "/"),
            "violations": [v("INTERNAL_ERROR", args.target, "%s: %s" % (type(e).__name__, e))],
            "warnings": [], "counts": {"hits": 0},
        }, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    sys.exit(main())
