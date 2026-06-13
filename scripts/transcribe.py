#!/usr/bin/env python3
"""Extract audio from a local ad video and transcribe it with whisper CLI."""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Transcribe a local feed-ad video.")
    parser.add_argument("video", help="Local video path")
    parser.add_argument("--project", default="", help="Project directory; transcript goes under transcripts/ when set")
    parser.add_argument("--output-dir", default="", help="Explicit output directory")
    parser.add_argument("--language", default="zh", help="Whisper language, default zh")
    parser.add_argument("--model", default="tiny", help="Whisper model, default tiny")
    args = parser.parse_args()

    video = Path(args.video).expanduser().resolve()
    if not video.exists():
        raise SystemExit(f"video not found: {video}")
    if not shutil.which("ffmpeg"):
        raise SystemExit("ffmpeg not found")
    if not shutil.which("whisper"):
        raise SystemExit("whisper CLI not found")

    if args.output_dir:
        out_dir = Path(args.output_dir).expanduser().resolve()
    elif args.project:
        out_dir = Path(args.project).expanduser().resolve() / "transcripts" / video.stem
    else:
        out_dir = video.parent / f"{video.stem}_transcript"
    out_dir.mkdir(parents=True, exist_ok=True)

    audio = out_dir / f"{video.stem}.wav"
    run([
        "ffmpeg",
        "-y",
        "-v",
        "error",
        "-i",
        str(video),
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        str(audio),
    ])
    run([
        "whisper",
        str(audio),
        "--language",
        args.language,
        "--model",
        args.model,
        "--output_dir",
        str(out_dir),
        "--output_format",
        "all",
    ])

    print(out_dir)


if __name__ == "__main__":
    main()
