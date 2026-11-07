"""diy-viewer 标签与徽章常量表。"""

import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "..", "diy-tools", "scripts"))
from diyc_check_docs_lib import HTTP_METHODS as _CHECK_HTTP_METHODS  # noqa: E402

BADGE_KEYS = {"status", "priority", "state"}
ENUM_KEYS = BADGE_KEYS | {"type", "decision", "layer", "route", "verdict", "technique", "gate", "class", "subclass", "source", "augment", "severity",
                          # 五产物的枚举键补入（12 行 / 11 distinct：
                          # scope 在 wds-assets 与 wds-evolution 两产物重复登记）。值域见各 SKILL.md 结构节
                          "design_system_mode", "complexity", "category", "mode", "code",
                          "scope", "stage", "recipe", "format", "prompt_lang", "entry",
                          # design 族新增顶层两键（值域四值/三值，
                          # 见 diy-design 引擎 validate）；进枚举表 = 值域白名单 + 徽章判定
                          "form_factor", "modes",
                          # cis-method sessions[].method 四分支值
                          # （创新策略|问题求解|设计思维|叙事，见 SKILL.md schema）；
                          # 同名键装 HTTP 动词的三个产物已在 FREE_TEXT_FIELDS 例外登记
                          "method"}
# 自由文本字段 (doc, key)：schema 无枚举约束——同名 key 在别的产物可以是枚举。
# 依据：diy-architecture SKILL.md:43 decision=what was chosen；diy-review SKILL.md:31 type=short tag；
# diy-design SKILL.md:65 route=/path
FREE_TEXT_FIELDS = {("architecture", "decision"), ("bug-log", "type"), ("design", "route"),
                    # 枚举键装非枚举内容的四处：
                    # brief 的 BD 决策是一句自由文本；readiness/change-proposal/test-review
                    # 的 route 装的是技能名（diy-*），不是 design 族的路由串
                    ("brief", "decision"), ("readiness", "route"),
                    ("change-proposal", "route"), ("test-review", "route"),
                    # test-gate 的 source 含日期（「用户会话 2026-09-21」）——无法静态登记白名单
                    ("test-gate", "source"),
                    # 新入 ENUM_KEYS 的键在别处装非枚举内容，
                    # 不登记就会把诊断打到那些产物上（同键异义，逐条给出产物出处）：
                    # scope：analysis 的范围边界、augment 的采样实现面、evolution 的本轮增量口径、
                    # readiness 的实点到文档清单（列表值）、research 的范围与方法学
                    ("analysis", "scope"), ("mutation-report", "scope"),
                    ("wds-evolution", "scope"), ("readiness", "scope"), ("research", "scope"),
                    # stage：prfaq 的 1..5 数字锚点、wds-brief / wds-trigger 各自一套中文锚点
                    ("prfaq", "stage"), ("wds-brief", "stage"), ("wds-trigger", "stage"),
                    # code：diyc-baseline 的违规码是集中表文本，与 wds-assets 的活动码不同义
                    ("diyc-baseline", "code"),
                    # entry：wds-scenarios 的 entry 是 Q6 的自由文本答案（wds-trigger 的两值
                    # 与 wds-evolution 的存量接入|上线后持续走值表）
                    ("wds-scenarios", "entry"),
                    # type：wds-design-system 的 prefixes[].type 装的是 26 个组件类型名
                    # （Button…Spacer），全局 type=类型 在此不是枚举——不登记则每次渲染刷 26 行
                    # 诊断（R-02），且其中一个类型名恰与 6 分类值同名（Form）会被误标成「表单」
                    ("wds-design-system", "type"),
                    # openapi 的 type 是 OpenAPI/JSON-Schema 机器锚点
                    # 值域（securityScheme: apiKey/http/oauth2…；schema: object/string/
                    # integer…），非本产品枚举域；不登记则 components 渲染每次刷 unmapped enum
                    ("openapi", "type"),
                    # format 同族（JSON-Schema format 锚点：date-time/
                    # password 等），与 wds-assets 的 format 枚举同键异义；不登记则
                    # components 渲染刷 unmapped enum（diy-lab 实测两条），照 4a type 先例
                    ("openapi", "format"),
                    # method 入 ENUM_KEYS 后，装 HTTP 动词（get/post…）的
                    # 三个产物面按 (文档, 键) 例外：api_refs[].method 是接口复合锚，不是
                    # cis-method 的四分支值域（test-plan ← test-design/augment/e2e；
                    # stories ← epics-stories 的 AC 锚；story-context ← create-story 平铺锚）
                    ("test-plan", "method"), ("stories", "method"),
                    ("story-context", "method")}
BADGE_CLASSES = {
    "已定稿": "ok", "已完成": "ok", "通过": "ok", "必须": "must",
    "已采纳": "ok",
    "草稿": "dim", "可选": "dim", "待办": "dim", "已跳过": "dim",
    "待定": "dim",
    "进行中": "warn", "应该": "warn",
    "已阻塞": "bad", "失败": "bad",
    "阻断": "bad", "记录不阻断": "warn",
    "建议": "warn", "观察": "dim",
    # R3 补全（2026-09-19 机器层中文化收口）：有明确极性的结论/状态着色；
    # 类型/刻度类值只进 VALUE_LABELS（渲染中性徽章），与既有 18 条口径一致。
    # 终态正向
    "已批准": "ok", "批准": "ok", "已结论": "ok", "已确证": "ok", "可得": "ok",
    "已锤炼": "ok", "生效": "ok", "就绪": "ok", "已确立": "ok", "全覆盖": "ok",
    # 进行中 / 待定 / 有保留
    "待审查": "warn", "审查中": "warn", "返工": "warn", "讨论": "warn",
    "已推断": "warn", "假设中": "warn", "部分可得": "warn", "待验证": "warn",
    "有风险就绪": "warn", "部分完成": "warn", "新现": "warn", "有保留批准": "warn",
    "部分覆盖": "warn", "欠火候": "warn", "关键": "warn",
    # 负向
    "已驳回": "bad", "错误": "bad", "缺失": "bad", "已推翻": "bad", "无法获取": "bad",
    "地基裂缝": "bad", "未就绪": "bad", "严重": "bad", "未完成": "bad",
    "打回": "bad", "要求修改": "bad",
    "无实现": "bad", "无测试": "bad", "孤儿用例": "bad", "从未运行": "bad",
    # 初始 / 非激活 / 未知
    "悬停": "dim", "空态": "dim", "加载中": "dim", "调查中": "dim",
    "待证据阻塞": "dim", "已反转": "dim", "未知": "dim", "未开始": "dim",
    "格式不支持": "dim", "自动生成": "dim", "超出范围": "dim",
    "可并行": "dim", "锦上添花": "dim",
    # 页状态收敛为单真源 5 值——design.yaml 的
    # `pages[].status` 与 `open_questions[].status` 的增量值；极性照 R3 口径分档
    # （进行中 / 待审 → warn · 非激活终态 → dim · 终态正向 → ok）。
    # 未开始 / 已批准 是既有映射，不动（补映射 ≠ 改既有映射）
    "结构稿中": "warn", "待验收": "warn", "已移除": "dim",
    "已解决": "ok",
}
KEY_RE = re.compile(r"[^a-z0-9]+")
META_KEYS = ("project", "x-project")
# HTTP 动词值域单点同源（check 引擎常量）；此前两处字面量各持一份，
# 漂移无门。渲染侧保持 set 语义（viewer_pages 成员判定）。
HTTP_METHODS = set(_CHECK_HTTP_METHODS)

from viewer_key_labels import KEY_LABELS  # noqa: F401,E402  re-export 保活（importer 零改）

# 值标签（词表正典来源）：机器层中文化后键=中文值、值=展示标签，多数同名。
