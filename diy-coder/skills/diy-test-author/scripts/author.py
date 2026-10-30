# -*- coding: utf-8 -*-
"""diy-test-author 确定性引擎：技术栈/框架探测（detect）+ 测试代码纪律审计（audit）。

子命令：
  detect  语言无关的项目探测（只读）：依次读 package.json / pyproject.toml /
          requirements*.txt / Cargo.toml / go.mod / pom.xml / build.gradle* / Gemfile /
          composer.json 等清单判定 project_type 与既有测试框架；再识别测试目录、
          既有测试文件模式与既有 fixtures（本技能相对 diy-e2e-tests 的增量面）。
          无框架 → 回执给 suggested，**本技能不装框架**（框架脚手架是 diy-test-framework
          的职责，步进门禁据此拒绝并路由）。清单损坏/缺失降级为 warning，探测继续，不崩。
  audit   红相脚手架纪律审计（只读，**本技能的核心确定性资产**，源 atdd/automate 两份
          checklist 的手工核对在此下沉）。`--files` 必填（= 本次会话生成的测试文件集；
          不设「全测试目录」缺省——历史文件不进场）。三项判定合并在一条命令里：
          ① 上游门禁：test-plan.yaml 在场且 `project.status: 已定稿`；文件里每个 TC 锚
             （注释 `TC: TC-x.y.z`）可解析且 TC 现场自检（`technique` / `kill_target` 非空）；
             锚定 TC 的 `status` 必须是 `待办`（`失败` 是已激活测试、`通过` 已收口，
             都不得被脚手架覆盖；范围内全通过即拒绝，不静默空跑）；
          ② 规则集：无占位断言 / 无 CSS 与 XPath 定位 / 无硬编码业务数据 /
             断言指向期望行为（非空断言）/ 无 waitForTimeout 与 sleep /
             无 isVisible 条件流 / 无 page object / 单断言原子 / 文件行数上限 /
             用例名带 [P0]-[P3] 优先级标签且跟随锚定 TC 的 priority /
             Given-When-Then 结构注释 / 用例名可读 / 确定性隔离（无顺序依赖、
             无共享状态、用例体内无随机与时钟源）/ try-catch 只许清理 /
             测试代码无调试语句 / 夹具自建数据自带 teardown 清理；
          ③ 红相形态：每个 test 体含 skip 且每个用例带 TC 锚（本次新生成文件，
             无「人手写遗留」豁免）。

规则来源：红相脚手架 / resilient
selector / data factory / 单断言 / network-first / Given-When-Then / P0-P3 标签 /
夹具 teardown 清理
（禁 waitForTimeout / 禁 isVisible 条件流 / 禁 page object / 禁硬编码数据 /
确定性隔离 / try-catch 只许清理 / 禁调试语句 / 文件行数上限）。
语言无关实现 = 按扩展名装载的 pattern 表（js/ts 族、py 族、其余语言的 generic 兜底族）。
分层执行：**行级规则**（硬等待 / 条件流 / 脆选择器 / page object / 顺序依赖 /
顶层共享状态 / 调试语句）对全文生效（helper 等 test 体外代码同样在测试面上）；
**块级规则**（占位断言 / 断言面 / 硬编码数据 / skip 形态 / 锚 / 优先级标签 / 用例名 /
GWT / 随机与时钟源 / try-catch）判在 test 体内——工厂文件里的字面量是合法归宿，
不因硬编码规则受牵连（随机源与时钟源同理：造数据是工厂的本职）。
**夹具文件规则**（路径命中 fixtures 目录候选或文件名标记）判在文件级：建了数据的夹具
必须自带 teardown 清理。块级规则依赖 test 块切分，本引擎覆盖 js/ts 与 py 两族；
其余语言降级为文件级规则（硬编码数据随行级规则判定，断言面、skip 形态、锚、
优先级标签、用例名、GWT 与用例体内确定性项均不判）——该降级登记在回报中。

违规码：复用冻结集（MISSING_FILE UNPARSABLE_YAML UNKNOWN_ID
ENUM_INVALID EMPTY_FIELD STATUS_MISMATCH）；本引擎新增（本行即登记）：
  PLACEHOLDER_ASSERTION  占位断言（expect(true) / assert True 一类）
  BRITTLE_SELECTOR       CSS / XPath 定位（应用 getByRole/getByLabel/getByText 语义定位）
  HARDCODED_DATA         硬编码业务数据（应走工厂/faker）
  MISSING_ASSERTION      test 体无断言（断言须指向期望行为）
  NOT_ATOMIC             单 test 多断言（源「one assertion per test」）
  HARD_WAIT              waitForTimeout / sleep 一类硬等待
  CONDITIONAL_FLOW       isVisible() 条件流
  PAGE_OBJECT            page object 类
  FILE_TOO_LONG          文件行数超上限
  SKIP_MISSING           红相脚手架：test 体缺 skip（必须全部 skip，否则会污染 CI）
  ANCHOR_MISSING         红相脚手架：用例缺 TC 锚
  PRIORITY_TAG_MISSING   用例名缺 [P0]-[P3] 优先级标签（源 atdd/automate 硬纪律）
  PRIORITY_TAG_MISMATCH  用例名标签与锚定 TC 的 priority 不一致
  NAME_UNDESCRIPTIVE     用例名无信息（test1 / example 一类占位名）
  GWT_MISSING            用例缺 Given-When-Then 结构注释
  ORDER_DEPENDENCY       顺序依赖（describe.serial / pytest.mark.dependency 一类）
  SHARED_STATE           跨用例共享可变状态（顶层 let/var、函数内 global）
  NONDETERMINISTIC_SOURCE 用例体内用随机 / 时钟源（数据走工厂、时钟注入）
  TRY_CATCH_TEST_LOGIC   try-catch 包住测试逻辑（只许用于清理）
  DEBUG_STATEMENT        测试代码里的 console.log / print / debugger 一类调试语句
  FIXTURE_NO_TEARDOWN    夹具自建数据无 teardown 清理

分工：本技能消费 diy-test-design 写的 TC，产出红相脚手架；
**零 YAML 写面**——本引擎不写任何文件，技能也不回填 TC status（脚手架不执行，没有实测
结果可回填；TC status 由 diy-dev 的 TDD 循环经 `diyc.py green` 回填）。
实例解析委托 SKILL.md 侧的 `diyc.py resolve`；本引擎不做 --instance / 白名单 / 目录推导，
--output-dir 必填（仅用于定位 test-plan.yaml）。契约同构：exit 0
唯一放行 / 1 = 违规或被拒绝 / 2 = 用法错误；--json 单行回执（ensure_ascii=False）；
violations[{code, where, msg}] + counts；where 正斜杠、相对 project-root。
"""
# trace: 领域引擎 + TC 锚链 + 写权边界
import argparse
import os
import sys


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from author_detect import cmd_detect  # noqa: E402
from author_rules import cmd_audit  # noqa: E402


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(
        description="diy-test-author 确定性引擎：栈/框架探测（detect）+ 测试代码纪律审计（audit）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("detect", help="语言无关框架探测（只读；无框架回 suggested，不装框架）")
    d.add_argument("--project-root", default=".", help="项目根（默认 .）")
    d.add_argument("--output-dir", required=True,
                   help="产物目录（必填；由调用方传入，引擎不做实例解析/目录推导）")
    d.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    d.set_defaults(func=cmd_detect)

    a = sub.add_parser("audit", help="红相脚手架纪律审计（只读；exit 0 唯一放行）")
    a.add_argument("--files", action="append", required=True,
                   help="本次会话生成的测试文件（可重复；必填，无全目录缺省）")
    a.add_argument("--project-root", default=".", help="项目根（默认 .）")
    a.add_argument("--output-dir", required=True,
                   help="产物目录（必填；用于定位 test-plan.yaml，引擎不写任何文件）")
    a.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    a.set_defaults(func=cmd_audit)

    args = ap.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
