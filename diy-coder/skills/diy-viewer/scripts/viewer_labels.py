"""diy-viewer 标签与徽章常量表。"""

import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "..", "diy-tools", "scripts"))
from diyc_check_docs_lib import HTTP_METHODS as _CHECK_HTTP_METHODS  # noqa: E402

BADGE_KEYS = {"status", "priority", "state"}
ENUM_KEYS = BADGE_KEYS | {"type", "decision", "layer", "route", "verdict", "technique", "gate", "class", "subclass", "source", "augment", "severity",
                          # trace: C·11 W3（§5.1）——B7b 五产物的枚举键补入（12 行 / 11 distinct：
                          # scope 在 wds-assets 与 wds-evolution 两产物重复登记）。值域见各 SKILL.md 结构节
                          "design_system_mode", "complexity", "category", "mode", "code",
                          "scope", "stage", "recipe", "format", "prompt_lang", "entry",
                          # trace: C·12 W2（裁定 C12-2 ③）——design 族新增顶层两键（值域四值/三值，
                          # 见 diy-design 引擎 validate）；进枚举表 = 值域白名单 + 徽章判定
                          "form_factor", "modes",
                          # trace: Q-105（用户裁定）——cis-method sessions[].method 四分支值
                          # （创新策略|问题求解|设计思维|叙事，见 SKILL.md schema）；
                          # 同名键装 HTTP 动词的三个产物已在 FREE_TEXT_FIELDS 例外登记
                          "method"}
# 自由文本字段 (doc, key)：schema 无枚举约束——同名 key 在别的产物可以是枚举。
# 依据：diy-architecture SKILL.md:43 decision=what was chosen；diy-review SKILL.md:31 type=short tag；
# diy-design SKILL.md:65 route=/path
FREE_TEXT_FIELDS = {("architecture", "decision"), ("bug-log", "type"), ("design", "route"),
                    # trace: C·2 假诊断清零——枚举键装非枚举内容的四处：
                    # brief 的 BD 决策是一句自由文本；readiness/change-proposal/test-review
                    # 的 route 装的是技能名（diy-*），不是 design 族的路由串
                    ("brief", "decision"), ("readiness", "route"),
                    ("change-proposal", "route"), ("test-review", "route"),
                    # test-gate 的 source 含日期（「用户会话 2026-09-21」）——无法静态登记白名单
                    ("test-gate", "source"),
                    # trace: C·11 W3（§5.1 连带）——新入 ENUM_KEYS 的键在别处装非枚举内容，
                    # 不登记就会把诊断打到那些产物上（同键异义，逐条给出产物出处）：
                    # scope：analysis 的范围边界、augment 的采样实现面、evolution 的本轮增量口径、
                    # readiness 的实点到文档清单（列表值）、research 的范围与方法学
                    ("analysis", "scope"), ("mutation-report", "scope"),
                    ("wds-evolution", "scope"), ("readiness", "scope"), ("research", "scope"),
                    # stage：prfaq 的 1..5 数字锚点、wds-brief / wds-trigger 各自一套中文锚点
                    ("prfaq", "stage"), ("wds-brief", "stage"), ("wds-trigger", "stage"),
                    # code：diyc-baseline 的违规码是冻结集文本，与 wds-assets 的活动码不同义
                    ("diyc-baseline", "code"),
                    # entry：wds-scenarios 的 entry 是 Q6 的自由文本答案（wds-trigger 的两值
                    # 与 wds-evolution 的存量接入|上线后持续走值表）
                    ("wds-scenarios", "entry"),
                    # type：wds-design-system 的 prefixes[].type 装的是 26 个组件类型名
                    # （Button…Spacer），全局 type=类型 在此不是枚举——不登记则每次渲染刷 26 行
                    # 诊断（R-02），且其中一个类型名恰与 6 分类值同名（Form）会被误标成「表单」
                    ("wds-design-system", "type"),
                    # trace: v4 批 4a——openapi 的 type 是 OpenAPI/JSON-Schema 机器锚点
                    # 值域（securityScheme: apiKey/http/oauth2…；schema: object/string/
                    # integer…），非本产品枚举域；不登记则 components 渲染每次刷 unmapped enum
                    ("openapi", "type"),
                    # trace: v4 批 4b——format 同族（JSON-Schema format 锚点：date-time/
                    # password 等），与 wds-assets 的 format 枚举同键异义；不登记则
                    # components 渲染刷 unmapped enum（diy-lab 实测两条），照 4a type 先例
                    ("openapi", "format"),
                    # trace: Q-105——method 入 ENUM_KEYS 后，装 HTTP 动词（get/post…）的
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
    # trace: C·3a 收口链④（任务书 §2.3：页状态收敛为单真源 5 值）——design.yaml 的
    # `pages[].status` 与 `open_questions[].status` 的增量值；极性照 R3 口径分档
    # （进行中 / 待审 → warn · 非激活终态 → dim · 终态正向 → ok）。
    # 未开始 / 已批准 是既有映射，不动（补映射 ≠ 改既有映射）
    "结构稿中": "warn", "待验收": "warn", "已移除": "dim",
    "已解决": "ok",
}
KEY_RE = re.compile(r"[^a-z0-9]+")
META_KEYS = ("project", "x-project")
# trace: Q-115——HTTP 动词值域单点同源（check 引擎常量）；此前两处字面量各持一份，
# 漂移无门。渲染侧保持 set 语义（viewer_pages 成员判定）。
HTTP_METHODS = set(_CHECK_HTTP_METHODS)

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
    # trace: v4 批 4a——openapi 接口契约扩展面（tags/通用错误 $ref/securitySchemes/
    # security）；未补键即英文裸键（零裸键纪律）。schema 见 diy-openapi/SKILL.md:结构
    "tags": "功能标签", "security": "安全要求", "securitySchemes": "鉴权方案",
    "responses": "响应定义", "schemas": "数据模型", "$ref": "引用",
    "x-decision": "关联决策", "in": "传参位置", "properties": "属性",
    "required": "必填字段",
    # trace: v4 批 4b——openapi 详情竖表行键（两层展示落形，零裸键纪律）；
    # 键名是 OpenAPI 机器锚点，产物保留英文、仅展示层译名（4a 先例）。
    # schema 单数不在列：全局表已有 selfcheck 语义「结构版本」，openapi 侧
    # schema 文本内联进请求体/响应行，不作行键，避免同键异义覆盖
    "parameters": "请求参数", "requestBody": "请求体", "externalDocs": "外部文档",
    "servers": "服务地址", "callbacks": "回调定义", "deprecated": "废弃标记",
    "headers": "响应头",
    "tasks": "任务", "blocked_reason": "阻塞原因", "test_refs": "关联用例",
    "augment": "编码后验证",
    "evidence": "执行证据", "tc": "用例", "red": "红", "green": "绿",
    "review": "审查记录", "verdict": "结论", "findings": "发现清单",
    "layer": "层", "route": "路由",
    "loop": "迭代记录", "rounds": "修复轮数", "outcome": "结果", "at": "时间",
    "technique": "设计技术", "kill_target": "目标缺陷",
    "fault_hypotheses": "故障假设", "dimension_audit": "五轴审计",
    "radius": "爆炸半径",
    "api_refs": "接口锚", "axis": "审计轴", "tcs": "轴内用例",
    "not_applicable": "不适用理由", "mutation": "变异配置",
    "enabled": "是否启用",
    "src": "来源",
    "static_checks": "静态检查链", "order": "顺序", "tool": "工具",
    "kills": "消灭问题", "gate": "门禁",
    "bugs": "缺陷记录", "class": "大类", "subclass": "中类",
    "symptom": "症状", "root_cause": "根因", "pattern": "模式",
    "source": "来源", "date": "日期", "trigger": "触发方法", "fix": "修复方案",
    "prevention": "根治机制", "taxonomy": "分类注册表",
    "plain": "通俗解释", "detail": "过程详情",
    # 修订历史（全产物通用顶层段）：{date, change, reason}
    "revisions": "修订历史", "change": "变更",
    # design 族（diy-design schema）：B2 补齐，防英文直出
    "direction": "方向", "frontend_framework": "前端框架", "tokens": "设计令牌",
    "color": "颜色", "spacing": "间距", "typography": "字号", "scale": "缩放",
    "pages": "页面", "states": "状态", "signals": "信号",
    "prototype": "结构稿", "implementation": "实现路径", "design_ref": "关联页面",
    # trace: 批 5b（cm_refs——design.yaml 顶层 cm_refs 引用位，同 feature_refs 同构）
    "cm_refs": "设计思维引用",
    "unit": "基准单位", "family_base": "正文字体", "family_heading": "标题字体",
    "bg": "背景", "surface": "表面", "text": "文字", "text_muted": "次要文字",
    "accent": "强调色", "accent_text": "强调色文字",
    # trace: C·3a 收口链④（§2.3：新增 3 键 + 从属字段 1 个）——本批增量键的中文标签。
    # open_questions 复用既有的「待决问题」（形状同 prd 同名键）；token_scope 取引擎与
    # SKILL.md 的自述语义「audit 的跳过清单」（design.py:693 / diy-design SKILL.md 规则段），
    # 不要读成「令牌作用域」；removed_reason 是自由文本（不进 ENUM_KEYS → 不做徽章，
    # 徽章化会把「被 v2 首页取代」这类原因句误标）
    "token_scope": "令牌豁免路径", "removed_reason": "移除原因",
    # trace: C·12 W2（裁定 C12-1/C12-2 ③）——design 族新增顶层两键的中文标签。
    # 语义照任务书 §0 表：form_factor = 目标表面（「写在什么上」）；modes = 默认主题模式。
    # dark 是 tokens.color 下的暗色覆盖子块（§7-5① 明暗对形状）——零裸键纪律（用户裁定
    # 2026-10-01 收严）：dark 自身 + 六角色（bg/surface/text/text_muted/accent/accent_text，
    # 六者既有标签在上方 design 族区）共七键必须全部中文，漏登记直出英文键名 = 显示缺陷
    "form_factor": "目标形态", "modes": "主题模式", "dark": "暗色",
    # spec-scan 族（diy-spec-scan schema）：规格预演扫描的歧义清单
    "scans": "扫描记录", "units": "扫描单元", "scanned": "已扫描",
    "quote": "原文摘录", "read_as": "我读到什么", "stuck": "卡在哪",
    "would_guess": "会猜成什么", "impact": "猜错后果", "suggestion": "建议裁定",
    "severity": "严重度", "units_total": "单元总数", "units_scanned": "已扫描单元数",
    "by_source": "分法计数", "卡点": "卡点", "穷举": "穷举", "交叉认证": "交叉认证",
    # deferred-actions 族（副作用纪律保留确认队列，§五 C·8）；
    # actions 是顶层列表键，渲染成 h2 标题（与 tasks / bugs 同款）
    "action": "动作", "command": "命令", "skill": "技能", "actions": "动作清单",
    # trace: C·2 缺口 2 落地（2026-09-21）——B3/B4/B5 批产物键普查补齐（test-gate /
    # test-framework / test-review / learning-progress / brainstorm / spec-kernel /
    # editorial-review / module-plan）。语义依据各技能 SKILL.md 结构节与引擎骨架常量；
    # viewer 递归渲染全部层级，故含嵌套键。同键异义者见 DOC_KEY_LABELS
    "actual": "实际值", "adopted": "符合数", "adr": "ADR 核对", "algorithm": "估算算法",
    "applied": "已加分项", "approach": "方案", "approved_by": "批准人",
    "artifacts": "内联制品", "assertion_style": "断言风格", "assessed": "画像日期",
    "assumptions": "假设清单", "audience": "目标读者", "basis": "依据",
    "bdd_naming": "BDD 命名", "blockers": "阻断项", "body": "正文", "bonus": "加分",
    "breakthroughs": "突破项", "brief": "简报正文", "build_order": "构建顺序",
    "by_level": "分层计数", "capabilities": "能力清单", "category": "类别",
    "changes": "改动说明", "checks": "自检记录", "ci": "流水线",
    "coherence": "一致性判决", "companions": "伴生文档", "completed_date": "完成日期",
    "completion_percentage": "完成度", "comprehension_note": "理解力提示",
    "concept": "核心构想", "confidence": "置信度", "constraints": "约束条件",
    "convention_baseline": "惯例基线", "corpus_size": "语料总数", "coverage": "覆盖矩阵",
    "covered": "已覆盖数", "critical": "致命", "current_step": "当前步骤",
    "data_factories": "数据工厂", "deductions": "扣分", "deferred": "后置项",
    "dependencies": "依赖项", "determinism": "确定性", "dimensions": "维度分",
    "domains": "非功能域", "dropped": "已丢弃", "duplicates": "重复覆盖",
    "duration_min": "课时时长", "estimated": "估算",
    "estimated_reduction_words": "预估削减", "excluded": "排除清单",
    "experience": "经验档", "expires": "失效日期",
    "file": "文件", "files": "文件清单", "files_reviewed": "已评审文件数",
    "fix_owner": "修复责任人", "fix_target": "修复目标", "fixtures": "夹具",
    "focus": "聚焦点", "framework": "测试框架", "gaps": "缺口清单",
    "gates": "门禁口径", "generated": "已生成", "grade": "等级",
    "hard_criteria": "硬判据", "heuristics": "盲区启发式", "high": "高",
    "idea": "关联想法", "ideas": "想法清单", "impact_words": "影响词数",
    "in_ci": "已入 CI", "inferred": "推断条目", "intent": "意图",
    "isolation": "隔离性", "items": "条目", "keys": "惯例键", "kind": "类别",
    "language": "语言", "learner": "学员画像", "lenses": "透镜", "line": "行号",
    "locations": "出现位置", "low": "低", "maintainability": "可维护性",
    "measured": "实测值", "medium": "中", "meets_length_target": "达标判定",
    "mode": "模式", "model": "结构模型", "monitoring": "监控方式",
    "network_first": "网络优先", "new": "新值", "next_recommended": "下一课推荐",
    "nfr": "非功能需求", "no": "序号", "non_goals": "非目标", "novelty": "差异点",
    "oracle": "判定基准", "original": "原文片段", "overall_risk": "总体风险",
    "p0": "P0 门槛", "p1": "P1 门槛", "package_manager": "包管理器",
    "pain_points": "痛点", "passed": "通过数", "paths": "路径清单", "pct": "覆盖率",
    "performance": "性能", "plans": "计划记录", "platform": "平台",
    "preservation": "保留走查", "priorities": "优先级",
    "priority_markers": "优先级标记", "prose": "文风编辑", "quick_wins": "速赢项",
    "reader_type": "读者类型", "recommendation": "处置建议",
    "recommendations": "建议清单", "ref": "引用", "resources": "资源",
    "result": "结果", "retired": "已退休", "reviews": "评审记录",
    "revised": "修订建议", "role": "角色",
    "row": "规则行号", "rows": "清单行数", "runner": "运行命令",
    "sampled": "采样数", "scope": "范围", "score": "得分",
    "sessions": "会话记录", "sessions_completed": "已完成课时数",
    "setups": "基建记录", "skills": "技能清单", "slug": "短名",
    "soft_criteria": "软判据", "sources": "来源清单", "specs": "规格记录",
    "stages": "阶段", "started_date": "开始日期",
    "static_check_alignment": "静态检查对齐", "structure": "结构",
    "success": "成功判据", "success_signal": "成功信号", "target": "目标",
    "techniques": "用过技术", "test_ids": "测试 ID", "tests": "已验证用例",
    "themes": "主题聚类", "thresholds": "阈值", "timeline": "时间线",
    "top": "最优先", "topic": "主题", "topics_explored": "已探索主题",
    "total": "合计", "totals": "合计", "unit_layer": "单元层",
    "unresolved": "未决条目", "vision": "批次愿景", "waivers": "豁免记录",
    "walkthrough": "三向走查", "what": "缺失内容",
    # trace: C·2——diyc-baseline（diy-tools 的豁免台账）键补齐，此前整页英文裸奔
    "baseline": "基线", "code": "违规码", "where": "位置",
    "on": "批准日期", "by": "批准人",
    # trace: C·2（V 验证补漏）——mutation-report（diy-augment 的变异运行记录）此前无类型名、
    # 键全裸奔。schema 见 diy-augment/SKILL.md:34
    "runs": "运行记录", "killed": "杀死数", "survivors": "幸存变异体",
    "equivalents": "等价变异体", "mutant": "变异体",
    # trace: C·2 缺口 2 落地（2026-09-21）——B1/B2 批产物键普查补齐（research / brief /
    # prfaq / checkpoint / readiness / project-context / story-context / retrospective /
    # change-proposal / spec / investigation）。语义依据各技能 SKILL.md 结构节与引擎骨架常量
    "a": "回答", "ac_refs": "关联验收标准", "acceptance": "验收判据", "accessed": "访问日期", "acs": "验收标准数",
    "action_items": "行动项", "addendum": "附录", "amended": "修订方式", "architecture": "架构结论",
    "area": "领域", "artifact": "目标产物", "augment_fail": "补测失败数", "availability": "可得性",
    "avoided": "避免方式", "backlog": "待探清单", "between": "关联部件", "blocked_count": "阻塞任务数",
    "boundaries": "自主边界", "carryover": "前序遗留", "case_info": "案件信息", "cases": "案件记录",
    "challenges": "挑战", "change_log": "变更日志", "change_type": "变更类型", "checkpoints": "带看记录",
    "claim": "断言", "cmd": "命令", "code_map": "代码地图", "commands": "验证命令", "concept_type": "概念类型",
    "concern": "关注点", "concerns": "关注点", "conclusion": "调查结论", "content": "内容", "contexts": "上下文包",
    "contract": "集成契约", "count": "出现次数", "counts": "计数", "critical_path": "关键路径",
    "current_state": "当前状态", "customer_faq": "客户问答", "customer_quote": "客户引语",
    "deep_dives": "深挖记录", "deployment": "部署就绪", "design_notes": "设计说明", "diagnostic_steps": "诊断步骤",
    "dimension": "维度", "distillate": "交付摘要", "do": "操作", "done": "是否完成", "done_when": "完成判据",
    "edits": "具体改动", "effort": "工作量", "error_handling": "错误处理", "essentials": "核心要素",
    "estimate": "估算", "event": "事件", "evidence_light": "无据标记", "executive_summary": "综合摘要",
    "exists": "是否存在", "expect": "预期结果", "extra_sections": "补充章节", "field": "字段",
    "files_scanned": "扫描文件数", "finding": "发现条目", "findings_by_severity": "严重度分布",
    "fix_direction": "修复方向", "follow_ups": "续案记录", "frs": "功能需求数", "getting_started": "上手方式",
    "handoff": "交接", "handoff_brief": "交接简报", "headline": "主标题", "how": "获取途径",
    "how_it_works": "运作方式", "hypotheses": "假设清单", "impacts": "影响清单", "inputs": "输入清单",
    "insights": "洞察", "integration": "部件集成", "internal_faq": "内部问答", "io_matrix": "输入输出矩阵",
    "item": "事项", "keep": "保留项", "key_dirs": "关键目录", "key_points": "要点", "label": "风险标签",
    "leader_quote": "负责人引语", "level": "扫描档位", "manual": "手工验证", "message": "问题描述",
    "metrics": "机械指标", "missing_evidence": "缺失证据", "must_frs": "必须需求数", "next": "下一步",
    "next_epic": "下一史诗", "observations": "亲手验证", "old": "原值", "opening": "开篇", "owner": "责任人",
    "part": "所属部件", "partial": "部分回顾", "parts": "部件清单", "patterns": "模式清单", "pitch": "推介叙事",
    "point": "差异点", "prep_items": "准备项", "preserve": "须保留行为", "press_release": "新闻稿",
    "prev_followup": "前轮承诺", "prfaq": "PRFAQ 正文", "prior_story": "前序故事", "problem": "问题",
    "problem_statement": "问题原述", "proposals": "变更提案", "q": "问题", "readiness": "就绪度",
    "recommended_action": "推荐动作", "reproduction": "复现方式", "researches": "研究记录",
    "resolution": "落定结论", "retro": "上轮回顾", "retros": "回顾记录", "review_order": "审阅顺序",
    "review_refs": "评审证据", "ripple": "下游连带", "rounds_total": "轮次总数", "rule": "规则正文",
    "rules": "实现规则", "scan": "扫描档案", "scenario": "场景", "section": "章节", "side_findings": "切向发现",
    "significant_changes": "重大变更", "sites": "停靠点", "solution": "解决方案", "spec": "规格引用",
    "stage": "阶段", "stakes": "利害档位", "stops": "停靠点", "stories_done": "故事完成数",
    "stories_total": "故事总数", "strength": "判定档位", "stronghold": "据点", "subheadline": "副标题",
    "synthesis": "综合结论", "target_users": "目标用户", "task": "任务描述", "tc_refs": "关联测试用例",
    "tech_health": "技术健康", "test": "验证方法", "testing": "测试就绪", "theme": "主题", "time_window": "时间窗",
    "timeline_impact": "时间线影响", "tree": "目录树", "url": "网址", "value": "价值要点", "value_props": "价值主张",
    "verification": "验证记录", "verify": "完成判据", "watch": "观测结果", "who": "用户角色",
    "why_separate": "分离理由", "wins": "亮点", "would_resolve": "解开条件",
    # trace: C·11 W3（§5.1）——B7b 批产物键补齐（59 条，机械重数见回报：登记源并集 − 假阳性
    # in/out + 实测补漏 related/pr）。键取自各产物 YAML 实测（骨架 + 富内容）+ 各 SKILL.md
    # 结构节；同键异义者不在此表（走 DOC_KEY_LABELS）
    # wds-design-system：11 段组件模板 + 前缀表 / 分类表 / 令牌命名空间
    "accessibility": "无障碍", "animations": "动效", "aria": "ARIA 标注", "behavior": "行为",
    "best_practices": "最佳实践", "categories": "分类表", "complexity": "复杂度",
    "design_system_mode": "设计系统开关", "interactions": "交互", "keyboard": "键盘操作",
    "layout": "布局", "library_component": "库组件", "namespaces": "令牌命名空间",
    "prefix": "前缀", "prefixes": "前缀表", "related": "关联组件", "screen_reader": "屏幕阅读器",
    "styling": "样式", "token_refs": "令牌引用", "usage": "用法", "used_in": "使用页面",
    "variants": "变体", "version": "版本", "visual_properties": "视觉属性",
    "when_not_to_use": "不适用场景", "when_to_use": "适用场景",
    # wds-assets：活动清单 / 资产引用 / 提示词索引 / 演示配方（`design` 与 wds-evolution 共用）
    "activities": "活动清单", "assets": "资产清单", "design": "设计", "format": "格式",
    "format_card": "配方卡", "frames": "帧清单", "job": "帧职责", "n": "序号",
    "presentation": "演示配方", "principles": "原则清单", "prompts": "提示词索引",
    "recipe": "配方", "style": "风格参数", "prompt_lang": "提示词语言",
    # wds-evolution：Kaizen 六相段 + 候选清单 + 优先级公式（`test`/`scope` 已有全局标签，
    # 不改：它们是跨产物共用键）
    "analysis": "分析", "candidates": "候选清单", "criteria": "判据清单", "delivery": "交付",
    "entry": "入口", "formula": "优先级公式", "implement": "实现",
    "kaizen_priority": "Kaizen 优先级", "learning": "学习因子", "pr": "变更请求",
    # analysis：question 四字段 + architecture 段 + 组件位置
    "codebase": "代码库路径", "data_flow": "数据流", "layers": "分层", "location": "位置",
    "mermaid": "Mermaid 图", "output_format": "输出形态", "overview": "总览",
    "tech_stack": "技术栈", "time_box": "时间盒",
    # v4 批 2c——selfcheck.yaml（diy-selfcheck 主产物，schema 骨架照批 2c 任务书 §3）：
    # 此前缺失的键渲染英文裸键（零裸键纪律）。id/date/status/summary/findings/target/
    # path/n/source/severity/claim/actual/confidence/total/by_source/revisions/change/
    # reason/project 已有全局标签，不在本块重复
    "schema": "结构版本", "anchor": "锚点", "disposals": "处置记录",
    "rescans": "复扫记录", "b_review": "B 部分机制评价",
    "md5": "MD5 指纹", "commit": "提交哈希", "exec_form": "执行形态",
    "shards": "分片数", "ss_ref": "关联预演条目", "issue": "问题",
    "round1": "第一轮复扫", "round2": "第二轮复扫", "cleared": "清零项",
    "ref_checked": "已核引用数", "ref_false": "失实引用数", "landing": "落点",
    # trace: Q-105（底单 :367 ⑧）——cis-method 四分支 deliverable 键补齐（115 缺 + deliverable）。
    # 键表逐条取自 steps/02~05「本分支结构」节；键名是 schema 机器锚点，产物保留英文、
    # 仅展示层译名（C·11 W3 先例）。constraints/timeline/action_items/resolution 已有全局标签，不重复。
    # cis-method 创新策略 分支 deliverable 键
    "business_model_innovation": "商业模式创新", "company_name": "公司名称", "competitive_dynamics": "竞争动态", "current_business_model": "现有商业模式",
    "current_situation": "现状", "decision_gates": "决策门", "disruption_vectors": "颠覆向量", "innovation_initiatives": "创新举措",
    "key_hypotheses": "关键假设", "key_risks": "关键风险", "lagging_indicators": "滞后指标", "leading_indicators": "领先指标",
    "market_insights": "市场洞察", "market_landscape": "市场格局", "market_opportunities": "市场机会", "model_weaknesses": "模式弱点",
    "option_a_cons": "选项A缺点", "option_a_description": "选项A描述", "option_a_name": "选项A名称", "option_a_pros": "选项A优点",
    "option_b_cons": "选项B缺点", "option_b_description": "选项B描述", "option_b_name": "选项B名称", "option_b_pros": "选项B优点",
    "option_c_cons": "选项C缺点", "option_c_description": "选项C描述", "option_c_name": "选项C名称", "option_c_pros": "选项C优点",
    "partnership_opportunities": "伙伴机会", "phase_1": "阶段一", "phase_2": "阶段二", "phase_3": "阶段三",
    "recommended_strategy": "推荐战略", "revenue_cost_structure": "收入成本结构", "risk_mitigation": "风险缓解", "strategic_challenge": "战略挑战",
    "strategic_focus": "战略焦点", "strategic_whitespace": "战略空白", "success_factors": "成功因素", "technology_enablers": "技术使能",
    "unmet_jobs": "未满足任务", "value_chain_opportunities": "价值链机会", "value_proposition": "价值主张",
    # cis-method 问题求解 分支 deliverable 键
    "action_steps": "行动步骤", "adjustment_triggers": "调整触发", "contributing_factors": "促成因素", "creative_alternatives": "创意备选",
    "driving_forces": "驱动力", "evaluation_criteria": "评估判据", "generated_solutions": "生成解法", "implementation_approach": "实施方式",
    "initial_problem": "初始问题", "key_insights": "关键洞察", "key_learnings": "关键收获", "problem_boundaries": "问题边界",
    "problem_category": "问题类别", "problem_context": "问题背景", "problem_title": "问题标题", "recommended_solution": "推荐方案",
    "refined_problem_statement": "精炼问题陈述", "resources_needed": "资源需求", "responsible_parties": "责任方", "restraining_forces": "阻碍力",
    "root_cause_analysis": "根因分析", "solution_analysis": "方案分析", "solution_methods": "解法方法", "solution_rationale": "推荐理由",
    "success_criteria": "成功判据", "success_metrics": "成功指标", "system_dynamics": "系统动态", "validation_plan": "验证计划",
    "what_to_avoid": "避免做法", "what_worked": "有效做法",
    # cis-method 设计思维 分支 deliverable 键
    "challenge_statement": "挑战陈述", "design_challenge": "设计挑战", "empathy_map": "共情图", "features_to_test": "待测特性",
    "generated_ideas": "生成想法", "hmw_questions": "怎样才能问题", "ideation_methods": "构思方法", "key_observations": "关键观察",
    "pov_statement": "观点陈述", "problem_insights": "问题洞察", "project_name": "项目名称", "prototype_approach": "原型方式",
    "prototype_description": "原型描述", "refinements": "精修建议", "testing_plan": "测试计划", "top_concepts": "入选概念",
    "user_feedback": "用户反馈", "user_insights": "用户洞察",
    # cis-method 叙事 分支 deliverable 键
    "adaptation_suggestions": "改编建议", "additional_versions": "额外版本", "audience_considerations": "受众适配", "best_channels": "最佳渠道",
    "character_voice": "角色声音", "complete_story": "完整故事", "conflict_tension": "冲突张力", "core_narrative": "核心叙事",
    "emotional_arc": "情绪弧", "emotional_touchpoints": "情绪触点", "extended_version": "长版", "feedback_plan": "反馈计划",
    "framework_name": "框架名称", "key_messages": "关键信息", "medium_version": "中版", "opening_hook": "开场钩子",
    "refinement_opportunities": "精修机会", "short_version": "短版", "story_beats": "故事节拍", "story_purpose": "故事目的",
    "story_type": "故事类型", "target_audience": "目标受众", "tone_notes": "语气注意", "transformation": "转变",
    "deliverable": "交付内容",
}
# 值标签（词表正典来源）：机器层中文化后键=中文值、值=展示标签，多数同名。
