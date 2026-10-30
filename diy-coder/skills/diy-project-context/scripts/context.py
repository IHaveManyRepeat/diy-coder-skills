# -*- coding: utf-8 -*-
"""diy-project-context 确定性引擎：棕地扫描（scan）+ project-context.yaml 校验（check）。

来源与分工（能力蓝本 = bmad-document-project + bmad-generate-project-context）：
  scan   只读扫描，绝不写文件：部件探测（多部件/单仓识别）、项目类型分类
         （documentation-requirements.csv 的 key_file_patterns 判据）、清单解析
         （package.json / pyproject.toml / Cargo.toml / go.mod / pom.xml / requirements.txt /
         pubspec.yaml / composer.json / *.csproj 按存在性探测）。语言无关：先探测再解析，
         未知清单降级「存在但未解析」+ MANIFEST_UNPARSED warning，不崩、不假设特定工具链。
         另有既有文档发现（README/ARCHITECTURE/API/DEPLOYMENT/docs 模式）与源码树渲染
         （深度/条目上限为内置常量）。关键目录回执 `critical_dirs` 取
         documentation-requirements.csv 的 critical_directories 列（按部件类型照录），
         只报**实际存在**的那些（深入档的阅读面，见 CRITICAL_DIRS）。
         scan_level 三档：快速=模式分析不读源码；
         深入=加源文件计数（读面 = `critical_dirs`）；穷尽=再加 LOC（读文件，受文件数/字节上限约束）。
         部件/类型判定是启发式——LLM 在步骤 01 与用户确认。
  check  校验 {output_dir}/project-context.yaml：schema / 枚举 / scan.parts 非空 /
         rules 的 PC-### 唯一与类别枚举；--previous 比对旧稿 PC-### 集合（rescan 防丢规则，
         旧有新无 → ID_UNSTABLE）；--final 附加定稿义务（zero [假设]、rules 非空且每条
         rule/why/where 非空、stack 非空）。exit 0 唯一放行。

新码登记（套件冻结集之外）：
  - 违规码：无——全部复用冻结集（MISSING_FILE / UNPARSABLE_YAML / ENUM_INVALID / EMPTY_FIELD /
    DUPLICATE_ID / UNKNOWN_ID / ID_UNSTABLE / ASSUMPTION_PRESENT）。
  - warning 码：MANIFEST_UNPARSED（探测到清单但无内置解析器或解析失败：降级 + 结构化 warning，
    由 LLM 在步骤 01/02 向用户补齐，绝不静默）。

禁手写实例解析：引擎不做 --instance / 白名单 / 目录推导；--output-dir 必填，
由调用方传入（SKILL.md 从 diyc.py resolve 取）。进度状态
落 {output_dir}/project-context.yaml 的 scan 字段，不建任何状态散文件。
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from context_checks import cmd_check  # noqa: E402
from context_lib import SCAN_LEVELS  # noqa: E402
from context_scan import cmd_scan  # noqa: E402


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(
        description="diy-project-context 确定性引擎：棕地扫描（scan，只读）+ project-context.yaml 校验（check）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("scan", help="扫描棕地项目：部件/类型/清单/既有文档/源码树（只读，不写产物）")
    s.add_argument("--project-root", default=".", help="项目根（默认 .）")
    s.add_argument("--output-dir", required=True,
                   help="产物目录（必填；由调用方传入，引擎不做实例解析/目录推导）")
    s.add_argument("--level", default="快速", choices=list(SCAN_LEVELS),
                   help="扫描档位：快速=模式分析（默认）/ 深入=加文件计数 / 穷尽=加 LOC")
    s.add_argument("--part", default=None, help="只扫指定部件（部件名以扫描回执为准）")
    s.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    s.set_defaults(func=cmd_scan)

    c = sub.add_parser("check", help="校验 project-context.yaml（schema/枚举/ID；--final 附加定稿义务）")
    c.add_argument("--project-root", default=".", help="项目根（默认 .）")
    c.add_argument("--output-dir", required=True,
                   help="产物目录（必填；由调用方传入，引擎不做实例解析/目录推导）")
    c.add_argument("--final", action="store_true",
                   help="定稿校验：rules 非空且 rule/why/where 非空 + stack 非空 + 零假设")
    c.add_argument("--previous", default=None,
                   help="旧稿路径（rescan 防丢规则：比对 PC-### 集合，旧有新无 → ID_UNSTABLE）")
    c.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    c.set_defaults(func=cmd_check)

    args = ap.parse_args()
    sys.exit(args.func(args))

if __name__ == "__main__":
    main()
