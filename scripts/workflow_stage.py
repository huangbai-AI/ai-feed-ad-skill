#!/usr/bin/env python3
"""Plan and mark staged feed-ad workflow runs."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STAGES = [
    "product_brief",
    "reference_search",
    "hot_video_search",
    "reference_analysis",
    "ad_script",
    "shot_prompt",
    "dreamina_generate",
    "quality_check",
    "loop_check",
    "batch_variants",
]

STAGE_LABELS = {
    "product_brief": "整理商品资料",
    "reference_search": "搜索同类参考广告",
    "hot_video_search": "搜索同类高赞视频并排序",
    "reference_analysis": "拆解参考广告",
    "ad_script": "重写原创广告脚本",
    "shot_prompt": "拆镜头和即梦提示词",
    "dreamina_generate": "调用即梦生成样片",
    "quality_check": "质量检测",
    "loop_check": "Loop 复盘和重试",
    "batch_variants": "批量生成候选并择优",
}


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


def project_state_path(project: Path) -> Path:
    return project / "project.json"


def assert_stage(stage: str) -> None:
    if stage not in STAGES:
        allowed = ", ".join(STAGES)
        raise SystemExit(f"unknown stage: {stage}; allowed: {allowed}")


def plan_stages(stop_at: str) -> list[dict[str, str]]:
    assert_stage(stop_at)
    stop_index = STAGES.index(stop_at)
    planned: list[dict[str, str]] = []
    for index, stage in enumerate(STAGES):
        if index <= stop_index:
            status = "pending"
        else:
            status = "not_planned"
        planned.append(
            {
                "stage": stage,
                "label": STAGE_LABELS[stage],
                "status": status,
            }
        )
    return planned


def command_plan(args: argparse.Namespace) -> None:
    project = Path(args.project).expanduser().resolve()
    state = read_json(project_state_path(project), {})
    if not state:
        raise SystemExit(f"project state not found: {project_state_path(project)}")

    run = {
        "created_at": now_iso(),
        "stop_at": args.stop_at,
        "stages": plan_stages(args.stop_at),
        "note": args.note,
    }
    state.setdefault("workflow_runs", []).append(run)
    state["status"] = "running"
    state["current_step"] = "product_brief"
    state["stop_at"] = args.stop_at
    state["updated_at"] = now_iso()
    write_json(project_state_path(project), state)

    path = project / "analysis" / f"workflow_plan_{stamp()}.json"
    write_json(path, run)
    print(json.dumps({"project": str(project), "plan_file": str(path), "stop_at": args.stop_at}, ensure_ascii=False, indent=2))


def command_mark(args: argparse.Namespace) -> None:
    assert_stage(args.stage)
    project = Path(args.project).expanduser().resolve()
    state = read_json(project_state_path(project), {})
    if not state:
        raise SystemExit(f"project state not found: {project_state_path(project)}")

    runs = state.setdefault("workflow_runs", [])
    if not runs:
        runs.append({"created_at": now_iso(), "stop_at": state.get("stop_at", args.stage), "stages": plan_stages(state.get("stop_at", args.stage))})

    latest = runs[-1]
    for item in latest.get("stages", []):
        if item.get("stage") == args.stage:
            item["status"] = args.status
            item["updated_at"] = now_iso()
            if args.note:
                item["note"] = args.note
            break

    state["current_step"] = args.stage
    state["status"] = "blocked" if args.status == "blocked" else "running"

    stop_at = latest.get("stop_at") or state.get("stop_at")
    if args.status == "complete" and stop_at == args.stage:
        state["status"] = "stopped_at_stage"
        latest["result"] = "stopped_at_stage"
        latest["stopped_at"] = args.stage

    state["updated_at"] = now_iso()
    write_json(project_state_path(project), state)
    print(json.dumps({"project": str(project), "stage": args.stage, "status": state["status"]}, ensure_ascii=False, indent=2))


def command_next(args: argparse.Namespace) -> None:
    project = Path(args.project).expanduser().resolve()
    state = read_json(project_state_path(project), {})
    if not state:
        raise SystemExit(f"project state not found: {project_state_path(project)}")

    stop_at = state.get("stop_at") or args.stop_at or "quality_check"
    assert_stage(stop_at)
    current = state.get("current_step") or "product_brief"
    assert_stage(current)

    if current == stop_at and state.get("status") in {"stopped_at_stage", "complete"}:
        print(json.dumps({"next_stage": "", "note": f"已停在 {stop_at}"}, ensure_ascii=False, indent=2))
        return

    current_index = STAGES.index(current)
    stop_index = STAGES.index(stop_at)
    if current_index >= stop_index:
        print(json.dumps({"next_stage": "", "note": f"下一步不超过 stop_at={stop_at}"}, ensure_ascii=False, indent=2))
        return

    next_stage = STAGES[current_index + 1]
    print(json.dumps({"next_stage": next_stage, "label": STAGE_LABELS[next_stage], "stop_at": stop_at}, ensure_ascii=False, indent=2))


def command_status(args: argparse.Namespace) -> None:
    project = Path(args.project).expanduser().resolve()
    state = read_json(project_state_path(project), {})
    if not state:
        raise SystemExit(f"project state not found: {project_state_path(project)}")

    print(
        json.dumps(
            {
                "project": str(project),
                "status": state.get("status"),
                "current_step": state.get("current_step"),
                "stop_at": state.get("stop_at"),
                "latest_workflow": (state.get("workflow_runs") or [])[-1] if state.get("workflow_runs") else None,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Plan staged AI feed-ad workflows.")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("plan")
    p.add_argument("--project", required=True)
    p.add_argument("--stop-at", default="quality_check")
    p.add_argument("--note", default="")
    p.set_defaults(func=command_plan)

    p = sub.add_parser("mark")
    p.add_argument("--project", required=True)
    p.add_argument("--stage", required=True)
    p.add_argument("--status", choices=["pending", "running", "complete", "blocked"], required=True)
    p.add_argument("--note", default="")
    p.set_defaults(func=command_mark)

    p = sub.add_parser("next")
    p.add_argument("--project", required=True)
    p.add_argument("--stop-at", default="")
    p.set_defaults(func=command_next)

    p = sub.add_parser("status")
    p.add_argument("--project", required=True)
    p.set_defaults(func=command_status)

    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
