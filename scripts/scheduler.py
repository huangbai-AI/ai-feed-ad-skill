#!/usr/bin/env python3
"""Run scheduled checks for feed-ad projects."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def discover_projects(args: argparse.Namespace) -> list[Path]:
    projects: list[Path] = []
    for item in args.project:
        path = Path(item).expanduser().resolve()
        if (path / "project.json").exists():
            projects.append(path)
        else:
            raise SystemExit(f"project.json not found: {path}")

    for root in args.project_root:
        root_path = Path(root).expanduser().resolve()
        for state_file in sorted(root_path.rglob("project.json")):
            projects.append(state_file.parent)

    if not projects:
        cwd = Path.cwd().resolve()
        if (cwd / "project.json").exists():
            projects.append(cwd)
        else:
            raise SystemExit("no project found; use --project or --project-root")

    unique: list[Path] = []
    seen: set[str] = set()
    for project in projects:
        key = str(project)
        if key not in seen:
            seen.add(key)
            unique.append(project)
    return unique


def latest_quality_check(project: Path) -> Path | None:
    analysis = project / "analysis"
    candidates = sorted(analysis.glob("*quality*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0] if candidates else None


def already_processed_quality(state: dict[str, Any], quality_path: Path) -> bool:
    status = str(state.get("status") or "")
    current_step = str(state.get("current_step") or "")
    if status != "running" or current_step not in {"retry_prompt", "dreamina_generate"}:
        return False

    quality_key = str(quality_path)
    quality_mtime = quality_path.stat().st_mtime
    for item in reversed(state.get("loop_runs") or []):
        if not isinstance(item, dict):
            continue
        if item.get("quality_check") != quality_key:
            continue
        last_mtime = item.get("quality_check_mtime")
        if last_mtime is None or float(last_mtime) == quality_mtime:
            return True
    return False


def should_skip(state: dict[str, Any], include_blocked: bool) -> tuple[bool, str]:
    status = str(state.get("status") or "").lower()
    step = str(state.get("current_step") or "").lower()
    if status == "complete":
        return True, "已完成"
    if not include_blocked and status == "blocked":
        return True, "已暂停"
    if "dreamina_cli_permission" in step:
        return True, "即梦账号没有 CLI 生成权限"
    return False, ""


def run_loop_controller(project: Path, quality_path: Path, args: argparse.Namespace) -> dict[str, Any]:
    helper = Path(__file__).with_name("loop_controller.py")
    cmd = [
        sys.executable,
        str(helper),
        "--project",
        str(project),
        "--quality-check",
        str(quality_path),
        "--max-retries",
        str(args.max_retries),
    ]
    if args.submit_loop:
        cmd.append("--submit")
        cmd.extend(["--duration", str(args.duration)])
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    return {
        "action": "loop_controller",
        "command": cmd,
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


def run_project(project: Path, args: argparse.Namespace) -> dict[str, Any]:
    state_path = project / "project.json"
    state = read_json(state_path, {})
    result: dict[str, Any] = {
        "project": str(project),
        "created_at": now_iso(),
        "status": state.get("status"),
        "current_step": state.get("current_step"),
        "action": "",
        "note": "",
    }

    skip, reason = should_skip(state, args.include_blocked)
    if skip:
        result["action"] = "skip"
        result["note"] = reason
        return result

    quality_path = latest_quality_check(project)
    if quality_path:
        if already_processed_quality(state, quality_path):
            result["action"] = "waiting_for_new_result"
            result["note"] = "这份质量检查已经处理过，等待新生成结果或新的质量检查。"
            return result
        result.update(run_loop_controller(project, quality_path, args))
        return result

    result["action"] = "waiting_for_agent"
    result["note"] = "还没有质量检查表，定时任务只记录当前步骤，等 Agent 继续创作或生成。"
    return result


def save_schedule_record(project: Path, record: dict[str, Any]) -> Path:
    path = project / "schedule_runs" / f"schedule_{stamp()}.json"
    write_json(path, record)
    return path


def run_once(projects: list[Path], args: argparse.Namespace, run_index: int) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "created_at": now_iso(),
        "run_index": run_index,
        "project_count": len(projects),
        "results": [],
    }
    for project in projects:
        (project / "schedule_runs").mkdir(parents=True, exist_ok=True)
        result = run_project(project, args)
        record_path = save_schedule_record(project, result)
        result["record_file"] = str(record_path)
        summary["results"].append(result)
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Schedule AI feed-ad project checks.")
    parser.add_argument("--project", action="append", default=[])
    parser.add_argument("--project-root", action="append", default=[])
    parser.add_argument("--interval-minutes", type=float, default=15)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--max-runs", type=int, default=0)
    parser.add_argument("--max-retries", type=int, default=3)
    parser.add_argument("--include-blocked", action="store_true")
    parser.add_argument("--submit-loop", action="store_true")
    parser.add_argument("--duration", type=int, default=5)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if not args.once and args.interval_minutes <= 0:
        raise SystemExit("--interval-minutes must be greater than 0 unless --once is used")

    projects = discover_projects(args)
    run_index = 0
    while True:
        run_index += 1
        summary = run_once(projects, args, run_index)
        print(json.dumps(summary, ensure_ascii=False, indent=2))

        if args.once:
            break
        if args.max_runs and run_index >= args.max_runs:
            break
        time.sleep(args.interval_minutes * 60)


if __name__ == "__main__":
    main()
