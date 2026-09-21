# -*- coding: utf-8 -*-
"""diy-bmb-builder 确定性引擎：技能树脚手架 + 模板机 + 预扫 + 结构扫描 + 过程日志 + 终门 + 报告渲染。

机制（技能工厂的 Build / Edit / Analyze 三意图共用这一个引擎）——

  scaffold  建技能目录骨架：`--name N` 归一到 hyphen-case（≤64），SKILL.md 从内置模板起手
            （四段中文标题 + 母本 §1/§2/§3/§4/§6 冻结句），按 `--dirs` stub 子目录。
            落点：默认 `{project-root}/.claude/skills/`（安装面，落此即用）；`--to-source` 落
            套件源 `{project-root}/diy-coder/skills/`（进 git 分发），该层缺席 → MISSING_FILE
            拒绝且**不代建父目录**；`--to-source` 与 `--dest` 互斥（同给 = 用法错误 exit 2）。
            目标已存在 → FILE_CONFLICT 拒绝；`--force` 才允许 rmtree 重建。
            **--force 硬护栏**：目标名命中 `diy-coder/skills/` 下已建技能名、或命中本套件
            禁改面（根脚本 / `diy-output` / `docs` / `diy-coder`）→ 即使 --force 也拒绝
            （FILE_CONFLICT）。护栏名单由**引擎自身位置**（`<套件根>/diy-coder/skills`）与
            静态名单合成，故与 --project-root 指到哪无关。
            回执另含 `files_created`（正斜杠、相对 project-root）。

  template  模板机：`{if-X}...{/if-X}` 条件块由内向外展开（X ∈ `--true` 则为真、否则整块删），
            再按 `--set k=v` 替换 `{k}`。两级失败语义照源：**残留 `{if-}` 标记 = exit 3 硬失败**
            （括号写错，发出去会把标记原样 ship）且零产出；**残留 `{token}` = 不算失败**，
            列进回执 `tokens_remaining` 交人判断（`{project-root}` 这类运行时 token 是合法的）。

  prepass   两套源预扫合并成一个子命令，`--set metrics|integrity|all`（默认 all），
            输出统一成**一份** JSON 回执：
              metrics  逐文件 token 计数（tiktoken，缺席时 chars//4 并标 method）、行数、
                       废话模式 grep（"make sure to"/"don't forget"/"it is important" 及
                       中文对应「务必/别忘了/重要的是」）、回指模式（"as described above" /
                       「如上所述」）、编号前缀文件名标记。**只出数、不判违规**。
              integrity 数字前缀阶段文件名散在技能根 → 违规（阶段文件须落 `steps/`）；
                       `## On Exit` / `## 退出时` 段 → 违规（diy 无 exit hook，永不执行）；
                       残留模板标记 → 违规；必备四段中文标题缺失 → 违规；`steps/` 编号缺口
                       与 SKILL.md 引用的步骤文件缺席 → 违规；语言直白度反模式（"you should"/
                       "please"/"handle appropriately"/"when ready" 及中文对应）→ **warning**。

  scan      机械面：`--check all|path-standards|scripts`（默认 all）。
            path-standards：`.md` 里的绝对路径 / `../` 越界 / `./<目录>/` 跨目录引用（围栏内豁免）。
            scripts：`scripts/*.py` 的套件合规——`# -*- coding: utf-8 -*-` 头、中文模块 docstring、
            `sys.stdout.reconfigure(encoding="utf-8")`、至少一处 `# trace:`；`input(` 判违规
            （无头态阻塞）。缺 argparse / 缺 `sys.exit` 记 warning。

  mlog      过程日志（memlog 的 diy 落点）：`--dir D` + 三动作 init / append / set-complete。
            **文件名由调用方经 `--file NAME` 显式给**（不靠 --dir 反推）；`init` 收 `--subject S`。
            `--file` **只收纯文件名**：含路径分隔符（`/` 或反斜杠）、`.`/`..`、空白名 → NAME_ILLEGAL
            （写面不许越出 `--dir`，否则边界形同虚设）。
            只追加、不重写历史；读改写走临时文件 + fsync + `os.replace`（崩不半写）。
            回执恒为一行 JSON，含共同键 + `{file, n, appended}` 三附加键（人读态与 --json 无关）。

  check     产物技能终门。基础项（中途可跑）：SKILL.md 在场；四段中文标题齐备；母本
            §1/§2/§3/§4/§6 锚串逐字在场；frontmatter 六字段（phase/precededBy/followedBy/
            required/line/outputs）+ name/description 齐备且形态合法；**自足性**——技能根相对
            引用（`steps/` `references/` `scripts/` `assets/`）必须落在技能目录内，越界引用
            （`../`）判内容依赖违规。`--final` 附加结构终门：SKILL.md ≤90 行、`steps/` 至少
            一个步骤文件、每步 H1 `# Step N — <中文步名>` + `**Read (input):**`/`**Write (output):**`
            行 + 步号连续 + 每步结尾点名下一个要读的文件（末步声明不再读）。
            **自足性豁免清单**（内容面判据，非字面「禁一切跨目录引用」）：`{project-root}` 令牌
            路径（母本 §1 的 diyc.py 调用、§3 的 diy-coder.yaml、§5 的 viewer 调用）、
            `{output_dir}` 产物路径、`path:<relative>` 引用式路径——三者一律豁免。

  render    由脚本把 `findings.json` 渲染成 `skill-analysis-report.md` + `.html`（十二件
            报告集里的最后两件）。**绝不手写 HTML**；findings.json 形状不对或主体仍是占位
            则拒绝渲染（零产出）。

违规码：复用 batch3-contract §3 冻结集（MISSING_FILE / UNPARSABLE_YAML / EMPTY_FIELD /
ENUM_INVALID / SET_MISMATCH）；本批点名的新增码中本引擎用到 NAME_ILLEGAL（名字/文件名形态非法；
`mlog --file` 只收纯文件名——含路径分隔符、`.`/`..`、空白名一律拒绝，否则 `--dir` 的边界形同虚设）、
FILE_CONFLICT（目标已存在 / 破坏性护栏 / 内容依赖越界）、TOKEN_UNRESOLVED（未解析 `{...}` 令牌
与残留模板标记）；未用到 UNKNOWN_ID / ID_UNSTABLE（本技能无 ID 集合面，`--previous` 判 no）。
另有一个**套件既有码** `INTERNAL_ERROR`：不在 §3 冻结清单内，也非本批新造——沿用 `diyc.py`
批次 3.5 P2 的顶层兜底先例（未预期异常转回执，不让异常裸奔、不静默吞错），故在此登记。
回执共同键 {ok, command, project_root, output_dir, violations[{code,where,msg}], warnings[], counts}；
warnings 与 violations 同形；where 正斜杠、相对 project-root；exit 0 唯一放行，1 = 违规/被拒绝，
2 = 用法错误（argparse），3 = template 残留 `{if-}` 标记。`--output-dir` 全部子命令必填
（引擎不读 diy-coder.yaml，不设默认）；`--project-root` 默认 `.`。路径参数里的 `{...}` 令牌
一律拒绝（TOKEN_UNRESOLVED）——**唯一例外 `{project-root}`**，由引擎按 `--project-root` 自解析。
"""
import argparse
import ast
import html as html_mod
import io
import json
import os
import re
import shutil
import sys
from datetime import datetime

import yaml

SKILL_FILE = "SKILL.md"
STEPS_DIR = "steps"
KNOWN_DIRS = ("steps", "references", "scripts", "assets")
DEFAULT_DIRS = "steps"
SCAN_MD_DIRS = ("steps", "references", "assets")
INSTALL_REL = (".claude", "skills")
SOURCE_REL = ("diy-coder", "skills")
FINDINGS_FILE = "findings.json"
REPORT_MD = "skill-analysis-report.md"
REPORT_HTML = "skill-analysis-report.html"

NAME_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
NAME_MAX = 64
SKILL_MD_MAX_LINES = 90
TOKEN_RE = re.compile(r"\{([a-zA-Z][a-zA-Z0-9_.-]*)\}")
IF_MARKER_RE = re.compile(r"\{/?if-[a-zA-Z0-9_-]+\}")
IF_BLOCK_RE = re.compile(r"\{if-([a-zA-Z0-9_-]+)\}(.*?)\{/if-\1\}", re.DOTALL)
PROJECT_ROOT_TOKEN = "{project-root}"

REGISTRY_FIELDS = ("phase", "precededBy", "followedBy", "required", "line", "outputs")
SECTION_TITLES = ("## 激活时", "## 工作流", "## 结构", "## 规则")
INVALID_SECTIONS = ("## On Exit", "## Exiting", "## 退出时")
# 技能根相对引用：须是带扩展名的文件（`steps/01-x.md`）；`steps/*.md`、`steps/01-<名>.md` 等占位不在此列
LOCAL_DIR_RE = re.compile(r"(?<![\w/.-])(steps|references|scripts|assets)/([\w.-]+\.[A-Za-z0-9]+)")
ESCAPE_RE = re.compile(r"(?<![\w/.\-])\.\./[^\s`\"'()]*")
ABS_PATH_RE = re.compile(r"(?<![\w/.\-])(?:[A-Za-z]:[\\/][^\s`\"'()]*"
                         r"|/(?:Users|home|opt|var|tmp|etc|usr|mnt)/[^\s`\"'()]*"
                         r"|~/[^\s`\"'()]*)")
CROSS_DIR_RE = re.compile(r"(?<![\w/.\-])\./(?:steps|references|scripts|assets)/[^\s`\"'()]*")
FENCE_RE = re.compile(r"^```", re.M)
STEP_FILE_RE = re.compile(r"^(\d{2})-([\w.-]+)\.md$", re.M)
STEP_MENTION_RE = re.compile(r"(?<![\w-])\d{2}-[\w.-]+\.md")
STEP_H1_RE = re.compile(r"^# Step (\d+) — .*[一-鿿]")

ENTRY_TYPES = ("decision", "direction", "assumption", "gap", "note", "event")
GRADES = ("excellent", "good", "fair", "poor")

# 母本冻结锚串（逐字；check 断言产物技能 SKILL.md 携带，本技能自己亦携带）
FROZEN_INSTANCE = ('实例解析（FR-4.5/D-9）由工具脚本执行：运行 '
                   '`python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" resolve '
                   '[--instance <name>] --json`，把回执里的 `output_dir` 当作本次运行唯一的读写根目录。')
FROZEN_CONFIG_HEAD = ('读 `{project-root}/diy-coder.yaml`；解析 '
                      '`project.communication_language` / `project.document_output_language` / '
                      '`paths.output_dir`。')
FROZEN_CONFIG_ANCHOR = ('解析 `project.communication_language` / '
                        '`project.document_output_language` / `paths.output_dir`')
FROZEN_CONFIG_LANG = ('全程用 `communication_language` 对话；产物里的叙述文字用 '
                      '`document_output_language` 写。机器锚点（ID、枚举值、文件名）逐字保留。')
FROZEN_CONFIG_FALLBACK = ('缺省链：`paths.output_dir` 一律取 `diyc.py resolve` 回执（引擎缺省 '
                          '`diy-output`，异常形状降级并 warning）；缺 `document_output_language` '
                          '落 `project.communication_language`；两者皆缺则跟随用户当前消息的语言，'
                          '并在收尾一行说明。')
FROZEN_CONFIG_INSTANCE = ('实例名只在本次激活参数出现 `--instance <name>` 时才传（无头侧入口 '
                          '`runner.py --instance`；交互侧由用户在发起消息里给出同一旗标）；'
                          '未传时回执的 `output_dir` 即主线平铺根。')
FROZEN_READ = ('读取纪律：预载预算 = 本文件、上述配置与回执、`steps/` 下当前那一个文件——绝不批量预载；'
               '执行期读取以每个步骤开头的 `Read (input)` 行为唯一权威，**主文件不列举封闭清单**。')
FROZEN_PRECISE = ('- **精准简练。** 写进产物的每条内容都要精准、简练：一条只讲一件事；'
                  '不复述上游已写的信息（引用 ID）；不写没有信息量的套话。')
FROZEN_DISCIPLINE = ('- **写作纪律。** 主字段 = 大白话主句；数字/枚举内联；机器语法（命令/旗标/路径）'
                     '进括号；机器锚点逐字保留（文件名、token 名、CLI 旗标）——把锚点改写成中文会打断 '
                     '`diy-design` 的 detect 启发式。schema 若定义 `plain`：一行写清该条目为什么存在，'
                     '绝不写是什么（转述会漂移）；只写难懂的条目。若定义 `detail`：过程叙述——结论留在主字段。')
FROZEN_ANCHORS = (FROZEN_INSTANCE, FROZEN_CONFIG_ANCHOR, FROZEN_READ,
                  FROZEN_PRECISE, FROZEN_DISCIPLINE)

# 起手模板（scaffold 用；`{skill-name}` 由脚手架替换，其余 {...} 是产物侧的运行时令牌，原样保留）
SKILL_TEMPLATE = "\n".join([
    "---",
    "name: {skill-name}",
    "description: '<5–8 词英文摘要>. Use when the user says \"<触发语>\".'",
    "# ↑ 中文：<一句话中文定位与触发语——两处占位填完后删本行>",
    "phase: any",
    "precededBy: []",
    "followedBy: []",
    "required: false",
    "line: any",
    "outputs: <产物描述；真零产物写 —>",
    "---",
    "",
    "# {skill-name} — <一句话定位>",
    "",
    "<一段：你是谁、输入是什么、产出是什么、边界在哪。>",
    "",
    "## 激活时",
    "",
    "1. " + FROZEN_CONFIG_HEAD,
    "   " + FROZEN_CONFIG_LANG,
    "   " + FROZEN_CONFIG_FALLBACK,
    "   " + FROZEN_CONFIG_INSTANCE,
    "   " + FROZEN_INSTANCE,
    "2. 硬门：<输入不满足时的拒绝行 + 零产出 + 路由>。",
    "3. " + FROZEN_READ,
    "4. 读 `steps/` 下的第一个步骤文件并照做（裸 `steps/*.md` 路径从本技能安装目录解析）。"
    "每步结尾点名下一个要读的文件。",
    "",
    "## 工作流",
    "",
    "全局步骤纪律：一次只加载一个 `steps/` 文件——绝不批量预载；每步输出整块给出，不在步骤中间提问。",
    "",
    "1. `steps/01-<名>.md` — <做什么>（每步开头一行 `Read (input)` / `Write (output)`）。",
    "",
    "## 结构",
    "",
    "<产物形状：路径与字段；无产物则写明「无 YAML 产物」与不做渲染的理由。>",
    "",
    "## 规则",
    "",
    "1. <硬规则：写面边界、门禁、终门命令、与相邻技能的边界句>。",
    "",
    FROZEN_PRECISE,
    "",
    FROZEN_DISCIPLINE,
    "",
])

# 静态禁改面（§2.6 的根脚本与目录名；已建技能名由引擎自身位置动态合成）
STATIC_PROTECTED = frozenset([
    "install.py", "viewer.py", "help.py", "runner.py", "diyc.py", "diyc_lib.py",
    "diyc_check.py", "diyc_writeback.py", "exp-sync.py", "diy-coder.yaml",
    "diy-output", "docs", "diy-coder", ".git", "suite-texts.md",
])
WASTE_PATTERNS = (
    (re.compile(r"\b[Mm]ake sure (?:to|you)\b"), 'Defensive: "make sure to/you"'),
    (re.compile(r"\b[Dd]on'?t forget (?:to|that)\b"), 'Defensive: "don\'t forget"'),
    (re.compile(r"\b[Rr]emember (?:to|that)\b"), 'Defensive: "remember to/that"'),
    (re.compile(r"\b[Bb]e sure to\b"), 'Defensive: "be sure to"'),
    (re.compile(r"\b[Pp]lease ensure\b"), 'Defensive: "please ensure"'),
    (re.compile(r"\b[Ii]t is important (?:to|that)\b"), 'Defensive: "it is important"'),
    (re.compile(r"务必"), "废话模式：务必"),
    (re.compile(r"别忘了"), "废话模式：别忘了"),
    (re.compile(r"重要的是"), "废话模式：重要的是"),
)
BACKREF_PATTERNS = (
    (re.compile(r"\bas described above\b"), 'Back-reference: "as described above"'),
    (re.compile(r"\bas mentioned (?:above|in|earlier)\b"), 'Back-reference: "as mentioned above"'),
    (re.compile(r"\bsee (?:above|the overview)\b"), 'Back-reference: "see above/the overview"'),
    (re.compile(r"如上所述"), "回指：如上所述"),
    (re.compile(r"见上文"), "回指：见上文"),
)
DIRECTNESS_PATTERNS = (
    (re.compile(r"\byou should\b", re.I), '直白度：you should → 改直陈祈使'),
    (re.compile(r"\bhandle appropriately\b", re.I), '直白度：handle appropriately → 写明怎么做'),
    (re.compile(r"\bwhen ready\b", re.I), '直白度：when ready → 换成可判定的条件'),
    (re.compile(r"你应当"), "直白度：你应当 → 改直陈祈使"),
    (re.compile(r"请确保"), "直白度：请确保 → 改直陈祈使"),
    (re.compile(r"适当处理"), "直白度：适当处理 → 写明怎么做"),
    (re.compile(r"准备好后"), "直白度：准备好后 → 换成可判定的条件"),
)
SCRIPT_DOCSTRING_ZH_RE = re.compile(r"[一-鿿]")


# trace: diy-bmb-builder 违规项构造（统一 {code, where, msg} 形态）
def v(code, where, msg):
    return {"code": code, "where": where, "msg": msg}


# trace: diy-bmb-builder 非空判定（None / 空白字符串均视为空）
def nonempty(value):
    return value is not None and str(value).strip() != ""


# trace: diy-bmb-builder where 显示口径（正斜杠 + 相对 project-root；越界回退绝对路径）
def display_path(path, project_root):
    try:
        rel = os.path.relpath(path, project_root)
    except ValueError:
        rel = os.path.abspath(path)
    if rel.startswith(".."):
        return os.path.abspath(path).replace("\\", "/")
    return rel.replace("\\", "/")


# trace: diy-bmb-builder 名字归一（小写、非字母数字折成单连字符、去首尾、截到 64）
def normalize_name(raw, max_len=NAME_MAX):
    text = re.sub(r"[^a-z0-9]+", "-", str(raw).strip().lower()).strip("-")
    if len(text) > max_len:
        text = text[:max_len].strip("-")
    return text


# trace: diy-bmb-builder 引擎自身所在的套件 skill 目录（护栏名单位置无关地取到）
def suite_skills_dir():
    here = os.path.dirname(os.path.abspath(__file__))       # .../skills/diy-bmb-builder/scripts
    skill_dir = os.path.dirname(here)                       # .../skills/diy-bmb-builder
    return os.path.dirname(skill_dir)                       # .../skills


# trace: diy-bmb-builder 禁改面名单（静态名单 + 套件内已建技能名）
def protected_names():
    names = set(STATIC_PROTECTED)
    base = suite_skills_dir()
    if os.path.isdir(base):
        names |= {name for name in os.listdir(base)
                  if name != "diy-bmb-builder" and os.path.isdir(os.path.join(base, name))}
    return names


# trace: diy-bmb-builder 路径参数解析：拒绝未解析 {…}（唯 {project-root} 例外，按 --project-root 自解析）
def resolve_arg_path(value, project_root):
    text = str(value)
    tokens = [tok for tok in TOKEN_RE.findall(text) if tok != "project-root"]
    if tokens:
        return None, v("TOKEN_UNRESOLVED", text.replace("\\", "/"),
                       "路径参数含未解析令牌 %s；唯一例外是 {project-root}"
                       "（由引擎按 --project-root 自解析，其余 {…} 一律拒绝）"
                       % "、".join("{%s}" % tok for tok in sorted(set(tokens))))
    resolved = text.replace(PROJECT_ROOT_TOKEN, project_root)
    if not os.path.isabs(resolved):
        resolved = os.path.join(project_root, resolved)
    return os.path.abspath(resolved), None


# trace: diy-bmb-builder 文本读取（非 UTF-8 或 IO 失败 → 中文 stderr 诊断 + 违规，不静默吞）
def read_text(path, show):
    try:
        with io.open(path, "r", encoding="utf-8") as handle:
            return handle.read(), None
    except UnicodeDecodeError as e:
        sys.stderr.write("诊断：%s 无法按 UTF-8 解码：%s\n" % (show, e.reason))
        return None, v("UNPARSABLE_YAML", show, "无法按 UTF-8 解码（%s）" % e.reason)
    except OSError as e:
        sys.stderr.write("诊断：%s 读取失败：%s\n" % (show, e))
        return None, v("MISSING_FILE", show, "文件无法读取：%s" % e)


# trace: diy-bmb-builder 原子写（同目录临时文件 + fsync + os.replace）
def write_text_atomic(path, text):
    parent = os.path.dirname(path)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent)
    tmp = path + ".tmp"
    with io.open(tmp, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, path)


# trace: diy-bmb-builder 回执输出（--json 单行 / 人读行）
def emit(payload, as_json, human_lines=None):
    if as_json or human_lines is None:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        human_lines(payload)


# trace: diy-bmb-builder 共同键回执骨架
def base_payload(command, args, counts=None):
    return {
        "ok": False,
        "command": command,
        "project_root": args.project_root,
        "output_dir": os.path.normpath(os.path.abspath(args.output_dir)).replace("\\", "/"),
        "violations": [],
        "warnings": [],
        "counts": counts if counts is not None else {},
    }


# trace: diy-bmb-builder 人读态渲染（每条 `CODE where: msg` + 末尾汇总行）
def human_lines(payload):
    for item in payload["violations"]:
        print("%s %s: %s" % (item["code"], item["where"], item["msg"]))
    for item in payload["warnings"]:
        print("WARN %s %s: %s" % (item["code"], item["where"], item["msg"]))
    print("汇总：违规 %d 条 · 警告 %d 条（exit %d）"
          % (len(payload["violations"]), len(payload["warnings"]),
             0 if payload["ok"] else 1))


# trace: diy-bmb-builder 收尾（ok 由 violations 决定；exit 码 0/1）
def finish(payload, args, human=None):
    payload["ok"] = not payload["violations"]
    emit(payload, args.json, human)
    return 0 if payload["ok"] else 1


# trace: diy-bmb-builder --out 落盘（调用方显式给的落点；与 --output-dir 无关）
def write_out(path_arg, payload):
    if not path_arg:
        return
    write_text_atomic(os.path.abspath(path_arg),
                      json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


# ---------------------------------------------------------------- scaffold

# trace: diy-bmb-builder 子目录参数解析（KNOWN_DIRS 闭集，越界 → ENUM_INVALID）
def parse_dirs(raw):
    requested = []
    for item in str(raw or "").split(","):
        name = item.strip()
        if not name:
            continue
        if name not in KNOWN_DIRS:
            return None, v("ENUM_INVALID", "scaffold --dirs", "未知子目录 %r（合法集 %s）"
                           % (name, "|".join(KNOWN_DIRS)))
        requested.append(name)
    return requested, None


# trace: diy-bmb-builder 目标基准目录（安装面 / 套件源 / --dest，三者互斥规则见 docstring）
def scaffold_base(args, root):
    if args.to_source:
        base = os.path.join(root, *SOURCE_REL)
        if not os.path.isdir(base):
            return None, v("MISSING_FILE", os.path.join(*SOURCE_REL).replace("\\", "/") + "/",
                           "套件源目录缺席：--to-source 只对 diy-coder 仓有效，不代建父目录")
        return base, None
    resolved, err = resolve_arg_path(args.dest or os.path.join(PROJECT_ROOT_TOKEN, *INSTALL_REL),
                                     root)
    if err is not None:
        return None, err
    return resolved, None


# trace: diy-bmb-builder scaffold 子命令（建技能目录骨架；护栏 + 落点 + files_created）
def cmd_scaffold(args):
    root = os.path.abspath(args.project_root)
    payload = base_payload("scaffold", args, {"files_created": 0, "dirs_stubbed": 0})
    raw = args.name
    name = normalize_name(raw)
    if not name or name != str(raw).strip():
        payload["violations"].append(v(
            "NAME_ILLEGAL", "scaffold --name",
            "技能名须为 hyphen-case（≤%d 字符）：%r 归一后为 %r；请直接用归一形态重跑"
            % (NAME_MAX, raw, name)))
        return finish(payload, args, human_scaffold)
    if args.to_source and not name.startswith("diy-"):
        payload["violations"].append(v(
            "NAME_ILLEGAL", "scaffold --name",
            "--to-source 落套件源，技能名须带 `diy-` 前缀（install.py 只分发该前缀）：%r" % name))
        return finish(payload, args, human_scaffold)
    dirs, dir_err = parse_dirs(args.dirs)
    if dir_err is not None:
        payload["violations"].append(dir_err)
        return finish(payload, args, human_scaffold)
    base, base_err = scaffold_base(args, root)
    if base_err is not None:
        payload["violations"].append(base_err)
        return finish(payload, args, human_scaffold)
    target = os.path.join(base, name)
    show = display_path(target, root)
    if args.force and name in protected_names():
        payload["violations"].append(v(
            "FILE_CONFLICT", show,
            "硬护栏：%r 命中套件已建技能名或禁改面，--force 也不得覆盖（改别的名字，"
            "或按 Edit 意图在交互态逐文件改）" % name))
        return finish(payload, args, human_scaffold)
    if os.path.exists(target):
        if not args.force:
            payload["violations"].append(v(
                "FILE_CONFLICT", show,
                "目标已存在：默认拒绝覆盖（Edit 意图改造走交互确认；无头态经 "
                "`diyc.py defer-add --reason 破坏性操作` 入队后不推进）"))
            return finish(payload, args, human_scaffold)
        shutil.rmtree(target)
    if os.path.exists(target):
        payload["violations"].append(v("FILE_CONFLICT", show, "目标仍存在：清场失败，已中止"))
        return finish(payload, args, human_scaffold)
    files_created = []
    try:
        os.makedirs(target)
        skill_md = os.path.join(target, SKILL_FILE)
        write_text_atomic(skill_md, SKILL_TEMPLATE.replace("{skill-name}", name))
        files_created.append(display_path(target, root) + "/")
        files_created.append(display_path(skill_md, root))
        for sub in dirs:
            os.makedirs(os.path.join(target, sub))
            files_created.append(display_path(os.path.join(target, sub), root) + "/")
    except OSError as e:
        sys.stderr.write("诊断：脚手架落盘失败 %s：%s\n" % (show, e))
        payload["violations"].append(v("FILE_CONFLICT", show, "落盘失败：%s" % e))
        return finish(payload, args, human_scaffold)
    payload["files_created"] = files_created
    payload["counts"] = {"files_created": len(files_created), "dirs_stubbed": len(dirs)}
    payload["skill"] = show
    payload["force"] = bool(args.force)
    return finish(payload, args, human_scaffold)


# trace: diy-bmb-builder scaffold 人读态（落了什么 + 下一步）
def human_scaffold(payload):
    human_lines(payload)
    if payload["ok"]:
        print("技能骨架：%s" % payload["skill"])
        for item in payload["files_created"]:
            print("- %s" % item)


# ---------------------------------------------------------------- template

# trace: diy-bmb-builder 条件块展开（由内向外；真则留内容、假则删块；塌掉多余空行）
def process_conditionals(text, true_conditions):
    kept = []
    dropped = []
    changed = True
    while changed:
        changed = False
        match = IF_BLOCK_RE.search(text)
        if match:
            changed = True
            condition, inner = match.group(1), match.group(2)
            if condition in true_conditions:
                replacement = inner
                if condition not in kept:
                    kept.append(condition)
            else:
                replacement = ""
                if condition not in dropped:
                    dropped.append(condition)
            text = text[:match.start()] + replacement + text[match.end():]
    return re.sub(r"\n{3,}", "\n\n", text), kept, dropped


# trace: diy-bmb-builder 变量替换（只换给了值的键；未给的原样留给 tokens_remaining）
def process_variables(text, variables):
    substituted = []
    for key, value in variables.items():
        placeholder = "{%s}" % key
        if placeholder in text:
            text = text.replace(placeholder, value)
            substituted.append(key)
    return text, substituted


# trace: diy-bmb-builder --set k=v 解析（无等号 → argparse 用法错误 exit 2）
def parse_set(raw):
    if "=" not in raw:
        raise argparse.ArgumentTypeError("--set 须为 k=v：%r" % raw)
    key, _, value = raw.partition("=")
    if not key.strip():
        raise argparse.ArgumentTypeError("--set 的键为空：%r" % raw)
    return key.strip(), value


# trace: diy-bmb-builder template 子命令（两级失败语义：残留 {if-} exit 3 / 残留 {token} 交人判断）
def cmd_template(args):
    root = os.path.abspath(args.project_root)
    payload = base_payload("template", args, {"substituted": 0, "conditions_true": 0,
                                              "conditions_false": 0, "tokens_remaining": 0})
    src, src_err = resolve_arg_path(args.src, root)
    if src_err is not None:
        payload["violations"].append(src_err)
        return finish(payload, args, human_template)
    dest, dest_err = resolve_arg_path(args.dest, root)
    if dest_err is not None:
        payload["violations"].append(dest_err)
        return finish(payload, args, human_template)
    src_show = display_path(src, root)
    if not os.path.isfile(src):
        payload["violations"].append(v("MISSING_FILE", src_show, "模板文件不存在"))
        return finish(payload, args, human_template)
    text, err = read_text(src, src_show)
    if err is not None:
        payload["violations"].append(err)
        return finish(payload, args, human_template)
    variables = dict(args.set or [])
    text, kept, dropped = process_conditionals(text, set(args.true or []))
    text, substituted = process_variables(text, variables)
    leftovers = sorted(set(IF_MARKER_RE.findall(text)))
    if leftovers:
        payload["violations"].append(v(
            "TOKEN_UNRESOLVED", src_show,
            "残留条件块标记 %s：模板括号写错，原样输出会把标记 ship 出去（本轮硬失败、零产出）"
            % "、".join(leftovers)))
        payload["ok"] = False
        emit(payload, args.json, human_lines)
        return 3
    tokens = sorted(tok for tok in set(TOKEN_RE.findall(text)) if not tok.startswith("if-"))
    try:
        write_text_atomic(dest, text)
    except OSError as e:
        sys.stderr.write("诊断：模板输出失败 %s：%s\n" % (display_path(dest, root), e))
        payload["violations"].append(v("FILE_CONFLICT", display_path(dest, root),
                                       "输出失败：%s" % e))
        return finish(payload, args, human_template)
    payload["tokens_remaining"] = ["{%s}" % tok for tok in tokens]
    payload["counts"] = {"substituted": len(substituted), "conditions_true": len(kept),
                         "conditions_false": len(dropped),
                         "tokens_remaining": len(payload["tokens_remaining"])}
    return finish(payload, args, human_template)


# trace: diy-bmb-builder template 人读态（替换了什么 / 还剩什么令牌）
def human_template(payload):
    human_lines(payload)
    if payload["ok"]:
        print("输出：%s" % payload["output_dir"])
        print("剩余令牌（交人判断，不算失败）：%s"
              % ("、".join(payload["tokens_remaining"]) or "无"))


# ---------------------------------------------------------------- 预扫（metrics / integrity）

# trace: diy-bmb-builder 技能内 .md 清单（根 + steps/references/assets 一层，不深挖）
def skill_md_files(target):
    files = []
    root_md = os.path.join(target, SKILL_FILE)
    if os.path.isfile(root_md):
        files.append(root_md)
    for sub in SCAN_MD_DIRS:
        directory = os.path.join(target, sub)
        if not os.path.isdir(directory):
            continue
        files += sorted(os.path.join(directory, name) for name in os.listdir(directory)
                        if name.lower().endswith(".md")
                        and os.path.isfile(os.path.join(directory, name)))
    return files


# trace: diy-bmb-builder .md 清单（全量，供 path-standards 扫）
def all_md_files(target):
    files = []
    for name in sorted(os.listdir(target)):
        path = os.path.join(target, name)
        if os.path.isfile(path) and name.lower().endswith(".md"):
            files.append(path)
    for sub in SCAN_MD_DIRS:
        directory = os.path.join(target, sub)
        if not os.path.isdir(directory):
            continue
        files += sorted(os.path.join(directory, name) for name in os.listdir(directory)
                        if name.lower().endswith(".md")
                        and os.path.isfile(os.path.join(directory, name)))
    return files


# trace: diy-bmb-builder token 计数（tiktoken cl100k_base；缺席降级 chars//4 并标 method）
_ENCODER = None


def count_tokens(text):
    global _ENCODER
    if _ENCODER is None:
        try:
            import tiktoken
            _ENCODER = tiktoken.get_encoding("cl100k_base")
        except Exception:
            _ENCODER = False
    if _ENCODER is False:
        return len(text) // 4, "fallback"
    return len(_ENCODER.encode(text)), "tiktoken"


# trace: diy-bmb-builder 模式命中（返 [{line, label, quote}]，行号 1 基）
def grep_patterns(text, patterns):
    hits = []
    for pattern, label in patterns:
        for match in pattern.finditer(text):
            line = text[:match.start()].count("\n") + 1
            raw = text.splitlines()[line - 1].strip() if line - 1 < len(text.splitlines()) else ""
            hits.append({"line": line, "label": label, "quote": raw[:120]})
    return hits


# trace: diy-bmb-builder metrics 面（只出数不判违规；废话/回指进 warning）
def metrics_result(target, root):
    entries = []
    warnings = []
    for path in skill_md_files(target):
        text, err = read_text(path, display_path(path, root))
        if err is not None:
            continue
        tokens, method = count_tokens(text)
        waste = grep_patterns(text, WASTE_PATTERNS)
        backrefs = grep_patterns(text, BACKREF_PATTERNS)
        numbered = bool(re.match(r"^\d{2}[-_]", os.path.basename(path)))
        entries.append({"file": display_path(path, root), "lines": len(text.splitlines()),
                        "tokens": tokens, "method": method, "waste": waste,
                        "backrefs": backrefs, "numbered_prefix": numbered})
        for hit in waste:
            warnings.append(v("ENUM_INVALID", "%s:%d" % (display_path(path, root), hit["line"]),
                              "废话模式（%s）：%s" % (hit["label"], hit["quote"])))
        for hit in backrefs:
            warnings.append(v("ENUM_INVALID", "%s:%d" % (display_path(path, root), hit["line"]),
                              "回指模式（%s）：%s" % (hit["label"], hit["quote"])))
    result = {
        "files": entries,
        "counts": {
            "files": len(entries),
            "lines": sum(e["lines"] for e in entries),
            "tokens": sum(e["tokens"] for e in entries),
            "waste": sum(len(e["waste"]) for e in entries),
            "backrefs": sum(len(e["backrefs"]) for e in entries),
            "numbered_prefix": sum(1 for e in entries if e["numbered_prefix"]),
        },
    }
    return result, warnings


# trace: diy-bmb-builder 围栏块位置判定（示例里的错形态不算违规）
def in_fenced_block(text, pos):
    return len(FENCE_RE.findall(text[:pos])) % 2 == 1


# trace: diy-bmb-builder integrity 面（结构判违规：阶段文件落点 / 禁用段 / 残留标记 / 四段 / steps 编号与引用 / 直白度）
def integrity_result(target, root):
    violations = []
    warnings = []
    skill_md = os.path.join(target, SKILL_FILE)
    show = display_path(skill_md, root)
    text, err = read_text(skill_md, show)
    if err is not None:
        violations.append(err)
        return violations, warnings, {"steps": 0, "issues": 1}
    for name in sorted(os.listdir(target)):
        path = os.path.join(target, name)
        if os.path.isfile(path) and name.lower().endswith(".md") and name != SKILL_FILE:
            violations.append(v(
                "NAME_ILLEGAL", display_path(path, root),
                "阶段文件散在技能根：一律落 `steps/NN-<名>.md`（技能根只许 SKILL.md）"))
    lines = text.splitlines()
    for i, line in enumerate(lines, 1):
        title = line.strip()
        if title in INVALID_SECTIONS:
            violations.append(v("ENUM_INVALID", "%s:%d" % (show, i),
                                "`%s` 段：diy 无 exit hook，该段永不执行，删掉" % title))
    for marker in sorted(set(IF_MARKER_RE.findall(text))):
        violations.append(v("TOKEN_UNRESOLVED", show,
                            "残留模板标记 %s：模板未展开就落盘" % marker))
    for section in SECTION_TITLES:
        if not any(line.strip() == section for line in lines):
            violations.append(v("EMPTY_FIELD", show, "缺必备段 `%s`" % section))
    steps_dir = os.path.join(target, STEPS_DIR)
    steps = []
    if os.path.isdir(steps_dir):
        steps = sorted(name for name in os.listdir(steps_dir)
                       if os.path.isfile(os.path.join(steps_dir, name))
                       and name.lower().endswith(".md"))
        numbers = []
        for name in steps:
            match = STEP_FILE_RE.match(name)
            if not match:
                violations.append(v("NAME_ILLEGAL", "%s/%s" % (STEPS_DIR, name),
                                    "步骤文件名须为 `NN-<名>.md`（两位数字前缀）"))
                continue
            numbers.append(int(match.group(1)))
        if numbers:
            expected = list(range(1, len(numbers) + 1))
            if numbers != expected:
                violations.append(v("SET_MISMATCH", STEPS_DIR,
                                    "步骤编号不连续：实为 %s，应为 %s"
                                    % (numbers, expected)))
    for match in LOCAL_DIR_RE.finditer(text):
        rel = "%s/%s" % (match.group(1), match.group(2).rstrip("/"))
        if not os.path.exists(os.path.join(target, match.group(1), match.group(2))):
            violations.append(v("MISSING_FILE", show, "SKILL.md 引用的 `%s` 不存在" % rel))
    for i, line in enumerate(lines, 1):
        for pattern, label in DIRECTNESS_PATTERNS:
            if pattern.search(line):
                warnings.append(v("ENUM_INVALID", "%s:%d" % (show, i), label))
    return violations, warnings, {"steps": len(steps), "issues": len(violations)}


# trace: diy-bmb-builder prepass 子命令（两套合一，一份 JSON；--set 默认 all）
def cmd_prepass(args):
    root = os.path.abspath(args.project_root)
    payload = base_payload("prepass", args, {})
    target, target_err = resolve_arg_path(args.target, root)
    if target_err is not None:
        payload["violations"].append(target_err)
        return finish(payload, args)
    show = display_path(target, root)
    if not os.path.isdir(target):
        payload["violations"].append(v("MISSING_FILE", show,
                                       "技能目录不存在：--target 须指向含 SKILL.md 的技能目录"))
        return finish(payload, args)
    if not os.path.isfile(os.path.join(target, SKILL_FILE)):
        payload["violations"].append(v("MISSING_FILE", show + "/" + SKILL_FILE,
                                       "%s 不存在：目标不是技能目录" % SKILL_FILE))
        return finish(payload, args)
    sets = set(args.set or ["all"])
    if "all" in sets:
        sets = {"metrics", "integrity"}
    counts = {}
    if "metrics" in sets:
        result, warns = metrics_result(target, root)
        payload["metrics"] = result
        payload["warnings"] += warns
        counts["metrics_files"] = result["counts"]["files"]
        counts["tokens"] = result["counts"]["tokens"]
    if "integrity" in sets:
        violations, warns, info = integrity_result(target, root)
        payload["integrity"] = {"steps": info["steps"], "issues": info["issues"]}
        payload["violations"] += violations
        payload["warnings"] += warns
        counts["steps"] = info["steps"]
    payload["counts"] = counts
    payload["target"] = show
    payload["sets"] = sorted(sets)
    payload["ok"] = not payload["violations"]
    write_out(args.out, payload)
    emit(payload, args.json, human_prepass)
    return 0 if payload["ok"] else 1


# trace: diy-bmb-builder prepass 人读态
def human_prepass(payload):
    human_lines(payload)
    counts = payload["counts"]
    if "tokens" in counts:
        print("metrics：文件 %d · token %d" % (counts.get("metrics_files", 0), counts["tokens"]))
    if "steps" in counts:
        print("integrity：步骤文件 %d · 违规 %d" % (counts["steps"], counts.get("issues", 0)))


# ---------------------------------------------------------------- scan（路径形态 / 脚本合规）

# trace: diy-bmb-builder path-standards 面（绝对路径 / ../ 越界 / ./<目录>/ 跨目录；围栏内豁免）
def scan_path_standards(target, root):
    violations = []
    files = []
    for path in all_md_files(target):
        show = display_path(path, root)
        files.append(show)
        text, err = read_text(path, show)
        if err is not None:
            violations.append(err)
            continue
        for pattern, message in ((ABS_PATH_RE, "绝对路径：换机即失效（改 project-root 相对或 {project-root} 令牌路径）"),
                                 (ESCAPE_RE, "`../` 越界引用：越出技能目录（内容依赖，改技能根相对 bare 路径）"),
                                 (CROSS_DIR_RE, "`./<目录>/` 跨目录引用：`./` 只表示同目录（改 bare 技能根相对路径）")):
            for match in pattern.finditer(text):
                if in_fenced_block(text, match.start()):
                    continue
                line = text[:match.start()].count("\n") + 1
                quote = text.splitlines()[line - 1].strip()[:120]
                violations.append(v("ENUM_INVALID", "%s:%d" % (show, line),
                                    "%s —— %s" % (message, quote)))
    return violations, {"files_scanned": len(files)}


# trace: diy-bmb-builder 内置 input() 调用判定（AST 精确判定；不靠正则，免得命中注释与文档里的字面提及）
def calls_input_builtin(text):
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return False
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id == "input"):
            return True
    return False


# trace: diy-bmb-builder scripts 面（套件代码惯例四件 + input( 违规；argparse/sys.exit 记 warning）
def scan_scripts(target):
    violations = []
    warnings = []
    directory = os.path.join(target, "scripts")
    scripts = []
    if os.path.isdir(directory):
        scripts = sorted(os.path.join(directory, name) for name in os.listdir(directory)
                         if name.lower().endswith(".py")
                         and os.path.isfile(os.path.join(directory, name)))
    for path in scripts:
        rel = "scripts/" + os.path.basename(path)
        text, err = read_text(path, rel)
        if err is not None:
            violations.append(err)
            continue
        head = text.splitlines()[0] if text.splitlines() else ""
        if head.strip() != "# -*- coding: utf-8 -*-":
            violations.append(v("EMPTY_FIELD", rel, "缺 `# -*- coding: utf-8 -*-` 头（套件代码惯例）"))
        if 'reconfigure(encoding="utf-8")' not in text:
            violations.append(v("EMPTY_FIELD", rel, "缺 `sys.stdout.reconfigure(encoding=\"utf-8\")`"))
        if not SCRIPT_DOCSTRING_ZH_RE.search(text.split('"""')[1] if text.count('"""') >= 2 else ""):
            violations.append(v("EMPTY_FIELD", rel, "缺中文模块 docstring"))
        if "# trace:" not in text:
            violations.append(v("EMPTY_FIELD", rel, "缺 `# trace:` 注释（实现自身也吃自家 trace 规范）"))
        if calls_input_builtin(text):
            violations.append(v("ENUM_INVALID", rel, "含 input() 调用：无头态阻塞，改旗标传入"))
        if "argparse" not in text:
            warnings.append(v("EMPTY_FIELD", rel, "未用 argparse：脚本无 CLI 面（若为纯库可忽略）"))
        if "sys.exit" not in text:
            warnings.append(v("EMPTY_FIELD", rel, "无 sys.exit：退出码面缺失"))
    return violations, warnings, {"scripts_scanned": len(scripts)}


# trace: diy-bmb-builder scan 子命令（机械面；--check 默认 all）
def cmd_scan(args):
    root = os.path.abspath(args.project_root)
    payload = base_payload("scan", args, {})
    target, target_err = resolve_arg_path(args.target, root)
    if target_err is not None:
        payload["violations"].append(target_err)
        return finish(payload, args)
    show = display_path(target, root)
    if not os.path.isdir(target) or not os.path.isfile(os.path.join(target, SKILL_FILE)):
        payload["violations"].append(v("MISSING_FILE", show,
                                       "技能目录不存在或缺 SKILL.md"))
        return finish(payload, args)
    checks = args.check
    summary = {}
    if checks in ("all", "path-standards"):
        violations, info = scan_path_standards(target, root)
        payload["violations"] += violations
        summary.update(info)
    if checks in ("all", "scripts"):
        violations, warns, info = scan_scripts(target)
        payload["violations"] += violations
        payload["warnings"] += warns
        summary.update(info)
    payload["scan"] = {"checks": checks, "files_scanned": summary.get("files_scanned", 0),
                       "scripts_scanned": summary.get("scripts_scanned", 0)}
    payload["counts"] = {"files_scanned": summary.get("files_scanned", 0),
                         "scripts_scanned": summary.get("scripts_scanned", 0)}
    payload["ok"] = not payload["violations"]
    write_out(args.out, payload)
    emit(payload, args.json, human_lines)
    return 0 if payload["ok"] else 1


# ---------------------------------------------------------------- mlog（过程日志）

# trace: diy-bmb-builder memlog 文件拆分（(frontmatter, body)；围栏按整行 --- 判定）
def split_memlog(text):
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("缺 frontmatter")
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        raise ValueError("frontmatter 未闭合")
    meta = {}
    for line in lines[1:end]:
        if ":" in line:
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip()
    return meta, "\n".join(lines[end + 1:]).lstrip("\n")


# trace: diy-bmb-builder memlog 渲染（frontmatter 单行值 + 空行 + 条目体）
def render_memlog(meta, body):
    front = "\n".join("%s: %s" % (key, " ".join(str(value).splitlines()))
                      for key, value in meta.items())
    return "---\n" + front + "\n---\n\n" + body.rstrip("\n") + "\n"


# trace: diy-bmb-builder memlog 条目计数（`- ` 起始行）
def memlog_count(body):
    return sum(1 for line in body.splitlines() if line.startswith("- "))


# trace: diy-bmb-builder mlog 子命令（只追加 + 原子写 + 恒发一行 JSON ack）
def cmd_mlog(args):
    root = os.path.abspath(args.project_root)
    payload = base_payload("mlog", args, {"n": 0})
    directory, dir_err = resolve_arg_path(args.dir, root)
    name = str(args.file)
    # 文件名校验（与 W3 的 mlog 同构）：只收纯文件名——路径分隔符 / `.` / `..` / 空白名一律拒绝，
    # 否则 --dir 的边界形同虚设，写面会越出 {output_dir}/build-logs。
    if "/" in name or "\\" in name or name in (".", "..") or not name.strip():
        payload["violations"].append(v(
            "NAME_ILLEGAL", "--file",
            "只收文件名、不收路径（不靠 --dir 反推、也不许越出 --dir）：%r" % name))
    path = os.path.join(directory or root, name) if name.strip() else (directory or root)
    show = display_path(path, root)
    payload["file"] = show
    payload["action"] = args.action
    if dir_err is not None:
        payload["violations"].append(dir_err)
    if payload["violations"]:
        return finish(payload, args, human_lines)
    action = args.action
    if action == "init":
        if os.path.exists(path):
            payload["violations"].append(v("FILE_CONFLICT", show,
                                           "日志已存在：续写走 append（init 只建新档）"))
            return finish(payload, args, human_lines)
        meta = {}
        if nonempty(args.subject):
            meta["subject"] = str(args.subject)
        meta["status"] = "active"
        meta["updated"] = datetime.now().strftime("%Y-%m-%dT%H:%M")
        write_text_atomic(path, render_memlog(meta, ""))
        payload["n"] = 0
    else:
        if not os.path.isfile(path):
            payload["violations"].append(v("MISSING_FILE", show,
                                           "日志不存在：先跑 `mlog init --subject S`"))
            return finish(payload, args, human_lines)
        text, err = read_text(path, show)
        if err is not None:
            payload["violations"].append(err)
            return finish(payload, args, human_lines)
        try:
            meta, body = split_memlog(text)
        except ValueError as e:
            payload["violations"].append(v("UNPARSABLE_YAML", show, "memlog 形状非法：%s" % e))
            return finish(payload, args, human_lines)
        if action == "append":
            if args.type not in ENTRY_TYPES:
                payload["violations"].append(v(
                    "ENUM_INVALID", "mlog --type",
                    "类型越界：%r（合法集 %s）" % (args.type, "|".join(ENTRY_TYPES))))
                return finish(payload, args, human_lines)
            if not nonempty(args.text):
                payload["violations"].append(v("EMPTY_FIELD", "mlog --text", "条目内容为空"))
                return finish(payload, args, human_lines)
            entry = "- (%s) %s" % (args.type, " ".join(str(args.text).split()))
            body = (body.rstrip("\n") + "\n" + entry) if body.strip() else entry
            payload["appended"] = True
        elif action == "set-complete":
            meta["status"] = "complete"
            payload["appended"] = False
        else:
            payload["violations"].append(v("ENUM_INVALID", "mlog",
                                           "未知动作 %r（合法集 init|append|set-complete）" % action))
            return finish(payload, args, human_lines)
        meta.pop("updated", None)
        meta["updated"] = datetime.now().strftime("%Y-%m-%dT%H:%M")
        write_text_atomic(path, render_memlog(meta, body))
        payload["n"] = memlog_count(body)
    payload["appended"] = bool(payload.get("appended", False))
    payload["counts"] = {"n": payload["n"]}
    payload["ok"] = True
    emit(payload, True, None)
    return 0


# ---------------------------------------------------------------- check（产物终门）

# trace: diy-bmb-builder frontmatter 解析（缺失/未闭合/非映射 → 违规）
def parse_frontmatter(text, show):
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, [v("EMPTY_FIELD", show, "缺 YAML frontmatter（须以 `---` 起）")]
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        return None, [v("EMPTY_FIELD", show, "frontmatter 未闭合")]
    try:
        data = yaml.safe_load("\n".join(lines[1:end])) or {}
    except yaml.YAMLError as e:
        return None, [v("UNPARSABLE_YAML", show, "frontmatter 解析失败：%s" % str(e).splitlines()[0])]
    if not isinstance(data, dict):
        return None, [v("EMPTY_FIELD", show, "frontmatter 不是映射")]
    return data, []


# trace: diy-bmb-builder frontmatter 六字段校验（形态：phase/line/outputs 非空、required 布尔、precededBy/followedBy 列表）
def check_frontmatter(data, show):
    violations = []
    name = data.get("name")
    if not nonempty(name):
        violations.append(v("EMPTY_FIELD", show + " frontmatter.name", "name 缺失"))
    elif not NAME_RE.match(str(name)):
        violations.append(v("NAME_ILLEGAL", show + " frontmatter.name",
                            "name 须为 hyphen-case：%r" % name))
    if not nonempty(data.get("description")):
        violations.append(v("EMPTY_FIELD", show + " frontmatter.description", "description 缺失"))
    for field in REGISTRY_FIELDS:
        if field not in data:
            violations.append(v("EMPTY_FIELD", "%s frontmatter.%s" % (show, field),
                                "登记元数据 %s 缺失（六字段封闭集）" % field))
    for field in ("phase", "line", "outputs"):
        if field in data and not nonempty(data.get(field)):
            violations.append(v("EMPTY_FIELD", "%s frontmatter.%s" % (show, field),
                                "%s 为空" % field))
    if "required" in data and not isinstance(data.get("required"), bool):
        violations.append(v("ENUM_INVALID", show + " frontmatter.required",
                            "required 须为布尔"))
    for field in ("precededBy", "followedBy"):
        if field in data and not isinstance(data.get(field), list):
            violations.append(v("ENUM_INVALID", "%s frontmatter.%s" % (show, field),
                                "%s 须为列表（空则 []）" % field))
    return violations


# trace: diy-bmb-builder 自足性（技能根相对引用须在目录内；../ 越界判内容依赖）
def check_self_sufficiency(target, root, texts):
    violations = []
    for show, text in texts:
        match = ESCAPE_RE.search(text)
        if match:
            line = text[:match.start()].count("\n") + 1
            violations.append(v("FILE_CONFLICT", "%s:%d" % (show, line),
                                "`../` 越界引用：技能目录外的内容依赖（自足判据禁内容依赖；"
                                "套件级调用与 {project-root} 令牌路径豁免）"))
        for hit in LOCAL_DIR_RE.finditer(text):
            rel = "%s/%s" % (hit.group(1), hit.group(2).rstrip("/"))
            if not os.path.exists(os.path.join(target, hit.group(1), hit.group(2))):
                violations.append(v("MISSING_FILE", show, "引用的 `%s` 不在技能目录内" % rel))
    return violations


# trace: diy-bmb-builder steps 形态（H1 中文步名 / Read-Write 行 / 结尾点名下一步；--final 面）
def check_steps(target, root, final):
    violations = []
    warnings = []
    directory = os.path.join(target, STEPS_DIR)
    steps = []
    if os.path.isdir(directory):
        steps = sorted(name for name in os.listdir(directory)
                       if os.path.isfile(os.path.join(directory, name))
                       and name.lower().endswith(".md"))
    if not steps and final:
        violations.append(v("MISSING_FILE", STEPS_DIR + "/",
                            "结构终门要求至少一个步骤文件（steps/ 在场且非空）："
                            "SKILL.md 的读取纪律以步骤文件为执行单元"))
        return violations, warnings
    for index, name in enumerate(steps, start=1):
        rel = "%s/%s" % (STEPS_DIR, name)
        text, err = read_text(os.path.join(directory, name), rel)
        if err is not None:
            violations.append(err)
            continue
        lines = text.replace("\r\n", "\n").split("\n")
        first = lines[0] if lines else ""
        if not STEP_H1_RE.match(first):
            violations.append(v("EMPTY_FIELD", rel, "H1 须为 `# Step N — <中文步名>`，实为 %r" % first))
        if not any(line.startswith("**Read (input):**") for line in lines):
            violations.append(v("EMPTY_FIELD", rel, "缺 `**Read (input):**` 行（冒号须半角）"))
        if not any(line.startswith("**Write (output):**") for line in lines):
            violations.append(v("EMPTY_FIELD", rel, "缺 `**Write (output):**` 行（冒号须半角）"))
        if final:
            if index < len(steps):
                if not any(other != name and other in text for other in steps):
                    violations.append(v("EMPTY_FIELD", rel,
                                        "步尾未点名下一个要读的步骤文件（可含分支路由）："
                                        "候选 %s" % "、".join(other for other in steps if other != name)))
            elif STEP_MENTION_RE.search(text):
                warnings.append(v("EMPTY_FIELD", rel,
                                  "末步仍点名步骤文件：末步须声明不再读任何 `steps/` 文件"))
    return violations, warnings


# trace: diy-bmb-builder check 子命令（基础项 + --final 结构终门）
def cmd_check(args):
    root = os.path.abspath(args.project_root)
    payload = base_payload("check", args, {"steps": 0, "lines": 0, "violations": 0})
    target, target_err = resolve_arg_path(args.target, root)
    if target_err is not None:
        payload["violations"].append(target_err)
        return finish(payload, args, human_lines)
    show = display_path(target, root)
    skill_md = os.path.join(target, SKILL_FILE)
    skill_show = display_path(skill_md, root)
    if not os.path.isdir(target):
        payload["violations"].append(v("MISSING_FILE", show, "技能目录不存在"))
        return finish(payload, args, human_lines)
    if not os.path.isfile(skill_md):
        payload["violations"].append(v("MISSING_FILE", skill_show, "%s 不存在" % SKILL_FILE))
        return finish(payload, args, human_lines)
    text, err = read_text(skill_md, skill_show)
    if err is not None:
        payload["violations"].append(err)
        return finish(payload, args, human_lines)
    lines = text.splitlines()
    for section in SECTION_TITLES:
        if not any(line.strip() == section for line in lines):
            payload["violations"].append(v("EMPTY_FIELD", skill_show, "缺四段之一 `%s`" % section))
    for anchor in FROZEN_ANCHORS:
        if anchor not in text:
            payload["violations"].append(v(
                "EMPTY_FIELD", skill_show,
                "母本锚串未逐字在场（须逐字复制、禁改写）：%r" % anchor[:32]))
    data, fm_violations = parse_frontmatter(text, skill_show)
    payload["violations"] += fm_violations
    if data is not None:
        payload["violations"] += check_frontmatter(data, skill_show)
    texts = [(skill_show, text)]
    for path in skill_md_files(target):
        if os.path.abspath(path) == os.path.abspath(skill_md):
            continue
        rel = display_path(path, root)
        body, body_err = read_text(path, rel)
        if body_err is None:
            texts.append((rel, body))
    payload["violations"] += check_self_sufficiency(target, root, texts)
    step_violations, step_warnings = check_steps(target, root, args.final)
    payload["violations"] += step_violations
    payload["warnings"] += step_warnings
    if args.final and len(lines) > SKILL_MD_MAX_LINES:
        payload["violations"].append(v(
            "SET_MISMATCH", skill_show,
            "SKILL.md 行数 %d 超固定阈值 %d（唯一硬阈值；token 计数只作信息面，不作门禁）"
            % (len(lines), SKILL_MD_MAX_LINES)))
    payload["target"] = show
    payload["final"] = bool(args.final)
    payload["counts"] = {"steps": _steps_count(target), "lines": len(lines),
                         "violations": len(payload["violations"])}
    payload["ok"] = not payload["violations"]
    emit(payload, args.json, human_lines)
    return 0 if payload["ok"] else 1


# trace: diy-bmb-builder 步骤文件计数（终门计数用）
def _steps_count(target):
    directory = os.path.join(target, STEPS_DIR)
    if not os.path.isdir(directory):
        return 0
    return sum(1 for name in os.listdir(directory)
               if name.lower().endswith(".md")
               and os.path.isfile(os.path.join(directory, name)))


# ---------------------------------------------------------------- render（报告渲染）

# trace: diy-bmb-builder findings 装载与形状校验（缺 schema_version/subject/findings → 拒绝渲染）
def load_findings(path, show):
    if not os.path.isfile(path):
        return None, [v("MISSING_FILE", show, "findings.json 不存在（先合成五透镜结果）")]
    text, err = read_text(path, show)
    if err is not None:
        return None, [err]
    try:
        data = json.loads(text)
    except ValueError as e:
        return None, [v("UNPARSABLE_YAML", show, "findings.json 解析失败：%s" % e)]
    if not isinstance(data, dict):
        return None, [v("EMPTY_FIELD", show, "findings.json 顶层不是对象")]
    violations = []
    if data.get("schema_version") != 2:
        violations.append(v("ENUM_INVALID", show + " schema_version",
                            "schema_version 须为 2（与既有 12 份报告可比）"))
    grade = data.get("grade")
    if grade is not None and str(grade) not in GRADES:
        violations.append(v("ENUM_INVALID", show + " grade",
                            "grade 越界：%r（合法集 %s，小写）" % (grade, "|".join(GRADES))))
    subject = data.get("subject")
    if not nonempty(subject) or str(subject).strip().lower() in ("subject", "<subject>"):
        violations.append(v("EMPTY_FIELD", show + " subject",
                            "subject 缺失或仍是占位（拒绝渲染占位报告）"))
    if not isinstance(data.get("findings"), list):
        violations.append(v("EMPTY_FIELD", show + " findings",
                            "findings 须为列表（无发现写空列表）"))
    if violations:
        return None, violations
    return data, []


# trace: diy-bmb-builder severity 计数由脚本派生（报告里不设 counts 字段）
def severity_counts(findings):
    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for item in findings:
        if isinstance(item, dict):
            severity = str(item.get("severity", "")).lower()
            if severity in counts:
                counts[severity] += 1
    return counts


# trace: diy-bmb-builder 报告 markdown 生成（Grade / verdict / 主题 / 强项 / 建议 / 逐条 findings）
def render_md(data):
    counts = severity_counts(data["findings"])
    out = ["# Analysis Report: %s" % data["subject"], "",
           "Generated: %s · Schema: 2" % data.get("generated", ""), "",
           "**Grade: %s**" % (data.get("grade") or "—"), "",
           "> %s" % data.get("verdict", ""), "",
           data.get("summary", ""), "",
           "| Severity | Count |", "| --- | --- |"]
    for name in ("critical", "high", "medium", "low"):
        out.append("| %s | %d |" % (name.capitalize(), counts[name]))
    themes = data.get("themes") or []
    if themes:
        out += ["", "## Themes"]
        for i, theme in enumerate(themes, 1):
            out += ["", "### %d. %s" % (i, theme.get("title", "")),
                    "", "- Root cause: %s" % theme.get("root_cause", ""),
                    "- Fix: %s" % theme.get("action", "")]
            if theme.get("finding_ids"):
                out.append("- Findings: %s" % "、".join("`%s`" % i for i in theme["finding_ids"]))
    if data.get("strengths"):
        out += ["", "## Strengths"] + ["- %s" % item for item in data["strengths"]]
    if data.get("recommendations"):
        out += ["", "## Recommendations"]
        for rec in data["recommendations"]:
            out.append("%s. %s（resolves: %s）"
                       % (rec.get("rank", "-"), rec.get("action", ""),
                          "、".join("`%s`" % i for i in (rec.get("resolves") or []))))
    out += ["", "## Findings"]
    for item in data["findings"]:
        if not isinstance(item, dict):
            continue
        out += ["", "### `%s` %s" % (item.get("id", ""), item.get("title", "")),
                "", "- lens: %s ｜ severity: %s ｜ location: %s"
                % (item.get("lens", ""), item.get("severity", ""), item.get("location", "")),
                "- evidence: %s" % item.get("evidence", ""),
                "- recommendation: %s" % item.get("recommendation", "")]
        for extra in ("proposed_smallest", "predicted_delta"):
            if item.get(extra):
                out.append("- %s: %s" % (extra, item[extra]))
    return "\n".join(out).rstrip("\n") + "\n"


# trace: diy-bmb-builder 报告 HTML 生成（自包含、无外部资源、值一律转义）
def render_html(data):
    counts = severity_counts(data["findings"])
    esc = html_mod.escape
    rows = "".join("<tr><td>%s</td><td>%d</td></tr>" % (name, counts[name])
                   for name in ("critical", "high", "medium", "low"))
    themes = ""
    for theme in data.get("themes") or []:
        themes += ("<section class='theme'><h3>%s</h3><p><b>Root cause:</b> %s</p>"
                   "<p><b>Fix:</b> %s</p><p class='ids'>%s</p></section>"
                   % (esc(str(theme.get("title", ""))), esc(str(theme.get("root_cause", ""))),
                      esc(str(theme.get("action", ""))),
                      esc("、".join(str(i) for i in (theme.get("finding_ids") or [])))))
    findings = ""
    for item in data["findings"]:
        if not isinstance(item, dict):
            continue
        extra = ""
        for key in ("proposed_smallest", "predicted_delta"):
            if item.get(key):
                extra += "<p><b>%s:</b> %s</p>" % (esc(key), esc(str(item[key])))
        findings += ("<article class='finding sev-%s'><h3><code>%s</code> %s</h3>"
                     "<p class='meta'>lens %s ｜ %s ｜ %s</p><p>%s</p><p><b>建议：</b>%s</p>%s</article>"
                     % (esc(str(item.get("severity", ""))), esc(str(item.get("id", ""))),
                        esc(str(item.get("title", ""))), esc(str(item.get("lens", ""))),
                        esc(str(item.get("severity", ""))), esc(str(item.get("location", ""))),
                        esc(str(item.get("evidence", ""))),
                        esc(str(item.get("recommendation", ""))), extra))
    strengths = "".join("<li>%s</li>" % esc(str(item))
                        for item in (data.get("strengths") or []))
    recons = "".join("<li>%s <span class='ids'>%s</span></li>"
                     % (esc(str(rec.get("action", ""))),
                        esc("、".join(str(i) for i in (rec.get("resolves") or []))))
                     for rec in (data.get("recommendations") or []))
    return ("<!DOCTYPE html>\n<html lang=\"zh-CN\"><head><meta charset=\"utf-8\">"
            "<title>Analysis Report: %s</title><style>"
            "body{font-family:system-ui,sans-serif;max-width:900px;margin:2rem auto;padding:0 1rem;"
            "line-height:1.6;color:#1a1a1a}h1{font-size:1.5rem}.grade{display:inline-block;"
            "padding:.2rem .7rem;border-radius:4px;background:#eef;font-weight:700}"
            "blockquote{border-left:3px solid #ccd;margin:1rem 0;padding:.2rem 1rem;color:#334}"
            "table{border-collapse:collapse}td,th{border:1px solid #dde;padding:.2rem .8rem}"
            ".finding{border:1px solid #e5e5ef;border-radius:6px;padding:.6rem 1rem;margin:.7rem 0}"
            ".finding h3{font-size:1rem;margin:.2rem 0}.meta,.ids{color:#667;font-size:.85rem}"
            "code{background:#f4f4f8;padding:0 .25rem}</style></head><body>"
            "<h1>Analysis Report: %s</h1><p class='meta'>Generated: %s · Schema: 2</p>"
            "<p class='grade'>Grade: %s</p><blockquote>%s</blockquote><p>%s</p>"
            "<h2>Severity</h2><table><tr><th>Severity</th><th>Count</th></tr>%s</table>"
            "<h2>Themes</h2>%s<h2>Strengths</h2><ul>%s</ul>"
            "<h2>Recommendations</h2><ol>%s</ol><h2>Findings</h2>%s</body></html>\n"
            % (esc(str(data["subject"])), esc(str(data["subject"])),
               esc(str(data.get("generated", ""))), esc(str(data.get("grade") or "—")),
               esc(str(data.get("verdict", ""))), esc(str(data.get("summary", ""))),
               rows, themes or "<p>无</p>", strengths or "<li>无</li>",
               recons or "<li>无</li>", findings or "<p>无发现——五透镜全过。</p>"))


# trace: diy-bmb-builder render 子命令（脚本渲染 md/html，禁手写 HTML）
def cmd_render(args):
    root = os.path.abspath(args.project_root)
    payload = base_payload("render", args, {"rendered": 0})
    run_dir, dir_err = resolve_arg_path(args.dir, root)
    if dir_err is not None:
        payload["violations"].append(dir_err)
        return finish(payload, args, human_lines)
    show = display_path(run_dir, root)
    if not os.path.isdir(run_dir):
        payload["violations"].append(v("MISSING_FILE", show, "运行目录不存在"))
        return finish(payload, args, human_lines)
    findings_path = os.path.join(run_dir, FINDINGS_FILE)
    data, violations = load_findings(findings_path, display_path(findings_path, root))
    if violations:
        payload["violations"] += violations
        return finish(payload, args, human_lines)
    try:
        write_text_atomic(os.path.join(run_dir, REPORT_MD), render_md(data))
        write_text_atomic(os.path.join(run_dir, REPORT_HTML), render_html(data))
    except OSError as e:
        sys.stderr.write("诊断：报告渲染失败 %s：%s\n" % (show, e))
        payload["violations"].append(v("FILE_CONFLICT", show, "渲染失败：%s" % e))
        return finish(payload, args, human_lines)
    payload["rendered"] = [("%s/%s" % (show, REPORT_MD)), ("%s/%s" % (show, REPORT_HTML))]
    payload["counts"] = {"rendered": 2, "findings": len(data["findings"]),
                         "severity": severity_counts(data["findings"])}
    return finish(payload, args, human_render)


# trace: diy-bmb-builder render 人读态（落了两件 + 计数；不报路径等待查看、不开浏览器）
def human_render(payload):
    human_lines(payload)
    if payload["ok"]:
        for item in payload["rendered"]:
            print("- %s" % item)


# ---------------------------------------------------------------- 命令行面

# trace: diy-bmb-builder 命令行面（子命令 + 旗标；--output-dir 全部必填，引擎不读配置）
def build_parser():
    ap = argparse.ArgumentParser(
        description="diy-bmb-builder 确定性引擎：技能树脚手架（scaffold）/ 模板机（template）/"
                    "预扫（prepass）/ 结构扫描（scan）/ 过程日志（mlog）/ 产物终门（check）/"
                    "报告渲染（render）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def add_common(parser):
        parser.add_argument("--project-root", default=".", help="项目根（默认 .）")
        parser.add_argument("--output-dir", required=True,
                            help="本次运行的产物目录（必填；由调用方经 diyc.py resolve 传入，"
                                 "引擎不读 diy-coder.yaml）")
        parser.add_argument("--json", action="store_true", help="输出单行 JSON 回执")

    s = sub.add_parser("scaffold", help="建技能目录骨架（默认落 {project-root}/.claude/skills/）")
    s.add_argument("--name", required=True, help="技能名（须已是 hyphen-case，≤64 字符）")
    s.add_argument("--dirs", default=DEFAULT_DIRS,
                   help="要 stub 的子目录，逗号分隔（默认 steps；可选 references,scripts,assets）")
    s.add_argument("--dest", help="落点父目录（默认 {project-root}/.claude/skills）")
    s.add_argument("--to-source", action="store_true",
                   help="落套件源 {project-root}/diy-coder/skills（与 --dest 互斥）")
    s.add_argument("--force", action="store_true",
                   help="目标已存在时清场重建（硬护栏：已建技能名与禁改面即使 --force 也拒绝）")
    add_common(s)
    s.set_defaults(func=cmd_scaffold)

    t = sub.add_parser("template", help="模板机（{if-X} 条件块 + {var} 替换；残留 {if-} 硬失败）")
    t.add_argument("--src", required=True, help="模板文件")
    t.add_argument("--dest", required=True, help="输出文件")
    t.add_argument("--set", action="append", type=parse_set, metavar="k=v",
                   help="变量替换（可重复）")
    t.add_argument("--true", action="append", metavar="X",
                   help="条件名视为真（可重复；未给的 {if-X} 整块删）")
    add_common(t)
    t.set_defaults(func=cmd_template)

    p = sub.add_parser("prepass", help="预扫（metrics 计量 / integrity 结构；两套合一）")
    p.add_argument("--target", required=True, help="技能目录")
    p.add_argument("--set", action="append", choices=("metrics", "integrity", "all"),
                   help="跑哪一套（可重复；默认 all）")
    p.add_argument("--out", help="另存 JSON 回执到该文件（调用方显式给的落点）")
    add_common(p)
    p.set_defaults(func=cmd_prepass)

    c = sub.add_parser("scan", help="机械面扫描（路径形态 / 脚本合规）")
    c.add_argument("--target", required=True, help="技能目录")
    c.add_argument("--check", choices=("all", "path-standards", "scripts"), default="all",
                   help="扫描面（默认 all；--lens 一词留给五透镜，不用作本旗标）")
    c.add_argument("--out", help="另存 JSON 回执到该文件")
    add_common(c)
    c.set_defaults(func=cmd_scan)

    m = sub.add_parser("mlog", help="过程日志（只追加；恒发一行 JSON ack）")
    m.add_argument("--dir", required=True, help="日志目录（W1 = {output_dir}/build-logs）")
    m.add_argument("--file", required=True, help="日志文件名（调用方显式给，如 <skill-name>.md）")
    m.add_argument("action", choices=("init", "append", "set-complete"), help="动作")
    m.add_argument("--subject", help="init 的标题")
    m.add_argument("--type", help="append 的条目类型（%s）" % "|".join(ENTRY_TYPES))
    m.add_argument("--text", help="append 的条目内容")
    add_common(m)
    m.set_defaults(func=cmd_mlog)

    k = sub.add_parser("check", help="产物技能终门（结构 / 母本逐字 / 自足 / 六字段）")
    k.add_argument("--target", required=True, help="技能目录")
    k.add_argument("--final", action="store_true",
                   help="结构终门：另加 SKILL.md ≤90 行 + steps 形态与步尾点名")
    add_common(k)
    k.set_defaults(func=cmd_check)

    r = sub.add_parser("render", help="由 findings.json 渲染报告 md/html（禁手写 HTML）")
    r.add_argument("--dir", required=True, help="分析运行目录（含 findings.json）")
    add_common(r)
    r.set_defaults(func=cmd_render)
    return ap


# trace: diy-bmb-builder 旗标互斥校验（--to-source 与 --dest 同给 = 用法错误 exit 2）
def validate_args(args):
    if args.cmd == "scaffold" and args.to_source and args.dest:
        return "--to-source 与 --dest 互斥：落套件源就不要再给 --dest"
    return None


# trace: diy-bmb-builder 入口（stdout/stderr 固定 UTF-8；未预期异常转 INTERNAL_ERROR，不静默）
def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    parser = build_parser()
    args = parser.parse_args()
    problem = validate_args(args)
    if problem:
        parser.error(problem)
    try:
        return args.func(args)
    except Exception as e:  # 未预期异常：报回执 + stderr 诊断，不裸奔
        sys.stderr.write("诊断：内部错误 %s：%s\n" % (type(e).__name__, e))
        payload = {
            "ok": False, "command": args.cmd, "project_root": args.project_root,
            "output_dir": os.path.normpath(os.path.abspath(args.output_dir)).replace("\\", "/"),
            "violations": [v("INTERNAL_ERROR", args.cmd, "%s: %s" % (type(e).__name__, e))],
            "warnings": [], "counts": {},
        }
        print(json.dumps(payload, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    sys.exit(main())
