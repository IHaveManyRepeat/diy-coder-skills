# -*- coding: utf-8 -*-
"""diyc 写回命令模块（批次 3 / W3）：transition、green、done、bug-add、reconcile。

把散落在各 SKILL.md 提示词里的多文件手改 YAML 收敛为原子脚本操作。规则来源
（.analysis/2026-09-13-cross-skill/batch3-contract.md）：

- §4.5 transition：diy-build-loop HALT 状态迁移，合法边表冻结；待审查→已完成 故意不在
  边表——强制走 done 命令做真源回填（BUG-012 机制化）。（2026-09-18 修订，SS-012-04：
  已完成→进行中 这条边清 `augment`——重开即清旧 verdict，与 runner.py --reopen-failed
  同语义；冻结契约 batch3-contract.md §4.5 的「不清 augment」括号注由此作废。）
- §4.6 green：diy-dev / diy-build-loop 红绿证据写回——sprint 任务 evidence 追加
  （同 tc 替换，HALT 续跑幂等）+ test-plan 该 TC status: 通过 回填。
- §4.7 done：待审查→已完成 终态写——sprint / stories / test-plan 三真源同批回填。
- §4.8 bug-add：diy-review 缺陷入库——枚举校验 + BUG- 序号铸造（现有最大 +1，三位补零）。
- §4.9 reconcile：diy-sprint Create/Update 机制化——任务集对账；TDD 门判定只经
  diyc_lib.Docs.story_covered()（与 check 共享唯一定义，禁止二份实现）。
- §4.10 defer-add（2026-09-15 副作用纪律修订）：保留确认类动作入队——reason 枚举校验 +
  DA- 序号铸造（现有最大 +1，三位补零）→ deferred-actions.yaml（append-only，
  无头/循环场景不阻塞任务，供用户事后确认执行）。

写回纪律（契约 §3）：全文 load → 就地改 → safe_dump(allow_unicode=True,
sort_keys=False) → 同目录临时文件 + os.replace 原子替换，统一经
diyc_lib.save_yaml_atomic（对齐 runner.save_sprint 先例）。校验不过零写入；
诊断中文；回执 schema 见契约 §3，写回命令含 updated（bump 后日期）。
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from diyc_writeback_records import _bug_add, _defer_add, _defer_set, _stamp  # noqa: E402
from diyc_writeback_reconcile import _reconcile  # noqa: E402
from diyc_writeback_state import _done, _green, _transition  # noqa: E402


def run(args) -> dict:
    # 入口（契约 §2）：args 由 diyc.py 组装（含 resolved output_dir 与 args.command）
    if args.command == "transition":
        return _transition(args)
    if args.command == "green":
        return _green(args)
    if args.command == "done":
        return _done(args)
    if args.command == "bug-add":
        return _bug_add(args)
    if args.command == "stamp":
        return _stamp(args)
    if args.command == "defer-add":
        return _defer_add(args)
    if args.command == "defer-set":
        return _defer_set(args)
    if args.command == "reconcile":
        return _reconcile(args)
    raise ValueError(f"diyc_writeback 不认识的子命令：{args.command!r}（diyc.py 接线 bug）")
