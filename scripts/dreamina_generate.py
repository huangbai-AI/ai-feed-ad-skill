#!/usr/bin/env python3
"""Submit and query Dreamina generation tasks."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def read_prompt(args: argparse.Namespace) -> str:
    if args.prompt:
        return args.prompt
    if args.prompt_file:
        return Path(args.prompt_file).expanduser().read_text(encoding="utf-8").strip()
    raise SystemExit("prompt or prompt-file is required")


def ensure_dreamina() -> str:
    found = shutil.which("dreamina")
    if found:
        return found

    common_bin_dir = Path.home() / ".local" / "bin"
    candidate = common_bin_dir / "dreamina"
    if candidate.exists():
        os.environ["PATH"] = f"{common_bin_dir}:{os.environ.get('PATH', '')}"
        return str(candidate)

    helper = Path(__file__).with_name("ensure_dreamina.py")
    subprocess.run([str(helper), "--install"], check=True)
    found = shutil.which("dreamina")
    if found:
        return found
    if candidate.exists():
        os.environ["PATH"] = f"{common_bin_dir}:{os.environ.get('PATH', '')}"
        return str(candidate)
    raise SystemExit("dreamina CLI install finished but command is still unavailable")


def run_dreamina(cmd: list[str]) -> tuple[int, str, str]:
    dreamina = ensure_dreamina()
    cmd = [dreamina, *cmd[1:]]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    return proc.returncode, proc.stdout, proc.stderr


def extract_submit_id(text: str) -> str:
    match = re.search(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}", text)
    return match.group(0) if match else ""


def save_record(project: str, record: dict) -> None:
    if not project:
        return
    task_dir = Path(project).expanduser().resolve() / "dreamina_tasks"
    task_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    name = record.get("submit_id") or record.get("mode") or "query"
    safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", name)
    path = task_dir / f"{stamp}_{safe_name}.json"
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def submit_text2video(args: argparse.Namespace) -> None:
    prompt = read_prompt(args)
    cmd = [
        "dreamina",
        "text2video",
        f"--prompt={prompt}",
        f"--duration={args.duration}",
        f"--ratio={args.ratio}",
        f"--model_version={args.model_version}",
        f"--poll={args.poll}",
    ]
    code, stdout, stderr = run_dreamina(cmd)
    submit_id = extract_submit_id(stdout + stderr)
    record = {
        "mode": "text2video",
        "created_at": now_iso(),
        "submit_id": submit_id,
        "command": ["dreamina", "text2video", "--prompt=<omitted>", f"--duration={args.duration}", f"--ratio={args.ratio}", f"--model_version={args.model_version}", f"--poll={args.poll}"],
        "returncode": code,
        "stdout": stdout,
        "stderr": stderr,
    }
    save_record(args.project, record)
    print(json.dumps(record, ensure_ascii=False, indent=2))
    raise SystemExit(code)


def submit_image2video(args: argparse.Namespace) -> None:
    prompt = read_prompt(args)
    image = Path(args.image).expanduser().resolve()
    if not image.exists():
        raise SystemExit(f"image not found: {image}")
    cmd = [
        "dreamina",
        "image2video",
        f"--image={image}",
        f"--prompt={prompt}",
        f"--duration={args.duration}",
        f"--model_version={args.model_version}",
        f"--video_resolution={args.video_resolution}",
        f"--poll={args.poll}",
    ]
    code, stdout, stderr = run_dreamina(cmd)
    submit_id = extract_submit_id(stdout + stderr)
    record = {
        "mode": "image2video",
        "created_at": now_iso(),
        "submit_id": submit_id,
        "image": str(image),
        "command": ["dreamina", "image2video", f"--image={image}", "--prompt=<omitted>", f"--duration={args.duration}", f"--model_version={args.model_version}", f"--video_resolution={args.video_resolution}", f"--poll={args.poll}"],
        "returncode": code,
        "stdout": stdout,
        "stderr": stderr,
    }
    save_record(args.project, record)
    print(json.dumps(record, ensure_ascii=False, indent=2))
    raise SystemExit(code)


def submit_multimodal2video(args: argparse.Namespace) -> None:
    prompt = read_prompt(args)
    cmd = ["dreamina", "multimodal2video", f"--prompt={prompt}", f"--duration={args.duration}", f"--ratio={args.ratio}", f"--model_version={args.model_version}", f"--video_resolution={args.video_resolution}", f"--poll={args.poll}"]
    for image in args.image:
        path = Path(image).expanduser().resolve()
        if not path.exists():
            raise SystemExit(f"image not found: {path}")
        cmd.append(f"--image={path}")
    for video in args.video:
        path = Path(video).expanduser().resolve()
        if not path.exists():
            raise SystemExit(f"video not found: {path}")
        cmd.append(f"--video={path}")
    for audio in args.audio:
        path = Path(audio).expanduser().resolve()
        if not path.exists():
            raise SystemExit(f"audio not found: {path}")
        cmd.append(f"--audio={path}")
    code, stdout, stderr = run_dreamina(cmd)
    submit_id = extract_submit_id(stdout + stderr)
    record = {
        "mode": "multimodal2video",
        "created_at": now_iso(),
        "submit_id": submit_id,
        "returncode": code,
        "stdout": stdout,
        "stderr": stderr,
    }
    save_record(args.project, record)
    print(json.dumps(record, ensure_ascii=False, indent=2))
    raise SystemExit(code)


def query(args: argparse.Namespace) -> None:
    cmd = ["dreamina", "query_result", f"--submit_id={args.submit_id}"]
    code, stdout, stderr = run_dreamina(cmd)
    record = {
        "mode": "query",
        "created_at": now_iso(),
        "submit_id": args.submit_id,
        "returncode": code,
        "stdout": stdout,
        "stderr": stderr,
    }
    save_record(args.project, record)
    print(json.dumps(record, ensure_ascii=False, indent=2))
    raise SystemExit(code)


def add_common_submit_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--prompt", default="")
    parser.add_argument("--prompt-file", default="")
    parser.add_argument("--project", default="")
    parser.add_argument("--duration", type=int, default=5)
    parser.add_argument("--model-version", default="seedance2.0fast")
    parser.add_argument("--video-resolution", default="720p")
    parser.add_argument("--poll", type=int, default=0)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Dreamina wrapper for AI feed-ad skill.")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("text2video")
    add_common_submit_args(p)
    p.add_argument("--ratio", default="9:16")
    p.set_defaults(func=submit_text2video)

    p = sub.add_parser("image2video")
    add_common_submit_args(p)
    p.add_argument("--image", required=True)
    p.set_defaults(func=submit_image2video)

    p = sub.add_parser("multimodal2video")
    add_common_submit_args(p)
    p.add_argument("--ratio", default="9:16")
    p.add_argument("--image", action="append", default=[])
    p.add_argument("--video", action="append", default=[])
    p.add_argument("--audio", action="append", default=[])
    p.set_defaults(func=submit_multimodal2video)

    p = sub.add_parser("query")
    p.add_argument("--submit-id", required=True)
    p.add_argument("--project", default="")
    p.set_defaults(func=query)

    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
