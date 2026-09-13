#!/usr/bin/env python3
# exp-sync.py — 全局经验库同步器（一期：上行 + 表格投影）
# 组织方式：按 bug 类型分桶（bugs/<subclass>.yaml，一个中类一个文件），
# 三级分类 class(大类)→subclass(中类)→type(小类，自由扩展，登记于 taxonomy.yaml)。
# 条目真源在项目 bug-log.yaml；经验库文件是投影——push 按 origin_project 分片重写本项目条目，
# 他项目条目原样保留（跨项目合并写入，不静默删他源数据）。
# index.html 为表格投影：大类→中类分节，供人工按类筛选浏览。
# 多机注意：单人使用按「后写者以本地为准」（限本项目分片）；同桶同项目并发覆盖的三方合并留二期。
# 用法（在项目根目录运行）：
#   python diy-coder/exp-sync.py init [repo-url]   # 初始化骨架，可选绑定远端，写回配置
#   python diy-coder/exp-sync.py push [--instance <name>]   # 上行 + 重生成 index.html + 推送（实例目录）
#   python diy-coder/exp-sync.py status            # 查看位置/远端/各桶条数
import html
import os
import re
import subprocess
import sys
from collections import defaultdict

import yaml

DEFAULT_ROOT = os.path.expanduser("~/.diy-coder/experience")

# 大类→中类 固定骨架；小类(type)动态登记进 taxonomy.yaml
BASE_TAXONOMY = {
    "functional": {"label": "功能型", "subcategories": {
        "logic": {"label": "逻辑"}, "boundary": {"label": "边界"},
        "data": {"label": "数据"}, "state": {"label": "状态"},
        "integration": {"label": "集成"}}},
    "non-functional": {"label": "非功能型", "subcategories": {
        "performance": {"label": "性能"}, "UX": {"label": "用户体验"},
        "security": {"label": "安全"}, "compatibility": {"label": "兼容性"},
        "reliability": {"label": "可靠性"}}},
}

FIELDS = ("id", "date", "origin_project", "source", "class", "subclass", "type",
          "trigger", "fix", "prevention")


# trace: S-17 AC-17.2 TC-17.2.1
def resolve_repo(cfg):
    # trace: 对抗审查修复——paths 段形状守卫（标量/列表时一行报错，不裸栈；与 viewer/runner/diy-help 同源）
    paths = cfg.get("paths")
    if paths is not None and not isinstance(paths, dict):
        sys.exit("[exp-sync] diy-coder.yaml 的 paths 不是映射，无法读取 experience_repo")
    repo = (paths or {}).get("experience_repo") or DEFAULT_ROOT
    return os.path.expandvars(os.path.expanduser(str(repo)))


# trace: S-17 AC-17.1 AC-17.2 TC-17.1.1 TC-17.2.2
def read_bugs_file(path):
    """读取桶文件条目；语法损坏或顶层非映射时一行中文报错退出。"""
    if not os.path.exists(path):
        return []
    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        sys.exit(f"[exp-sync] 桶文件解析失败（{e.__class__.__name__}）：{path}——先修复或删除该桶再重试")
    if not isinstance(data, dict):
        sys.exit(f"[exp-sync] 桶文件顶层不是映射（{type(data).__name__}）：{path}——先修复或删除该桶再重试")
    bugs = data.get("bugs")
    if bugs is None:
        return []
    if not isinstance(bugs, list):
        sys.exit(f"[exp-sync] 桶文件 bugs 不是列表（{type(bugs).__name__}）：{path}——先修复或删除该桶再重试")
    return bugs


# trace: S-17 AC-17.2 TC-17.2.1
def sh(*args, cwd, check=True):
    r = subprocess.run(args, cwd=cwd, capture_output=True, text=True, encoding="utf-8")
    if check and r.returncode != 0:
        sys.exit(f"[exp-sync] 命令失败: {' '.join(args)}\n{r.stderr.strip()}")
    return r


# trace: S-17 AC-17.2 TC-17.2.1
def read_config(root):
    cfg_path = os.path.join(root, "diy-coder.yaml")
    if not os.path.exists(cfg_path):
        sys.exit("[exp-sync] 找不到 diy-coder.yaml，请在项目根目录运行")
    try:
        with open(cfg_path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        sys.exit(f"[exp-sync] diy-coder.yaml 解析失败（{e.__class__.__name__}）：{cfg_path}")
    if not isinstance(data, dict):
        sys.exit(f"[exp-sync] diy-coder.yaml 顶层不是映射（{type(data).__name__}）：{cfg_path}")
    return data, cfg_path


# trace: S-17 AC-17.2 TC-17.2.1 init 后把仓库路径写回项目配置
def write_back_repo_path(cfg_path, repo):
    with open(cfg_path, encoding="utf-8") as f:
        txt = f.read()
    if "experience_repo:" in txt:
        txt = re.sub(r'experience_repo:.*',
                     f'experience_repo: "{repo.replace(os.sep, "/")}"            # exp-sync.py init 写入（项目级配置，sync.sh 不覆盖）',
                     txt, count=1)
    with open(cfg_path, "w", encoding="utf-8") as f:
        f.write(txt)


# trace: S-17 AC-17.1 TC-17.1.1
def load_taxonomy(repo):
    path = os.path.join(repo, "taxonomy.yaml")
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            sys.exit(f"[exp-sync] taxonomy.yaml 解析失败（{e.__class__.__name__}）：{path}——先修复再重试")
        if not isinstance(data, dict):
            sys.exit(f"[exp-sync] taxonomy.yaml 顶层不是映射（{type(data).__name__}）：{path}")
        return data, path, []
    data = {"categories": BASE_TAXONOMY}
    return data, path, None


# trace: S-17 AC-17.1 TC-17.1.1 三级分类注册表落盘
def save_taxonomy(repo, path, taxo):
    with open(path, "w", encoding="utf-8") as f:
        f.write("# taxonomy.yaml — 三级分类注册表：class(大类)→subclass(中类)→types(小类)\n"
                "# 小类由 exp-sync.py push 自动登记（发现新 type 即追加，防同义词漂移）\n")
        yaml.safe_dump(taxo, f, allow_unicode=True, sort_keys=False)


# trace: S-17 AC-17.1 TC-17.1.1
def render_html(repo):
    buckets = {}
    bugs_dir = os.path.join(repo, "bugs")
    if os.path.isdir(bugs_dir):
        for fn in sorted(os.listdir(bugs_dir)):
            if not fn.endswith(".yaml"):
                continue
            for e in read_bugs_file(os.path.join(bugs_dir, fn)):
                if isinstance(e, dict):
                    buckets.setdefault(e.get("subclass", "other"), []).append(e)
    tpath = os.path.join(repo, "taxonomy.yaml")
    with open(tpath, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    taxo = data if isinstance(data, dict) else {}
    cats = taxo.get("categories") or {}
    parts = [
        "<!doctype html><html lang=zh-CN><meta charset=utf-8>",
        "<title>经验库 — 缺陷模式</title>",
        "<style>body{font-family:system-ui;margin:24px;max-width:1200px}",
        "h1{font-size:20px}h2{margin-top:28px;border-bottom:2px solid #888;padding-bottom:4px}",
        "h3{margin:16px 0 4px}table{border-collapse:collapse;width:100%;margin-bottom:20px}",
        "th,td{border:1px solid #ccc;padding:6px 10px;text-align:left;vertical-align:top;font-size:13px}",
        "th{background:#f0f0f0}td.t{font-weight:600;white-space:nowrap}",
        ".pre{color:#060}.trig{color:#600}small{color:#888}</style>",
        "<h1>经验库 — 缺陷模式（按类型组织）</h1>",
        f"<small>生成于 {__import__('datetime').date.today()}，共 {sum(len(v) for v in buckets.values())} 条 · 真源在各项目 bug-log.yaml</small>",
    ]
    for cls_key, cls in cats.items():
        rows = []
        for sub_key, sub in (cls.get("subcategories") or {}).items():
            entries = buckets.pop(sub_key, [])
            if not entries:
                continue
            cells = "".join(
                f"<tr><td class=t>{html.escape(str(e.get('id') or ''))}</td>"
                f"<td class=t>{html.escape(str(e.get('type') or ''))}</td>"
                f"<td>{html.escape(str(e.get('origin_project') or ''))}</td>"
                f"<td>{html.escape(str(e.get('date') or ''))}</td>"
                f"<td class=trig>{html.escape(str(e.get('trigger') or ''))}</td>"
                f"<td>{html.escape(str(e.get('fix') or ''))}</td>"
                f"<td class=pre>{html.escape(str(e.get('prevention') or ''))}</td></tr>"
                for e in entries)
            rows.append(f"<h3>{html.escape(str((sub or {}).get('label') or sub_key))}（{sub_key}）· {len(entries)} 条</h3>"
                        "<table><tr><th>编号</th><th>小类</th><th>项目</th><th>时间</th>"
                        "<th>触发方法</th><th>修复方案</th><th>根治机制</th></tr>" + cells + "</table>")
        if rows:
            parts.append(f"<h2>{html.escape(str(cls.get('label') or cls_key))}</h2>" + "".join(rows))
    if buckets:
        cells = "".join(e.get("subclass", "other") + " " + str(e.get("id")) for es in buckets.values() for e in es)
        parts.append(f"<h2>未归类</h2><p>{html.escape(cells)}（taxonomy.yaml 缺对应中类）</p>")
    with open(os.path.join(repo, "index.html"), "w", encoding="utf-8") as f:
        f.write("".join(parts))


# trace: S-17 AC-17.2 TC-17.2.1
def do_init(root, cfg, cfg_path):
    url = sys.argv[2] if len(sys.argv) > 2 else None
    repo = resolve_repo(cfg)
    os.makedirs(os.path.join(repo, "bugs"), exist_ok=True)
    readme = os.path.join(repo, "README.md")
    if not os.path.exists(readme):
        with open(readme, "w", encoding="utf-8") as f:
            f.write("# diy-experience — 全局经验库\n\n"
                    "按 **bug 类型** 组织（非按项目）：bugs/<subclass>.yaml 一个中类一桶；"
                    "三级分类 class→subclass→type 登记在 taxonomy.yaml（type 自动扩展）。\n"
                    "index.html 是表格投影（大类→中类分节：项目/时间/触发方法/修复方案/根治机制）。\n"
                    "上行：项目根运行 `python diy-coder/exp-sync.py push`；各机器 clone 后配置 "
                    "diy-coder.yaml 的 paths.experience_repo 指向本地 clone。\n")
    taxo_path = os.path.join(repo, "taxonomy.yaml")
    if not os.path.exists(taxo_path):
        save_taxonomy(repo, taxo_path, {"categories": BASE_TAXONOMY})
    if not os.path.isdir(os.path.join(repo, ".git")):
        sh("git", "init", cwd=repo)
    if url:
        if sh("git", "remote", "add", "origin", url, cwd=repo, check=False).returncode != 0:
            sh("git", "remote", "set-url", "origin", url, cwd=repo)
        sh("git", "add", "-A", cwd=repo)
        if sh("git", "diff", "--cached", "--quiet", cwd=repo, check=False).returncode != 0:
            sh("git", "commit", "-m", "init: experience repo skeleton", cwd=repo)
        sh("git", "push", "-u", "origin", "HEAD", cwd=repo, check=False)
    write_back_repo_path(cfg_path, repo)
    state = f"，远端: {url}" if url else "（未绑远端：gitee 建私有仓库后重跑 init <url>）"
    print(f"[exp-sync] 经验库已就绪: {repo}{state}")


# trace: S-17 AC-17.1 AC-17.2 TC-17.1.1 TC-17.2.2
def do_push(root, cfg, cfg_path, instance=None):
    repo = resolve_repo(cfg)
    if not os.path.isdir(os.path.join(repo, ".git")):
        sys.exit("[exp-sync] 经验库未初始化，先运行 exp-sync.py init")
    bugs_dir = os.path.join(repo, "bugs")
    if not os.path.isdir(bugs_dir):
        sys.exit(f"[exp-sync] 经验库结构不完整（缺 {bugs_dir}），先运行 exp-sync.py init 修复")
    # trace: 对抗审查修复——output_dir 值形状异常时一行报错（paths 段形状已由 resolve_repo 公共入口拒掉）
    output_dir_name = (cfg.get("paths") or {}).get("output_dir", "diy-output")
    if not isinstance(output_dir_name, str):
        sys.exit("[exp-sync] diy-coder.yaml 的 output_dir 不是字符串，无法定位 output_dir")
    out_dir = os.path.join(root, output_dir_name)
    if instance:
        out_dir = os.path.join(out_dir, instance)
    log_path = os.path.join(out_dir, "bug-log.yaml")
    if not os.path.exists(log_path):
        sys.exit(f"[exp-sync] 找不到 {log_path}")
    try:
        with open(log_path, encoding="utf-8") as f:
            log = yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        sys.exit(f"[exp-sync] bug-log.yaml 解析失败（{e.__class__.__name__}）：{log_path}——先修复再 push")
    if not isinstance(log, dict):
        sys.exit(f"[exp-sync] bug-log.yaml 顶层不是映射（{type(log).__name__}）：{log_path}")
    proj = (log.get("project") or {}).get("name") or (cfg.get("project") or {}).get("name") or "default"
    bugs = []
    for b in log.get("bugs") or []:
        e = {k: b.get(k) for k in FIELDS if b.get(k) is not None}
        e.setdefault("origin_project", proj)
        if "id" in e:
            bugs.append(e)
    # 按中类分桶；写桶时按 origin_project 分片：本项目条目整段重写（幂等、支持项目内删除），
    # 他项目条目原样保留（跨项目合并写入，防止整文件重写冲掉他源数据）
    buckets = defaultdict(list)
    for e in bugs:
        buckets.setdefault(e.get("subclass") or "other", []).append(e)
    new_types = []
    for sub, entries in sorted(buckets.items()):
        target = os.path.join(bugs_dir, f"{sub}.yaml")
        kept = [e for e in read_bugs_file(target)
                if not isinstance(e, dict) or e.get("origin_project") != proj]
        with open(target, "w", encoding="utf-8") as f:
            f.write(f"# bugs/{sub}.yaml — 中类「{sub}」缺陷模式桶（跨项目，按 type 小类细分）\n"
                    f"# 投影文件：真源在各项目 bug-log.yaml；push 按 origin_project 分片重写本项目条目\n")
            yaml.safe_dump({"bugs": kept + entries}, f, allow_unicode=True, sort_keys=False)
        new_types += [e["type"] for e in entries if e.get("type")]
    # taxonomy 自动扩展：登记未收录的小类
    taxo, taxo_path, _ = load_taxonomy(repo)
    registered = 0
    for cat in (taxo.get("categories") or {}).values():
        for sub in (cat.get("subcategories") or {}).values():
            sub.setdefault("types", [])
    for sub, entries in buckets.items():
        for cat in (taxo.get("categories") or {}).values():
            sc = (cat.get("subcategories") or {}).get(sub)
            if sc is None:
                continue
            for t in {e.get("type") for e in entries if e.get("type")}:
                if t not in sc["types"]:
                    sc["types"].append(t)
                    registered += 1
    if registered:
        save_taxonomy(repo, taxo_path, taxo)
    render_html(repo)
    has_remote = bool(sh("git", "remote", cwd=repo).stdout.strip())
    if has_remote:
        sh("git", "pull", "--rebase", "--autostash", cwd=repo, check=False)
    sh("git", "add", "-A", cwd=repo)
    if sh("git", "diff", "--cached", "--quiet", cwd=repo, check=False).returncode != 0:
        sh("git", "commit", "-m", f"exp: {proj} patterns -> {len(bugs)} entries, {registered} new types", cwd=repo)
        if has_remote:
            sh("git", "push", cwd=repo)
            print(f"[exp-sync] 已推送 {len(bugs)} 条（{len(buckets)} 桶，新登记 {registered} 个小类）→ 远端")
        else:
            print(f"[exp-sync] 已本地提交 {len(bugs)} 条（{len(buckets)} 桶，新登记 {registered} 个小类；未绑远端）")
    else:
        print("[exp-sync] 无变化，已是最新")


# trace: S-17 AC-17.2 TC-17.2.2
def do_status(root, cfg, cfg_path):
    repo = resolve_repo(cfg)
    print(f"[exp-sync] 经验库路径: {repo}")
    if not os.path.isdir(os.path.join(repo, ".git")):
        print("[exp-sync] 状态: 未初始化（运行 exp-sync.py init）")
        return
    remotes = sh("git", "remote", cwd=repo).stdout.split()
    print(f"[exp-sync] 状态: 已初始化，远端: {remotes[0] if remotes else '未绑定'}")
    bugs_dir = os.path.join(repo, "bugs")
    if not os.path.isdir(bugs_dir):
        print(f"[exp-sync] 桶目录缺失（{bugs_dir}），先运行 exp-sync.py init 修复")
        return
    total = 0
    for fn in sorted(os.listdir(bugs_dir)):
        if not fn.endswith(".yaml"):
            continue
        n = len(read_bugs_file(os.path.join(bugs_dir, fn)))
        total += n
        print(f"  - {fn}: {n} 条")
    print(f"  共 {total} 条 · 表格投影: {os.path.join(repo, 'index.html')}")


# 实例名白名单（与 viewer/runner/diy-help 同源）：字母数字开头和结尾，中间可含 . _ -。
# 末字符禁点：Windows 目录名尾点被静默折叠（b. ≡ b）；fullmatch 避免 $ 放行尾换行
INSTANCE_RE = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9_-])?")


# trace: 2026-09-13 质量分析 F-customization-1（实例模式推送提示失效）
def read_instance(args):
    """提取 `--instance <name>`（FR-4.5/D-9 惯例）；未给出返回 None，非法即拒。"""
    name = None
    if "--instance" in args:
        i = args.index("--instance")
        if i + 1 >= len(args):
            sys.exit("[exp-sync] --instance 缺名称")
        name = args[i + 1]
    if name is not None and not INSTANCE_RE.fullmatch(name):
        sys.exit(f"[exp-sync] 实例名非法（字母数字开头和结尾，中间可含 . _ -）: {name}")
    return name


# trace: S-17 AC-17.1 AC-17.2 TC-17.1.1 TC-17.2.1 TC-17.2.2
def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    instance = read_instance(sys.argv[2:])
    if instance and cmd != "push":
        sys.exit(f"[exp-sync] --instance 仅 push 支持（当前子命令: {cmd}）")
    root = os.getcwd()
    cfg, cfg_path = read_config(root)
    if cmd == "init":
        do_init(root, cfg, cfg_path)
    elif cmd == "push":
        do_push(root, cfg, cfg_path, instance)
    elif cmd == "status":
        do_status(root, cfg, cfg_path)
    else:
        sys.exit(f"[exp-sync] 未知子命令: {cmd}（可用: init / push / status）")


if __name__ == "__main__":
    main()
