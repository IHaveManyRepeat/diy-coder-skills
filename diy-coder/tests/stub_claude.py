# trace: S-10 AC-10.1 TC-10.1.1（测试基础设施：无头 claude 任务桩，非交付逻辑）
"""无头 claude CLI 任务桩。行为路由由环境变量驱动：

DIY_STUB_ROUTING  "S-1:done,S-2:fail,S-3:blocked"（未注册任务默认 fail）
含 "diy-augment" 的调用视为补测会话：log 记 "<story> augment" 后按 DIY_STUB_AUGMENT
（pass 默认 / fail / skip / none=不留痕）写 augment 字段退出 0；任务状态零写回
DIY_STUB_AUGMENT  补测会话结论（模拟 diy-augment 窄写权留痕）
DIY_STUB_LOG      每次调用追加一行 "<story> <action>"（调用计数）
DIY_STUB_SPRINT   桩要写回的 sprint.yaml 路径
DIY_STUB_SENTINEL 若 stdin 读到非空内容则写入该文件（无头断言）
DIY_STUB_SLEEP    done 两段写回之间的停留秒数（并发扫描窗口）
"""
import os
import re
import sys
import time
from datetime import date
from pathlib import Path

import yaml


def atomic_write(path: Path, data: str) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(data, encoding="utf-8")
    os.replace(tmp, path)


def write_status(sprint_path: str, story: str, status: str) -> None:
    path = Path(sprint_path)
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    doc["project"]["updated"] = date.today().isoformat()
    for task in doc["tasks"]:
        if task["story"] == story:
            task["status"] = status
    atomic_write(path, yaml.safe_dump(doc, allow_unicode=True, sort_keys=False))


def write_augment(sprint_path: str, story: str, value: str) -> None:
    # 补测会话留痕：只写本任务 augment 字段（status 不碰——模拟 diy-augment 窄写权）
    path = Path(sprint_path)
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    doc["project"]["updated"] = date.today().isoformat()
    for task in doc["tasks"]:
        if task["story"] == story:
            task["augment"] = value
    atomic_write(path, yaml.safe_dump(doc, allow_unicode=True, sort_keys=False))


def main() -> int:
    stdin_data = sys.stdin.read()
    sentinel = os.environ.get("DIY_STUB_SENTINEL")
    if stdin_data and sentinel:
        Path(sentinel).write_text(stdin_data, encoding="utf-8")

    joined = " ".join(sys.argv)
    match = re.search(r"S-\d+", joined)
    if not match:
        return 2
    story = match.group(0)
    routing = dict(
        item.split(":", 1)
        for item in os.environ.get("DIY_STUB_ROUTING", "").split(",")
        if ":" in item
    )
    # diy-augment 补测会话：只记日志、零写回（补测不参与任务状态机）
    action = "augment" if "diy-augment" in joined else routing.get(story, "fail")

    log = os.environ.get("DIY_STUB_LOG")
    if log:
        with open(log, "a", encoding="utf-8") as fh:
            fh.write(f"{story} {action}\n")

    if action == "augment":
        aug = os.environ.get("DIY_STUB_AUGMENT", "pass")
        sprint = os.environ.get("DIY_STUB_SPRINT")
        if sprint and aug != "none":
            write_augment(sprint, story, aug)
        return 0
    if action == "fail":
        return 1
    sprint = os.environ.get("DIY_STUB_SPRINT")
    if not sprint:
        return 3
    if action == "blocked":
        write_status(sprint, story, "blocked")
        return 0
    write_status(sprint, story, "in-progress")
    sleep_for = float(os.environ.get("DIY_STUB_SLEEP", "0"))
    if sleep_for:
        time.sleep(sleep_for)
    write_status(sprint, story, "done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
