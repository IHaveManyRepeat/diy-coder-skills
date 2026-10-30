#!/usr/bin/env python3
"""diy-viewer: render diy-coder YAML artifacts (single source) into human-friendly HTML.

The YAML files are the single source of truth. This script only projects them
into disposable HTML under <output_dir>/<view_dir>/.

Usage:
    python viewer.py --project-root . [yaml paths ...]
"""

import argparse
import sys
import webbrowser
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "diy-tools" / "scripts"))
from diyc_lib_base import load_yaml_text  # noqa: E402

import viewer_refs as _refs
from viewer_glossary import DOC_KEY_LABELS, DOC_LABELS, VALUE_LABELS
from viewer_labels import BADGE_CLASSES, ENUM_KEYS, KEY_LABELS
from viewer_pages import (build_assets_page, build_index, build_timeline_page,
                          collect_asset_files, collect_timeline, page,
                          render_doc_page, sort_docs)
from viewer_refs import (build_id_index, collect_dangling, compute_orphans,
                         esc, iter_ref_values)
from viewer_render import resolve_instance


def load_config(project_root: Path) -> dict:
    cfg_path = project_root / "diy-coder.yaml"
    cfg = {}
    if cfg_path.exists():
        try:
            cfg = load_yaml_text(cfg_path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as e:
            print(f"[diy-viewer] warning: cannot parse {cfg_path}: {e}", file=sys.stderr)
        else:
            # trace: 对抗审查修复——配置为手写文件，顶层/paths/viewer 段或值为非预期形状时
            # 一行警告 + 降级默认，不裸栈（同类守卫：runner.py / exp-sync.py / diy-help）
            if not isinstance(cfg, dict):
                print(f"[diy-viewer] warning: {cfg_path} 顶层不是映射，按默认配置处理",
                      file=sys.stderr)
                cfg = {}
    paths, viewer = cfg.get("paths"), cfg.get("viewer")
    if paths is not None and not isinstance(paths, dict):
        print(f"[diy-viewer] warning: {cfg_path} 的 paths 不是映射，按默认处理", file=sys.stderr)
        paths = None
    if viewer is not None and not isinstance(viewer, dict):
        print(f"[diy-viewer] warning: {cfg_path} 的 viewer 不是映射，按默认处理", file=sys.stderr)
        viewer = None
    output_dir = (paths or {}).get("output_dir", "diy-output")
    view_dir = (paths or {}).get("view_dir", ".view")
    if not isinstance(output_dir, str) or not isinstance(view_dir, str):
        print(f"[diy-viewer] warning: {cfg_path} 的 output_dir/view_dir 不是字符串，按默认处理",
              file=sys.stderr)
        if not isinstance(output_dir, str):
            output_dir = "diy-output"
        if not isinstance(view_dir, str):
            view_dir = ".view"
    return {
        "output_dir": output_dir,
        "view_dir": view_dir,
        "auto_open": bool((viewer or {}).get("auto_open", True)),
    }  # 展示语言固定中文；回复语言属 agent 侧 SKILL.md 契约，脚本不读此键


def _is_interactive() -> bool:
    # trace: 2026-09-13 裁定——自动打开仅发生在人工交互终端（stdout 连 TTY）；
    # AI/自动化环境（Claude 会话、runner 子进程、CI、沙箱）stdout 为管道，天然判非交互
    return sys.stdout.isatty()


def should_open(auto_open: bool, no_open: bool, force_open: bool,
                interactive: bool) -> bool:
    # trace: 2026-09-13 裁定——打开浏览器是给在场人看的副作用：自动化环境静默跳过，
    # 不报路径、不阻塞流程。优先级：--no-open 一票否决 > --open 显式强制 > 配置 + 交互终端
    if no_open:
        return False
    return force_open or (auto_open and interactive)


def load_docs(paths) -> tuple:
    # trace: S-11 AC-11.1 TC-11.1.1 形状守卫：语法/形状/空文档三类异常统一降级为一行报告，不崩
    docs, errors = [], []
    for p in paths:
        try:
            data = load_yaml_text(p.read_text(encoding="utf-8"))
        except (yaml.YAMLError, OSError) as e:
            errors.append(f"{p.name}: {e}")
            continue
        if data is None:
            errors.append(f"{p.name}: empty document")
            continue
        if not isinstance(data, dict):
            errors.append(f"{p.name}: 顶层不是映射（{type(data).__name__}），已跳过")
            continue
        docs.append((p.stem, data))
    return docs, errors


def nested_instance_dirs(out_dir: Path) -> list:
    # trace: 主线目录无 YAML 而其下存在含 YAML 的子目录 → 疑似实例目录（忘传 --instance）
    try:
        return sorted(
            d.name for d in out_dir.iterdir()
            if d.is_dir() and next(d.glob("*.yaml"), None) is not None
        )
    except OSError:
        return []


def select_explicit_docs(all_docs: list, files, out_dir: Path, errors: list) -> tuple:
    # trace: 显式路径优先：路径存在 → 直接按该路径渲染该文件；不存在 → 回落 basename
    # 在解析根内查找；路径存在但在解析根之外 → stderr 警告后仍渲染给定文件
    # （不得静默替换为同名文件）。显式文档覆盖同名条目，其后仍参与 ID 索引与导航。
    req: set = set()
    explicit = []
    for f in files:
        p = Path(f)
        if p.is_file():
            try:
                inside = p.resolve().is_relative_to(out_dir.resolve())
            except OSError:
                inside = False
            if not inside:
                print(f"[diy-viewer] warning: {p} 不在解析根 {out_dir} 内，按给定路径渲染",
                      file=sys.stderr)
            explicit.append(p)
        else:
            req.add(p.name)
    ex_docs, ex_errors = load_docs(explicit)
    errors.extend(ex_errors)
    for name, data in ex_docs:
        idx = next((i for i, (n, _) in enumerate(all_docs) if n == name), None)
        if idx is None:
            all_docs.append((name, data))
        else:
            all_docs[idx] = (name, data)
    # trace: 对抗审查修复——load_docs 以 p.stem 为名，过滤须按 stem 匹配，
    # 否则显式给出的非 .yaml 扩展文件（如 prd.yml）被静默丢弃（违背 B5② 契约）
    wanted = {Path(n).stem for n in req} | {p.stem for p in explicit}
    docs = [(n, d) for n, d in all_docs if n in wanted]
    known = {n for n, _ in all_docs}
    for m in sorted(m for m in req if Path(m).stem not in known):
        errors.append(f"{m}: not found under {out_dir}")
    return docs, all_docs


def main() -> int:
    # trace: S-11 AC-11.1（stderr 含中文与 em dash：Windows 管道默认 cp936 会写出 GBK，消费方按 UTF-8 解码即崩）
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    # trace: S-16 AC-16.1 AC-16.2 TC-16.1.1 TC-16.2.1 D-9（--instance 接线：实例目录解析与主线平铺兼容）
    ap = argparse.ArgumentParser(description="diy-coder YAML → HTML viewer")
    ap.add_argument("--project-root", default=".", help="project root directory")
    ap.add_argument("--open", dest="force_open", action="store_true",
                    help="force-open the browser even in non-interactive environments "
                         "(overridden by --no-open)")
    ap.add_argument("--no-open", action="store_true", help="do not open the browser")
    ap.add_argument("--instance", default=None,
                    help="instance name (FR-4.5/D-9): artifacts under <output_dir>/<name>/; "
                         "absent = mainline flat path (zero migration)")
    ap.add_argument("files", nargs="*", help="specific yaml files (default: all under output_dir)")
    args = ap.parse_args()

    root = Path(args.project_root).resolve()
    cfg = load_config(root)
    out_dir = root / cfg["output_dir"]
    out_dir = resolve_instance(out_dir, args.instance)

    if not out_dir.exists():
        print(f"[diy-viewer] output dir not found: {out_dir}. Run a diy-* workflow first.", file=sys.stderr)
        return 1
    if not out_dir.is_dir():
        print(f"[diy-viewer] output path is not a directory: {out_dir}", file=sys.stderr)
        return 1

    # trace: 主线空而其下存在实例目录 → 把「忘传 --instance」变成一行可见诊断
    if not any(out_dir.glob("*.yaml")):
        inst_dirs = nested_instance_dirs(out_dir)
        if inst_dirs:
            print(f"[diy-viewer] found instance dirs: {', '.join(inst_dirs)} — "
                  "pass --instance <name>", file=sys.stderr)

    # ID 链接索引与跨文档导航必须基于全量文档构建，即使本次只渲染子集。
    all_docs, errors = load_docs(sorted(out_dir.glob("*.yaml")))
    # `assets/<活动>/` 下的产物渲染不到（viewer 只扫
    # 顶层 *.yaml，非递归是防同名互覆的既定口径）→ 有内容就给一行诊断，让「有东西没渲染」可见。
    # 只报不改：渲染成功仍 rc=0
    assets_dir = out_dir / "assets"
    try:
        has_assets = assets_dir.is_dir() and any(p.is_file() for p in assets_dir.rglob("*"))
    except OSError:
        has_assets = False
    if has_assets:
        # 清单页落地后「未渲染」成假事实——HTML 产物不进
        # YAML 渲染管线，但已列入 assets 清单页；「点开查看」锚保留（断言同步改）
        print(f"[diy-viewer] note: {assets_dir} 下有已列入清单页的资产（HTML 产物不进 YAML "
              f"渲染管线）—— 见 assets 清单页，页面里的资产链接可直接点开查看", file=sys.stderr)
    docs = all_docs
    if args.files:
        docs, all_docs = select_explicit_docs(all_docs, args.files, out_dir, errors)
    # select 之后重排（select_explicit_docs 的显式路径 append 条目
    # 也要参与排序，故不放 sort_docs 调用后）；三消费点（index 卡片序 / others 导航序 / 渲染循环序）全走
    # all_docs 序，docs 是其子集，照排序后序重新过滤保持同序
    all_docs = sort_docs(all_docs)
    if args.files:
        keep = {n for n, _ in docs}
        docs = [(n, d) for n, d in all_docs if n in keep]

    # trace: 来源展示：output_dir 相对项目根路径（含实例名）
    try:
        source_disp = out_dir.relative_to(root).as_posix()
    except ValueError:
        source_disp = str(out_dir)

    view_dir = out_dir / cfg["view_dir"]
    view_dir.mkdir(parents=True, exist_ok=True)
    # 资产相对链接前缀 = 页面所在目录 → output_dir；
    # 默认 view_dir=`.view`（一层）即 `../`，配置成多级目录时按级数补足（否则链接打不开）
    # _OUT_DIR 同步赋值（doc_path_value 的 design 族路径存在性基准）
    # （状态定义在 viewer_refs 模块，跨件写走模块属性形态）
    view_depth = [p for p in Path(cfg["view_dir"]).parts if p not in (".", "")]
    _refs._ASSET_REL_PREFIX = "../" * len(view_depth)
    _refs._OUT_DIR = out_dir

    written = []
    build_id_index(all_docs)
    # trace: S-12 AC-12.1 TC-12.1.1 悬空引用按文档汇总（索引构建后、渲染前）
    _refs.DANGLING_BY_DOC.clear()
    for n, d in all_docs:
        found = []
        collect_dangling(d, found)
        if found:
            _refs.DANGLING_BY_DOC[n] = sorted(set(found))
    # trace: S-12 AC-12.2 TC-12.2.1 孤儿判定：AC（stories）与用例（test-plan）引用并集
    referenced: set = set()
    for n, d in all_docs:
        if n in ("stories", "test-plan"):
            referenced.update(x.strip() for x in iter_ref_values(d))
    prd_data = next((d for n, d in all_docs if n == "prd"), None)
    _refs.ORPHAN_IDS.clear()
    if isinstance(prd_data, dict):
        _refs.ORPHAN_IDS.update(compute_orphans(prd_data, referenced))
    for name, data in docs:
        others = all_docs
        f = view_dir / f"{name}.html"
        # trace: S-11 AC-11.1 TC-11.1.1 逐文件隔离：单文件渲染失败降级为错误页，不中断整批
        try:
            body = render_doc_page(name, data, others, source_disp)
        except Exception as e:  # noqa: BLE001 兜底隔离，失败详情写入错误页与索引
            errors.append(f"{name}.yaml: 渲染失败（{e.__class__.__name__}: {e}）")
            body = page(DOC_LABELS.get(name, name),
                        f'<div class="alert alert-bad">⚠ 渲染失败：{esc(e)}</div>',
                        source=source_disp)
        f.write_text(body, encoding="utf-8")
        written.append(f)
    # assets 产物清单页：assets/ 有文件才渲染（空/缺失静默）；
    # 时间轴页（Layer 1 裁定）：全部产物 revisions 皆空不渲染。两页均只增不改既有页面
    extra_cards = []
    asset_groups = collect_asset_files(out_dir / "assets")
    if asset_groups:
        (view_dir / "assets.html").write_text(
            build_assets_page(asset_groups, source_disp), encoding="utf-8")
        n_files = sum(len(v) for v in asset_groups.values())
        extra_cards.append(
            '<a class="doc-card" href="assets.html"><div class="name">资产产物清单</div>'
            f'<div class="sub">{n_files} 个文件 · {len(asset_groups)} 个活动</div></a>')
    timeline = collect_timeline(all_docs)
    if timeline:
        (view_dir / "timeline.html").write_text(
            build_timeline_page(timeline, source_disp), encoding="utf-8")
        extra_cards.append(
            '<a class="doc-card" href="timeline.html"><div class="name">决策时间轴</div>'
            f'<div class="sub">{len(timeline)} 条修订</div></a>')
    index = view_dir / "index.html"
    index.write_text(build_index(all_docs, errors, source_disp, extra_cards),
                     encoding="utf-8")
    for e in errors:
        print(f"[diy-viewer] skipped — {e}", file=sys.stderr)

    print(f"[diy-viewer] rendered {len(written)} doc(s) -> {view_dir}")
    if errors:
        print(f"[diy-viewer] {len(errors)} file(s) skipped (see stderr)", file=sys.stderr)

    # trace: 2026-09-13 裁定——自动打开仅限人工交互终端；AI/自动化环境静默跳过（不阻塞）
    if docs and should_open(cfg["auto_open"], args.no_open, args.force_open,
                            _is_interactive()):
        webbrowser.open(index.resolve().as_uri())
    return 0


if __name__ == "__main__":
    sys.exit(main())
