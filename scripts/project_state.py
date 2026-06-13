#!/usr/bin/env python3
"""Create and update feed-ad project state files."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_DIRS = [
    "product",
    "references",
    "transcripts",
    "analysis",
    "scripts",
    "shots",
    "dreamina_tasks",
    "loop_runs",
    "schedule_runs",
    "outputs",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def state_path(project: Path) -> Path:
    return project / "project.json"


def init_project(args: argparse.Namespace) -> None:
    project = Path(args.project).expanduser().resolve()
    project.mkdir(parents=True, exist_ok=True)
    for name in PROJECT_DIRS:
        (project / name).mkdir(exist_ok=True)

    state = read_json(state_path(project), {})
    state.setdefault("project_name", project.name)
    state.setdefault("created_at", now_iso())
    state["updated_at"] = now_iso()
    state.setdefault("status", "draft")
    state.setdefault("current_step", "product_brief")
    state.setdefault("product", {})
    state.setdefault("references", [])
    state.setdefault("analyses", [])
    state.setdefault("scripts", [])
    state.setdefault("shots", [])
    state.setdefault("dreamina_tasks", [])
    state.setdefault("loop_runs", [])
    state.setdefault("schedule", {"enabled": False, "interval_minutes": 15})

    if args.product_name:
        state["product"]["product_name"] = args.product_name
    if args.category:
        state["product"]["category"] = args.category
    if args.platform:
        state["product"]["platform"] = args.platform

    write_json(state_path(project), state)
    print(state_path(project))


def set_step(args: argparse.Namespace) -> None:
    project = Path(args.project).expanduser().resolve()
    state = read_json(state_path(project), {})
    if not state:
        raise SystemExit(f"project state not found: {state_path(project)}")
    state["current_step"] = args.step
    state["status"] = args.status
    state["updated_at"] = now_iso()
    write_json(state_path(project), state)
    print(json.dumps({"project": str(project), "step": args.step, "status": args.status}, ensure_ascii=False))


def add_reference(args: argparse.Namespace) -> None:
    project = Path(args.project).expanduser().resolve()
    state = read_json(state_path(project), {})
    if not state:
        raise SystemExit(f"project state not found: {state_path(project)}")

    item = {
        "platform": args.platform,
        "url": args.url,
        "local_file": args.local_file,
        "screenshot": args.screenshot,
        "hook": args.hook,
        "main_selling_point": args.main_selling_point,
        "why_reference": args.why_reference,
        "created_at": now_iso(),
    }
    state.setdefault("references", []).append({k: v for k, v in item.items() if v})
    state["updated_at"] = now_iso()
    write_json(state_path(project), state)
    print(json.dumps(item, ensure_ascii=False))


def add_task(args: argparse.Namespace) -> None:
    project = Path(args.project).expanduser().resolve()
    state = read_json(state_path(project), {})
    if not state:
        raise SystemExit(f"project state not found: {state_path(project)}")

    item = {
        "submit_id": args.submit_id,
        "mode": args.mode,
        "shot_id": args.shot_id,
        "prompt_file": args.prompt_file,
        "status": args.status,
        "created_at": now_iso(),
    }
    state.setdefault("dreamina_tasks", []).append({k: v for k, v in item.items() if v})
    state["updated_at"] = now_iso()
    write_json(state_path(project), state)
    print(json.dumps(item, ensure_ascii=False))


def show(args: argparse.Namespace) -> None:
    project = Path(args.project).expanduser().resolve()
    print(json.dumps(read_json(state_path(project), {}), ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage AI feed-ad project state.")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("init")
    p.add_argument("--project", required=True)
    p.add_argument("--product-name", default="")
    p.add_argument("--category", default="")
    p.add_argument("--platform", default="")
    p.set_defaults(func=init_project)

    p = sub.add_parser("set-step")
    p.add_argument("--project", required=True)
    p.add_argument("--step", required=True)
    p.add_argument("--status", default="running")
    p.set_defaults(func=set_step)

    p = sub.add_parser("add-reference")
    p.add_argument("--project", required=True)
    p.add_argument("--platform", default="")
    p.add_argument("--url", default="")
    p.add_argument("--local-file", default="")
    p.add_argument("--screenshot", default="")
    p.add_argument("--hook", default="")
    p.add_argument("--main-selling-point", default="")
    p.add_argument("--why-reference", default="")
    p.set_defaults(func=add_reference)

    p = sub.add_parser("add-task")
    p.add_argument("--project", required=True)
    p.add_argument("--submit-id", required=True)
    p.add_argument("--mode", default="")
    p.add_argument("--shot-id", default="")
    p.add_argument("--prompt-file", default="")
    p.add_argument("--status", default="submitted")
    p.set_defaults(func=add_task)

    p = sub.add_parser("show")
    p.add_argument("--project", required=True)
    p.set_defaults(func=show)

    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
