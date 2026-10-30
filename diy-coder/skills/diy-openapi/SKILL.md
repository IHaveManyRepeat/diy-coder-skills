---
name: diy-openapi
description: Derive or update an OpenAPI 3.1 interface contract (openapi.yaml) from prd.yaml and architecture.yaml for interface-first review. Use when the user wants to define an API contract, generate openapi, or revise an existing openapi.yaml.
# ↑ 中文：从 prd.yaml 与 architecture.yaml 推导或更新 OpenAPI 3.1 接口契约（openapi.yaml），供接口先行评审。用户想定义 API 契约、生成 openapi，或修订既有 openapi.yaml 时触发。
phase: 3-solutioning
precededBy: [diy-architecture]
followedBy: []
required: false
line: mainline
outputs: openapi.yaml
---

# diy-openapi — 接口契约（OpenAPI 3.1 单一源）

你是接口契约设计者。产物是**一个合法的 OpenAPI 3.1 YAML 文件**——不是散文，不是 markdown 副本。契约从 prd.yaml 的需求与 architecture.yaml 的决策推导而来。

## 激活时

1. 读 `{project-root}/diy-coder.yaml`；解析 `project.communication_language` / `project.document_output_language` / `paths.output_dir`。
   全程用 `communication_language` 对话；产物里的叙述文字（`info.description` / `summary` / `description`）用 `document_output_language` 写。机器锚点（ID、枚举值、文件名）逐字保留。
   缺省链：`paths.output_dir` 一律取 `diyc.py resolve` 回执（引擎缺省 `diy-output`，异常形状降级并 warning）；缺 `document_output_language` 落 `project.communication_language`；两者皆缺则跟随用户当前消息的语言，并在收尾一行说明。
   实例名只在本次激活参数出现 `--instance <name>` 时才传（无头侧入口 `runner.py --instance`；交互侧由用户在发起消息里给出同一旗标）；未传时回执的 `output_dir` 即主线平铺根。
   实例解析（FR-4.5/D-9）由工具脚本执行：运行 `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" resolve [--instance <name>] --json`，把回执里的 `output_dir` 当作本次运行唯一的读写根目录。
2. 读 `{output_dir}/prd.yaml` 与 `{output_dir}/architecture.yaml`。任一份缺席、或其 `project.status` 不是 `已定稿` → 向用户预警并问是否照样继续。
3. 接口面判定：由 architecture 的 components/decisions 加 FR 集合推导。项目没有接口面（纯 CLI、库、技能集）→ 说明并停止——没有接口的 openapi.yaml 是虚构。
4. 目标文件：`{output_dir}/openapi.yaml`。判意图：**Create**（文件缺席）或 **Update**（文件在场）。含糊时直接问。
`{output_dir}/openapi.yaml` 只在续接检测、定目标任务、按 `id:` 定位改一条记录、或判 Create/Update 时才打开；校验/统计走 `diyc.py` 回执，模型只读结论简报，绝不重读规则原文。

## 工作流

1. 逐功能推导端点——一功能内全部端点一批带用户走查；跨功能共享资源单归属：归主功能，他功能仅经 `x-fr` 关联；延后的细节落 `[假设]`。
2. 写 `{output_dir}/openapi.yaml`，`x-project.status: 草稿`；告知用户路径。
3. 立即渲染供审阅。渲染是静默旁路——只写调用命令，不新增「打开浏览器 / 报告路径等待查看 / 阻塞等待」交互点：`python "{project-root}/.claude/skills/diy-viewer/scripts/viewer.py" --project-root "{project-root}"`（resolved 实例时附 `--instance <name>`）。审阅发生在 接口总览 表与 HTML 上，不在裸 YAML 上。
4. Update 模式：改写前 `cp {output_dir}/openapi.yaml {output_dir}/openapi.yaml.prev`；把变更信号落到被点名的 operation 上、bump `updated`、`operationId` 保持稳定；新稿写完后跑 `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" check --type openapi --previous {output_dir}/openapi.yaml.prev --json`（exit 0 = 无记录丢失）。**非 0 一律不删 `.prev`**：`ID_UNSTABLE` → 从快照找回被丢记录、补进新稿、重跑到 exit 0 再删；`MISSING_FILE` / `UNPARSABLE_YAML` → 快照不可用、安全网失效，停手告知用户，确认前不得再写。清理干净才删掉 `.prev` 文件；重跑渲染刷新 HTML：`python "{project-root}/.claude/skills/diy-viewer/scripts/viewer.py" --project-root "{project-root}"`（resolved 实例时附 `--instance <name>`）。
5. 终门（机械）：先写 `x-project.status: 已定稿`——`已定稿` 是门检查的对象，不是门的产物——再跑 `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" check --type openapi --final --json`；exit 0 是唯一放行，逐条修完上报的违规再重跑（`known[]` 里的条目是用户已认可的基线，不是待修违规）；JSON 回执（含计数）即收口证据。门失败 → `x-project.status` 回退 `草稿`，修完重走本步。白话门槛：合法 OpenAPI 3.1 结构、零未确认假设、每个 `x-fr` ID 与每个功能 tag 的 `F-x` 锚都能在 prd.yaml 里解析到、`securitySchemes` ＋ `security` 在场、每个 operation 挂通用错误 `$ref`、每个 operation 都经用户审阅。
6. 重跑渲染：`python "{project-root}/.claude/skills/diy-viewer/scripts/viewer.py" --project-root "{project-root}"`（resolved 实例时附 `--instance <name>`）；收尾一行：路径 + JSON 回执里的计数。

## 结构

`openapi.yaml`（标准 OpenAPI 3.1 之上的 diy-coder 约定）：

```yaml
openapi: 3.1.0
x-project:                       # diy-coder 元数据扩展（viewer 渲染它）；元数据只在这里
  name: string
  status: 草稿 | 已定稿          # 写状态的唯一位置
  created:                        # 建文件时留空，跑 diyc stamp 盖秒级章（此后不改）
  updated:                        # 每次写回后跑 diyc stamp 刷秒级章
  revisions: []                  # {date, change, reason} —— 改既有 operation 时追加
info:
  title: string
  version: 0.1.0                 # 契约版本，与 status 无关
  description: one paragraph
tags:                             # 顶层声明：每个功能一条，名含功能锚（F-x 功能名）
  - name: F-1 用户管理
security: []                      # 顶层安全要求块必在场；security: [] = 显式无鉴权（决策留痕，不裸奔）
paths:
  /users:
    get:
      operationId: listUsers
      summary: string
      tags: [F-1 用户管理]        # 每个 operation 必挂功能 tags（锚 F-x 须在 prd.yaml 解析到）
      x-fr: [FR-x.y]             # 只引用 prd.yaml 里已有的 ID
      responses:
        "200":                   # 状态码是字符串，带引号
          description: OK
        "404":
          $ref: "#/components/responses/NotFound"   # 每个 operation 至少一条通用错误 $ref
components:
  schemas:
    ProblemDetails:              # RFC 9457 problem details——通用错误体
      type: object
      required: [type, title, status]
      properties:
        type: {type: string}
        title: {type: string}
        status: {type: integer}
  responses:                     # 通用状态码默认清单＝400/401/403/404/409/500 按需定义，至少一条
    NotFound:
      description: 资源不存在
      content:
        application/problem+json:
          schema: {$ref: "#/components/schemas/ProblemDetails"}
  securitySchemes:
    apiKey:
      type: apiKey
      name: Authorization
      in: header
      x-decision: D-1             # 引架构侧安全决策 ID（无鉴权时该留痕在架构侧决策）
```

## 规则

- **合法 OpenAPI 3.1 高于一切。** 根键遵循规范；项目元数据住在 `x-project` 扩展里（与 prd 的 project 块同形；viewer 会读它）。
- **ID 链是硬契约。** 每个 operation 带 `x-fr: [FR-x.y]`，引用 prd.yaml 里已有的 FR ID——只引用，绝不复制。Update 对账确曾改写既有 operation 时，往 `x-project.revisions` 追加一条 `{date, change, reason}`（落点在 `x-project` 块内——裸根键违反合法 3.1；`change` 引用 `operationId`、不复制内容）。
- **DRY。** 重复的形状进 `components/schemas`、重复的状态码响应进 `components/responses`，一律 `$ref` 引用；不重复内联 body 与错误体。
- **鉴权必答。** 接口面在场（本技能未停止）→ 必设计 `components.securitySchemes` ＋顶层 `security`：有鉴权时每 scheme 带 `x-decision: D-*` 引架构侧安全决策；无鉴权＝显式 `security: []` ＋架构侧 `D-*` 决策留痕——两者皆不许缺席（终门硬校验，缺席即红）。
- **范围 = FR 集合。** 只建模需求真正要的端点——不臆造 CRUD、不做没人要的版本机制。
- **未决项留在文件里。** 任何等用户确认的推断——字段名、状态码、错误形状——都要带 `[假设]` 前缀写在 YAML **值**上，绝不只在对话里列。

- **精准简练。** 写进产物的每条内容都要精准、简练：一条只讲一件事；不复述上游已写的信息（引用 ID）；不写没有信息量的套话。

- **写作纪律。** 主字段 = 大白话主句；数字/枚举内联；机器语法（命令/旗标/路径）进括号；机器锚点逐字保留（文件名、token 名、CLI 旗标）——把锚点改写成中文会打断 `diy-design` 的 detect 启发式。schema 若定义 `plain`：一行写清该条目为什么存在，绝不写是什么（转述会漂移）；只写难懂的条目。若定义 `detail`：过程叙述——结论留在主字段。
