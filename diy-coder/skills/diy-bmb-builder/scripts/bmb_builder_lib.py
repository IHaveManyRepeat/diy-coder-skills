# -*- coding: utf-8 -*-
"""bmb-builder 通用小件：常量与回执零件。"""

import io
import json
import os
import re
import sys

from diyc_lib import v, violation_line, warn_line, write_atomic

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


# trace: diy-bmb-builder 非空判定（None / 空白字符串均视为空）


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
        print(violation_line(item))
    for item in payload["warnings"]:
        print(warn_line(item))
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
    write_atomic(os.path.abspath(path_arg),
                      json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
