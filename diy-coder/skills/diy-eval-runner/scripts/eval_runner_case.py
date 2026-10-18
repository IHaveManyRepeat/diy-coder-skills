# -*- coding: utf-8 -*-
"""diy-eval-runner case 执行链：adapter / 暂存 / transcript / run_case / trigger。"""
import io
import json
import os
import re
import shutil
import subprocess
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import v  # noqa: E402

from eval_runner_lib import (  # noqa: E402
    DEFAULT_SKILL_DIR, read_json, utc_now_iso, write_json, write_text,
)


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
