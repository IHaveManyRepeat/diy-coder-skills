#!/usr/bin/env python3
"""diy-viewer: render diy-coder YAML artifacts (single source) into human-friendly HTML.

The YAML files are the single source of truth. This script only projects them
into disposable HTML under <output_dir>/<view_dir>/.

Usage:
    python viewer.py --project-root . [yaml paths ...]
"""

import argparse
import datetime
import html
import json
import re
import sys
import webbrowser
from pathlib import Path

import yaml

BADGE_KEYS = {"status", "priority", "state"}
ENUM_KEYS = BADGE_KEYS | {"type", "decision", "layer", "route", "verdict", "technique", "gate", "class", "subclass", "source", "augment", "severity"}
# 自由文本字段 (doc, key)：schema 无枚举约束——同名 key 在别的产物可以是枚举。
# 依据：diy-architecture SKILL.md:43 decision=what was chosen；diy-review SKILL.md:31 type=short tag；
# diy-design SKILL.md:65 route=/path
FREE_TEXT_FIELDS = {("architecture", "decision"), ("bug-log", "type"), ("design", "route")}
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
}
KEY_RE = re.compile(r"[^a-z0-9]+")
META_KEYS = ("project", "x-project")
HTTP_METHODS = {"get", "put", "post", "delete", "options", "head", "patch", "trace"}

# 展示层中文标签：YAML 键名仍为英文，键名→中文展示标签；枚举值已是中文
# （机器层中文化），值标签表因此键值同名，兼作已知值域白名单（徽章判定依据）。
KEY_LABELS = {
    "id": "编号", "title": "标题", "name": "名称", "status": "状态",
    "created": "创建日期", "updated": "更新日期", "description": "描述",
    "goal": "目标", "goals": "目标", "metric": "度量标准", "priority": "优先级",
    "type": "类型", "state": "状态", "project": "项目信息",
    "purpose": "项目定位", "users": "目标用户", "need": "核心需求",
    "features": "功能组", "requirements": "需求条目", "statement": "需求描述",
    "nfrs": "非功能需求", "out_of_scope": "不在范围内",
    "open_questions": "待决问题", "question": "问题", "answer": "结论",
    "strictness": "严格度",
    "decisions": "技术决策", "alternatives": "备选方案", "choice": "选定方案",
    "option": "选项", "rationale": "理由", "why": "理由", "why_not": "未选原因",
    "affects": "影响需求", "components": "组件", "responsibility": "职责",
    "stack": "技术栈", "depends_on": "依赖",
    "risks": "风险", "risk": "风险", "mitigation": "缓解措施",
    "epics": "史诗", "epic": "所属史诗", "feature_refs": "关联功能组",
    "stories": "故事", "story": "所属故事", "narrative": "用户故事",
    "acceptance_criteria": "验收标准", "ac": "验收标准",
    "given": "给定", "when": "当", "then": "那么", "refs": "关联需求",
    "test_cases": "测试用例", "steps": "验证步骤", "coverage_gaps": "覆盖缺口",
    "reason": "原因", "decision": "处理决定", "note": "备注", "notes": "备注",
    "method": "方法", "path": "路径", "operationId": "操作 ID",
    "summary": "摘要", "x-fr": "关联需求",
    "tasks": "任务", "blocked_reason": "阻塞原因", "test_refs": "关联用例",
    "augment": "编码后验证",
    "evidence": "执行证据", "tc": "用例", "red": "红", "green": "绿",
    "review": "审查记录", "verdict": "结论", "findings": "发现清单",
    "layer": "层", "route": "路由",
    "loop": "迭代记录", "rounds": "修复轮数", "outcome": "结果", "at": "时间",
    "technique": "设计技术", "kill_target": "目标缺陷",
    "static_checks": "静态检查链", "order": "顺序", "tool": "工具",
    "kills": "消灭问题", "gate": "门禁",
    "bugs": "缺陷记录", "class": "大类", "subclass": "中类",
    "symptom": "症状", "root_cause": "根因", "pattern": "模式",
    "source": "来源", "date": "日期", "trigger": "触发方法", "fix": "修复方案",
    "prevention": "根治机制", "taxonomy": "分类注册表",
    "plain": "通俗解释", "detail": "过程详情",
    # design 族（diy-design schema）：B2 补齐，防英文直出
    "direction": "方向", "frontend_framework": "前端框架", "tokens": "设计令牌",
    "color": "颜色", "spacing": "间距", "typography": "字号", "scale": "缩放",
    "pages": "页面", "states": "状态", "signals": "信号",
    "prototype": "结构稿", "implementation": "实现路径", "design_ref": "关联页面",
    "unit": "基准单位", "family_base": "正文字体", "family_heading": "标题字体",
    "bg": "背景", "surface": "表面", "text": "文字", "text_muted": "次要文字",
    "accent": "强调色", "accent_text": "强调色文字",
    # spec-scan 族（diy-spec-scan schema）：规格预演扫描的歧义清单
    "scans": "扫描记录", "units": "扫描单元", "scanned": "已扫描",
    "quote": "原文摘录", "read_as": "我读到什么", "stuck": "卡在哪",
    "would_guess": "会猜成什么", "impact": "猜错后果", "suggestion": "建议裁定",
    "severity": "严重度", "units_total": "单元总数", "units_scanned": "已扫描单元数",
}
# 值标签（词表正典来源）：机器层中文化后键=中文值、值=展示标签，多数同名。
VALUE_LABELS = {
    "草稿": "草稿", "已定稿": "已定稿", "待办": "待办",
    "进行中": "进行中", "待审查": "待审查", "已完成": "已完成",
    "已阻塞": "已阻塞", "通过": "通过", "失败": "失败", "已跳过": "已跳过",
    "必须": "必须", "应该": "应该", "可选": "可选",
    "单元": "单元", "集成": "集成", "端到端": "端到端",
    "已豁免": "已豁免", "接受缺口": "接受缺口",
    "正确性": "正确性", "边界": "边界", "覆盖审计": "覆盖审计", "设计采用": "设计采用",
    "意图缺口": "意图缺口", "规格缺陷": "规格缺陷", "小修": "小修", "后置": "后置",
    "等价类": "等价类", "决策表": "决策表", "状态迁移": "状态迁移",
    "成对组合": "成对组合", "错误猜测": "错误猜测", "蜕变测试": "蜕变测试",
    "属性测试": "属性测试", "场景": "场景",
    "覆盖分支": "覆盖分支", "MC-DC 覆盖": "MC-DC 覆盖", "白盒路径": "白盒路径",
    "变异杀伤": "变异杀伤",
    "阻断": "阻断", "记录不阻断": "记录不阻断",
    "功能型": "功能型", "非功能型": "非功能型",
    "逻辑": "逻辑", "数据": "数据", "状态": "状态",
    "性能": "性能", "用户体验": "用户体验", "安全": "安全",
    "兼容性": "兼容性", "可靠性": "可靠性",
    "开发": "开发", "审查发现": "审查发现", "证伪轮": "证伪轮", "用户": "用户",
    "待定": "待定", "已采纳": "已采纳",
    "图标": "图标", "文字": "文字", "形状": "形状", "动效": "动效", "色彩": "色彩",
    # spec-scan：八类执行歧义 + 三档严重度
    "分支无定义": "分支无定义", "术语冲突": "术语冲突",
    "接口缺口": "接口缺口", "输入不明": "输入不明",
    "输出不明": "输出不明", "时序不明": "时序不明",
    "直接矛盾": "直接矛盾", "隐含假设": "隐含假设",
    "建议": "建议", "观察": "观察",
    # R3 补全（2026-09-19 机器层中文化收口）：引擎值域常量里 viewer 未登记的中文取值。
    # 采集口径：AST 扫描 skills/*/scripts/*.py 的值域常量（含函数内联比较），剔除
    # 「不改清单」（P0-P3 / 大写档 / 产物名 / QA / [假设] 令牌）。下列值多为同一词跨语境共用。
    # 状态与结论（investigate / readiness / quick-dev / correct-course / brief / test-review / prfaq）
    "调查中": "调查中", "已结论": "已结论", "待证据阻塞": "待证据阻塞",
    "症状驱动": "症状驱动", "探索": "探索",
    "已确证": "已确证", "已推断": "已推断", "假设中": "假设中",
    "可得": "可得", "部分可得": "部分可得", "缺失": "缺失", "无法获取": "无法获取",
    "待验证": "待验证", "已推翻": "已推翻",
    "就绪": "就绪", "有风险就绪": "有风险就绪", "未就绪": "未就绪",
    "审查中": "审查中", "已批准": "已批准", "已驳回": "已驳回",
    "生效": "生效", "已反转": "已反转",
    "已确立": "已确立", "新现": "新现", "未知": "未知",
    "全覆盖": "全覆盖", "部分覆盖": "部分覆盖",
    "批准": "批准", "返工": "返工", "讨论": "讨论",
    "打回": "打回", "要求修改": "要求修改", "有保留批准": "有保留批准",
    "已锤炼": "已锤炼", "欠火候": "欠火候", "地基裂缝": "地基裂缝",
    "未开始": "未开始", "部分完成": "部分完成", "未完成": "未完成",
    "无实现": "无实现", "无测试": "无测试", "孤儿用例": "孤儿用例", "从未运行": "从未运行",
    "悬停": "悬停", "空态": "空态", "加载中": "加载中", "错误": "错误",
    # 档位与原因（严重度 / 变更规模 / 排除与后置原因 / 复盘筹备档）
    "严重": "严重", "高": "高", "中": "中", "低": "低",
    "轻微": "轻微", "中等": "中等", "重大": "重大",
    "格式不支持": "格式不支持", "自动生成": "自动生成", "超出范围": "超出范围",
    "用户配置": "用户配置", "破坏性操作": "破坏性操作", "越界改动": "越界改动",
    "仅人工可做": "仅人工可做",
    "关键": "关键", "可并行": "可并行", "锦上添花": "锦上添花",
    # 类型 / 模式 / 分类类值（徽章中性色：语义是归类，不是结论）
    "显式指定": "显式指定", "冲刺任务": "冲刺任务", "Git 提交": "Git 提交",
    "全程轨迹": "全程轨迹", "仅规格": "仅规格", "裸提交": "裸提交",
    "增量": "增量", "批量": "批量",
    "修改": "修改", "新增": "新增", "删除": "删除",
    "直接调整": "直接调整", "回滚": "回滚", "MVP 复审": "MVP 复审",
    "新建": "新建", "更新": "更新", "校验": "校验",
    "工单": "工单", "归档": "归档", "日志": "日志",
    "描述": "描述", "范围": "范围", "提交": "提交",
    "商业": "商业", "内部": "内部", "开源": "开源", "社区": "社区",
    "个人兴趣": "个人兴趣", "投资人": "投资人", "公开": "公开",
    "全量": "全量", "重扫": "重扫", "深挖": "深挖",
    "快速": "快速", "深入": "深入", "穷尽": "穷尽",
    "技术栈": "技术栈", "语言": "语言", "框架": "框架", "测试": "测试",
    "质量": "质量", "工作流": "工作流", "反模式": "反模式",
    "网页": "网页", "移动端": "移动端", "后端": "后端", "前端": "前端",
    "命令行": "命令行", "库": "库", "桌面端": "桌面端", "游戏": "游戏",
    "扩展": "扩展", "基础设施": "基础设施", "嵌入式": "嵌入式", "全栈": "全栈",
    "新功能": "新功能", "缺陷修复": "缺陷修复", "重构": "重构", "杂务": "杂务",
    "一次成型": "一次成型", "计划-编码-审查": "计划-编码-审查",
    "总是": "总是", "先问": "先问", "从不": "从不",
    "市场": "市场", "技术": "技术", "领域": "领域",
    "流程": "流程", "文档": "文档", "团队": "团队",
    "组长": "组长", "负责人": "负责人", "入门": "入门", "进阶": "进阶", "资深": "资深",
    "两者": "两者", "脚手架": "脚手架", "配置": "配置", "钩子": "钩子", "脚本": "脚本",
    "静态检查": "静态检查", "契约": "契约", "预热": "预热", "报告": "报告",
    "可维护性": "可维护性", "合成": "合成",
    "覆盖": "覆盖", "非功能需求": "非功能需求", "启发式": "启发式",
}
DOC_LABELS = {
    "prd": "产品需求文档", "architecture": "架构设计", "epics": "史诗列表",
    "stories": "故事列表", "test-plan": "测试计划", "openapi": "接口契约",
    "sprint": "冲刺任务",
    "bug-log": "缺陷模式库", "design": "设计稿",
    "spec-scan": "规格歧义扫描",
}
# 文档级标签覆盖（B1）：同一 key 在不同文档语义不同——bug-log 的 type 是缺陷三级分类，
# 其余文档（test-plan/openapi 等）回落全局 type=类型
DOC_KEY_LABELS = {
    "bug-log": {"type": "小类"},
    # spec-scan：全局 unit=基准单位（design 族）在扫描记录里指扫描单元；
    # target/lines/files 收在此处——checkpoint 的 target 语义不同，不加全局映射
    "spec-scan": {"unit": "单元", "type": "歧义类型", "kind": "目标类型",
                  "target": "扫描目标", "lines": "行数", "files": "文件数"},
}
# 术语表（展示层，FR-4.1 可读性）：标签/徽章/标题命中即挂悬浮解释，YAML 单一源不动。
# key = 渲染后的展示文本（已 esc，纯中文无 HTML 字符，查找安全）。
GLOSSARY = {
    # 结构概念
    "功能组": "一组相关功能需求，对应产品的一个能力方向",
    "需求条目": "一条具体的功能需求，编号 FR-x.y，是故事/测试等所有下游工作的源头",
    "非功能需求": "不规定做什么功能，规定做得怎么样的要求（如性能、可维护性）",
    "严格度": "验收松紧档位；公开=发布级，必须需求须逐条满足才算完成",
    "史诗": "一组相关故事的集合，比故事大一档，通常对应产品一大块能力",
    "用户故事": "从使用者角度描述的一小段需求：谁、要什么、为什么",
    "验收标准": "做完后怎样算合格的可检查条件，编号 AC-x.y，测试用例直接对着它设计",
    "测试用例": "一次具体测试的做法描述，编号 TC-x.y.z，每条至少绑定一个验收标准",
    "任务": "冲刺里的执行单元，一个任务对应一个故事，由 runner 自动驱动",
    "接口契约": "OpenAPI 3.1 格式的 API 定义文件，机器可读",
    "冲刺任务": "按顺序执行的任务清单，串行驱动：同一时间至多一个任务在跑",
    # 状态与流程
    "已定稿": "内容已确认锁定，后续修改需走变更流程（改产物+过 ID 链校验）",
    "待审查": "编码完成，等待分层审查（正确性/边界/覆盖/设计采用）后决定完成或打回",
    "已阻塞": "任务被卡住（缺规格/歧义/超修复上限），需要人来处理",
    "红": "TDD 第一步：先写测试并确认它失败，证明测试真的在测东西",
    "绿": "实现完成后测试转通过；必须先有红再有绿才算数",
    "执行证据": "编码过程留下的红绿执行记录，写进冲刺任务供审查核对",
    "迭代记录": "自动循环（编码→审查→打回→修复）的执行摘要：跑了几轮、结果如何",
    "修复轮数": "被审查打回后重修的次数，上限 2 次，超了转阻塞",
    "阻塞原因": "任务被卡住的具体原因，人工处理后重跑",
    # 审查
    "审查记录": "分层审查（正确性/边界/覆盖审计/设计采用）的结论与发现清单",
    "发现清单": "审查发现的问题列表，每条带路由：小修/后置/规格缺陷/意图缺口",
    "正确性": "第一层审查：实现是否按验收标准做对了",
    "边界": "专抓边界情况：空值、最大最小、刚好越界",
    "覆盖审计": "第三层审查：检查测试是否真的覆盖了验收标准，而非走形式",
    "设计采用": "第四层审查（仅界面任务）：实现必须构建在设计稿框架代码上，不得重写",
    "小修": "问题路由：执行者当场修掉",
    "后置": "问题路由：记录下来以后再修，不阻塞本任务",
    "规格缺陷": "规格本身写错或写不清；执行者无权改规格，转人工",
    "意图缺口": "验收标准没覆盖到真实意图，需要回到规格层补",
    "证伪轮": "审查通过后主动再攻击一轮：按历史缺陷模式找漏洞，命中就打回",
    # 测试技术
    "设计技术": "设计这条用例的思考方法（等价类/错误猜测等）",
    "目标缺陷": "这条用例专门要杀死的那类缺陷；说不出目标缺陷的用例是凑数",
    "等价类": "把输入分成几组，每组挑一个代表来测，组内其他输入预期行为相同",
    "决策表": "多条件组合时列成真值表，保证每种组合都有测试安排",
    "状态迁移": "按状态变化的每条路径（含非法路径）设计用例",
    "成对组合": "多因素时只测两两组合，数学上能覆盖绝大多数组合缺陷",
    "错误猜测": "凭经验和历史 bug 猜最可能出错的位置，针对性下钩",
    "蜕变测试": "难以直接算出预期值时，检查输入变化后输出关系是否仍然成立",
    "属性测试": "验证在任何输入下都成立的普遍性质，而非单个例子",
    "场景": "模拟一个完整使用场景走一遍，端到端验证",
    "单元": "只测一个函数或模块的测试",
    "集成": "测多个模块配合是否正确",
    "端到端": "从用户视角走完整流程的测试",
    "已豁免": "这条验收标准不再要求测试覆盖（通常是历史完成的故事，补测成本大于收益）",
    "接受缺口": "明确接受没有测试覆盖，留档说明原因",
    "P0": "最高优先级：不通过就不能交付",
    "P1": "重要：当前周期应通过",
    "P2": "次要：有余力再处理",
    # 静态检查链
    "静态检查链": "编码后自动运行的工具序列：快的先跑拦住低级错误，慢的后跑，层层过滤",
    "门禁": "该工具结果的使用方式：阻断=不过不算完成；记录不阻断=只记一笔",
    "阻断": "不过此关就不算绿，必须修",
    "记录不阻断": "只记录发现，不阻塞交付",
    "消灭问题": "这个工具专门负责抓的问题类型；说不出来就该删掉该工具",
    # 缺陷模式库
    "大类": "缺陷一级分类：功能型/非功能型",
    "中类": "缺陷二级分类：逻辑/数据/状态/性能/安全等十个桶",
    "小类": "缺陷三级分类：自由扩展的标签，登记进注册表防止同义词漂移",
    "根因": "导致缺陷的真正原因，治这个才不会复发",
    "模式": "这个缺陷的可复用特征，供错误猜测时对照",
    "触发方法": "什么做法会再次踩到这个坑",
    "根治机制": "防复发的机制性措施，如状态单一真源、校验标红",
    "分类注册表": "小类标签的登记簿，新词自动入册，防止同一概念叫出多个名字",
    # 架构
    "技术决策": "一次方案拍板：在备选项中选定一个并记录理由，编号 D-x",
    "备选方案": "当时考虑过但没选的方案，记录原因防止未来重复论证",
    "未选原因": "备选方案落选的理由",
    "影响需求": "该决策会波及的需求编号",
    "缓解措施": "降低风险发生概率或损失的应对手段",
    # PRD
    "度量标准": "该目标是否达成的可量化判据",
    "不在范围内": "明确排除的事项，防止范围蔓延",
    "待决问题": "尚未拍板的问题，定稿前必须有结论",
    # viewer 特有
    "悬空引用": "引用了一个在所有文档里都不存在的编号，ID 链断了",
    "引用不存在": "指向的编号在所有文档里找不到，通常是条目删了但引用没改",
    "孤儿": "必须级需求没有被任何故事或测试用例引用，可能被遗漏了",
    "关联需求": "向上引用的需求编号（ID 链），点击可看详情",
    "关联用例": "该任务必须通过的测试用例编号；为空则任务无法启动（TDD 门）",
    "编码后验证": "任务完成编码后由 diy-augment 跑的覆盖率驱动补测：通过=已完整交付；失败=有缺陷待裁断处理；已跳过=环境缺工具未跑",
    "关联功能组": "该史诗对应的功能组编号",
    "待确认假设": "[假设] 标记的推测内容，需人工逐条确认后才能定稿",
}
# 徽章值词汇表（B3）：值命中 VALUE_LABELS/已知分类/术语表（如 P0/P1/P2）才出徽章，
# 自由文本/URL 回落 cell() 纯文本
BADGE_VALUES = ({k.lower() for k in VALUE_LABELS}
                | {k.lower() for k in BADGE_CLASSES}
                | {k.lower() for k in GLOSSARY})
_VALUE_LABELS_CI = {k.lower(): v for k, v in VALUE_LABELS.items()}
# ID 链：带 id 字段的条目卡片生成锚点；文本中命中的 ID 链接到其所在文档并带悬停预览。
# 引用型字段（REF_KEYS）在正文只显示编号链接；点击后右侧浮动详情面板展示完整内容
# （页面尾部以 <template> 预渲染全部 ID 详情，面板内链接可链式查看）。
ID_RE = re.compile(r"\b[A-Z]{1,4}-\d+(?:\.\d+)*\b")
ID_FULL_RE = re.compile(r"[A-Z]{1,4}-\d+(?:\.\d+)*")
# trace: S-15 AC-15.1 design_ref（AC 绑定 design.yaml 页面引用）入引用链，悬空即标红
REF_KEYS = {"affects", "refs", "depends_on", "feature_refs", "story", "test_refs", "ac", "epic", "x-fr", "design_ref"}
# 过程性字段默认折叠（FR-4.1 可读性，D-10 后白话化纪律）：结论常驻、过程按需展开
FOLDED_KEYS = {"evidence", "findings"}
FOLDED_NOTE_LEN = 80
PREVIEW_KEYS = ("statement", "then", "title", "question", "goal", "risk", "name",
                "decision", "description", "narrative")
ID_INDEX: dict = {}
# S-12 ID 链一致性（FR-4.4）：悬空引用按文档汇总，渲染时行内标红 + 顶部告警
DANGLING_BY_DOC: dict = {}
# S-12 孤儿 must FR（AC-12.2）：未被任何 AC/用例引用，条目行标红
ORPHAN_IDS: set = set()


# 当前渲染文档名（B1 文档级标签覆盖的查表上下文）；模板按节点归属文档逐条切换
_RENDER_DOC = ""
_UNMAPPED_SEEN: set = set()


def _diag_unmapped(value) -> None:
    # trace: B1/B3 未映射枚举诊断（只打 stderr，不改输出）：契约漂移一行可见
    s = str(value)
    if not s or s in _UNMAPPED_SEEN:
        return
    _UNMAPPED_SEEN.add(s)
    print(f"[diy-viewer] unmapped enum: {s}", file=sys.stderr)


def is_enum_key(k: str) -> bool:
    # trace: B1/B3 枚举判定带文档上下文：自由文本字段不做徽章尝试、不报漂移诊断
    return k in ENUM_KEYS and (_RENDER_DOC, k) not in FREE_TEXT_FIELDS


def key_label(k: str) -> str:
    # trace: B1 文档级覆盖优先（bug-log type→小类），再回落全局表（type→类型）
    label = DOC_KEY_LABELS.get(_RENDER_DOC, {}).get(k)
    if label is None:
        label = KEY_LABELS.get(k)
    if label is None:
        if is_enum_key(k):
            _diag_unmapped(k)
        return k
    return label


def gloss(text: str) -> str:
    """术语包装：已转义的展示文本命中术语表 → 悬浮解释（展示层增强，不改正文）。"""
    tip = GLOSSARY.get(text)
    if not tip:
        return text
    return f'<span class="term" data-tip="{esc(tip)}">{text}</span>'


def _collect_ids(node, doc: str, _seen=None) -> None:
    # trace: S-11 AC-11.1 TC-11.1.1 防环：自引用锚点（YAML 合法）结构只访问一次，不无限递归
    if _seen is None:
        _seen = set()
    if isinstance(node, dict):
        if id(node) in _seen:
            return
        _seen.add(id(node))
        i = node.get("id")
        if isinstance(i, str) and i not in ID_INDEX:
            preview = next(
                (str(node[k]) for k in PREVIEW_KEYS
                 if isinstance(node.get(k), str) and node[k].strip()),
                i,
            )
            ID_INDEX[i] = {"doc": doc, "preview": preview[:120], "node": node}
        for v in node.values():
            _collect_ids(v, doc, _seen)
    elif isinstance(node, list):
        if id(node) in _seen:
            return
        _seen.add(id(node))
        for x in node:
            _collect_ids(x, doc, _seen)


def is_id_string(v) -> bool:
    return isinstance(v, str) and ID_FULL_RE.fullmatch(v.strip()) is not None


def iter_ref_values(node, _seen=None):
    # trace: S-12 AC-12.1 AC-12.2 产出引用型字段的全部字符串值（悬空/孤儿共用遍历）；
    # S-11 AC-11.1 TC-11.1.1 防环：自引用结构只访问一次
    if _seen is None:
        _seen = set()
    if isinstance(node, dict):
        if id(node) in _seen:
            return
        _seen.add(id(node))
        for k, v in node.items():
            if k in REF_KEYS:
                vals = v if isinstance(v, list) else [v]
                for x in vals:
                    if isinstance(x, str):
                        yield x
            else:
                yield from iter_ref_values(v, _seen)
    elif isinstance(node, list):
        if id(node) in _seen:
            return
        _seen.add(id(node))
        for x in node:
            yield from iter_ref_values(x, _seen)


def collect_dangling(node, found: list) -> None:
    # trace: S-12 AC-12.1 TC-12.1.1 收集引用型字段中不可解析的 ID（悬空引用）
    found.extend(
        x.strip() for x in iter_ref_values(node)
        if is_id_string(x) and x.strip() not in ID_INDEX)


def compute_orphans(prd_data, referenced: set) -> set:
    # trace: S-12 AC-12.2 TC-12.2.1 must FR 未被任何 AC/用例引用 → 孤儿
    orphans = set()
    for feat in prd_data.get("features") or []:
        if not isinstance(feat, dict):
            continue
        for req in feat.get("requirements") or []:
            if (isinstance(req, dict) and is_id_string(req.get("id"))
                    and str(req.get("priority", "")).strip().lower() == "必须"
                    and req["id"].strip() not in referenced):
                orphans.add(req["id"].strip())
    return orphans


def dangling_ref(i: str) -> str:
    # trace: S-12 AC-12.1 TC-12.1.1 悬空引用：红字 + 错误徽章，断裂显式可见
    return (f'<span class="dangling">{esc(i)}</span>'
            f'<span class="badge b-bad">{gloss("引用不存在")}</span>')


def id_link(i: str, hit: dict) -> str:
    return (f'<a class="idl" href="{esc(hit["doc"])}.html#{esc(i)}"'
            f' title="{esc(hit["preview"])}">{esc(i)}</a>')


def render_compact_kv(d: dict) -> str:
    """紧凑 kv 表（字段竖排）：详情面板内的条目渲染。"""
    rows = "".join(
        f'<tr><th>{gloss(esc(key_label(k)))}</th>'
        f'<td>{badge(k, v) if is_enum_key(k) else cell(v)}</td></tr>'
        for k, v in d.items()
    )
    return f'<table class="kv compact"><tbody>{rows}</tbody></table>'


def render_detail(node) -> str:
    """引用目标完整详情（供右侧面板）：引用字段显示为编号链接，可链式查看。"""
    if is_flat_dict(node):
        return render_compact_kv(node)
    scalars = {k: x for k, x in node.items() if not isinstance(x, (dict, list))}
    complex_ = {k: x for k, x in node.items() if isinstance(x, (dict, list))}
    out = render_compact_kv(scalars) if scalars else ""
    for k, x in complex_.items():
        out += render_value(k, x, 4)
    return out


def render_ref_item(i: str) -> str:
    """单个 ID 引用：仅编号链接，详情点击后在右侧面板查看。"""
    hit = ID_INDEX.get(i.strip())
    if not hit:
        return dangling_ref(i)  # trace: S-12 AC-12.1 悬空引用标红
    return id_link(i, hit)


def ref_cell(i: str) -> str:
    """正文引用字段：编号链接 + 目标摘要，审阅无需跳页。"""
    s = i.strip()
    hit = ID_INDEX.get(s)
    if not hit:
        return dangling_ref(i)  # trace: S-12 AC-12.1 悬空引用标红
    out = id_link(i, hit)
    if hit["preview"] and hit["preview"] != s:
        out += f'<span class="refsum">{esc(hit["preview"])}</span>'
    return out


def render_ref_list(items: list) -> str:
    """ID 引用列表：纯编号链接。"""
    lis = []
    for x in items:
        hit = ID_INDEX.get(str(x).strip())
        if hit is None:
            lis.append(f"<li>{dangling_ref(x)}</li>")  # trace: S-12 AC-12.1
        else:
            lis.append(f"<li>{id_link(str(x), hit)}</li>")
    return f'<ul class="reflist">{"".join(lis)}</ul>'


def build_templates() -> str:
    """全量 ID 详情模板：点击编号链接时填充右侧面板。"""
    # trace: B1 详情模板按节点归属文档切换标签上下文（跨文档打开面板时 type 仍按源文档语义）
    global _RENDER_DOC
    parts = []
    for i, h in ID_INDEX.items():
        prev, _RENDER_DOC = _RENDER_DOC, h.get("doc", "")
        try:
            parts.append(f'<template data-detail="{esc(i)}">{render_detail(h["node"])}</template>')
        finally:
            _RENDER_DOC = prev
    return "".join(parts)


def build_id_index(docs: list) -> None:
    ID_INDEX.clear()
    for name, data in docs:
        _collect_ids(data, name)


def linkify(text: str) -> str:
    def sub(m):
        i = m.group(0)
        hit = ID_INDEX.get(i)
        if not hit:
            return i
        return (f'<a class="idl" href="{esc(hit["doc"])}.html#{esc(i)}"'
                f' title="{esc(hit["preview"])}">{i}</a>')

    return ID_RE.sub(sub, text)


def load_config(project_root: Path) -> dict:
    cfg_path = project_root / "diy-coder.yaml"
    cfg = {}
    if cfg_path.exists():
        try:
            cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as e:
            print(f"[diy-viewer] warning: cannot parse {cfg_path}: {e}", file=sys.stderr)
        else:
            # trace: 对抗审查修复——配置为手写文件，顶层/paths/viewer 段或值为非预期形状时
            # 一行警告 + 降级默认，不裸栈（同类守卫：runner.py / exp-sync.py / diy-help）
            if not isinstance(cfg, dict):
                print(f"[diy-viewer] warning: {cfg_path} 顶层不是映射，按默认配置处理",
                      file=sys.stderr)
                cfg = {}
    paths, viewer = cfg.get("paths"), cfg.get("viewer")
    if paths is not None and not isinstance(paths, dict):
        print(f"[diy-viewer] warning: {cfg_path} 的 paths 不是映射，按默认处理", file=sys.stderr)
        paths = None
    if viewer is not None and not isinstance(viewer, dict):
        print(f"[diy-viewer] warning: {cfg_path} 的 viewer 不是映射，按默认处理", file=sys.stderr)
        viewer = None
    output_dir = (paths or {}).get("output_dir", "diy-output")
    view_dir = (paths or {}).get("view_dir", ".view")
    if not isinstance(output_dir, str) or not isinstance(view_dir, str):
        print(f"[diy-viewer] warning: {cfg_path} 的 output_dir/view_dir 不是字符串，按默认处理",
              file=sys.stderr)
        if not isinstance(output_dir, str):
            output_dir = "diy-output"
        if not isinstance(view_dir, str):
            view_dir = ".view"
    return {
        "output_dir": output_dir,
        "view_dir": view_dir,
        "auto_open": bool((viewer or {}).get("auto_open", True)),
    }  # 展示语言固定中文；回复语言属 agent 侧 SKILL.md 契约，脚本不读此键


def _is_interactive() -> bool:
    # trace: 2026-09-13 裁定——自动打开仅发生在人工交互终端（stdout 连 TTY）；
    # AI/自动化环境（Claude 会话、runner 子进程、CI、沙箱）stdout 为管道，天然判非交互
    return sys.stdout.isatty()


def should_open(auto_open: bool, no_open: bool, force_open: bool,
                interactive: bool) -> bool:
    # trace: 2026-09-13 裁定——打开浏览器是给在场人看的副作用：自动化环境静默跳过，
    # 不报路径、不阻塞流程。优先级：--no-open 一票否决 > --open 显式强制 > 配置 + 交互终端
    if no_open:
        return False
    return force_open or (auto_open and interactive)


def resolve_instance(out_dir: Path, instance):
    # trace: S-16 AC-16.1 AC-16.2 TC-16.1.1 TC-16.2.1 D-9
    # 目录即实例：带实例名 → <output_dir>/<实例名>/；无 → 主线平铺零迁移。
    # 白名单首字符字母数字，天然拒绝点目录、分隔符与盘符注入；
    # 末字符禁点（对抗审查修复：Windows 目录名尾点被静默折叠，b. ≡ b 破坏实例隔离）
    if instance is None:
        return out_dir
    if not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9_-])?", instance):
        raise SystemExit(
            f"[diy-viewer] 非法实例名: {instance!r}（字母数字开头和结尾，中间可含 . _ -）")
    return out_dir / instance


def slugify(s: str) -> str:
    return KEY_RE.sub("-", str(s).strip().lower()).strip("-") or "x"


def esc(v) -> str:
    return html.escape(str(v), quote=True)


def cell(v) -> str:
    """Render a scalar value; keeps line breaks, highlights [假设]."""
    if v is None:
        return '<span class="dim">—</span>'
    if isinstance(v, (dict, list)):
        return f'<code class="dim">{esc(json.dumps(v, ensure_ascii=False, default=str))}</code>'
    text = esc(v)
    if text.startswith("[假设]"):
        return f'<span class="assume" title="assumption, needs confirmation">{linkify(text)}</span>'
    return linkify(text).replace("\n", "<br>")


def badge(key: str, v) -> str:
    # trace: B3 值感知——值不在词汇表（决策自由文本/route URL 等）→ 回落 cell() 纯文本；
    # None 与非标量同样回落 cell()（「—」/降级），不再输出字面 None
    if v is not None and not isinstance(v, (dict, list)):
        s = str(v).strip()
        if s.lower() in BADGE_VALUES:
            cls = BADGE_CLASSES.get(s.lower(), "neutral")
            text = _VALUE_LABELS_CI.get(s.lower(), s)
            return f'<span class="badge b-{cls}">{gloss(esc(text))}</span>'
        _diag_unmapped(s)
    return cell(v)


def render_table(items: list, with_row_ids: bool = True) -> str:
    headers: list = []
    for item in items:
        for k in item:
            if k not in headers:
                headers.append(k)
    th = "".join(f"<th>{gloss(esc(key_label(h)))}</th>" for h in headers)
    rows = []
    for item in items:
        tds = []
        for h in headers:
            v = item.get(h)
            tds.append(f"<td>{badge(h, v) if is_enum_key(h) else cell(v)}</td>")
        rid = item.get("id") if with_row_ids else None
        anchor = f' id="{esc(rid)}"' if isinstance(rid, str) and rid else ""
        # trace: S-12 AC-12.2 TC-12.2.1 孤儿 must FR：行标红 + 徽章提示
        if isinstance(rid, str) and rid in ORPHAN_IDS:
            tds[0] = f'<span class="badge b-bad">{gloss("孤儿")}</span>' + tds[0]
            rows.append(f'<tr class="orphan"{anchor}>{"".join(tds)}</tr>')
        else:
            rows.append(f"<tr{anchor}>{''.join(tds)}</tr>")
    return (f'<div class="table-scroll"><table class="data">'
            f'<thead><tr>{th}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>')


def render_dict_fields(d: dict) -> str:
    def field(k, v):
        if k in REF_KEYS and is_id_string(v):
            return ref_cell(str(v))
        return badge(k, v) if is_enum_key(k) else cell(v)

    rows = "".join(
        f'<tr><th>{gloss(esc(key_label(k)))}</th><td>{field(k, v)}</td></tr>'
        for k, v in d.items()
    )
    return f'<table class="kv"><tbody>{rows}</tbody></table>'


def is_flat_dict(d) -> bool:
    return isinstance(d, dict) and all(not isinstance(x, (dict, list)) for x in d.values())


def render_value(key: str, v, depth: int) -> str:
    out = _render_value_raw(key, v, depth)
    fold = key in FOLDED_KEYS or (
        key == "note" and isinstance(v, str) and len(v) > FOLDED_NOTE_LEN)
    if fold:
        n = len(v) if isinstance(v, list) else ""
        label = key_label(key) + (f"（{n} 项）" if n != "" else "")
        return (f'<details class="detail"><summary>展开{esc(label)}</summary>'
                f'<div class="d-body">{out}</div></details>')
    return out


def _render_value_raw(key: str, v, depth: int) -> str:
    lvl = min(depth + 2, 6)
    title = f'<h{lvl} id="{slugify(key)}">{gloss(esc(key_label(key)))}</h{lvl}>' if key else ""
    if isinstance(v, dict):
        if not v:
            return title + '<p class="dim">（空）</p>'
        # plain（通俗速览）置顶、detail（过程详情）折叠置底，其余字段按原序渲染
        plain_html = (f'<p class="plain">{cell(v["plain"])}</p>'
                      if isinstance(v.get("plain"), str) else "")
        skip = {"plain", "detail"}
        scalars = {k: x for k, x in v.items()
                   if k not in skip and not isinstance(x, (dict, list))}
        complex_ = {k: x for k, x in v.items()
                    if k not in skip and isinstance(x, (dict, list))}
        detail_html = ""
        d = v.get("detail")
        if isinstance(d, str) and d.strip():
            detail_html = ('<details class="detail"><summary>展开过程详情</summary>'
                           f'<div class="d-body">{cell(d)}</div></details>')
        elif isinstance(d, (dict, list)):
            detail_html = ('<details class="detail"><summary>展开过程详情</summary>'
                           f'<div class="d-body">{render_value("", d, depth + 1)}</div></details>')
        out = title + plain_html
        if scalars:
            out += render_dict_fields(scalars)
        for k, x in complex_.items():
            out += render_value(k, x, depth + 1)
        return out + detail_html
    if isinstance(v, list):
        if not v:
            return title + '<p class="dim">（空）</p>'
        if key in REF_KEYS and all(isinstance(x, str) for x in v):
            return title + render_ref_list(v)
        # 含 plain/detail 的条目走卡片（速览行+折叠块形态），纯 flat 条目保持表格总览
        if all(is_flat_dict(x) for x in v) and not any(
                ("plain" in x or "detail" in x) for x in v if isinstance(x, dict)):
            return title + render_table(v)
        if all(isinstance(x, dict) for x in v):
            cards = []
            for x in v:
                cid = x.get("id")
                anchor = f' id="{esc(cid)}"' if isinstance(cid, str) and cid else ""
                cards.append(f'<div class="card"{anchor}>{render_value("", x, depth + 1)}</div>')
            return title + "".join(cards)
        # trace: 对抗审查修复——列表标量命中值词表（signals: icon/motion 等）时中文化，未命中原样
        lis = []
        for x in v:
            label = _VALUE_LABELS_CI.get(str(x).strip().lower()) if isinstance(x, str) else None
            lis.append(f"<li>{cell(label or x)}</li>")
        return title + "<ul>" + "".join(lis) + "</ul>"
    if key in REF_KEYS and is_id_string(v):
        return title + ref_cell(v)
    return title + (badge(key, v) if is_enum_key(key) else f"<p>{cell(v)}</p>")


CSS = """
:root{--ink:#1a2333;--mut:#6b7280;--line:#e3e8ef;--bg:#f6f8fa;--card:#fff;
--accent:#1d4ed8;--ok:#15803d;--warn:#b45309;--bad:#b91c1c;--dim:#6b7280}
*{box-sizing:border-box}body{margin:0;font-family:"Segoe UI","Microsoft YaHei",
system-ui,sans-serif;color:var(--ink);background:var(--bg);line-height:1.65}
main{max-width:1080px;margin:0 auto;padding:32px 24px 64px}
header.top{background:#fff;border-bottom:1px solid var(--line);padding:14px 24px}
header.top .wrap{max-width:1080px;margin:0 auto;display:flex;justify-content:
space-between;align-items:baseline}header.top a{color:var(--accent);
text-decoration:none;font-size:.9em}h1{font-size:1.6em;margin:0 0 4px}
h2,h3,h4,h5,h6{margin:1.6em 0 .5em}h2{font-size:1.25em;border-bottom:
1px solid var(--line);padding-bottom:.3em}table{border-collapse:collapse;
width:100%;background:var(--card);border:1px solid var(--line);border-radius:
8px;overflow:hidden;font-size:.92em}th,td{padding:8px 12px;text-align:left;
vertical-align:top;border-bottom:1px solid var(--line)}thead th{background:
#eef2f7;font-weight:600}tbody tr:last-child td{border-bottom:none}
table.kv th{width:180px;background:#eef2f7;font-weight:600}ul{padding-left:22px}
.table-scroll{overflow-x:auto}table.data th,table.data td{white-space:nowrap}
.card{background:var(--card);border:1px solid var(--line);border-radius:8px;
padding:4px 18px;margin:10px 0}.card h3,.card h4,.card h5{margin:.7em 0 .3em}
.badge{display:inline-block;padding:1px 10px;border-radius:999px;font-size:.8em;
font-weight:600;border:1px solid transparent}.b-ok{color:var(--ok);background:
#ecfdf3;border-color:#b7e7c8}.b-warn{color:var(--warn);background:#fff8eb;
border-color:#f3ddab}.b-bad{color:var(--bad);background:#fef2f2;
border-color:#f3c1c1}.b-dim{color:var(--dim);background:#f3f4f6;
border-color:#e0e2e6}.b-must{color:#fff;background:var(--accent)}.b-neutral{
color:var(--ink);background:#eef2f7;border-color:var(--line)}
.assume{background:#fef9c3;padding:0 4px;border-radius:4px}.refsum{
color:var(--dim);font-size:.85em;margin-left:6px}
.dangling{color:var(--bad);font-weight:600}
.alert-bad{background:#fef2f2;border-color:#f3c1c1;color:var(--bad)}
tr.orphan td{background:#fef2f2}
.idl{color:var(--accent);text-decoration:underline dotted;text-underline-offset:3px}
.idl:hover{background:#eef2f7;border-radius:3px}
.reflist{list-style:none;padding-left:0;margin:4px 0}
.reflist>li{margin:6px 0}
main{transition:margin-right .25s ease}
body.pane-open main{margin-right:46%}
#refpane{position:fixed;top:0;right:0;width:46%;height:100vh;background:var(--card);
border-left:1px solid var(--line);box-shadow:-6px 0 20px rgba(0,0,0,.08);
transform:translateX(105%);transition:transform .25s ease;overflow-y:auto;z-index:50}
#refpane.open{transform:translateX(0)}
#refpane .rp-head{position:sticky;top:0;background:var(--card);border-bottom:
1px solid var(--line);padding:12px 20px;display:flex;align-items:center;gap:12px;z-index:1}
#refpane .rp-head h3{margin:0;font-size:1.05em}
#refpane .rp-head .src{color:var(--accent);text-decoration:none;font-size:.85em;margin-left:auto}
#refpane .rp-close{border:1px solid var(--line);background:#fff;border-radius:6px;
padding:2px 10px;cursor:pointer;font-size:.85em;color:var(--ink)}
#refpane .rp-close:hover{background:#eef2f7}
#refpane .rp-body{padding:4px 20px 32px}
@media(max-width:860px){#refpane{width:100vw}body.pane-open main{margin-right:0}}
tr:target td{background:#fff8eb}
.card:target{border-color:var(--warn);box-shadow:0 0 0 3px #fff8eb}
.dim{color:var(--mut)}p{margin:.4em 0}
.doc-meta{color:var(--mut);font-size:.9em;margin-bottom:8px}
.alert{background:#fff8eb;border:1px solid #f3ddab;color:var(--warn);border-radius:
8px;padding:10px 16px;margin:0 0 18px;font-weight:600}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));
gap:16px}a.doc-card{display:block;background:var(--card);border:1px solid
var(--line);border-radius:10px;padding:18px 20px;text-decoration:none;
color:var(--ink);transition:box-shadow .15s}a.doc-card:hover{box-shadow:0 4px
14px rgba(0,0,0,.08)}a.doc-card .name{font-weight:700;color:var(--accent);
font-size:1.05em}a.doc-card .sub{color:var(--mut);font-size:.85em;margin-top:4px}
.term{border-bottom:1px dotted var(--accent);cursor:help}
.term:hover{background:#eef2f7;border-radius:3px}
#gloss-tip{position:fixed;display:none;z-index:99;max-width:340px;background:
#1a2333;color:#fff;font-size:.85em;line-height:1.5;padding:8px 12px;border-radius:
8px;box-shadow:0 4px 14px rgba(0,0,0,.25);pointer-events:none}
.plain{color:var(--mut);font-size:.95em;background:#f6f8fa;border-left:3px
solid #cbd5e1;padding:6px 12px;margin:6px 0 10px;border-radius:0 6px 6px 0}
details.detail{margin:10px 0 4px;border:1px dashed var(--line);border-radius:8px}
details.detail summary{cursor:pointer;padding:7px 14px;color:var(--mut);
font-size:.88em;user-select:none}
details.detail summary:hover{color:var(--accent)}
details.detail[open] summary{border-bottom:1px dashed var(--line)}
details.detail .d-body{padding:6px 14px 10px;font-size:.95em;color:var(--mut)}
.foot{color:var(--mut);font-size:.85em;border-top:1px solid var(--line);
margin-top:40px;padding-top:12px}
"""


PANE_JS = """
(function(){
var pane=document.getElementById('refpane');
var body=document.getElementById('rp-body');
var title=document.getElementById('rp-title');
var src=document.getElementById('rp-src');
function closePane(){pane.classList.remove('open');document.body.classList.remove('pane-open');}
document.getElementById('rp-close').addEventListener('click',closePane);
document.addEventListener('keydown',function(e){if(e.key==='Escape')closePane();});
document.addEventListener('click',function(e){
  var a=e.target.closest('a.idl');
  if(!a)return;
  var id=(a.textContent||'').trim();
  var tpl=document.querySelector('template[data-detail="'+id+'"]');
  if(!tpl)return;
  e.preventDefault();
  title.textContent=id;
  src.setAttribute('href',a.getAttribute('href')||'#');
  body.innerHTML='';
  body.appendChild(tpl.content.cloneNode(true));
  pane.classList.add('open');
  document.body.classList.add('pane-open');
  pane.scrollTop=0;
});
})();
"""


TOOLTIP_JS = """
(function(){
var tip=null;
function show(t){
  if(!tip){tip=document.createElement('div');tip.id='gloss-tip';
  document.body.appendChild(tip);}
  tip.textContent=t.getAttribute('data-tip');
  tip.style.display='block';
  var r=t.getBoundingClientRect();
  var left=Math.max(8,Math.min(r.left,window.innerWidth-tip.offsetWidth-8));
  var top=r.bottom+6;
  if(top+tip.offsetHeight>window.innerHeight){top=r.top-tip.offsetHeight-6;}
  tip.style.left=left+'px';tip.style.top=top+'px';
}
function hide(){if(tip){tip.style.display='none';}}
document.addEventListener('mouseover',function(e){
  var t=e.target.closest('.term');
  if(t){show(t);}else{hide();}
});
document.addEventListener('scroll',hide,true);
})();
"""


def page(title: str, body: str, nav: str = "", source: str = "") -> str:
    # trace: B4 新鲜度 meta：页脚落生成时间与来源目录（含实例名），.view 落后于 YAML 一眼可见
    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    src = f" · 来源 {esc(source)}" if source else ""
    foot = f'<footer class="foot">生成于 {stamp}{src}</footer>'
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<style>{CSS}</style>
</head>
<body>
<header class="top"><div class="wrap"><h1>{esc(title)}</h1><nav>{nav}</nav></div></header>
<main>
{body}
{foot}
</main>
<aside id="refpane" aria-label="引用详情">
<div class="rp-head"><h3 id="rp-title"></h3>
<a class="src" id="rp-src" href="#">在原文档中打开 ↗</a>
<button class="rp-close" id="rp-close" type="button">✕ 关闭</button></div>
<div class="rp-body" id="rp-body"></div>
</aside>
{build_templates()}
<script>{PANE_JS}</script>
<script>{TOOLTIP_JS}</script>
</body>
</html>
"""


def count_assumptions(node, _seen=None) -> int:
    # trace: S-11 AC-11.1 TC-11.1.1 防环：自引用结构只访问一次（build_index 卡片在渲染隔离外，不得崩）
    if _seen is None:
        _seen = set()
    if isinstance(node, str):
        return 1 if node.startswith("[假设]") else 0
    if isinstance(node, dict):
        if id(node) in _seen:
            return 0
        _seen.add(id(node))
        return sum(count_assumptions(v, _seen) for v in node.values())
    if isinstance(node, list):
        if id(node) in _seen:
            return 0
        _seen.add(id(node))
        return sum(count_assumptions(x, _seen) for x in node)
    return 0


def get_meta(data) -> dict:
    """Project meta block: `project` (diy docs) or `x-project` (OpenAPI extension)."""
    if not isinstance(data, dict):
        return {}
    for k in META_KEYS:
        if isinstance(data.get(k), dict):
            return data[k]
    return {}


def render_openapi_section(data: dict) -> str:
    """OpenAPI doc extras: 3.1 sanity check + endpoint overview table."""
    alerts = []
    version = data.get("openapi")
    if not isinstance(version, str) or not version.startswith("3.1"):
        alerts.append(f"⚠ openapi 字段缺失或非 3.1（当前：{version}）——不符合 OpenAPI 3.1 语法")
    rows = []
    for path, item in (data.get("paths") or {}).items():
        if not isinstance(item, dict):
            continue
        for method, op in item.items():
            if method.lower() not in HTTP_METHODS or not isinstance(op, dict):
                continue
            fr = op.get("x-fr")
            rows.append({
                "method": method.upper(),
                "path": path,
                "operationId": op.get("operationId"),
                "summary": op.get("summary"),
                "x-fr": ", ".join(str(x) for x in fr) if isinstance(fr, list) else fr,
            })
    out = "".join(f'<div class="alert">{a}</div>' for a in alerts)
    if rows:
        out += '<h2 id="api-overview">接口总览</h2>' + render_table(rows)
    return out


def render_augment_panel(data, others: list) -> str:
    # trace: 2026-09-13 裁定——补测待裁断聚合面板：sprint 页集中列出 augment:失败 任务
    # 与其失败用例（跨 test-plan/stories 反查），裁断三途径同屏可见；无失败任务零输出
    fails = [t for t in (data.get("tasks") or [])
             if isinstance(t, dict) and t.get("augment") == "失败"]
    if not fails:
        return ""
    tp = next((d for n, d in others if n == "test-plan"), None)
    tc_by_id = {}
    if isinstance(tp, dict):
        for tc in tp.get("test_cases") or []:
            if isinstance(tc, dict) and isinstance(tc.get("id"), str):
                tc_by_id[tc["id"].strip()] = tc
    story_title = {}
    st = next((d for n, d in others if n == "stories"), None)
    if isinstance(st, dict):
        for s in st.get("stories") or []:
            if isinstance(s, dict) and isinstance(s.get("id"), str):
                story_title[s["id"].strip()] = str(s.get("title", "")).strip()
    rows = []
    for t in fails:
        sid = str(t.get("story", "")).strip()
        head = render_ref_item(sid) if sid else '<span class="dim">—</span>'
        title = story_title.get(sid)
        if title:
            head += f'<span class="refsum">{esc(title)}</span>'
        refs = t.get("test_refs") if isinstance(t.get("test_refs"), list) else []
        hits = []
        for r in refs:
            tc = tc_by_id.get(str(r).strip())
            if not isinstance(tc, dict) or tc.get("status") != "失败":
                continue
            item = render_ref_item(str(r))
            kt = str(tc.get("kill_target", "")).strip()
            if kt:
                item += f'<span class="refsum">{esc(kt)}</span>'
            n = tc.get("note")
            if isinstance(n, str) and n.strip():
                item += f'<div class="dim">{cell(n)}</div>'
            hits.append(item)
        hits_html = "<br>".join(hits) if hits else '<span class="dim">（test_refs 中无 fail 用例记录）</span>'
        rows.append(f"<tr><td>{head}</td><td>{hits_html}</td></tr>")
    return (
        '<h2 id="augment-panel">补测待裁断</h2>'
        f'<div class="alert alert-bad">⚠ {len(fails)} 个任务编码后验证未通过 —— '
        '裁断三途径：代码缺陷 → <code>python runner.py --reopen-failed</code> 批量重开修复；'
        '用例设计问题 → 直接更新 test-plan.yaml；规格问题 → 回 stories.yaml / prd.yaml 层处理</div>'
        f'<table class="data"><thead><tr><th>{gloss("任务")}</th>'
        f'<th>失败用例与目标缺陷</th></tr></thead><tbody>{"".join(rows)}</tbody></table>'
    )


def render_doc_page(name: str, data, others: list, source: str = "") -> str:
    global _RENDER_DOC
    _RENDER_DOC = name  # trace: B1 文档级标签覆盖上下文
    meta = get_meta(data)
    meta_line = []
    if isinstance(meta, dict):
        for k in ("name", "status", "updated", "created"):
            if meta.get(k) is not None:
                meta_line.append(badge(k, meta[k]) if k == "status" else esc(meta[k]))
    n_open = count_assumptions(data)
    alert = (
        f'<div class="alert">⚠ {gloss("待确认假设")} {n_open} 项 —— 即页面中黄底标注内容，逐条确认后方可定稿</div>'
        if n_open else ""
    )
    # trace: S-12 AC-12.1 TC-12.1.1 悬空引用计入页面顶部告警
    dang = DANGLING_BY_DOC.get(name) or []
    if dang:
        ids = "、".join(f"<code>{esc(i)}</code>" for i in dang)
        alert += f'<div class="alert alert-bad">⚠ {gloss("悬空引用")}：{ids}（未定义的 ID）</div>'
    body = f'<p class="doc-meta">{" · ".join(meta_line)}</p>' + alert
    if name == "sprint":
        body += render_augment_panel(data, others)  # trace: 2026-09-13 裁定 补测待裁断面板
    if name == "openapi":
        body += render_openapi_section(data)
    for k, v in (data or {}).items():
        if k in META_KEYS:
            body += render_value(k, v, 0)
            break
    body += "".join(
        render_value(k, v, 0) for k, v in (data or {}).items() if k not in META_KEYS
    )
    links = ['<a href="index.html">⌂ 首页</a>'] + [
        f'<a href="{esc(n)}.html">{gloss(esc(DOC_LABELS.get(n, n)))}</a>' for n, _ in others if n != name
    ]
    return page(DOC_LABELS.get(name, name), body, " · ".join(links), source)


def build_index(docs: list, errors=None, source: str = "") -> str:
    cards = []
    for name, data in docs:
        meta = get_meta(data)
        st = meta.get("status")
        status_html = badge("status", st) if st else ""
        n_open = count_assumptions(data)
        open_html = f'<span class="badge b-warn">待确认 {n_open}</span>' if n_open else ""
        # trace: 2026-09-13 裁定——索引卡片露出补测待裁断数（不点进 sprint 页也可见）
        if name == "sprint":
            n_fail = len([t for t in (data.get("tasks") or [])
                          if isinstance(t, dict) and t.get("augment") == "失败"])
            if n_fail:
                open_html += f'<span class="badge b-bad">补测待裁断 {n_fail}</span>'
        cards.append(
            f'<a class="doc-card" href="{esc(name)}.html">'
            f'<div class="name">{gloss(esc(DOC_LABELS.get(name, name)))}'
            f'<span class="sub"> {esc(name)}.yaml</span></div>'
            f'<div class="sub">{status_html} {open_html} {esc(meta.get("updated", ""))}</div></a>'
        )
    if not cards:
        body = '<p class="dim">未找到 YAML 文档。</p>'
    else:
        body = f'<div class="grid">{"".join(cards)}</div>'
    # trace: S-11 AC-11.1 TC-11.1.1 跳过的文件在索引中保留错误卡片（HTML 可见标记）
    if errors:
        body += (f'<div class="alert alert-bad">⚠ {len(errors)} 个文件未能渲染'
                 f'（形状异常、语法损坏或渲染失败）</div>'
                 + "<ul>" + "".join(f"<li>{esc(e)}</li>" for e in errors) + "</ul>")
    return page("diy-coder 文档索引", body, source=source)


def load_docs(paths) -> tuple:
    # trace: S-11 AC-11.1 TC-11.1.1 形状守卫：语法/形状/空文档三类异常统一降级为一行报告，不崩
    docs, errors = [], []
    for p in paths:
        try:
            data = yaml.safe_load(p.read_text(encoding="utf-8"))
        except (yaml.YAMLError, OSError) as e:
            errors.append(f"{p.name}: {e}")
            continue
        if data is None:
            errors.append(f"{p.name}: empty document")
            continue
        if not isinstance(data, dict):
            errors.append(f"{p.name}: 顶层不是映射（{type(data).__name__}），已跳过")
            continue
        docs.append((p.stem, data))
    return docs, errors


def nested_instance_dirs(out_dir: Path) -> list:
    # trace: B5① 主线目录无 YAML 而其下存在含 YAML 的子目录 → 疑似实例目录（忘传 --instance）
    try:
        return sorted(
            d.name for d in out_dir.iterdir()
            if d.is_dir() and next(d.glob("*.yaml"), None) is not None
        )
    except OSError:
        return []


def select_explicit_docs(all_docs: list, files, out_dir: Path, errors: list) -> tuple:
    # trace: B5② 显式路径优先：路径存在 → 直接按该路径渲染该文件；不存在 → 回落 basename
    # 在解析根内查找；路径存在但在解析根之外 → stderr 警告后仍渲染给定文件
    # （不得静默替换为同名文件）。显式文档覆盖同名条目，其后仍参与 ID 索引与导航。
    req: set = set()
    explicit = []
    for f in files:
        p = Path(f)
        if p.is_file():
            try:
                inside = p.resolve().is_relative_to(out_dir.resolve())
            except OSError:
                inside = False
            if not inside:
                print(f"[diy-viewer] warning: {p} 不在解析根 {out_dir} 内，按给定路径渲染",
                      file=sys.stderr)
            explicit.append(p)
        else:
            req.add(p.name)
    ex_docs, ex_errors = load_docs(explicit)
    errors.extend(ex_errors)
    for name, data in ex_docs:
        idx = next((i for i, (n, _) in enumerate(all_docs) if n == name), None)
        if idx is None:
            all_docs.append((name, data))
        else:
            all_docs[idx] = (name, data)
    # trace: 对抗审查修复——load_docs 以 p.stem 为名，过滤须按 stem 匹配，
    # 否则显式给出的非 .yaml 扩展文件（如 prd.yml）被静默丢弃（违背 B5② 契约）
    wanted = {Path(n).stem for n in req} | {p.stem for p in explicit}
    docs = [(n, d) for n, d in all_docs if n in wanted]
    known = {n for n, _ in all_docs}
    for m in sorted(m for m in req if Path(m).stem not in known):
        errors.append(f"{m}: not found under {out_dir}")
    return docs, all_docs


def main() -> int:
    # trace: S-11 AC-11.1（stderr 含中文与 em dash：Windows 管道默认 cp936 会写出 GBK，消费方按 UTF-8 解码即崩）
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    # trace: S-16 AC-16.1 AC-16.2 TC-16.1.1 TC-16.2.1 D-9（--instance 接线：实例目录解析与主线平铺兼容）
    ap = argparse.ArgumentParser(description="diy-coder YAML → HTML viewer")
    ap.add_argument("--project-root", default=".", help="project root directory")
    ap.add_argument("--open", dest="force_open", action="store_true",
                    help="force-open the browser even in non-interactive environments "
                         "(overridden by --no-open)")
    ap.add_argument("--no-open", action="store_true", help="do not open the browser")
    ap.add_argument("--instance", default=None,
                    help="instance name (FR-4.5/D-9): artifacts under <output_dir>/<name>/; "
                         "absent = mainline flat path (zero migration)")
    ap.add_argument("files", nargs="*", help="specific yaml files (default: all under output_dir)")
    args = ap.parse_args()

    root = Path(args.project_root).resolve()
    cfg = load_config(root)
    out_dir = root / cfg["output_dir"]
    out_dir = resolve_instance(out_dir, args.instance)

    if not out_dir.exists():
        print(f"[diy-viewer] output dir not found: {out_dir}. Run a diy-* workflow first.", file=sys.stderr)
        return 1
    if not out_dir.is_dir():
        print(f"[diy-viewer] output path is not a directory: {out_dir}", file=sys.stderr)
        return 1

    # trace: B5① 主线空而其下存在实例目录 → 把「忘传 --instance」变成一行可见诊断
    if not any(out_dir.glob("*.yaml")):
        inst_dirs = nested_instance_dirs(out_dir)
        if inst_dirs:
            print(f"[diy-viewer] found instance dirs: {', '.join(inst_dirs)} — "
                  "pass --instance <name>", file=sys.stderr)

    # ID 链接索引与跨文档导航必须基于全量文档构建，即使本次只渲染子集。
    all_docs, errors = load_docs(sorted(out_dir.glob("*.yaml")))
    docs = all_docs
    if args.files:
        docs, all_docs = select_explicit_docs(all_docs, args.files, out_dir, errors)

    # trace: B4 来源展示：output_dir 相对项目根路径（含实例名）
    try:
        source_disp = out_dir.relative_to(root).as_posix()
    except ValueError:
        source_disp = str(out_dir)

    view_dir = out_dir / cfg["view_dir"]
    view_dir.mkdir(parents=True, exist_ok=True)

    written = []
    build_id_index(all_docs)
    # trace: S-12 AC-12.1 TC-12.1.1 悬空引用按文档汇总（索引构建后、渲染前）
    DANGLING_BY_DOC.clear()
    for n, d in all_docs:
        found = []
        collect_dangling(d, found)
        if found:
            DANGLING_BY_DOC[n] = sorted(set(found))
    # trace: S-12 AC-12.2 TC-12.2.1 孤儿判定：AC（stories）与用例（test-plan）引用并集
    referenced: set = set()
    for n, d in all_docs:
        if n in ("stories", "test-plan"):
            referenced.update(x.strip() for x in iter_ref_values(d))
    prd_data = next((d for n, d in all_docs if n == "prd"), None)
    ORPHAN_IDS.clear()
    if isinstance(prd_data, dict):
        ORPHAN_IDS.update(compute_orphans(prd_data, referenced))
    for name, data in docs:
        others = all_docs
        f = view_dir / f"{name}.html"
        # trace: S-11 AC-11.1 TC-11.1.1 逐文件隔离：单文件渲染失败降级为错误页，不中断整批
        try:
            body = render_doc_page(name, data, others, source_disp)
        except Exception as e:  # noqa: BLE001 兜底隔离，失败详情写入错误页与索引
            errors.append(f"{name}.yaml: 渲染失败（{e.__class__.__name__}: {e}）")
            body = page(DOC_LABELS.get(name, name),
                        f'<div class="alert alert-bad">⚠ 渲染失败：{esc(e)}</div>',
                        source=source_disp)
        f.write_text(body, encoding="utf-8")
        written.append(f)
    index = view_dir / "index.html"
    index.write_text(build_index(all_docs, errors, source_disp), encoding="utf-8")
    for e in errors:
        print(f"[diy-viewer] skipped — {e}", file=sys.stderr)

    print(f"[diy-viewer] rendered {len(written)} doc(s) -> {view_dir}")
    if errors:
        print(f"[diy-viewer] {len(errors)} file(s) skipped (see stderr)", file=sys.stderr)

    # trace: 2026-09-13 裁定——自动打开仅限人工交互终端；AI/自动化环境静默跳过（不阻塞）
    if docs and should_open(cfg["auto_open"], args.no_open, args.force_open,
                            _is_interactive()):
        webbrowser.open(index.resolve().as_uri())
    return 0


if __name__ == "__main__":
    sys.exit(main())
