# -*- coding: utf-8 -*-
"""diy-elicit 确定性引擎（形 B：只读工具，无 check、无写回命令、零写面）。

机制：本技能对当前 section 做迭代式深挖增强——按上下文从方法库 `methods.csv`
（69 方法 / 12 类）选 5 个方法，用户选号执行、`r` 洗牌、`a` 全列、`x` 交还；增强版
留在会话里，落盘归调用方（产物持有者）。引擎只做机械可判的那部分：库加载、随机抽 N
（跨类别优先）、按类筛选、全列——**智能选 5 个的主体是 LLM**，引擎只保证抽样与呈现的
确定性（`r` 洗牌与无参默认走同一条抽样路径）。

  methods [--random N | --category C | --all] [--json]
    --random N     随机抽 N 条（跨类别优先）；N 须为正整数，超过库大小则给全库（打乱序）
    --category C   按类筛选；C 取中文化后 CSV 的 category 列（12 个中文类名），
                   非法值 → exit 1 + ENUM_INVALID
    --all          全列（69 条，库内顺序）
    无参           默认 `--random 5`（首屏 5 个候选）
    --json         单行 JSON 回执（ensure_ascii=False）

形 B 契约（任务书 §2.2「形态分派表」）：只收 `[--json]`——**免** `--project-root` /
`--output-dir`（本引擎无 `{output_dir}` 语义）；库路径按引擎自身位置推算
（`Path(__file__).resolve().parent` → `parent.parent/methods.csv`，即技能目录根、与
`scripts/` 平级），两种安装布局（源码 `diy-coder/skills/` 与安装 `.claude/skills/`）同构。
回执共同键豁免 `project_root` / `output_dir` / `violations` 三键，改为
`{ok, command, counts}`；载荷键 `methods:[{num, category, method_name, description,
output_pattern}]`（成功）与失败键 `msg` 属 SS-028-04「归 W」自定的实现细节——形 B 无
`violations` 位，故诊断码统一走 `msg` 首 token（--json 态）与 stderr 人读行（两种态）。
exit 码：0 唯一放行；筛选类非法值 → 1；argparse 级用法错误 → 2。人读态 = 每条方法一行
`N. 方法名｜类名｜描述｜output_pattern` + 末尾一行 `OK methods <计数摘要>`；失败时 stderr
一行中文诊断（含码）、stdout 一行结论。

只读保证：本模块只用标准库（argparse / csv / json / os / random / sys），**无任何写盘
设施**——不开只写句柄、不做原子替换、不建临时文件，命令面只有 `methods` 一条。

规则来源：诊断码取 batch3-contract §3 冻结集（`MISSING_FILE` / `EMPTY_FIELD` /
`ENUM_INVALID`），**无新增码**。
"""
import argparse
import csv
import io
import json
import os
import random
import sys

COLUMNS = ("num", "category", "method_name", "description", "output_pattern")
METHODS_FILE = "methods.csv"
DEFAULT_CANDIDATES = 5
LIBRARY_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            os.pardir, METHODS_FILE)
LIBRARY_PATH = os.path.normpath(LIBRARY_PATH)


# trace: B4 diy-elicit 方法库装载（只读）；返回 (rows, error)；error = (code, msg)
def load_library(path):
    if not os.path.isfile(path):
        return [], ("MISSING_FILE", "方法库不在场：%s" % path)
    rows, bad_lines = [], []
    try:
        with io.open(path, encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            missing = [name for name in COLUMNS if name not in (reader.fieldnames or [])]
            if missing:
                return [], ("EMPTY_FIELD", "方法库表头缺列：%s" % " / ".join(missing))
            for line_no, raw in enumerate(reader, start=2):
                row = dict((name, (raw.get(name) or "").strip()) for name in COLUMNS)
                if not all(row[name] for name in COLUMNS):
                    bad_lines.append(line_no)
                    continue
                try:
                    row["num"] = int(row["num"])
                except ValueError:
                    bad_lines.append(line_no)
                    continue
                rows.append(row)
    except (OSError, UnicodeDecodeError) as exc:
        return [], ("MISSING_FILE", "方法库不可读：%s" % exc)
    if bad_lines:
        return [], ("EMPTY_FIELD", "方法库关键列为空或 num 非数字（CSV 行号）：%s"
                    % " / ".join(str(n) for n in bad_lines))
    if not rows:
        return [], ("EMPTY_FIELD", "方法库为空（0 条）")
    return rows, None


# trace: B4 diy-elicit 随机抽 N（跨类别优先：先每类取一条，再补足；同一条不重复）
def sample_cross_category(rows, count):
    order = list(range(len(rows)))
    random.shuffle(order)
    picked, used_categories, taken = [], set(), set()
    for index in order:
        if len(picked) >= count:
            break
        category = rows[index]["category"]
        if category in used_categories:
            continue
        used_categories.add(category)
        taken.add(index)
        picked.append(rows[index])
    for index in order:
        if len(picked) >= count:
            break
        if index in taken:
            continue
        picked.append(rows[index])
    return picked


# trace: B4 diy-elicit 回执输出（--json 单行 / 人读行）
def emit(payload, as_json, human_lines):
    if as_json:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        for line in human_lines:
            print(line)


# trace: B4 diy-elicit 失败收口（诊断码走 msg 首 token + stderr 人读行；形 B 无 violations 位）
def refuse(args, error, counts):
    code, msg = error
    print("%s %s" % (code, msg), file=sys.stderr)
    payload = {"ok": False, "command": "methods", "counts": counts,
               "msg": "%s：%s" % (code, msg)}
    emit(payload, args.json, ["未通过 methods：%s（exit 1）" % msg])
    return 1


# trace: B4 diy-elicit methods 子命令（库加载 / 随机抽 N / 按类筛选 / 全列；只读）
def cmd_methods(args):
    rows, error = load_library(LIBRARY_PATH)
    categories = sorted({row["category"] for row in rows})
    counts = {"total": len(rows), "categories": len(categories), "returned": 0}
    if error is None and args.category is not None and args.category not in categories:
        error = ("ENUM_INVALID", "--category 的值不在方法库枚举内：%s；可选值：%s"
                 % (args.category, " / ".join(categories)))
    if error is not None:
        return refuse(args, error, counts)
    if args.all:
        picked = list(rows)
    elif args.category is not None:
        picked = [row for row in rows if row["category"] == args.category]
    else:
        want = args.random if args.random is not None else DEFAULT_CANDIDATES
        picked = sample_cross_category(rows, min(want, len(rows)))
    counts = {"total": len(rows), "categories": len(categories), "returned": len(picked)}
    payload = {"ok": True, "command": "methods", "counts": counts, "methods": picked}
    human = ["%d. %s｜%s｜%s｜%s" % (row["num"], row["method_name"], row["category"],
                                    row["description"], row["output_pattern"])
             for row in picked]
    human.append("OK methods 返回 %d 条 / 库 %d 条 · %d 类"
                 % (counts["returned"], counts["total"], counts["categories"]))
    emit(payload, args.json, human)
    return 0


# trace: B4 diy-elicit 正整数字面（非法 N → argparse 用法错误 exit 2）
def positive_int(text):
    try:
        value = int(text)
    except ValueError:
        raise argparse.ArgumentTypeError("须为正整数：%r" % text)
    if value <= 0:
        raise argparse.ArgumentTypeError("须为正整数：%r" % text)
    return value


# trace: B4 diy-elicit 命令行面（形 B：只收 --json；筛选三旗标互斥）
def build_parser():
    parser = argparse.ArgumentParser(
        description="diy-elicit 只读方法库引擎：加载 / 随机抽 N（跨类别优先）/ 按类筛选 / 全列"
                    "（形 B：无 check、无写回、零写面）")
    sub = parser.add_subparsers(dest="cmd", required=True)
    methods = sub.add_parser("methods", help="方法库加载 / 随机抽 N / 按类筛选 / 全列（只读）")
    group = methods.add_mutually_exclusive_group()
    group.add_argument("--random", type=positive_int, metavar="N",
                       help="随机抽 N 条（跨类别优先；缺省 5；N 超库大小则给全库）")
    group.add_argument("--category", metavar="C",
                       help="按类筛选（取库内中文类名；非法值 exit 1 + ENUM_INVALID）")
    group.add_argument("--all", action="store_true", help="全列方法库（69 条，库内顺序）")
    methods.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    methods.set_defaults(func=cmd_methods)
    return parser


# trace: B4 diy-elicit 入口（stdout/stderr 固定 UTF-8；退出码由子命令返回）
def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    args = build_parser().parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
