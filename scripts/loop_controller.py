#!/usr/bin/env python3
"""Control one feed-ad quality loop."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PASS_VALUES = {"pass", "passed", "ok", "通过"}
RETRY_VALUES = {"retry", "needs_retry", "fail", "failed", "需要重试", "重试", "不通过"}
MANUAL_VALUES = {"manual", "manual_review", "blocked", "需要人工确认", "人工确认"}
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


def latest_quality_check(project: Path) -> Path:
    analysis = project / "analysis"
    candidates = sorted(analysis.glob("*quality*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidates:
        raise SystemExit(f"quality check not found under: {analysis}")
    return candidates[0]


def normalize_overall(value: Any) -> str:
    raw = str(value or "").strip()
    lower = raw.lower()
    if raw in PASS_VALUES or lower in PASS_VALUES:
        return "pass"
    if raw in RETRY_VALUES or lower in RETRY_VALUES:
        return "retry"
    if raw in MANUAL_VALUES or lower in MANUAL_VALUES:
        return "manual_review"
    return "manual_review"


def failed_checks(checks: dict[str, Any]) -> list[dict[str, str]]:
    targets: list[dict[str, str]] = []
    for key, item in checks.items():
        if key not in MAJOR_DEFECT_CHECKS:
            continue
        if isinstance(item, dict):
            result = str(item.get("result") or item.get("overall") or "").strip().lower()
            notes = str(item.get("notes") or item.get("question") or "")
        else:
            result = str(item).strip().lower()
            notes = ""
        if result in RETRY_VALUES or "重试" in result or "不通过" in result:
            targets.append(
                {
                    "shot_id": "shot_001",
                    "problem": key,
                    "change_needed": notes or "fix this failed check",
                }
            )
    return targets


def is_major_defect_target(item: dict[str, Any]) -> bool:
    key = str(item.get("problem_key") or item.get("check") or item.get("id") or "").strip()
    if key in MAJOR_DEFECT_CHECKS:
        return True
    text = " ".join(str(item.get(name) or "") for name in ["problem", "reason", "change_needed", "fix", "notes"])
    return any(keyword in text for keyword in MAJOR_DEFECT_KEYWORDS)


def retry_targets(quality: dict[str, Any]) -> list[dict[str, str]]:
    targets = quality.get("retry_targets") or []
    normalized: list[dict[str, str]] = []
    if isinstance(targets, list):
        for item in targets:
            if isinstance(item, dict):
                if not is_major_defect_target(item):
                    continue
                normalized.append(
                    {
                        "shot_id": str(item.get("shot_id") or item.get("id") or "shot_001"),
                        "problem": str(item.get("problem") or item.get("reason") or "needs retry"),
                        "change_needed": str(item.get("change_needed") or item.get("fix") or "只修正这个重大错误"),
                    }
                )
    if normalized:
        return normalized
    from_checks = failed_checks(quality.get("checks") or {})
    if from_checks:
        return from_checks
    return []


def prompt_from_state(state: dict[str, Any], shot_id: str) -> str:
    shots = state.get("shots") or []
    if not isinstance(shots, list):
        return ""
    for shot in shots:
        if not isinstance(shot, dict):
            continue
        if str(shot.get("id") or shot.get("shot_id") or "") == shot_id:
            return str(shot.get("prompt") or shot.get("dreamina_prompt") or "")
    return ""


def prompt_from_json(path: Path, shot_id: str) -> str:
    data = read_json(path, {})
    shots = data.get("shots") if isinstance(data, dict) else []
    if not isinstance(shots, list):
        return ""
    for shot in shots:
        if not isinstance(shot, dict):
            continue
        if str(shot.get("id") or shot.get("shot_id") or "") == shot_id:
            return str(shot.get("prompt") or shot.get("dreamina_prompt") or "")
    return ""


def original_prompt(project: Path, state: dict[str, Any], shot_id: str) -> str:
    prompt = prompt_from_state(state, shot_id)
    if prompt:
        return prompt

    candidates = [
        project / "shots" / f"{shot_id}_prompt.txt",
        project / "shots" / f"{shot_id}.txt",
        project / "shots" / f"{shot_id}.md",
    ]
    for path in candidates:
        if path.exists():
            return path.read_text(encoding="utf-8").strip()

    json_candidates = [
        project / "shots" / "shot_plan.json",
        project / "analysis" / "shot_plan.json",
        project / "scripts" / "shot_plan.json",
    ]
    for path in json_candidates:
        if path.exists():
            prompt = prompt_from_json(path, shot_id)
            if prompt:
                return prompt
    return ""


def compose_retry_prompt(project: Path, state: dict[str, Any], target: dict[str, str], attempt: int) -> str:
    shot_id = target["shot_id"]
    source_prompt = original_prompt(project, state, shot_id)
    product = state.get("product") or {}
    product_name = product.get("product_name") or product.get("name") or ""
    selling_points = product.get("selling_points") or product.get("卖点") or []
    if isinstance(selling_points, list):
        selling_points_text = "、".join(str(item) for item in selling_points)
    else:
        selling_points_text = str(selling_points)

    lines = [
        "信息流广告单镜头重试提示词",
        f"重试轮次：{attempt}",
        f"镜头：{shot_id}",
        f"商品：{product_name}",
        f"核心卖点：{selling_points_text}",
        "",
        "原提示词：",
        source_prompt or "未找到原提示词，请保持商品、场景和脚本方向，只修正下方失败点。",
        "",
        "这次必须修正：",
        f"- 问题：{target['problem']}",
        f"- 改动：{target['change_needed']}",
        "",
        "硬性要求：",
        "- 只修正上面的失败点，不重写广告创意。",
        "- 保持原商品颜色、形状、包装、材质和关键部件。",
        "- 保持原人物身份、服装、发型、场景和脚本方向。",
        "- 商品不要消失、遮挡、变形，也不要新增无关道具。",
        "- 人物不要断手断脚、多手多指、脸崩或身体结构异常。",
        "- 字幕必须清晰可读，不要乱码、严重模糊、闪烁或穿模。",
        "",
        "负面要求：不要编造价格、销量、认证、医疗功效；不要因为钩子、CTA 或广告感改动原方向。",
    ]
    return "\n".join(lines).strip() + "\n"


def retry_count(state: dict[str, Any]) -> int:
    count = 0
    for item in state.get("loop_runs") or []:
        if isinstance(item, dict) and item.get("result") in {"retry", "retry_submitted"}:
            count += 1
    return count


def already_processed_quality(state: dict[str, Any], quality_path: Path) -> dict[str, Any] | None:
    quality_key = str(quality_path)
    quality_mtime = quality_path.stat().st_mtime
    for item in reversed(state.get("loop_runs") or []):
        if not isinstance(item, dict):
            continue
        if item.get("quality_check") != quality_key:
            continue
        last_mtime = item.get("quality_check_mtime")
        if last_mtime is None or float(last_mtime) == quality_mtime:
            return item
    return None


def refresh_result_report(project: Path) -> str:
    helper = Path(__file__).with_name("result_report.py")
    if not helper.exists():
        return ""
    proc = subprocess.run(
        [sys.executable, str(helper), "--project", str(project)],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return ""
    return proc.stdout.strip()


def submit_prompt(project: Path, prompt_file: Path, args: argparse.Namespace) -> dict[str, Any]:
    helper = Path(__file__).with_name("dreamina_generate.py")
    cmd = [
        sys.executable,
        str(helper),
        "text2video",
        "--prompt-file",
        str(prompt_file),
        "--project",
        str(project),
        "--duration",
        str(args.duration),
        "--model-version",
        args.model_version,
        "--poll",
        str(args.poll),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    combined = proc.stdout + proc.stderr
    return {
        "command": cmd,
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "dreamina_cli_blocked": "current account is not maestro vip" in combined
        or "没有 dreamina_cli 使用权限" in combined,
    }


def save_loop_record(project: Path, state: dict[str, Any], record: dict[str, Any]) -> Path:
    path = project / "loop_runs" / f"loop_{stamp()}.json"
    write_json(path, record)
    compact = {
        "created_at": record["created_at"],
        "quality_check": record.get("quality_check"),
        "quality_check_mtime": record.get("quality_check_mtime"),
        "result": record.get("result"),
        "major_defects": record.get("major_defects", []),
        "retry_files": record.get("retry_files", []),
        "record_file": str(path),
    }
    state.setdefault("loop_runs", []).append(compact)
    state["updated_at"] = now_iso()
    write_json(project_state_path(project), state)
    return path


def run_loop(args: argparse.Namespace) -> None:
    project = Path(args.project).expanduser().resolve()
    for name in ["shots", "analysis", "dreamina_tasks", "loop_runs", "outputs"]:
        (project / name).mkdir(parents=True, exist_ok=True)

    state = read_json(project_state_path(project), {})
    if not state:
        raise SystemExit(f"project state not found: {project_state_path(project)}")

    quality_path = Path(args.quality_check).expanduser().resolve() if args.quality_check else latest_quality_check(project)
    quality = read_json(quality_path, {})
    overall = normalize_overall(quality.get("overall"))
    processed = already_processed_quality(state, quality_path)
    record: dict[str, Any] = {
        "created_at": now_iso(),
        "project": str(project),
        "quality_check": str(quality_path),
        "quality_check_mtime": quality_path.stat().st_mtime,
        "overall": quality.get("overall"),
        "result": overall,
        "retry_files": [],
        "submissions": [],
        "major_defects": [],
        "next_action": "",
    }
    if processed and not args.force:
        record["result"] = "waiting_for_new_result"
        record["previous_result"] = processed.get("result")
        record["next_action"] = "这份重大错误质检已经处理过，等待新生成结果或新的质检文件；如需重跑请加 --force。"
        print(json.dumps(record, ensure_ascii=False, indent=2))
        return

    if overall == "pass":
        state["status"] = "complete"
        state["current_step"] = "output_ready"
        record["next_action"] = "广告样片通过，进入交付或批量扩展。"
        path = save_loop_record(project, state, record)
        record["record_file"] = str(path)
        record["result_report"] = refresh_result_report(project)
        print(json.dumps(record, ensure_ascii=False, indent=2))
        return

    if overall == "manual_review":
        state["status"] = "blocked"
        state["current_step"] = "manual_review"
        record["next_action"] = "需要人工确认后再继续。"
        path = save_loop_record(project, state, record)
        record["record_file"] = str(path)
        record["result_report"] = refresh_result_report(project)
        print(json.dumps(record, ensure_ascii=False, indent=2))
        return

    used_retries = retry_count(state)
    if used_retries >= args.max_retries:
        state["status"] = "blocked"
        state["current_step"] = "loop_retry_limit"
        record["result"] = "blocked"
        record["next_action"] = f"已达到最大重试次数 {args.max_retries}，停止自动重试。"
        path = save_loop_record(project, state, record)
        record["record_file"] = str(path)
        record["result_report"] = refresh_result_report(project)
        print(json.dumps(record, ensure_ascii=False, indent=2))
        return

    attempt = used_retries + 1
    targets = retry_targets(quality)
    record["major_defects"] = targets
    if not targets:
        state["status"] = "blocked"
        state["current_step"] = "manual_review"
        record["result"] = "no_major_defect_retry_skipped"
        record["next_action"] = "质检要求重试，但没有重大错误目标；已停止自动重试，需人工修正质检或直接交付。"
        path = save_loop_record(project, state, record)
        record["record_file"] = str(path)
        record["result_report"] = refresh_result_report(project)
        print(json.dumps(record, ensure_ascii=False, indent=2))
        return

    for target in targets:
        shot_id = target["shot_id"]
        prompt_text = compose_retry_prompt(project, state, target, attempt)
        prompt_file = project / "shots" / f"retry_{attempt:02d}_{shot_id}.txt"
        prompt_file.write_text(prompt_text, encoding="utf-8")
        record["retry_files"].append(str(prompt_file))
        if args.submit:
            submission = submit_prompt(project, prompt_file, args)
            submission["prompt_file"] = str(prompt_file)
            record["submissions"].append(submission)
            if submission["dreamina_cli_blocked"]:
                state["status"] = "blocked"
                state["current_step"] = "dreamina_cli_permission"
                record["result"] = "blocked"
                record["next_action"] = "当前即梦账号没有 CLI 生成权限，已暂停定时和自动重试。"
                path = save_loop_record(project, state, record)
                record["record_file"] = str(path)
                print(json.dumps(record, ensure_ascii=False, indent=2))
                return

    state["status"] = "running"
    state["current_step"] = "dreamina_generate" if args.submit else "retry_prompt"
    record["result"] = "retry_submitted" if args.submit else "retry"
    record["next_action"] = "已按重大错误生成重试提示词。" if not args.submit else "已按重大错误提交重试生成，等待查询结果。"
    path = save_loop_record(project, state, record)
    record["record_file"] = str(path)
    record["result_report"] = refresh_result_report(project)
    print(json.dumps(record, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run one AI feed-ad quality loop.")
    parser.add_argument("--project", required=True)
    parser.add_argument("--quality-check", default="")
    parser.add_argument("--max-retries", type=int, default=3)
    parser.add_argument("--submit", action="store_true")
    parser.add_argument("--duration", type=int, default=5)
    parser.add_argument("--model-version", default="seedance2.0fast")
    parser.add_argument("--poll", type=int, default=0)
    parser.add_argument("--force", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    run_loop(args)


if __name__ == "__main__":
    main()
