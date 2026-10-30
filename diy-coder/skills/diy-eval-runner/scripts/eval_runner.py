# -*- coding: utf-8 -*-
"""diy-eval-runner 确定性引擎：技能评测四模式（run）+ 结果聚合（aggregate）+ run 目录终门（check）+ memlog（mlog）。

子命令：
  run        四模式执行器（baseline / variant / quality / trigger，`--mode` 可重复）。
             baseline = 同一输入跑两 config（`skill` 已 stage 技能 / `bare` 什么都不 stage，
             裸模型是长期地板）；variant = 全量 vs `--variant-path` 精简最小版；quality =
             单 config（`skill`）+ 由调用方派只读 grader 逐条判 rubric；trigger = 合成技能
             （唯一名后缀）+ 逐问句真跑，**只认 `tool_use`**。
             产物 = `{output_dir}/eval-runs/<YYYYMMDD-HHMMSS>-<label>/`（**零 YAML 主产物**）。
  aggregate  对 run 目录下的 timing.json 记录按 config 分组，算 mean / **样本标准差（n-1
             贝塞尔校正）** / min / max；`--against` 指定基准 config（缺省 `bare`）给
             delta 与 delta_pct。`--self-test` 用固定夹具校验公式。
  check      run 目录结构合规 + 结果自洽（execution-summary 计数与实际目录一致、
             quality 的 grading.json 在场且举证非空、trigger 的 detection 必须是 tool_use），
             并报累计 run 目录数。**终门 = check --run-dir D**——run 目录追加式，无「定稿态」，
             故本引擎不做 `--final` 旗标。
  mlog       memlog 三子命令（init / append / set-complete）：原子追加、只追加、每次操作
             恒发一行 JSON ack `{ok, file, n, appended}`（`--dir D` + `--file NAME` 由调用方显式给，不靠 `--dir` 反推文件名）。

纪律（本引擎实现的硬规则）：
  · **隔离契约**：子进程环境从零构建、绝不继承——只有 `PATH` + 全新空 `HOME`
    （`<case>/.home`）+ `CLAUDE_CONFIG_DIR`（指向其中）+ `auth_env` 变量（**仅当宿主非空
    才传**：传空串会毁掉运行时自己的凭据回落）+ adapter 声明的 `env_passthrough` 键。
  · **不硬编码模型名**：一切运行时差异走 adapter 缝（`--adapter` / `--invocation`）。
  · **令牌纪律**：路径参数里 `{project-root}` 由 `--project-root` 自解析（唯一例外），
    其余任何 `{...}` 令牌一律拒绝（`TOKEN_UNRESOLVED`）。adapter 的 `invocation` 模板
    （`{prompt}` / `{query}` / `{cwd}`）是另一命名空间，不在此列。
  · **run 目录永不删除、覆盖、轮转**：同名（同秒同 label）已存在时另铸后缀目录，绝不覆写。
  · **降级不静默**：`invocation` 解析为空 → 只 stage、结果记 `skipped`；
    invocation 命令不在 PATH（无头下即 `runner.py` 白名单未覆盖该命令族）→ warning +
    跳过该 mode 并明示（**不入队**——确认是当场决策，队列语义是「用户稍后自行执行」）。

违规码：复用套件冻结集（MISSING_FILE EMPTY_FIELD ENUM_INVALID UNKNOWN_ID
SET_MISMATCH）；本引擎新增（本行即登记）：
  TOKEN_UNRESOLVED   路径参数含未解析的 `{...}` 令牌（`{project-root}` 除外）
  UNPARSABLE_JSON    run 目录里的 JSON 回执/产物不可解析（run.json / execution-summary.json
                     / timing.json / grading.json / triggers-result.json）
  NAME_ILLEGAL       `--file` 不是纯文件名（含路径分隔符——不许用路径冒充文件名）
  FILE_CONFLICT      memlog 已存在而调用方要 init（只追加、永不覆盖）

警告码（warnings 与 violations 同形，承载「有代码但不阻断」的项）：
  ADAPTER_MISSING    未配置 invocation（既无 `--invocation` 也无 adapter.json 的 invocation
                     键）→ 只 stage、结果记 skipped
  ADAPTER_INVALID    adapter.json 存在但读不了/形状非法 → 逐键取默认继续
  MODE_SKIPPED       invocation 命令不在 PATH（白名单未覆盖）→ 跳过该 mode（不入队）
  INCOMPLETE_RUN     发现同 label 的未完成 run（无 execution-summary.json）——只提示，
                     不自动续跑、不合并、不覆盖
  AGAINST_FALLBACK   `aggregate` 缺省基准 config 不在场 → 退回 run 的另一个非 `skill` config

引擎自定义回执键（命令级附加键，不进共同键）：`mlog` 的 ack `{ok, file, n, appended}`
（恒发一行 JSON，共同键 + `file` / `action` / `n` / `appended`）；
`aggregate` 的
`configs` / `delta` / `against` / `subject`；`check` 的 `run_dir` / `skipped_modes`；
`run` 的 `run_id` / `run_dir` / `modes`。

契约同构：exit 0 唯一放行 / 1 = 违规或被拒绝 / 2 = 用法错误（argparse
默认）；`--json` 单行回执（ensure_ascii=False）；无 `--json` 中文人读行（每违规一行
`CODE where: msg` + 汇总行）；`where` 正斜杠、相对 project-root；`--project-root` 全部
子命令都收（默认 `.`）；`--output-dir` 必填于会写盘的子命令（`run` 与 `mlog`），只读子命令
（`check` / `aggregate`）收到即回显、缺席时由 run 目录结构推导或不填（仅回执完整性用）。
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))

from eval_runner_aggregate import cmd_aggregate  # noqa: E402
from eval_runner_check import cmd_check  # noqa: E402
from eval_runner_lib import ENTRY_TYPES  # noqa: E402
from eval_runner_memlog import cmd_mlog  # noqa: E402
from eval_runner_run import cmd_run  # noqa: E402


# --------------------------------------------------------------- main

def main(argv=None):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(
        description="diy-eval-runner 确定性引擎：技能评测四模式（run）+ 结果聚合"
                    "（aggregate）+ run 目录终门（check）+ memlog（mlog）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("run", help="四模式执行器（baseline / variant / quality / trigger）")
    r.add_argument("--skill", required=True, help="被测技能目录（含 SKILL.md）")
    r.add_argument("--evals", default=None, help="用例文件（省略则按发现链找）")
    r.add_argument("--mode", action="append", default=None,
                   help="baseline / variant / quality / trigger，可重复（默认 quality）")
    r.add_argument("--runs", type=int, default=1, help="每 case / 每问句重复次数（默认 1）")
    r.add_argument("--invocation", nargs="+", default=None,
                   help="调用命令模板（argv；{prompt} / {cwd} 由引擎填充）——不硬编码模型名")
    r.add_argument("--variant-path", default=None, help="variant 模式：对比用的精简最小版")
    r.add_argument("--adapter", default=None, help="adapter.json（缺席即逐键取默认）")
    r.add_argument("--queries", default=None, help="trigger 模式的问句文件")
    r.add_argument("--label", default=None, help="run id 后缀（默认 evals / <技能名>-triggers）")
    r.add_argument("--timeout", type=int, default=600, help="单次调用的超时秒数（默认 600）")
    r.add_argument("--project-root", default=".", help="项目根（默认 .）")
    r.add_argument("--output-dir", required=True,
                   help="产物目录（必填；run 目录落 <output-dir>/eval-runs/）")
    r.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    r.set_defaults(func=cmd_run)

    a = sub.add_parser("aggregate", help="按 config 聚合 timing 指标（mean / n-1 标准差 / delta）")
    a.add_argument("--run-dir", default=None, help="run 目录")
    a.add_argument("--against", default=None,
                   help="基准 config（skill / bare / variant；缺省 bare）")
    a.add_argument("--self-test", action="store_true", help="用固定夹具校验公式并退出")
    a.add_argument("--project-root", default=".", help="项目根（默认 .）")
    a.add_argument("--output-dir", default=None, help="产物目录（仅回执完整性用）")
    a.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    a.set_defaults(func=cmd_aggregate)

    c = sub.add_parser("check", help="run 目录结构合规 + 结果自洽（终门；exit 0 唯一放行）")
    c.add_argument("--run-dir", required=True, help="run 目录")
    c.add_argument("--project-root", default=".", help="项目根（默认 .）")
    c.add_argument("--output-dir", default=None, help="产物目录（仅回执完整性用）")
    c.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    c.set_defaults(func=cmd_check)

    m = sub.add_parser("mlog", help="memlog：init / append / set-complete（只追加，恒发一行 ack）")
    m.add_argument("--dir", required=True, help="memlog 所在目录")
    m.add_argument("--file", required=True, help="文件名，由调用方显式给")
    m.add_argument("action", choices=("init", "append", "set-complete"), help="操作")
    m.add_argument("--type", default=None,
                   help="append 的条目类型（合法集 %s；越界由引擎判 ENUM_INVALID、exit 1）"
                        % "|".join(ENTRY_TYPES))
    m.add_argument("--text", default=None, help="append 的条目正文（单行化）")
    m.add_argument("--subject", default=None, help="init 的主题")
    m.add_argument("--project-root", default=".", help="项目根（默认 .）")
    m.add_argument("--output-dir", required=True,
                   help="产物目录（必填——mlog 会写盘）")
    m.add_argument("--json", action="store_true", help="保留旗标（mlog 恒发一行 JSON ack）")
    m.set_defaults(func=cmd_mlog)

    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
