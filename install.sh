#!/usr/bin/env bash
set -euo pipefail

REPO="${AI_FEED_AD_REPO:-huangbai-AI/ai-feed-ad-skill}"
BRANCH="${AI_FEED_AD_BRANCH:-main}"
SKILL_NAME="${AI_FEED_AD_SKILL_NAME:-ai-feed-ad-skill}"
CODEX_HOME_DIR="${CODEX_HOME:-"$HOME/.codex"}"
INSTALL_DIR="$CODEX_HOME_DIR/skills/$SKILL_NAME"
TMP_DIR="$(mktemp -d)"

cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

need_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "缺少命令：$1" >&2
    exit 1
  fi
}

script_dir() {
  local source="${BASH_SOURCE[0]}"
  while [ -L "$source" ]; do
    local dir
    dir="$(cd -P "$(dirname "$source")" >/dev/null 2>&1 && pwd)"
    source="$(readlink "$source")"
    [[ "$source" != /* ]] && source="$dir/$source"
  done
  cd -P "$(dirname "$source")" >/dev/null 2>&1 && pwd
}

copy_skill() {
  local source_dir="$1"
  mkdir -p "$(dirname "$INSTALL_DIR")"

  if [ -d "$INSTALL_DIR" ]; then
    local backup_dir="$INSTALL_DIR.backup.$(date +%Y%m%d%H%M%S)"
    mv "$INSTALL_DIR" "$backup_dir"
    echo "已备份旧版本：$backup_dir"
  fi

  mkdir -p "$INSTALL_DIR"
  if command -v rsync >/dev/null 2>&1; then
    rsync -a \
      --exclude ".git/" \
      --exclude "__pycache__/" \
      --exclude "*.pyc" \
      --exclude ".DS_Store" \
      --exclude "outputs/" \
      --exclude "dreamina_tasks/" \
      --exclude "loop_runs/" \
      --exclude "schedule_runs/" \
      "$source_dir/" "$INSTALL_DIR/"
  else
    (cd "$source_dir" && tar --exclude ".git" --exclude "__pycache__" --exclude "*.pyc" --exclude ".DS_Store" -cf - .) | (cd "$INSTALL_DIR" && tar -xf -)
  fi

  chmod +x "$INSTALL_DIR"/scripts/*.py 2>/dev/null || true
}

SOURCE_DIR=""

if [ "${BASH_SOURCE[0]}" != "$0" ]; then
  SOURCE_DIR=""
else
  LOCAL_DIR="$(script_dir)"
  if [ -f "$LOCAL_DIR/SKILL.md" ] && [ -d "$LOCAL_DIR/templates" ]; then
    SOURCE_DIR="$LOCAL_DIR"
  fi
fi

if [ -z "$SOURCE_DIR" ]; then
  need_command curl
  need_command tar
  ARCHIVE="$TMP_DIR/source.tar.gz"
  EXTRACT_DIR="$TMP_DIR/source"
  mkdir -p "$EXTRACT_DIR"
  curl -fsSL "https://github.com/$REPO/archive/refs/heads/$BRANCH.tar.gz" -o "$ARCHIVE"
  tar -xzf "$ARCHIVE" -C "$EXTRACT_DIR" --strip-components 1
  SOURCE_DIR="$EXTRACT_DIR"
fi

if [ ! -f "$SOURCE_DIR/SKILL.md" ]; then
  echo "安装失败：没有找到 SKILL.md" >&2
  exit 1
fi

copy_skill "$SOURCE_DIR"

echo "安装完成：$INSTALL_DIR"
echo "重启 Codex 后即可使用：ai-feed-ad-skill"
