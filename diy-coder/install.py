#!/usr/bin/env python3
"""diy-coder 安装脚本（D-8，Python 单文件三平台通用）。

用法:
    python install.py                # 安装到本仓库（开发期同步，替代 sync.sh）
    python install.py <目标项目根>    # 安装到其他项目

做三件事: 拷贝 skills 目录 → 初始化 diy-coder.yaml（仅首次）→ 环境冒烟检查。
"""
import os
import shutil
import subprocess
import sys

# trace: D-8 NFR-4 安装入口：拷贝即用 + 冒烟校验（Python 单文件，三平台零方言）


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    src = os.path.dirname(os.path.abspath(__file__))
    arg = sys.argv[1].strip() if len(sys.argv) > 1 and sys.argv[1].strip() else None
    dst_root = os.path.abspath(arg) if arg else os.path.dirname(src)

    skill_dst = os.path.join(dst_root, ".claude", "skills")
    os.makedirs(skill_dst, exist_ok=True)
    count = 0
    for name in sorted(os.listdir(os.path.join(src, "skills"))):
        if not name.startswith("diy-"):
            continue
        dst = os.path.join(skill_dst, name)
        if os.path.isdir(dst):
            shutil.rmtree(dst)
        shutil.copytree(os.path.join(src, "skills", name), dst,
                        ignore=shutil.ignore_patterns("__pycache__"))
        count += 1

    # A-9（决策 1）：仓库根的 runner / exp-sync 分发进 diy-tools/scripts/——
    # 引用处按此安装形态路径写，均由人手动执行
    tools_scripts = os.path.join(skill_dst, "diy-tools", "scripts")
    for tool in ("runner.py", "exp-sync.py"):
        shutil.copyfile(os.path.join(src, tool), os.path.join(tools_scripts, tool))

    # diy-coder.yaml 是项目级配置（experience_repo 等各项目不同）：仅首次安装创建，之后不覆盖
    cfg = os.path.join(dst_root, "diy-coder.yaml")
    if not os.path.isfile(cfg):
        shutil.copyfile(os.path.join(src, "diy-coder.yaml"), cfg)
        cfg_note = "已创建"
    else:
        cfg_note = "已存在，未覆盖"

    ok = smoke(src)
    print(f"[diy-coder] 已安装 {count} 个 skill -> {skill_dst}")
    print(f"[diy-coder] diy-coder.yaml {cfg_note}")
    print(f"[diy-coder] 冒烟{'通过' if ok else '未全过（按上面提示修环境即可，skills 已就位）'}")
    return 0 if ok else 1


def smoke(src: str) -> bool:
    # trace: D-8 R-2 安装冒烟：python 版本 / PyYAML / viewer 引擎 / diyc 引擎可执行
    ok = True
    v = sys.version_info
    if v < (3, 10):
        print(f"[冒烟] python {v.major}.{v.minor} 低于 3.10，viewer/runner 需要 3.10+")
        ok = False
    else:
        print(f"[冒烟] python {v.major}.{v.minor} OK")
    try:
        import yaml
        print(f"[冒烟] PyYAML {yaml.__version__} OK")
    except ImportError:
        print("[冒烟] PyYAML 未安装：pip install pyyaml（viewer/help/runner 均用宿主 python 直跑）")
        ok = False
    viewer = os.path.join(src, "skills", "diy-viewer", "scripts", "viewer.py")
    r = subprocess.run([sys.executable, viewer, "--help"], capture_output=True)
    if r.returncode == 0:
        print("[冒烟] viewer.py 可执行 OK")
    else:
        print("[冒烟] viewer.py --help 失败（多与上面的 PyYAML 缺失相关）")
        ok = False
    diyc = os.path.join(src, "skills", "diy-tools", "scripts", "diyc.py")
    r = subprocess.run([sys.executable, diyc, "--help"], capture_output=True)
    if r.returncode == 0:
        print("[冒烟] diyc.py 可执行 OK")
    else:
        print("[冒烟] diyc.py --help 失败（多与上面的 PyYAML 缺失相关）")
        ok = False
    return ok


if __name__ == "__main__":
    sys.exit(main())
