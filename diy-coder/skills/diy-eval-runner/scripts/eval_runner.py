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
             恒发一行 JSON ack `{ok, file, n, appended}`（与 W1 的 mlog 逐字同构——
             `--dir D` + `--file NAME` 由调用方显式给，不靠 `--dir` 反推文件名）。

纪律（本引擎实现的硬规则）：
  · **隔离契约**：子进程环境从零构建、绝不继承——只有 `PATH` + 全新空 `HOME`
    （`<case>/.home`）+ `CLAUDE_CONFIG_DIR`（指向其中）+ `auth_env` 变量（**仅当宿主非空
    才传**：传空串会毁掉运行时自己的凭据回落）+ adapter 声明的 `env_passthrough` 键。
  · **不硬编码模型名**：一切运行时差异走 adapter 缝（`--adapter` / `--invocation`）。
  · **令牌纪律**：路径参数里 `{project-root}` 由 `--project-root` 自解析（唯一例外），
    其余任何 `{...}` 令牌一律拒绝（`TOKEN_UNRESOLVED`）。adapter 的 `invocation` 模板
    （`{prompt}` / `{query}` / `{cwd}`）是另一命名空间，不在此列。
  · **run 目录永不删除、覆盖、轮转**：同名（同秒同 label）已存在时另铸后缀目录，绝不覆写。
  · **降级不静默**：`invocation` 解析为空 → 只 stage、结果记 `skipped`（源侧行为保留）；
    invocation 命令不在 PATH（无头下即 `runner.py` 白名单未覆盖该命令族）→ warning +
    跳过该 mode 并明示（**不入队**——确认是当场决策，队列语义是「用户稍后自行执行」）。

违规码：复用 batch3-contract §3 冻结集（MISSING_FILE EMPTY_FIELD ENUM_INVALID UNKNOWN_ID
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
（与 W1 的 mlog 逐字同构：恒发一行 JSON，共同键 + `file` / `action` / `n` / `appended`）；
`aggregate` 的
`configs` / `delta` / `against` / `subject`；`check` 的 `run_dir` / `skipped_modes`；
`run` 的 `run_id` / `run_dir` / `modes`。

契约同构（batch3-contract §3）：exit 0 唯一放行 / 1 = 违规或被拒绝 / 2 = 用法错误（argparse
默认）；`--json` 单行回执（ensure_ascii=False）；无 `--json` 中文人读行（每违规一行
`CODE where: msg` + 汇总行）；`where` 正斜杠、相对 project-root；`--project-root` 全部
子命令都收（默认 `.`）；`--output-dir` 必填于会写盘的子命令（`run` 与 `mlog`），只读子命令
（`check` / `aggregate`）收到即回显、缺席时由 run 目录结构推导或不填（仅回执完整性用）。
"""
# trace: B5 diy-eval-runner 验收 #2 / #3 / #7 / #12 / #13（四模式真跑 + 零 YAML 主产物 +
#        终门 check --run-dir + 降级路径不入队）
import argparse
import io
import json
import math
import os
import re
import shutil
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone

MODES = ("baseline", "variant", "quality", "trigger")
CONFIG_MODES = ("baseline", "variant", "quality")
# 每个模式用到的 config；顺序固定（`skill` 恒为被测侧 = delta 的被减项）
CONFIG_ORDER = {"baseline": ("skill", "bare"),
                "variant": ("skill", "variant"),
                "quality": ("skill",)}
SUBJECT_CONFIG = "skill"
DEFAULT_AGAINST = "bare"
DEFAULT_MODE = "quality"
EVAL_RUNS_SUBDIR = "eval-runs"
MEMLOG_NAME = ".memlog.md"
QUERIES_DIR = "queries"
ENTRY_TYPES = ("decision", "direction", "assumption", "gap", "note", "event")
FAILURE_STATUS = ("error", "timeout", "exception", "adapter-missing")
CASE_FILES = ("prompt.txt", "case.json", "timing.json")
DEFAULT_SKILL_DIR = ".claude/skills"
DEFAULT_THRESHOLD = 0.5
TOKEN_RE = re.compile(r"\{([^{}]*)\}")


# --------------------------------------------------------------- 基础工具

def utc_now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def stamp():
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def memlog_now():
    return datetime.now().strftime("%Y-%m-%dT%H:%M")


def v(code, where, msg):
    """违规/警告同形构造（warnings 与 violations 逐键一致）。"""
    return {"code": code, "where": str(where).replace("\\", "/"), "msg": msg}


def display_path(path, root):
    """回执里的路径：相对 project-root、正斜杠；越界用绝对路径（母本 §7）。"""
    try:
        rel = os.path.relpath(os.path.abspath(path), os.path.abspath(root))
    except ValueError:
        return os.path.abspath(path).replace("\\", "/")
    if rel.startswith(".."):
        return os.path.abspath(path).replace("\\", "/")
    return rel.replace("\\", "/")


def norm(path):
    return os.path.normpath(os.path.abspath(path)).replace("\\", "/")


def write_json(path, data):
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def read_json(path):
    """读 JSON；(数据, 错误) —— 不抛，调用方决定记违规还是降级。"""
    try:
        with io.open(path, "r", encoding="utf-8", errors="replace") as fh:
            return json.load(fh), None
    except (OSError, ValueError) as e:
        return None, str(e)


def write_text(path, text):
    """写文本。`newline="\\n"` 关掉平台换行翻译——transcript 必须逐字节保真落盘。"""
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def resolve_path_arg(raw, project_root, flag, violations):
    """路径参数解析：`{project-root}` 自解析，其余 `{...}` 令牌一律拒绝（纪律 2）。"""
    if raw is None:
        return None
    text = str(raw)
    if "{project-root}" in text:
        text = text.replace("{project-root}", project_root)
    leftovers = TOKEN_RE.findall(text)
    if leftovers:
        violations.append(v("TOKEN_UNRESOLVED", flag,
                            "路径参数含未解析令牌 {%s}——除 {project-root}（由 --project-root "
                            "自解析）外，其余 {...} 令牌一律拒绝" % leftovers[0]))
        return None
    return os.path.abspath(text)


def emit(payload, as_json, human_lines=None):
    """统一收口：--json 单行回执；否则中文人读行。返回 exit code。"""
    ok = bool(payload.get("ok"))
    if as_json:
        print(json.dumps(payload, ensure_ascii=False))
        return 0 if ok else 1
    for line in (human_lines or []):
        print(line)
    for item in payload.get("violations", []):
        print("VIOL %s %s: %s" % (item["code"], item["where"], item["msg"]))
    for item in payload.get("warnings", []):
        print("WARN %s %s: %s" % (item["code"], item["where"], item["msg"]))
    print("汇总：%s（违规 %d / 警告 %d）"
          % ("OK" if ok else "FAIL", len(payload.get("violations", [])),
             len(payload.get("warnings", []))))
    return 0 if ok else 1


def receipt(command, ok, project_root, output_dir, violations, warnings, counts, **extra):
    payload = {
        "ok": ok,
        "command": command,
        "project_root": project_root,
        "output_dir": output_dir,
        "violations": violations,
        "warnings": warnings,
        "counts": counts,
    }
    payload.update(extra)
    return payload


# --------------------------------------------------------------- adapter

def load_adapter(path):
    """读 adapter.json；形状非法抛 ValueError（调用方降级为默认键 + warning）。"""
    data, err = read_json(path)
    if err is not None:
        raise ValueError("adapter 不可读：%s" % err)
    if not isinstance(data, dict):
        raise ValueError("adapter 必须是 JSON 对象")
    inv = data.get("invocation")
    if inv is not None and not isinstance(inv, list):
        raise ValueError("adapter 的 invocation 必须是 argv 数组")
    return data


def find_adapter(explicit, anchor_dir):
    """adapter 发现：`--adapter` > 用例/问句文件旁的 adapter.json（缺席即取默认键）。"""
    if explicit is not None:
        return explicit if os.path.isfile(explicit) else None
    for name in ("adapter.json",):
        cand = os.path.join(anchor_dir, name)
        if os.path.isfile(cand):
            return cand
    return None


def validate_load_signal(load_signal):
    """子串式 load_signal 直接拒跑（源侧硬规则）。

    运行时的 init 事件会把发现的每个技能名列出来，整篇子串匹配的触发率永远 100%。
    """
    if (load_signal or {}).get("type") == "string":
        return ("load_signal 的 type 'string'（整篇 transcript 子串匹配）不受支持："
                "运行时的 init 事件会列出每个被发现的技能名，子串匹配会让触发率恒为 100%。"
                '改用具名工具调用判定：{"skill_tool": "Skill", "read_tool": "Read"}。')
    return None


def build_argv(invocation, text, cwd):
    out = []
    for tok in invocation:
        out.append(str(tok).replace("{prompt}", text).replace("{query}", text)
                   .replace("{cwd}", cwd))
    return out


def build_case_env(adapter, home_dir, host_env):
    """从零构建子进程环境——**绝不从 os.environ 继承**（隔离契约）。

    继承宿主环境会把 shell 配置、令牌与运行时状态带进清场环境。环境里恰好只有：
    PATH、全新的空 HOME、HOME 内的 CLAUDE_CONFIG_DIR、adapter 的 auth 变量（**仅当宿主
    非空**——传空串会毁掉运行时自己的凭据回落）、以及 adapter 声明的 env_passthrough 键。
    """
    adapter = adapter or {}
    env = {
        "PATH": host_env.get("PATH", ""),
        "HOME": str(home_dir),
        "CLAUDE_CONFIG_DIR": str(os.path.join(str(home_dir), ".claude")),
    }
    auth_env = adapter.get("auth_env")
    if auth_env:
        val = host_env.get(str(auth_env))
        if val:
            env[str(auth_env)] = val
    for key in adapter.get("env_passthrough") or []:
        val = host_env.get(str(key))
        if val is not None:
            env[str(key)] = val
    return env


# --------------------------------------------------------------- 暂存（技能 + 夹具）

def stage_skill(skill_path, cwd, skills_subdir):
    """把被测技能放到清场目录里运行时的技能发现位置（软链优先，失败则整拷）。"""
    dest_root = os.path.join(cwd, skills_subdir)
    os.makedirs(dest_root, exist_ok=True)
    dest = os.path.join(dest_root, os.path.basename(skill_path))
    if not os.path.exists(dest):
        try:
            os.symlink(os.path.abspath(skill_path), dest)
        except OSError:
            shutil.copytree(skill_path, dest, dirs_exist_ok=True)
    return dest


def resolve_fixtures(files, project_root, cases_dir, warnings, where):
    """夹具路径解析：project-root 相对 > 用例文件目录相对 > 绝对路径（保留相对结构）。"""
    out = []
    for entry in files or []:
        entry = str(entry)
        for cand in (os.path.join(project_root, entry), os.path.join(cases_dir, entry), entry):
            cand = os.path.abspath(cand)
            if os.path.isfile(cand):
                out.append((cand, entry))
                break
        else:
            warnings.append(v("MISSING_FILE", where, "夹具文件不存在：%s" % entry))
    return out


def compose_prompt(case):
    """`state_prefix` 前置到 input —— 单发把技能按到流程中段（源侧关键发明）。"""
    text = str(case.get("input", ""))
    prefix = case.get("state_prefix")
    if prefix:
        return "%s\n\n%s" % (str(prefix).rstrip(), text)
    return text


# --------------------------------------------------------------- transcript 记账

def read_transcript(transcript_cfg, captured, cwd):
    """返回 (transcript 文本, 来源说明)；来源命名它从哪来。"""
    cfg = transcript_cfg or {}
    if cfg.get("format") == "file":
        rel = cfg.get("path", "transcript.jsonl")
        path = os.path.join(cwd, rel)
        if os.path.isfile(path):
            return io.open(path, encoding="utf-8", errors="replace").read(), "file:%s" % rel
        return "", "file:%s (missing)" % rel
    return captured.decode("utf-8", errors="replace"), "stdout"


def account_transcript(text):
    """从 JSONL transcript 取 token 用量与步骤/工具调用计数（未知形状降级为 0，不失败）。"""
    input_tokens = output_tokens = total_steps = 0
    tool_calls = {}
    found = False
    for raw in text.splitlines():
        raw = raw.strip()
        if not raw:
            continue
        try:
            evt = json.loads(raw)
        except ValueError:
            continue
        if not isinstance(evt, dict):
            continue
        etype = evt.get("type")
        if etype == "assistant":
            total_steps += 1
            msg = evt.get("message", {})
            usage = msg.get("usage") if isinstance(msg, dict) else None
            if isinstance(usage, dict):
                found = True
                input_tokens += int(usage.get("input_tokens", 0) or 0)
                output_tokens += int(usage.get("output_tokens", 0) or 0)
            for item in (msg.get("content", []) if isinstance(msg, dict) else []):
                if isinstance(item, dict) and item.get("type") == "tool_use":
                    name = item.get("name", "?")
                    tool_calls[name] = tool_calls.get(name, 0) + 1
        elif etype == "result":
            usage = evt.get("usage")
            if isinstance(usage, dict):
                found = True
                # result 事件的 usage 是权威值，覆盖此前累加
                input_tokens = int(usage.get("input_tokens", input_tokens) or input_tokens)
                output_tokens = int(usage.get("output_tokens", output_tokens) or output_tokens)
    return {"input_tokens": input_tokens, "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens, "tokens_reported": found,
            "total_steps": total_steps, "tool_calls": tool_calls,
            "total_tool_calls": sum(tool_calls.values())}


# --------------------------------------------------------------- 单 case 执行

def run_case(case, case_dir, run_dir, adapter, timeout, config, skill_path,
             fixtures, skip_reason):
    """跑一个 case 的一个 config：stage → invoke → 记账 → 落盘。

    `skip_reason` 非空 = 降级路径（只 stage、结果记 skipped，不崩不静默）。
    """
    case_id = str(case.get("id", "unnamed"))
    cwd = os.path.join(case_dir, "cwd")
    os.makedirs(cwd, exist_ok=True)

    for src, rel in fixtures:
        dest = os.path.join(cwd, rel)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.copy2(src, dest)
    if skill_path is not None:
        stage_skill(skill_path, cwd, (adapter or {}).get("skill_dir", DEFAULT_SKILL_DIR))

    prompt = compose_prompt(case)
    write_text(os.path.join(case_dir, "prompt.txt"), prompt)
    write_json(os.path.join(case_dir, "case.json"), case)

    rel_dir = os.path.relpath(case_dir, run_dir).replace("\\", "/")
    if skip_reason or adapter is None:
        reason = skip_reason or "未配置运行时 adapter"
        write_json(os.path.join(case_dir, "timing.json"), {
            "case_id": case_id, "config": config, "status": "skipped",
            "reason": reason, "captured_at": utc_now_iso(),
        })
        return {"case_id": case_id, "config": config, "status": "skipped",
                "reason": reason, "dir": rel_dir, "prompt_chars": len(prompt)}

    transcript_path = os.path.join(case_dir, "transcript.jsonl")
    argv = build_argv(adapter["invocation"], prompt, cwd)
    home_dir = os.path.join(case_dir, ".home")
    os.makedirs(os.path.join(home_dir, ".claude"), exist_ok=True)
    env = build_case_env(adapter, home_dir, os.environ)

    start = time.time()
    captured, return_code, error_tail, status = b"", 0, "", "ok"
    try:
        proc = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              cwd=cwd, env=env, timeout=timeout)
        captured = proc.stdout or b""
        return_code = proc.returncode
        error_tail = (proc.stderr or b"").decode("utf-8", errors="replace")[-2000:]
        if return_code != 0:
            status = "error"
    except FileNotFoundError as e:
        write_json(os.path.join(case_dir, "timing.json"), {
            "case_id": case_id, "config": config, "status": "adapter-missing",
            "elapsed_s": round(time.time() - start, 3),
            "reason": "invocation 命令不存在：%s" % e, "captured_at": utc_now_iso()})
        return {"case_id": case_id, "config": config, "status": "adapter-missing",
                "reason": str(e), "dir": rel_dir}
    except subprocess.TimeoutExpired as e:
        captured = e.stdout or b""
        return_code, status = -1, "timeout"
        error_tail = "TIMEOUT after %ss" % timeout
    elapsed = time.time() - start

    text, source = read_transcript(adapter.get("transcript", {}), captured, cwd)
    write_text(transcript_path, text)
    acc = account_transcript(text)
    write_json(os.path.join(case_dir, "timing.json"), {
        "case_id": case_id, "config": config, "status": status,
        "elapsed_s": round(elapsed, 3), "return_code": return_code,
        "transcript_source": source, "input_tokens": acc["input_tokens"],
        "output_tokens": acc["output_tokens"], "total_tokens": acc["total_tokens"],
        "tokens_reported": acc["tokens_reported"], "total_steps": acc["total_steps"],
        "total_tool_calls": acc["total_tool_calls"], "captured_at": utc_now_iso(),
    })
    return {"case_id": case_id, "config": config, "status": status,
            "elapsed_s": round(elapsed, 3), "return_code": return_code,
            "dir": rel_dir, "tokens": acc["total_tokens"],
            "tool_calls": acc["tool_calls"], "error_tail": error_tail}


# --------------------------------------------------------------- trigger 专用

def write_synthetic_skill(skills_dir, skill_name, description, unique):
    """写一个运行时能发现的合成技能（唯一名后缀把它与同名真技能区分开）。"""
    clean_name = "%s-trig-%s" % (skill_name, unique)
    root = os.path.join(skills_dir, clean_name)
    os.makedirs(root, exist_ok=True)
    indented = "\n  ".join(str(description).split("\n"))
    write_text(os.path.join(root, "SKILL.md"),
               "---\nname: %s\ndescription: |\n  %s\n---\n\n# %s\n\nThis skill handles: %s\n"
               % (clean_name, indented, skill_name, description))
    return clean_name


def parse_skill_md(skill_path):
    """取 SKILL.md frontmatter 的 (name, description)。"""
    text = io.open(os.path.join(skill_path, "SKILL.md"), encoding="utf-8").read()
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not m:
        raise ValueError("SKILL.md 缺 frontmatter")
    name, desc, in_desc = None, [], False
    for line in m.group(1).splitlines():
        if line.startswith("name:"):
            name, in_desc = line.split(":", 1)[1].strip(), False
        elif line.startswith("description:"):
            val = line.split(":", 1)[1].strip()
            if val in ("|", ">"):
                in_desc = True
            else:
                desc, in_desc = [val], False
        elif in_desc and line.startswith(("  ", "\t")):
            desc.append(line.strip())
        elif in_desc:
            in_desc = False
    if not name:
        raise ValueError("SKILL.md frontmatter 缺 name")
    return name, " ".join(desc).strip()


def detect_load(transcript_text, load_signal, clean_name):
    """合成技能触发了吗？**只有 `tool_use` 事件算数**。

    流式 transcript 的 init 事件会把每个被发现的技能名列出来，所以「名字在整篇里出现过」
    什么也证明不了。触发 = 一次点名合成技能的技能调用工具，或一次落在合成技能目录内的读取
    ——这是运行时真正把技能拉进上下文的两种方式。
    """
    sig = load_signal or {}
    skill_tool = sig.get("skill_tool", "Skill")
    read_tool = sig.get("read_tool", "Read")
    for raw in transcript_text.splitlines():
        raw = raw.strip()
        if not raw:
            continue
        try:
            evt = json.loads(raw)
        except ValueError:
            continue
        if not isinstance(evt, dict) or evt.get("type") != "assistant":
            continue
        msg = evt.get("message", {})
        for item in (msg.get("content", []) if isinstance(msg, dict) else []):
            if not isinstance(item, dict) or item.get("type") != "tool_use":
                continue
            name, inp = item.get("name"), item.get("input", {})
            if not isinstance(inp, dict):
                inp = {}
            if name == skill_tool and clean_name in json.dumps(inp, ensure_ascii=False):
                return True
            if name == read_tool and clean_name in str(inp.get("file_path", "")):
                return True
    return False


def run_query_once(query, skill_name, description, adapter, stage_dir, timeout,
                   skip_reason, unique):
    """跑一条问句的一次：stage 合成技能 → invoke → 取 transcript → 判触发。

    唯一名后缀由调用方按**问句**给（同一问句的多次重复用同一个名字）：既足以把它与同名真
    技能区分开，又让「同一问句的多次重复」在 run 目录里可比、可审。
    """
    skill_subdir = adapter.get("skill_dir", DEFAULT_SKILL_DIR) if adapter else DEFAULT_SKILL_DIR
    skills_dir = os.path.join(stage_dir, skill_subdir)
    os.makedirs(skills_dir, exist_ok=True)
    os.makedirs(os.path.join(stage_dir, ".home", ".claude"), exist_ok=True)
    clean_name = write_synthetic_skill(skills_dir, skill_name, description, unique)
    # 合成技能与 .home 留在 query 目录里（run 目录永不删改；这也是「只认 tool_use」的现场证据）
    if skip_reason or adapter is None:
        return False, clean_name, None
    argv = build_argv(adapter["invocation"], query, stage_dir)
    env = build_case_env(adapter, os.path.join(stage_dir, ".home"), os.environ)
    try:
        proc = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                              cwd=stage_dir, env=env, timeout=timeout)
        captured = proc.stdout or b""
    except subprocess.TimeoutExpired as e:
        captured = e.stdout or b""
    except FileNotFoundError:
        return False, clean_name, None
    cfg = adapter.get("transcript", {})
    if cfg.get("format") == "file":
        path = os.path.join(stage_dir, cfg.get("path", "transcript.jsonl"))
        text = io.open(path, encoding="utf-8", errors="replace").read() if os.path.isfile(path) else ""
    else:
        text = captured.decode("utf-8", errors="replace")
    return detect_load(text, adapter.get("load_signal", {}), clean_name), clean_name, text


# --------------------------------------------------------------- memlog（与 W1 同构）

def memlog_split(text):
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        raise ValueError(".memlog.md 缺 frontmatter")
    end = next((i for i in range(1, len(lines)) if lines[i] == "---"), None)
    if end is None:
        raise ValueError(".memlog.md 的 frontmatter 未闭合")
    meta = {}
    for line in lines[1:end]:
        if ":" in line:
            k, val = line.split(":", 1)
            meta[k.strip()] = val.strip()
    return meta, "\n".join(lines[end + 1:]).lstrip("\n")


def memlog_render(meta, body):
    fm = "\n".join("%s: %s" % (k, " ".join(str(val).splitlines())) for k, val in meta.items())
    return "---\n%s\n---\n\n%s\n" % (fm, body.rstrip("\n"))


def memlog_touch(meta):
    meta.pop("updated", None)
    meta["updated"] = memlog_now()


def memlog_count(body):
    return sum(1 for ln in body.splitlines() if ln.startswith("- "))


def write_atomic(path, text):
    """临时文件 + flush + fsync + 原子改名：崩溃不会留半条记录。"""
    tmp = path + ".tmp"
    with io.open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def memlog_init(path, subject):
    """建 memlog；已存在抛 FileExistsError（只追加，永不覆盖）。"""
    if os.path.exists(path):
        raise FileExistsError(path)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    meta = {"status": "active"}
    if subject:
        meta = {"subject": subject, "status": "active"}
    memlog_touch(meta)
    write_atomic(path, memlog_render(meta, ""))
    return 0


def memlog_append(path, entry_type, text):
    meta, body = memlog_split(io.open(path, encoding="utf-8").read())
    entry = "- (%s) %s" % (entry_type, " ".join(str(text).split()))
    body = (body.rstrip("\n") + "\n" + entry) if body.strip() else entry
    memlog_touch(meta)
    write_atomic(path, memlog_render(meta, body))
    return memlog_count(body)


def memlog_set_complete(path):
    meta, body = memlog_split(io.open(path, encoding="utf-8").read())
    meta["status"] = "complete"
    memlog_touch(meta)
    write_atomic(path, memlog_render(meta, body))
    return memlog_count(body)


# --------------------------------------------------------------- run 子命令

def configs_for(modes):
    out = []
    for mode in ("baseline", "variant", "quality"):
        if mode in modes:
            for cfg in CONFIG_ORDER[mode]:
                if cfg not in out:
                    out.append(cfg)
    return out


def discover_cases(skill_dir, explicit, project_root):
    """用例发现链（找不到就停——运行器不发明用例）。"""
    chain = []
    if explicit:
        chain.append(explicit)
    chain.append(os.path.join(skill_dir, "evals", "cases.json"))
    name = os.path.basename(os.path.normpath(skill_dir))
    chain.append(os.path.join(project_root, "evals", name, "cases.json"))
    chain.append(os.path.join(project_root, "evals", "cases.json"))
    for cand in chain:
        if os.path.isfile(cand):
            return cand
    return None


def unique_run_dir(base, label):
    """run 目录唯一化：同名已存在则另铸后缀，**绝不覆盖**既有 run。"""
    cand = os.path.join(base, "%s-%s" % (stamp(), label))
    n = 2
    while os.path.exists(cand):
        cand = os.path.join(base, "%s-%s-%d" % (stamp(), label, n))
        n += 1
    return cand


def finish_run(args, root, out, violations, warnings, counts, run_id=None, run_dir=None,
               modes=None):
    payload = receipt("run", not violations, args.project_root, norm(out) if out else "",
                      violations, warnings, counts,
                      run_id=run_id, run_dir=norm(run_dir) if run_dir else None,
                      modes=list(modes or []))
    lines = ["评测运行：%s" % (run_id or "未开始"),
             "run 目录：%s" % (norm(run_dir) if run_dir else "（未创建）")]
    return emit(payload, args.json, lines)


def cmd_run(args):
    violations, warnings = [], []
    root = os.path.abspath(args.project_root)
    out = resolve_path_arg(args.output_dir, root, "--output-dir", violations)
    skill = resolve_path_arg(args.skill, root, "--skill", violations)
    cases_arg = resolve_path_arg(args.evals, root, "--evals", violations)
    variant = resolve_path_arg(args.variant_path, root, "--variant-path", violations)
    adapter_arg = resolve_path_arg(args.adapter, root, "--adapter", violations)
    queries_arg = resolve_path_arg(args.queries, root, "--queries", violations)
    counts = {"cases": 0, "configs": 0, "results": 0, "executed": 0, "skipped": 0,
              "failures": 0, "trigger_queries": 0}
    if violations:
        return finish_run(args, root, out, violations, warnings, counts)

    modes = list(args.mode) if args.mode else [DEFAULT_MODE]
    bad = [m for m in modes if m not in MODES]
    if bad:
        violations.append(v("ENUM_INVALID", "--mode",
                            "模式 %r 非法——合法值恰四个：%s" % (bad[0], " / ".join(MODES))))
        return finish_run(args, root, out, violations, warnings, counts)
    modes = [m for m in MODES if m in modes]

    # 门禁①：target 技能必须存在且含 SKILL.md
    if not skill or not os.path.isdir(skill) or not os.path.isfile(os.path.join(skill, "SKILL.md")):
        violations.append(v("MISSING_FILE", display_path(args.skill, root) if skill else "--skill",
                            "target 技能目录不存在或不含 SKILL.md——评测对象必须是技能目录"))
    if violations:
        return finish_run(args, root, out, violations, warnings, counts)

    # 用法错误（exit 2）：variant 必须给 --variant-path
    if "variant" in modes and not variant:
        print("diy-eval-runner: --mode variant 必须同时给 --variant-path（对比用的精简最小版）",
              file=sys.stderr)
        return 2
    if variant and not os.path.isfile(os.path.join(variant, "SKILL.md")):
        violations.append(v("MISSING_FILE", display_path(variant, root),
                            "--variant-path 不含 SKILL.md"))
    need_config = any(m in CONFIG_MODES for m in modes)

    # 门禁②：用例文件（找不到就停——运行器不发明用例）
    cases_file = None
    if need_config:
        cases_file = discover_cases(skill, cases_arg, root)
        if cases_file is None:
            violations.append(v("MISSING_FILE", "%s/evals/cases.json" % os.path.basename(skill),
                                "找不到用例文件（--evals > <技能>/evals/cases.json > "
                                "<project-root>/evals/<技能名>/cases.json）——运行器不发明用例"))
    queries = None
    if "trigger" in modes:
        if not queries_arg or not os.path.isfile(queries_arg):
            violations.append(v("MISSING_FILE", display_path(queries_arg, root) if queries_arg
                                else "--queries",
                                "trigger 模式需要 --queries（问句文件，形态 "
                                '{"query": ..., "should_trigger": true|false}）'))
        else:
            queries, err = read_json(queries_arg)
            if err is not None or not isinstance(queries, list):
                violations.append(v("UNPARSABLE_JSON", display_path(queries_arg, root),
                                    "问句文件必须是 JSON 数组：%s" % (err or "形状不是数组")))
                queries = None
    if violations:
        return finish_run(args, root, out, violations, warnings, counts)

    # adapter：缺席取默认键、形状非法降级 + warning
    adapter, adapter_note = None, "none"
    anchor_dir = os.path.dirname(cases_file or queries_arg or skill)
    adapter_path = find_adapter(adapter_arg, anchor_dir)
    if adapter_path is not None:
        try:
            adapter = load_adapter(adapter_path)
            adapter_note = display_path(adapter_path, root)
        except ValueError as e:
            warnings.append(v("ADAPTER_INVALID", display_path(adapter_path, root),
                              "%s——逐键取默认继续" % e))
            adapter, adapter_note = None, "invalid"
    if args.invocation:
        adapter = dict(adapter or {})
        adapter["invocation"] = list(args.invocation)

    # 门禁④：子串式 load_signal 拒跑（源侧硬规则）
    if "trigger" in modes and adapter is not None:
        msg = validate_load_signal(adapter.get("load_signal"))
        if msg:
            violations.append(v("ENUM_INVALID", adapter_note or "--adapter", msg))
            return finish_run(args, root, out, violations, warnings, counts)

    invocation = (adapter or {}).get("invocation")
    skip_reason = ""
    if not invocation:
        warnings.append(v("ADAPTER_MISSING", "--invocation",
                          "未配置 invocation（既无 --invocation 也无 adapter.json 的 "
                          "invocation 键）：只 stage、结果记 skipped，既不崩也不静默。"
                          "给 --invocation <命令…> 或 adapter.json 的 invocation 键即可真跑。"))
        skip_reason = "未配置 invocation"
    else:
        exe = str(invocation[0])
        if shutil.which(exe) is None and not os.path.isfile(exe):
            for mode in modes:
                warnings.append(v("MODE_SKIPPED", mode,
                                  "invocation 命令 `%s` 不可解析（无头下即 runner.py 白名单"
                                  "未覆盖该命令族）——跳过 mode `%s`：只 stage、不执行，"
                                  "不入队；调用方需额外命令族时经 `runner.py --allow` 传入。"
                                  % (exe, mode)))
            skip_reason = "invocation 命令不可解析：%s" % exe

    if need_config:
        try:
            cases, err = read_json(cases_file)
        except Exception as e:  # 读取层兜底：任何意外都转成违规，不裸栈
            cases, err = None, str(e)
        if err is not None:
            violations.append(v("UNPARSABLE_JSON", display_path(cases_file, root),
                                "用例文件不可读：%s" % err))
            return finish_run(args, root, out, violations, warnings, counts)
        if isinstance(cases, dict) and "cases" in cases:
            cases = cases["cases"]
        if not isinstance(cases, list):
            violations.append(v("EMPTY_FIELD", display_path(cases_file, root),
                                "用例文件必须是数组或 {cases: [...]}"))
            return finish_run(args, root, out, violations, warnings, counts)
    else:
        cases = []

    configs = configs_for(modes)
    label = args.label or (("%s-triggers" % os.path.basename(os.path.normpath(skill)))
                           if modes == ["trigger"] else "evals")
    runs_base = os.path.join(out, EVAL_RUNS_SUBDIR)
    os.makedirs(runs_base, exist_ok=True)
    run_dir = unique_run_dir(runs_base, label)

    # 续接提示（不自动续跑、不合并、不覆盖；本批不做 --resume）
    for name in sorted(os.listdir(runs_base)):
        cand = os.path.join(runs_base, name)
        if not name.endswith("-%s" % label) or not os.path.isdir(cand):
            continue
        if not os.path.isfile(os.path.join(cand, "execution-summary.json")):
            warnings.append(v("INCOMPLETE_RUN", display_path(cand, root),
                              "已有未完成 run `%s`；如需重跑请另起 run-id"
                              "（时间戳天然不同）——不自动续跑、不合并、不覆盖。" % name))
    os.makedirs(run_dir, exist_ok=True)

    skill_name = os.path.basename(os.path.normpath(skill))
    try:
        memlog_init(os.path.join(run_dir, MEMLOG_NAME), os.path.basename(run_dir))
        memlog_append(os.path.join(run_dir, MEMLOG_NAME), "event",
                      "run 启动：mode=%s configs=%s" % ("/".join(modes), "/".join(configs) or "-"))
    except (OSError, ValueError) as e:
        warnings.append(v("EMPTY_FIELD", MEMLOG_NAME, "run memlog 初始化失败：%s" % e))

    case_count = len(cases) if need_config else len(queries or [])
    write_json(os.path.join(run_dir, "run.json"), {
        "run_id": os.path.basename(run_dir),
        "cases_file": display_path(cases_file, root) if cases_file else None,
        "skill_path": norm(skill),
        "variant_path": norm(variant) if variant else None,
        "mode": modes,
        "configs": configs,
        "runs_per_case": max(1, args.runs),
        "adapter": adapter_note,
        "started_at": utc_now_iso(),
        "case_count": case_count,
        "query_count": len(queries or []),
        "load_signal": (adapter or {}).get("load_signal") or {},
    })

    results, skipped_modes = [], []
    if skip_reason:
        skipped_modes = [{"mode": m, "reason": skip_reason} for m in modes]

    # 模式面：config 三模式（baseline / variant / quality）
    for config in configs:
        config_skill = variant if config == "variant" else (
            None if config == "bare" else skill)
        for case in cases:
            case_id = str(case.get("id", "unnamed"))
            fixtures = resolve_fixtures(case.get("files", []), root,
                                        os.path.dirname(cases_file), warnings,
                                        "cases[%s]" % case_id)
            for i in range(max(1, args.runs)):
                base_dir = os.path.join(run_dir, config, case_id)
                case_dir = os.path.join(base_dir, "run-%d" % (i + 1)) \
                    if args.runs > 1 else base_dir
                results.append(run_case(case, case_dir, run_dir, adapter,
                                        int(case.get("timeout", args.timeout)), config,
                                        config_skill, fixtures, skip_reason))

    # trigger 模式：合成技能 + 逐问句真跑，只认 tool_use
    if "trigger" in modes:
        queries_dir = os.path.join(run_dir, QUERIES_DIR)
        os.makedirs(queries_dir, exist_ok=True)
        if skip_reason:
            counts["trigger_queries"] = len(queries)
            write_json(os.path.join(run_dir, "triggers-result.json"), {
                "run_id": os.path.basename(run_dir), "completed_at": utc_now_iso(),
                "skill_name": skill_name, "status": "skipped", "reason": skip_reason,
                "detection": "tool_use", "results": [],
                "summary": {"total": len(queries), "passed": 0, "failed": 0,
                            "skipped": len(queries)}})
        else:
            try:
                skill_name, description = parse_skill_md(skill)
            except (OSError, ValueError) as e:
                violations.append(v("EMPTY_FIELD", display_path(skill, root),
                                    "SKILL.md frontmatter 不可解析：%s" % e))
                return finish_run(args, root, out, violations, warnings, counts)
            threshold = DEFAULT_THRESHOLD
            per_query, synthetics, ran = {}, {}, {}
            for idx, item in enumerate(queries):
                runs = []
                unique = uuid.uuid4().hex[:8]      # 每个问句一个后缀，其多次重复共用
                for run_idx in range(1, max(1, args.runs) + 1):
                    stage = os.path.join(queries_dir, "q%03d-r%d" % (idx, run_idx))
                    os.makedirs(stage, exist_ok=True)
                    hit, clean_name, text = run_query_once(
                        str(item.get("query", "")), skill_name, description, adapter,
                        stage, args.timeout, skip_reason, unique)
                    if text is not None:
                        write_text(os.path.join(stage, "transcript.jsonl"), text)
                    synthetics[idx] = clean_name
                    if text is None:
                        ran[idx] = False
                    runs.append(hit)
                per_query[idx] = runs
            if ran:
                # 预检之后命令仍不可解析（竞态/被清出 PATH）：不静默——按源侧语义记
                # adapter-missing，本轮不出触发率
                reason = "invocation 命令在运行期不可解析：%s" % invocation[0]
                warnings.append(v("MODE_SKIPPED", "trigger", "%s——本 mode 无触发率可出。" % reason))
                skipped_modes.append({"mode": "trigger", "reason": reason})
                counts["trigger_queries"] = len(queries)
                write_json(os.path.join(run_dir, "triggers-result.json"), {
                    "run_id": os.path.basename(run_dir), "completed_at": utc_now_iso(),
                    "skill_name": skill_name, "status": "adapter-missing",
                    "reason": reason, "detection": "tool_use", "results": [],
                    "summary": {"total": len(queries), "passed": 0, "failed": 0}})
            else:
                trig_results = []
                for idx, item in enumerate(queries):
                    runs = per_query.get(idx, [])
                    rate = (sum(1 for x in runs if x) / len(runs)) if runs else 0.0
                    should = bool(item.get("should_trigger", True))
                    passed = (rate >= threshold) if should else (rate < threshold)
                    trig_results.append({
                        "query": item.get("query", ""), "should_trigger": should,
                        "trigger_rate": round(rate, 3),
                        "triggers": sum(1 for x in runs if x), "runs": len(runs),
                        "pass": passed, "synthetic": synthetics.get(idx, ""),
                    })
                counts["trigger_queries"] = len(trig_results)
                write_json(os.path.join(run_dir, "triggers-result.json"), {
                    "run_id": os.path.basename(run_dir), "completed_at": utc_now_iso(),
                    "skill_name": skill_name, "description": description,
                    "detection": "tool_use", "threshold": threshold,
                    "runs_per_query": max(1, args.runs), "results": trig_results,
                    "summary": {"total": len(trig_results),
                                "passed": sum(1 for x in trig_results if x["pass"]),
                                "failed": sum(1 for x in trig_results if not x["pass"])},
                })

    executed = sum(1 for x in results if x.get("status") == "ok")
    skipped = sum(1 for x in results if x.get("status") == "skipped")
    failures = sum(1 for x in results if x.get("status") in FAILURE_STATUS)
    write_json(os.path.join(run_dir, "execution-summary.json"), {
        "run_id": os.path.basename(run_dir), "completed_at": utc_now_iso(),
        "mode": modes, "total": len(results), "executed": executed,
        "skipped": skipped, "failures": failures, "run_dir": norm(run_dir),
        "skipped_modes": skipped_modes, "results": results,
    })
    counts.update({"cases": len(cases), "configs": len(configs), "results": len(results),
                   "executed": executed, "skipped": skipped, "failures": failures})
    return finish_run(args, root, out, violations, warnings, counts,
                      run_id=os.path.basename(run_dir), run_dir=run_dir, modes=modes)


# --------------------------------------------------------------- aggregate 子命令

NUMERIC = (int, float)


def sample_stddev(values):
    """样本标准差（n-1 贝塞尔校正）；少于两个值时返回 0.0（样本方差无定义）。"""
    n = len(values)
    if n < 2:
        return 0.0
    mean = sum(values) / n
    return math.sqrt(sum((x - mean) ** 2 for x in values) / (n - 1))


def summarize_metric(values):
    return {"n": len(values),
            "mean": (sum(values) / len(values)) if values else 0.0,
            "stddev": sample_stddev(values),
            "min": min(values) if values else 0.0,
            "max": max(values) if values else 0.0}


def summarize_config(records):
    by_metric = {}
    for rec in records:
        if not isinstance(rec, dict):
            continue
        for key, val in rec.items():
            if isinstance(val, bool) or not isinstance(val, NUMERIC):
                continue    # bool 在 Python 里是 int，但不是指标
            by_metric.setdefault(key, []).append(float(val))
    return {"runs": len(records),
            "metrics": {k: summarize_metric(x) for k, x in sorted(by_metric.items())}}


def load_records(run_dir, warnings):
    """读 run 目录下全部 timing.json（跳过 trigger 的 query 目录）。"""
    records, bad = [], []
    for dirpath, _dirs, files in os.walk(run_dir):
        if "timing.json" not in files:
            continue
        if os.path.sep + QUERIES_DIR + os.path.sep in dirpath + os.path.sep:
            continue
        path = os.path.join(dirpath, "timing.json")
        data, err = read_json(path)
        if err is not None:
            bad.append((path, err))
            continue
        records.append(data)
    for path, err in bad:
        warnings.append(v("UNPARSABLE_JSON", display_path(path, run_dir),
                          "timing.json 不可解析、已跳过：%s" % err))
    return records


def delta_configs(subject, against):
    """逐共享指标：delta = subject.mean − against.mean（源侧同形：B − A）。"""
    out = {}
    for name in sorted(set(subject["metrics"]) & set(against["metrics"])):
        s, a = subject["metrics"][name], against["metrics"][name]
        diff = s["mean"] - a["mean"]
        pct = (diff / a["mean"] * 100.0) if a["mean"] != 0 else None
        out[name] = {"subject_mean": s["mean"], "against_mean": a["mean"],
                     "delta": diff, "delta_pct": pct,
                     "subject_stddev": s["stddev"], "against_stddev": a["stddev"]}
    return out


def aggregate_self_test():
    """固定夹具校验 mean / n-1 标准差 / min / max / delta（源侧 --self-test 同款数值）。"""
    config_a = [{"elapsed_s": 10.0, "total_tokens": 100},
                {"elapsed_s": 12.0, "total_tokens": 200},
                {"elapsed_s": 14.0, "total_tokens": 300}]
    config_b = [{"elapsed_s": 13.0, "total_tokens": 90},
                {"elapsed_s": 15.0, "total_tokens": 110},
                {"elapsed_s": 17.0, "total_tokens": 100}]
    a, b = summarize_config(config_a), summarize_config(config_b)
    el = a["metrics"]["elapsed_s"]
    assert el["n"] == 3 and abs(el["mean"] - 12.0) < 1e-9
    assert abs(el["stddev"] - 2.0) < 1e-9, el      # 10,12,14 → sqrt((4+0+4)/2) = 2
    assert el["min"] == 10.0 and el["max"] == 14.0
    assert abs(a["metrics"]["total_tokens"]["stddev"] - 100.0) < 1e-9
    assert summarize_config([{"x": 5}])["metrics"]["x"]["stddev"] == 0.0
    with_bool = summarize_config([{"ok": True, "x": 1}, {"ok": False, "x": 3}])
    assert "ok" not in with_bool["metrics"]
    d = delta_configs(b, a)     # subject = b（13,15,17 → 15）− against = a（12）→ +3
    assert abs(d["elapsed_s"]["delta"] - 3.0) < 1e-9, d
    assert abs(d["elapsed_s"]["delta_pct"] - 25.0) < 1e-9, d
    return ["mean", "stddev_n_minus_1", "min", "max", "single_value_stddev",
            "bool_excluded", "delta", "delta_pct"]


def cmd_aggregate(args):
    violations, warnings = [], []
    root = os.path.abspath(args.project_root)
    out = resolve_path_arg(args.output_dir, root, "--output-dir", violations)
    if violations:
        return emit(receipt("aggregate", False, args.project_root, "", violations,
                            warnings, {}), args.json)
    if args.self_test:
        checked = aggregate_self_test()
        payload = receipt("aggregate", True, args.project_root, norm(out) if out else "",
                          [], [], {"checked": len(checked)}, self_test="passed",
                          checked=checked)
        return emit(payload, args.json, ["aggregate 自检通过：%s" % " / ".join(checked)])
    if not args.run_dir:
        print("diy-eval-runner: aggregate 需要 --run-dir D（或改用 --self-test）", file=sys.stderr)
        return 2
    run_dir = resolve_path_arg(args.run_dir, root, "--run-dir", violations)
    if violations:
        return emit(receipt("aggregate", False, args.project_root, "", violations,
                            warnings, {}), args.json)
    if not os.path.isdir(run_dir):
        violations.append(v("MISSING_FILE", display_path(run_dir, root), "run 目录不存在"))
        return emit(receipt("aggregate", False, args.project_root, "", violations,
                            warnings, {}), args.json)

    records = load_records(run_dir, warnings)
    grouped = {}
    for rec in records:
        if isinstance(rec, dict):
            grouped.setdefault(str(rec.get("config", "?")), []).append(rec)
    run_json, _err = read_json(os.path.join(run_dir, "run.json"))
    known = []
    if isinstance(run_json, dict) and isinstance(run_json.get("configs"), list):
        known = [str(c) for c in run_json["configs"]]
    for cfg in known:
        grouped.setdefault(cfg, [])
    configs = {name: summarize_config(recs) for name, recs in sorted(grouped.items())}
    counts = {"configs": len(configs), "runs": sum(c["runs"] for c in configs.values()),
              "metrics": len(configs.get(SUBJECT_CONFIG, {}).get("metrics", {}))}

    against = args.against or DEFAULT_AGAINST
    subject = SUBJECT_CONFIG if SUBJECT_CONFIG in configs else None
    delta = {}
    if subject is None:
        warnings.append(v("EMPTY_FIELD", display_path(run_dir, root),
                          "本次 run 无 `skill` config（trigger 模式无配置对比面）——"
                          "只出各 config 的均值与离散度，无 delta"))
    elif against not in configs:
        others = [c for c in configs if c != subject]
        if args.against:
            violations.append(v("UNKNOWN_ID", "--against",
                                "基准 config `%s` 不在本次 run 里（在场：%s）"
                                % (against, " / ".join(configs))))
        elif len(others) == 1:
            warnings.append(v("AGAINST_FALLBACK", "--against",
                              "缺省基准 config `%s` 不在场——退回 `%s` 作基准"
                              "（delta = %s − %s）" % (against, others[0], subject, others[0])))
            against = others[0]
        else:
            warnings.append(v("EMPTY_FIELD", "--against",
                              "缺省基准 config `%s` 不在场且无法唯一退回（在场：%s）——"
                              "本次不出 delta" % (against, " / ".join(configs))))
    if not violations and subject is not None and against in configs and against != subject:
        delta = delta_configs(configs[subject], configs[against])

    payload = receipt("aggregate", not violations, args.project_root,
                      norm(out) if out else "", violations, warnings, counts,
                      run_dir=norm(run_dir), subject=subject, against=against,
                      configs=configs, delta=delta)
    lines = ["聚合：%s" % norm(run_dir)]
    for name, conf in configs.items():
        mean = conf["metrics"].get("elapsed_s", {}).get("mean")
        lines.append("- %s：runs=%d elapsed_s 均值=%s" % (name, conf["runs"], mean))
    if delta:
        lines.append("- delta（%s − %s）：%s" % (subject, against,
                                                json.dumps(delta, ensure_ascii=False)))
    return emit(payload, args.json, lines)


# --------------------------------------------------------------- check 子命令（终门）

def check_run_json(run_dir, root, violations):
    path = os.path.join(run_dir, "run.json")
    if not os.path.isfile(path):
        violations.append(v("MISSING_FILE", display_path(path, root),
                            "run.json 缺失——不是 run 目录"))
        return None
    data, err = read_json(path)
    if err is not None:
        violations.append(v("UNPARSABLE_JSON", display_path(path, root), "解析失败：%s" % err))
        return None
    for key in ("run_id", "skill_path", "mode", "configs", "runs_per_case",
                "adapter", "started_at", "case_count"):
        if key not in data:
            violations.append(v("EMPTY_FIELD", "%s.%s" % (display_path(path, root), key),
                                "run.json 缺必填字段 %s" % key))
    modes = data.get("mode")
    modes = modes if isinstance(modes, list) else [modes]
    # configs 只在真的跑了 config 模式时才要求非空（trigger-only 的 run 合法地没有 config）
    empties = [k for k in ("run_id", "skill_path", "runs_per_case", "started_at")
               if data.get(k) in (None, "", [], {})]
    if "adapter" not in data:
        empties.append("adapter")
    if data.get("case_count") is None:
        empties.append("case_count")
    if not modes:
        empties.append("mode")
    if any(m in CONFIG_MODES for m in modes) and not data.get("configs"):
        empties.append("configs")
    for key in empties:
        violations.append(v("EMPTY_FIELD", "%s.%s" % (display_path(path, root), key),
                            "run.json 的 %s 为空（缺必填面）" % key))
    for mode in modes:
        if mode not in MODES:
            violations.append(v("ENUM_INVALID", "%s.mode" % display_path(path, root),
                                "模式 %r 非法——合法值恰四个：%s" % (mode, " / ".join(MODES))))
    return data


def check_case_dirs(run_dir, root, results, modes, violations):
    """逐结果验目录与文件；quality 另验 grading.json 的举证非空。"""
    timings = set()
    for dirpath, _dirs, files in os.walk(run_dir):
        if "timing.json" in files:
            timings.add(norm(dirpath))
    seen = set()
    for res in results:
        reldir = res.get("dir")
        if not reldir:
            violations.append(v("EMPTY_FIELD", "execution-summary.json results[]",
                                "结果条目缺 dir——check 靠它定位 case 目录"))
            continue
        case_dir = norm(os.path.join(run_dir, reldir))
        seen.add(case_dir)
        if not os.path.isdir(case_dir):
            violations.append(v("MISSING_FILE", display_path(case_dir, root),
                                "结果声明的 case 目录不存在"))
            continue
        for name in CASE_FILES:
            if not os.path.isfile(os.path.join(case_dir, name)):
                violations.append(v("MISSING_FILE", "%s/%s" % (display_path(case_dir, root), name),
                                    "case 目录缺 %s" % name))
        if not os.path.isdir(os.path.join(case_dir, "cwd")):
            violations.append(v("MISSING_FILE", "%s/cwd" % display_path(case_dir, root),
                                "case 目录缺 cwd/"))
        if res.get("status") == "ok" and not os.path.isfile(
                os.path.join(case_dir, "transcript.jsonl")):
            violations.append(v("MISSING_FILE", "%s/transcript.jsonl"
                                % display_path(case_dir, root), "已执行的 case 缺 transcript"))
        if "quality" in modes and res.get("config") == SUBJECT_CONFIG \
                and res.get("status") == "ok":
            check_grading(case_dir, root, res.get("case_id"), violations)
    if timings != seen:
        missing = sorted(t for t in seen - timings)
        extra = sorted(t for t in timings - seen)
        violations.append(v("SET_MISMATCH", display_path(run_dir, root),
                            "execution-summary 的 results 与实际 timing.json 目录不符"
                            "（results 有而磁盘无：%s；磁盘有而 results 无：%s）"
                            % (len(missing), len(extra))))


def check_grading(case_dir, root, case_id, violations):
    """quality 的评分账本：不给部分分（passed 是布尔）、举证责任在通过方（证据非空）。"""
    path = os.path.join(case_dir, "grading.json")
    where = display_path(path, root)
    if not os.path.isfile(path):
        violations.append(v("MISSING_FILE", where,
                            "quality 模式已执行的 case 缺 grading.json——评分账本归 grader，"
                            "引擎不代填、不默认通过"))
        return
    data, err = read_json(path)
    if err is not None:
        violations.append(v("UNPARSABLE_JSON", where, "解析失败：%s" % err))
        return
    exps = data.get("expectations")
    if not isinstance(exps, list) or not exps:
        violations.append(v("EMPTY_FIELD", "%s.expectations" % where,
                            "expectations 缺失或为空——rubric 逐条判、不给部分分"))
        return
    for i, exp in enumerate(exps):
        spot = "%s.expectations[%d]" % (where, i)
        if not isinstance(exp, dict):
            violations.append(v("EMPTY_FIELD", spot, "条目不是对象"))
            continue
        if not str(exp.get("text", "")).strip():
            violations.append(v("EMPTY_FIELD", "%s.text" % spot, "expectation 缺 text"))
        if not isinstance(exp.get("passed"), bool):
            violations.append(v("ENUM_INVALID", "%s.passed" % spot,
                                "passed 必须是布尔——不给部分分"))
        if not str(exp.get("evidence", "")).strip():
            violations.append(v("EMPTY_FIELD", "%s.evidence" % spot,
                                "evidence 为空——举证责任在通过方，无证据不得判过"))
    summary = data.get("summary") if isinstance(data.get("summary"), dict) else {}
    passed = sum(1 for e in exps if isinstance(e, dict) and e.get("passed") is True)
    if summary.get("passed") != passed or summary.get("total") != len(exps) \
            or summary.get("failed") != len(exps) - passed:
        violations.append(v("SET_MISMATCH", "%s.summary" % where,
                            "summary 与 expectations 不符（应 passed=%d / failed=%d / total=%d）"
                            % (passed, len(exps) - passed, len(exps))))
    fb = data.get("rubric_feedback")
    if not isinstance(fb, dict):
        violations.append(v("EMPTY_FIELD", "%s.rubric_feedback" % where,
                            "grader 必须反向批评 rubric（weak / uncovered / overall 三键在场，"
                            "哪怕是空数组）"))
    else:
        for key in ("weak", "uncovered", "overall"):
            if key not in fb:
                violations.append(v("EMPTY_FIELD", "%s.rubric_feedback.%s" % (where, key),
                                    "缺 rubric 反馈键 %s" % key))


def check_trigger(run_dir, root, modes, violations):
    path = os.path.join(run_dir, "triggers-result.json")
    where = display_path(path, root)
    if not os.path.isfile(path):
        violations.append(v("MISSING_FILE", where, "trigger 模式的 run 缺 triggers-result.json"))
        return 0
    data, err = read_json(path)
    if err is not None:
        violations.append(v("UNPARSABLE_JSON", where, "解析失败：%s" % err))
        return 0
    if data.get("status") in ("skipped", "adapter-missing"):
        if not str(data.get("reason", "")).strip():
            violations.append(v("EMPTY_FIELD", "%s.reason" % where,
                                "降级跳过的 trigger run 必须写明 reason（不静默）"))
        return 0
    if data.get("detection") != "tool_use":
        violations.append(v("ENUM_INVALID", "%s.detection" % where,
                            "触发判定必须是 tool_use——整篇 transcript 子串匹配会让触发率恒为 "
                            "100%，本技能禁止"))
    results = data.get("results")
    if not isinstance(results, list) or not results:
        violations.append(v("EMPTY_FIELD", "%s.results" % where, "results 缺失或为空"))
        return 0
    threshold = data.get("threshold", DEFAULT_THRESHOLD)
    passed = 0
    for i, item in enumerate(results):
        spot = "%s.results[%d]" % (where, i)
        if not isinstance(item, dict):
            violations.append(v("EMPTY_FIELD", spot, "条目不是对象"))
            continue
        runs, triggers = item.get("runs"), item.get("triggers")
        if not isinstance(runs, int) or runs < 1 or not isinstance(triggers, int):
            violations.append(v("EMPTY_FIELD", spot, "runs / triggers 缺失或非整数"))
            continue
        rate = round(triggers / runs, 3)
        if abs(float(item.get("trigger_rate", -1)) - rate) > 1e-9:
            violations.append(v("SET_MISMATCH", "%s.trigger_rate" % spot,
                                "触发率与 triggers/runs 不符（应 %s）" % rate))
        should = bool(item.get("should_trigger", True))
        want = (rate >= threshold) if should else (rate < threshold)
        if bool(item.get("pass")) != want:
            violations.append(v("SET_MISMATCH", "%s.pass" % spot,
                                "pass 与阈值判定不符（threshold=%s / should_trigger=%s）"
                                % (threshold, should)))
        if item.get("pass"):
            passed += 1
        for run_idx in range(1, runs + 1):
            stage = os.path.join(run_dir, QUERIES_DIR, "q%03d-r%d" % (i, run_idx))
            if not os.path.isdir(stage):
                violations.append(v("MISSING_FILE", display_path(stage, root),
                                    "缺问句运行目录"))
                continue
            if not os.path.isdir(os.path.join(stage, ".home")):
                violations.append(v("MISSING_FILE", "%s/.home" % display_path(stage, root),
                                    "问句运行目录缺清场 HOME"))
            name = str(item.get("synthetic", ""))
            if not name or not os.path.isdir(os.path.join(stage, DEFAULT_SKILL_DIR, name)):
                violations.append(v("MISSING_FILE", "%s/%s/%s" % (display_path(stage, root),
                                    DEFAULT_SKILL_DIR, name or "<synthetic>"),
                                    "问句运行目录缺合成技能（唯一名后缀）"))
    summary = data.get("summary") if isinstance(data.get("summary"), dict) else {}
    if summary.get("total") != len(results) or summary.get("passed") != passed \
            or summary.get("failed") != len(results) - passed:
        violations.append(v("SET_MISMATCH", "%s.summary" % where,
                            "summary 与 results 不符（应 passed=%d / failed=%d / total=%d）"
                            % (passed, len(results) - passed, len(results))))
    return len(results)


def cmd_check(args):
    violations, warnings = [], []
    root = os.path.abspath(args.project_root)
    run_dir = resolve_path_arg(args.run_dir, root, "--run-dir", violations)
    out = resolve_path_arg(args.output_dir, root, "--output-dir", violations)
    if violations:
        return emit(receipt("check", False, args.project_root, "", violations, warnings, {}),
                    args.json)
    if not out:
        parent = os.path.dirname(norm(run_dir))
        out = os.path.dirname(parent) if os.path.basename(parent) == EVAL_RUNS_SUBDIR else ""
    if not os.path.isdir(run_dir):
        violations.append(v("MISSING_FILE", display_path(run_dir, root), "run 目录不存在"))
        return emit(receipt("check", False, args.project_root, norm(out) if out else "",
                            violations, warnings, {}), args.json)

    run_json = check_run_json(run_dir, root, violations)
    modes = (run_json or {}).get("mode") or []
    modes = modes if isinstance(modes, list) else [modes]

    summary, err = read_json(os.path.join(run_dir, "execution-summary.json"))
    if err is not None:
        violations.append(v("MISSING_FILE" if not os.path.isfile(
            os.path.join(run_dir, "execution-summary.json")) else "UNPARSABLE_JSON",
            "execution-summary.json",
            "缺 execution-summary.json（run 未完成）或不可解析：%s" % err))
        summary = None
    results = []
    if isinstance(summary, dict):
        results = summary.get("results") if isinstance(summary.get("results"), list) else []
        if summary.get("total") != len(results):
            violations.append(v("SET_MISMATCH", "execution-summary.json total",
                                "total=%s 与 results 条数 %d 不符"
                                % (summary.get("total"), len(results))))
        for key, want in (("executed", sum(1 for x in results if x.get("status") == "ok")),
                          ("skipped", sum(1 for x in results if x.get("status") == "skipped")),
                          ("failures", sum(1 for x in results
                                           if x.get("status") in FAILURE_STATUS))):
            if summary.get(key) != want:
                violations.append(v("SET_MISMATCH", "execution-summary.json %s" % key,
                                    "%s=%s 与 results 实际 %d 不符" % (key, summary.get(key), want)))
        check_case_dirs(run_dir, root, results, modes, violations)

    memlog = os.path.join(run_dir, MEMLOG_NAME)
    if not os.path.isfile(memlog):
        violations.append(v("MISSING_FILE", display_path(memlog, root),
                            "run 根缺 .memlog.md（决策与轮次 trail）"))
    else:
        try:
            meta, _body = memlog_split(io.open(memlog, encoding="utf-8").read())
            if not str(meta.get("updated", "")).strip():
                violations.append(v("EMPTY_FIELD", "%s.updated" % display_path(memlog, root),
                                    "memlog frontmatter 缺 updated"))
        except (OSError, ValueError) as e:
            violations.append(v("EMPTY_FIELD", display_path(memlog, root),
                                "memlog 不可解析：%s" % e))

    trigger_queries = check_trigger(run_dir, root, modes, violations) if "trigger" in modes else 0
    runs_root = os.path.dirname(norm(run_dir))
    run_dirs = 0
    if os.path.isdir(runs_root):
        run_dirs = len([d for d in os.listdir(runs_root)
                        if os.path.isdir(os.path.join(runs_root, d))])
    counts = {"results": len(results), "case_dirs": len(results),
              "executed": sum(1 for x in results if x.get("status") == "ok"),
              "skipped": sum(1 for x in results if x.get("status") == "skipped"),
              "failures": sum(1 for x in results if x.get("status") in FAILURE_STATUS),
              "trigger_queries": trigger_queries, "run_dirs": run_dirs}
    payload = receipt("check", not violations, args.project_root, norm(out) if out else "",
                      violations, warnings, counts, run_dir=norm(run_dir),
                      modes=modes, runs_root=runs_root)
    lines = ["终门 check：%s" % norm(run_dir),
             "结果 %d / run 目录累计 %d（run 目录永不删除、覆盖、轮转；清理归用户决定）"
             % (len(results), run_dirs)]
    return emit(payload, args.json, lines)


# --------------------------------------------------------------- mlog 子命令

def cmd_mlog(args):
    """memlog：原子追加、只追加。

    每次操作**恒发一行 JSON ack**（与 W1 的 mlog 同构）：共同键 + 命令级附加键
    `{file, n, appended}`（另带 `action`），人读态与 `--json` 开关都不改这条形状——
    调用方永远不必回读文件就知道新状态。
    """
    violations, warnings = [], []
    root = os.path.abspath(args.project_root)
    out = resolve_path_arg(args.output_dir, root, "--output-dir", violations)
    directory = resolve_path_arg(args.dir, root, "--dir", violations)
    name = str(args.file)
    if "/" in name or "\\" in name or name in (".", ".."):
        violations.append(v("NAME_ILLEGAL", "--file",
                            "只收文件名、不收路径（不靠 --dir 反推、也不许越出 --dir）：%r" % name))
    path = os.path.join(directory or root, name)
    payload = receipt("mlog", False, args.project_root, norm(out) if out else "",
                      violations, warnings, {"n": 0},
                      file=display_path(path, root), action=args.action)

    def finish(ok, n=0, appended=False, as_json=True):
        """成功的 ack = 共同键 + `{file, n, appended}`（恒发一行 JSON，与人读态无关）；
        被拒路径只回共同键 + `file` / `action`，并照 §2.2 的 `--json` 开关——与 W1 同形。"""
        payload["ok"] = bool(ok)
        payload["counts"] = {"n": n}
        if ok:
            payload["n"] = n
            payload["appended"] = bool(appended)
        return emit(payload, as_json,
                    ["mlog %s：%s（条目 %d）" % (args.action, "OK" if ok else "被拒绝", n)])

    if violations:
        return finish(False, as_json=args.json)
    try:
        if args.action == "init":
            memlog_init(path, args.subject)
            return finish(True, 0, False)
        if args.action == "set-complete":
            return finish(True, memlog_set_complete(path), False)
        if args.type not in ENTRY_TYPES:
            violations.append(v("ENUM_INVALID", "mlog --type",
                                "类型越界：%r（合法集 %s）" % (args.type, "|".join(ENTRY_TYPES))))
            return finish(False, as_json=args.json)
        if not str(args.text or "").strip():
            violations.append(v("EMPTY_FIELD", "mlog --text", "条目内容为空"))
            return finish(False, as_json=args.json)
        n = memlog_append(path, args.type, args.text)
        return finish(True, n, True)
    except FileExistsError:
        violations.append(v("FILE_CONFLICT", display_path(path, root),
                            "日志已存在：续写走 append（init 只建新档，只追加、永不覆盖）"))
    except OSError as e:
        violations.append(v("MISSING_FILE", display_path(path, root),
                            "日志不存在或不可写：先跑 `mlog init --subject S`（%s）" % e))
    except ValueError as e:
        violations.append(v("UNPARSABLE_YAML", display_path(path, root),
                            "memlog 形状非法：%s" % e))
    return finish(False, as_json=args.json)


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
    m.add_argument("--dir", required=True, help="memlog 所在目录（W3 = run 根目录）")
    m.add_argument("--file", required=True, help="文件名，由调用方显式给（W3 = .memlog.md）")
    m.add_argument("action", choices=("init", "append", "set-complete"), help="操作")
    m.add_argument("--type", default=None,
                   help="append 的条目类型（合法集 %s；越界由引擎判 ENUM_INVALID、exit 1）"
                        % "|".join(ENTRY_TYPES))
    m.add_argument("--text", default=None, help="append 的条目正文（单行化）")
    m.add_argument("--subject", default=None, help="init 的主题")
    m.add_argument("--project-root", default=".", help="项目根（默认 .）")
    m.add_argument("--output-dir", required=True,
                   help="产物目录（必填——mlog 会写盘；与 W1 的 mlog 同形）")
    m.add_argument("--json", action="store_true", help="保留旗标（mlog 恒发一行 JSON ack）")
    m.set_defaults(func=cmd_mlog)

    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
