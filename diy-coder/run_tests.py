# -*- coding: utf-8 -*-
"""全量测试入口：有 pytest-xdist 就并行，缺失时自动安装。

安装失败：交互环境提示用户裁断（重试安装 / 串行运行）；非交互环境（夜队列）
自动回退串行，绝不等待输入。串行等价于 `python -m pytest tests -q`。

用法：cd diy-coder && python run_tests.py
"""
import importlib
import importlib.util
import os
import subprocess
import sys
from importlib import metadata

HERE = os.path.dirname(os.path.abspath(__file__))
XDIST_REQ = "pytest-xdist>=3.8,<4"


def have_xdist():
    """按发行版元数据判定：残留的空 xdist 目录会让 find_spec 误报 namespace 包。"""
    try:
        metadata.distribution("pytest-xdist")
    except metadata.PackageNotFoundError:
        return False
    spec = importlib.util.find_spec("xdist")
    return spec is not None and spec.loader is not None


def install_xdist():
    print("[run_tests] 未检测到 pytest-xdist，尝试自动安装……")
    proc = subprocess.run([sys.executable, "-m", "pip", "install", XDIST_REQ])
    importlib.invalidate_caches()
    return proc.returncode == 0 and have_xdist()


def ask_retry_or_serial():
    print("[run_tests] pytest-xdist 安装失败。")
    try:
        choice = input("[run_tests] 1) 重试安装  2) 串行运行（约 9 分钟）[1/2，默认 2]: ")
    except EOFError:
        return "serial"
    return "retry" if choice.strip() == "1" else "serial"


def main():
    os.chdir(HERE)
    parallel = have_xdist() or install_xdist()
    while not parallel and sys.stdin.isatty():
        if ask_retry_or_serial() == "retry":
            parallel = install_xdist()
        else:
            break
    if not parallel and not sys.stdin.isatty():
        print("[run_tests] 非交互环境：自动安装失败，回退串行。"
              "如需并行，先执行 pip install %s" % XDIST_REQ)

    cmd = [sys.executable, "-m", "pytest", "tests", "-q"]
    if parallel:
        cmd += ["-n", "auto", "--dist", "loadfile"]
    else:
        print("[run_tests] 串行模式（未使用 pytest-xdist）。")
    return subprocess.call(cmd)


if __name__ == "__main__":
    sys.exit(main())
