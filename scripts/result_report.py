#!/usr/bin/env python3
"""Write a compact result report for one feed-ad project."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RETRY_VALUES = {"retry", "needs_retry", "fail", "failed", "需要重试", "重试", "不通过"}
PASS_VALUES = {"pass", "passed", "ok", "通过"}
MAJOR_DEFECT_CHECKS = {
    "human_body_defect",
    "product_mismatch",
    "human_inconsistent",
    "product_lost_or_deformed",
    "visual_text_defect",
    "fabricated_claim",
}
MAJOR_DEFECT_KEYWORDS = {
    "断手",
    "断脚",
    "多手",
    "多指",
    "脸崩",
    "身体结构",
    "颜色",
    "形状",
    "包装",
    "材质",
    "前后不一致",
    "消失",
    "遮挡",
    "变形",
    "字幕乱码",
    "乱码",
    "严重模糊",
    "闪烁",
    "穿模",
    "编造价格",
    "编造销量",
    "编造认证",
    "医疗功效",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def read_json(path: Path | None, default: Any) -> Any:
    if not path or not path.exists() or not path.is_file():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def newest(paths: list[Path]) -> Path | None:
    existing = [path for path in paths if path.exists()]
    return max(existing, key=lambda path: path.stat().st_mtime) if existing else None


def newest_glob(root: Path, pattern: str) -> Path | None:
    return newest(list(root.glob(pattern)))


def read_text(path: Path | None, limit: int = 6000) -> str:
    if not path or not path.exists():
        return ""
    text = path.read_text(encoding="utf-8").strip()
    return text[:limit]


def normalize_result(value: Any) -> str:
    raw = str(value or "").strip()
    lower = raw.lower()
    if raw in PASS_VALUES or lower in PASS_VALUES:
        return "pass"
    if raw in RETRY_VALUES or lower in RETRY_VALUES:
        return "retry"
    if raw:
        return raw
    return "manual_review"


def is_major_defect_target(item: dict[str, Any]) -> bool:
    key = str(item.get("problem_key") or item.get("check") or item.get("id") or "").strip()
    if key in MAJOR_DEFECT_CHECKS:
        return True
    text = " ".join(str(item.get(name) or "") for name in ["problem", "reason", "change_needed", "fix", "notes"])
    return any(keyword in text for keyword in MAJOR_DEFECT_KEYWORDS)


def collect_product(state: dict[str, Any]) -> dict[str, Any]:
    product = state.get("product") or {}
    return product if isinstance(product, dict) else {"raw": product}


def collect_ad_type(project: Path, state: dict[str, Any]) -> dict[str, Any]:
    candidates = [
        project / "analysis" / "production_type.json",
        project / "analysis" / "ad_type.json",
    ]
    data = read_json(newest(candidates) or Path(""), {})
    if not isinstance(data, dict):
        data = {}
    return {
        "production_type": data.get("production_type") or state.get("production_type") or "",
        "production_subtype": data.get("production_subtype") or state.get("production_subtype") or "",
        "source_id": data.get("source_id") or state.get("source_id") or "",
        "source_file": str(newest(candidates) or ""),
    }


def collect_script(project: Path) -> dict[str, Any]:
    json_path = newest([project / "scripts" / "ad_script.json", project / "analysis" / "ad_script.json"])
    if json_path:
        return {"file": str(json_path), "content": read_json(json_path, {})}
    md_path = newest([project / "scripts" / "ad_script.md", project / "scripts" / "ad_script.txt"])
    return {"file": str(md_path or ""), "text": read_text(md_path)}


def collect_prompt(project: Path) -> dict[str, str]:
    retry_prompt = newest(list((project / "shots").glob("retry_*.txt")))
    base_prompt = newest([project / "shots" / "shot_001.txt", project / "shots" / "shot_001_prompt.txt"])
    prompt_path = retry_prompt or base_prompt
    return {"file": str(prompt_path or ""), "text": read_text(prompt_path)}


def collect_tasks(project: Path, state: dict[str, Any]) -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    raw_state_tasks = state.get("dreamina_tasks") or []
    if isinstance(raw_state_tasks, list):
        for item in raw_state_tasks:
            if isinstance(item, dict):
                tasks.append(item)
    for path in sorted((project / "dreamina_tasks").glob("*.json")):
        data = read_json(path, {})
        if isinstance(data, dict):
            tasks.append({"file": str(path), **data})
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for task in tasks:
        key = str(task.get("submit_id") or task.get("task_id") or task.get("id") or task.get("file") or task)
        if key in seen:
            continue
        seen.add(key)
        unique.append(task)
    return unique


def collect_outputs(project: Path) -> list[str]:
    outputs: list[Path] = []
    for pattern in ["*.mp4", "*.mov", "*.webm"]:
        outputs.extend((project / "outputs").glob(pattern))
    return [str(path) for path in sorted(outputs)]


def collect_quality(project: Path) -> dict[str, Any]:
    quality_path = newest_glob(project / "analysis", "*quality*.json")
    quality = read_json(quality_path or Path(""), {})
    checks = quality.get("checks") if isinstance(quality, dict) else {}
    major_defects: list[dict[str, str]] = []
    if isinstance(checks, dict):
        for key, item in checks.items():
            if key not in MAJOR_DEFECT_CHECKS:
                continue
            if isinstance(item, dict):
                result = normalize_result(item.get("result"))
                notes = str(item.get("notes") or item.get("question") or "")
            else:
                result = normalize_result(item)
                notes = ""
            if result == "retry":
                major_defects.append({"check": key, "notes": notes})
    targets = quality.get("retry_targets") if isinstance(quality, dict) else []
    if isinstance(targets, list):
        for item in targets:
            if isinstance(item, dict):
                if not is_major_defect_target(item):
                    continue
                major_defects.append(
                    {
                        "check": str(item.get("problem_key") or item.get("check") or ""),
                        "problem": str(item.get("problem") or item.get("reason") or ""),
                        "change_needed": str(item.get("change_needed") or item.get("fix") or ""),
                    }
                )
    overall = normalize_result(quality.get("overall") if isinstance(quality, dict) else "")
    return {
        "file": str(quality_path or ""),
        "overall": overall,
        "major_defects": major_defects,
        "needs_retry": overall == "retry" and bool(major_defects),
        "raw": quality,
    }


def collect_loop(project: Path) -> dict[str, Any]:
    path = newest_glob(project / "loop_runs", "*.json")
    return {"file": str(path or ""), "latest": read_json(path or Path(""), {})}


def collect_batch(project: Path) -> dict[str, Any]:
    ranking_path = newest([project / "analysis" / "batch_ranking.json"])
    variants_path = newest([project / "analysis" / "batch_variants.json"])
    ranking = read_json(ranking_path or Path(""), {})
    return {
        "variants_file": str(variants_path or ""),
        "ranking_file": str(ranking_path or ""),
        "winner": ranking.get("winner") if isinstance(ranking, dict) else None,
    }


def next_action(quality: dict[str, Any], loop: dict[str, Any]) -> tuple[str, dict[str, str]]:
    latest_loop = loop.get("latest") or {}
    loop_result = str(latest_loop.get("result") or "")
    if quality.get("needs_retry"):
        retry_files = latest_loop.get("retry_files") or []
        if retry_files:
            return (
                "按报告里的重大错误重试提示词继续生成，并等待新结果。",
                {"action": "submit_retry", "file": str(retry_files[0]), "command": "python scripts/loop_controller.py --project . --max-retries 3 --submit --duration 10"},
            )
        return (
            "运行 Loop 生成重大错误重试提示词。",
            {"action": "run_loop", "command": "python scripts/loop_controller.py --project . --max-retries 3"},
        )
    if quality.get("overall") == "pass":
        return ("样片通过，可以交付或进入批量候选。", {"action": "deliver_or_batch", "command": "python scripts/batch_variants.py plan --project . --count 9"})
    if loop_result == "waiting_for_new_result":
        return ("等待新生成结果或新的重大错误质检。", {"action": "wait", "command": ""})
    return ("需要人工确认质检结果，再决定是否重试。", {"action": "manual_review", "command": ""})


def build_report(project: Path) -> dict[str, Any]:
    state = read_json(project / "project.json", {})
    quality = collect_quality(project)
    loop = collect_loop(project)
    action_text, agent_next_step = next_action(quality, loop)
    return {
        "created_at": now_iso(),
        "project": str(project),
        "product": collect_product(state),
        "ad_type": collect_ad_type(project, state),
        "script": collect_script(project),
        "prompt": collect_prompt(project),
        "tasks": collect_tasks(project, state),
        "outputs": collect_outputs(project),
        "quality": quality,
        "retry_needed": quality.get("needs_retry"),
        "loop": loop,
        "batch": collect_batch(project),
        "next_action": action_text,
        "agent_next_step": agent_next_step,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Write a compact feed-ad result report.")
    parser.add_argument("--project", required=True)
    parser.add_argument("--output", default="")
    args = parser.parse_args()

    project = Path(args.project).expanduser().resolve()
    output = Path(args.output).expanduser().resolve() if args.output else project / "analysis" / "result_report.json"
    report = build_report(project)
    write_json(output, report)
    print(output)


if __name__ == "__main__":
    main()
