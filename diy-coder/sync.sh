#!/usr/bin/env bash
# diy-coder 安装/同步脚本（D-8 安装脚本的极简前身）
# 把 diy-coder/skills/ 下的技能安装到目标项目的 .claude/skills/，并把配置模板放到目标项目根。
# 用法：
#   ./sync.sh              # 安装到本仓库（开发期 dogfood）
#   ./sync.sh <目标项目根>  # 安装到其他项目
set -euo pipefail
SRC="$(cd "$(dirname "$0")" && pwd)"
DST_ROOT="${1:-"$SRC/.."}"
SKILL_DST="$DST_ROOT/.claude/skills"

mkdir -p "$SKILL_DST"
count=0
for d in "$SRC"/skills/diy-*; do
  name="$(basename "$d")"
  rm -rf "$SKILL_DST/$name"
  cp -r "$d" "$SKILL_DST/"
  count=$((count + 1))
done
cp "$SRC/diy-coder.yaml" "$DST_ROOT/diy-coder.yaml"
echo "[diy-coder] synced $count skill(s) -> $SKILL_DST (+ $DST_ROOT/diy-coder.yaml)"
