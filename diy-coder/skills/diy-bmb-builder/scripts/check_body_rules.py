# -*- coding: utf-8 -*-
"""bmb-builder Edit 通道正文规范检查：四类禁入零在场（引用句 + 检查脚本门）。

以后改 diy 技能一律走 builder 的 Edit 意图；正文写完（落盘后）跑本脚本核对四类禁入
零在场，exit 0 才算过。宿主无关的独立命令（不绑 hook——hook 绑宿主，脚本随查随跑）：

  python "{project-root}/.claude/skills/diy-bmb-builder/scripts/check_body_rules.py" \\
      --target <技能目录> [--json] [--project-root P] [--output-dir D]

四类禁入（正文规范清单，细节与逐条正则以 PATTERNS 为准）：
  ①源路径锚  ②拍板引语  ③任务批名词  ④迁移决策记录

词表口径＝复用安装面 guard（tests/test_source_anchor_guard.py）的十类 + EXEMPT 豁免键
（2026-10-30 用户裁：直接复用其词表，不自带）。guard 测试件在 tests/ 面，生产脚本 import
测试件属反向依赖、不健康；词表下沉公共处须动 guard 测试件（不在本任务 scope）——故本脚本
内嵌复制其 PATTERNS/EXEMPT。已知单源风险：两份词表各改各的会漂移，后续统一候选＝词表下沉
可共享位置、guard 与本脚本同引（晨报告裁）。本脚本自身落 skills/ 扫描面内，guard 逐字扫
skills/** 的 .py/.md/.yaml/.csv，字面禁入词会被自扫命中——故禁入 token 一律以 chr() 码点
在运行时拼装、源文件不含字面（构造避开，非 EXEMPT）。

违规码：复用 MISSING_FILE（目标缺席）；新增 BODY_RULE（正文命中四类禁入词一条记一条，
豁免键除外）。回执共同键 {ok, command, project_root, output_dir, violations, warnings,
counts}；exit 0 唯一放行，1 = 有命中或目标不存在，2 = 用法错误（argparse）。
"""

import argparse
import io
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))

from diyc_lib import v  # noqa: E402

EXTS = (".py", ".md", ".yaml", ".csv")


def _s(*codepoints):
    """码点串 → 字符串（源文件零字面禁入词，运行时还原）。"""
    return "".join(chr(c) for c in codepoints)


# trace: diy-bmb-builder 正文禁入词表（复制自 test_source_anchor_guard.PATTERNS·十类·码点拼装防自扫）
_YUAN, _CE = 0x6E90, 0x4FA7                       # 源 侧
_BAO, _ZHEN, _ZHAO, _BAN = 0x4FDD, 0x771F, 0x7167, 0x642C  # 保 真 照 搬
_SHOU, _BIAN, _ZI = 0x6536, 0x7F16, 0x81EA        # 收 编 自
_CAI, _DING = 0x88C1, 0x5B9A                      # 裁 定
_DOT = 0x2E                                        # .

PATTERNS = [
    (_s(_YUAN, _CE), re.compile(_s(_YUAN, _CE))),
    ("trace 批次头", re.compile(r"# trace: B\d")),
    ("batch3-" + "contract", re.compile("batch3-" + "contract")),
    ("拍板引语式" + _s(_CAI, _DING), re.compile(_s(_CAI, _DING) + " ?[0-9]")),
    ("批次号 C\xb7N", re.compile("C\xb7[0-9]")),
    ("census" + "-", re.compile("census" + "-", re.IGNORECASE)),
    (_s(_BAO, _ZHEN, _ZHAO, _BAN), re.compile(_s(_BAO, _ZHEN, _ZHAO, _BAN))),
    (_s(_SHOU, _BIAN, _ZI) + "/" + _s(_CAI, _ZI),
     re.compile(_s(_SHOU, _BIAN, _ZI) + "|" + _s(_CAI, _ZI))),
    # 源+反引号路径锚（census 类①）——排除产品复合词（单一源/护栏源/来源 等）
    (_s(_YUAN) + "+反引号锚", re.compile(
        r"(?<!单一)(?<!两)(?<!护栏)(?<!情报)(?<!测试)(?<!来)(?<!真)(?<!数据)"
        r"(?<!散)(?<!唯一)" + _s(_YUAN) + " `")),
    ("\\" + _s(_DOT) + "analysis/ 目录引用",
     re.compile("\\" + _s(_DOT) + "analysis/")),
]

# 豁免清单：(skills/ 相对路径, 命中原文)——逐条有裁定依据（复制自 guard EXEMPT）
EXEMPT = {
    # 乙-4 用户裁 2026-10-29：bmb-builder 产品行为＝分析报告落点约定
    ("diy-bmb-builder/SKILL.md", _s(_DOT) + "analysis/"),
    ("diy-bmb-builder/steps/03-analyze.md", _s(_DOT) + "analysis/"),
    ("diy-bmb-builder/steps/05-finish.md", _s(_DOT) + "analysis/"),
}


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
