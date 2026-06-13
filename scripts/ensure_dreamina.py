#!/usr/bin/env python3
"""Ensure the official Dreamina CLI is available."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys


INSTALL_URL = "https://jimeng.jianying.com/cli"
COMMON_BIN_DIR = os.path.expanduser("~/.local/bin")


def find_dreamina() -> str:
    found = shutil.which("dreamina")
    if found:
        return found

    candidate = os.path.join(COMMON_BIN_DIR, "dreamina")
    if os.path.exists(candidate) and os.access(candidate, os.X_OK):
        return candidate

    return ""


def install_dreamina() -> None:
    if not shutil.which("curl"):
        raise SystemExit("未找到 curl，无法自动安装 dreamina")

    # Do not pipe network content directly into a shell. Fetch first, then run bash.
    cmd = f"set -euo pipefail; tmp=$(mktemp); curl -fsSL {INSTALL_URL} -o \"$tmp\"; bash \"$tmp\"; rm -f \"$tmp\""
    subprocess.run(["bash", "-lc", cmd], check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Check and install Dreamina CLI when missing.")
    parser.add_argument("--install", action="store_true", help="Install Dreamina CLI if missing")
    parser.add_argument("--json", action="store_true", help="Print JSON result")
    args = parser.parse_args()

    path = find_dreamina()
    installed = False
    if not path and args.install:
        install_dreamina()
        installed = True
        path = find_dreamina()

    if not path:
        msg = "dreamina CLI 未安装。可运行：curl -fsSL https://jimeng.jianying.com/cli | bash"
        if args.json:
            print('{"ok": false, "installed": false, "path": "", "message": "%s"}' % msg)
        raise SystemExit(1)

    if COMMON_BIN_DIR not in os.environ.get("PATH", ""):
        os.environ["PATH"] = f"{COMMON_BIN_DIR}:{os.environ.get('PATH', '')}"

    if args.json:
        print('{"ok": true, "installed": %s, "path": "%s"}' % (str(installed).lower(), path))
    else:
        print(path)


if __name__ == "__main__":
    main()
