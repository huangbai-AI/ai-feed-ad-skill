#!/usr/bin/env python3
"""Plan, record, rank, and export high-engagement reference videos."""

from __future__ import annotations

import argparse
import json
import math
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus


DEFAULT_PLATFORMS = ["douyin", "xiaohongshu", "tiktok", "instagram", "youtube"]

PLATFORM_LABELS = {
    "douyin": "抖音",
    "xiaohongshu": "小红书",
    "tiktok": "TikTok",
    "instagram": "Instagram",
    "youtube": "YouTube Shorts",
    "juliang": "巨量创意",
    "meta": "Meta Ads Library",
    "google": "Google Ads Transparency Center",
}

METRIC_WEIGHTS = {
    "likes": 0.35,
    "views": 0.25,
    "comments": 0.15,
    "shares": 0.15,
    "collects": 0.10,
}

SEED_LIBRARY_PATH = Path(__file__).resolve().parents[1] / "templates" / "hot_video_seed_library.json"


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


def safe_slug(value: str, fallback: str = "video") -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-._")
    return (slug or fallback)[:96]


def project_state_path(project: Path) -> Path:
    return project / "project.json"


def candidates_path(project: Path) -> Path:
    return project / "references" / "hot_video_candidates.json"


def product_text(product: dict[str, Any], key: str, fallback: str = "") -> str:
    value = product.get(key) or product.get(
        {
            "product_name": "商品名",
            "category": "类目",
            "target_audience": "目标人群",
        }.get(key, ""),
        fallback,
    )
    if isinstance(value, list):
        return "、".join(str(item) for item in value if str(item).strip())
    return str(value or fallback).strip()


def product_list(product: dict[str, Any], *keys: str) -> list[str]:
    values: list[str] = []
    for key in keys:
        raw = product.get(key)
        if raw is None:
            continue
        if isinstance(raw, list):
            values.extend(str(item).strip() for item in raw if str(item).strip())
        else:
            values.extend(part.strip() for part in str(raw).replace("，", ",").split(",") if part.strip())
    return values


def dedupe_keep_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        normalized = value.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return result


def build_keywords(product: dict[str, Any]) -> dict[str, list[str]]:
    name = product_text(product, "product_name", "商品")
    category = product_text(product, "category", "")
    audience = product_text(product, "target_audience", "")
    pain_points = product_list(product, "pain_points", "核心痛点")
    selling_points = product_list(product, "selling_points", "卖点")
    scenes = product_list(product, "usage_scenes", "使用场景")
    competitors = product_list(product, "competitors", "竞品")

    category_terms = dedupe_keep_order([name, category, f"{name} 测评", f"{name} 推荐", f"{name} 好物"])
    pain_terms = dedupe_keep_order([*pain_points, *selling_points])
    scene_terms = dedupe_keep_order([*scenes, audience])
    competitor_terms = dedupe_keep_order(competitors)

    return {
        "category_terms": category_terms,
        "pain_terms": pain_terms,
        "scene_terms": scene_terms,
        "competitor_terms": competitor_terms,
        "combined_terms": dedupe_keep_order(
            [
                f"{name} 高赞",
                f"{name} 爆款视频",
                f"{name} 测评",
                f"{name} 使用体验",
                f"{category} 高赞",
                *[f"{name} {term}" for term in scene_terms[:3]],
                *[f"{name} {term}" for term in pain_terms[:3]],
            ]
        ),
    }


def platform_search_url(platform: str, query: str) -> str:
    encoded = quote_plus(query)
    if platform == "douyin":
        return f"https://www.douyin.com/search/{encoded}"
    if platform == "xiaohongshu":
        return f"https://www.xiaohongshu.com/search_result?keyword={encoded}"
    if platform == "tiktok":
        return f"https://www.tiktok.com/search?q={encoded}"
    if platform == "instagram":
        return f"https://www.instagram.com/explore/search/keyword/?q={encoded}"
    if platform == "youtube":
        return f"https://www.youtube.com/results?search_query={encoded}+shorts"
    if platform == "juliang":
        return "https://cc.oceanengine.com/"
    if platform == "meta":
        return f"https://www.facebook.com/ads/library/?active_status=all&ad_type=all&country=ALL&media_type=all&search_type=keyword_unordered&search_terms={encoded}"
    if platform == "google":
        return "https://adstransparency.google.com/"
    return ""


def command_plan(args: argparse.Namespace) -> None:
    project = Path(args.project).expanduser().resolve()
    state = read_json(project_state_path(project), {})
    if not state:
        raise SystemExit(f"project state not found: {project_state_path(project)}")

    product = dict(state.get("product") or {})
    if args.product_name:
        product["product_name"] = args.product_name
    if args.category:
        product["category"] = args.category

    platforms = [item.strip() for item in args.platforms.split(",") if item.strip()] if args.platforms else DEFAULT_PLATFORMS
    keywords = build_keywords(product)
    tasks = []
    for platform in platforms:
        for query in keywords["combined_terms"][: args.queries_per_platform]:
            tasks.append(
                {
                    "platform": platform,
                    "platform_label": PLATFORM_LABELS.get(platform, platform),
                    "query": query,
                    "search_url": platform_search_url(platform, query),
                    "capture_required": "点赞/收藏/分享等热度数据可能需要登录态，无法读取时人工录入。",
                }
            )

    plan = {
        "created_at": now_iso(),
        "project": str(project),
        "product": product,
        "keywords": keywords,
        "tasks": tasks,
        "rules": [
            "只记录公开可访问或用户授权的内容。",
            "无法自动读取热度时，保存链接、截图，并用 add/import-json 录入数据。",
            "排名只用于参考，不复制原视频文案、人物、音乐或品牌素材。",
        ],
    }
    output = project / "references" / "hot_video_search_plan.json"
    write_json(output, plan)

    state["hot_video_search"] = {"plan_file": str(output), "planned_at": plan["created_at"], "task_count": len(tasks)}
    state["current_step"] = "hot_video_search"
    state["status"] = "running"
    state["updated_at"] = now_iso()
    write_json(project_state_path(project), state)

    print(json.dumps({"plan_file": str(output), "task_count": len(tasks)}, ensure_ascii=False, indent=2))


def parse_count(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().lower().replace(",", "").replace(" ", "")
    if not text:
        return 0.0
    multiplier = 1.0
    replacements = [
        ("万", 10000),
        ("w", 10000),
        ("亿", 100000000),
        ("k", 1000),
        ("m", 1000000),
    ]
    for suffix, scale in replacements:
        if text.endswith(suffix):
            multiplier = float(scale)
            text = text[: -len(suffix)]
            break
    match = re.search(r"[-+]?\d+(?:\.\d+)?", text)
    if not match:
        return 0.0
    return float(match.group(0)) * multiplier


def metric_score(metrics: dict[str, Any]) -> float:
    score = 0.0
    for key, weight in METRIC_WEIGHTS.items():
        count = parse_count(metrics.get(key))
        if count <= 0:
            continue
        score += min(math.log10(count + 1) / 6.0, 1.0) * 100 * weight
    return round(score, 2)


def text_blob(candidate: dict[str, Any]) -> str:
    fields = [
        "title",
        "keyword",
        "hook",
        "main_selling_point",
        "scene",
        "cta",
        "why_reference",
        "notes",
    ]
    return " ".join(str(candidate.get(field) or "") for field in fields).lower()


def keyword_terms(product: dict[str, Any]) -> list[str]:
    keywords = build_keywords(product)
    flat: list[str] = []
    for values in keywords.values():
        flat.extend(values)
    pieces: list[str] = []
    for item in flat:
        pieces.append(item)
        pieces.extend(part for part in re.split(r"[\s,/，、]+", item) if len(part) >= 2)
    return dedupe_keep_order([piece.lower() for piece in pieces if piece.strip()])


def relevance_score(candidate: dict[str, Any], product: dict[str, Any]) -> float:
    terms = keyword_terms(product)
    if not terms:
        return 50.0
    blob = text_blob(candidate)
    matched = [term for term in terms if term and term in blob]
    score = min(len(matched) / max(len(terms[:12]), 1), 1.0) * 100
    return round(score, 2)


def completeness_score(candidate: dict[str, Any]) -> float:
    important = ["platform", "url", "title", "hook", "main_selling_point", "why_reference"]
    present = sum(1 for key in important if str(candidate.get(key) or "").strip())
    metrics = candidate.get("metrics") or {}
    metric_present = sum(1 for key in METRIC_WEIGHTS if parse_count(metrics.get(key)) > 0)
    return round((present / len(important)) * 70 + (metric_present / len(METRIC_WEIGHTS)) * 30, 2)


def normalize_candidate(raw: dict[str, Any]) -> dict[str, Any]:
    metrics = dict(raw.get("metrics") or {})
    for key in METRIC_WEIGHTS:
        if key in raw and key not in metrics:
            metrics[key] = raw.get(key)
    candidate = {
        "source_type": raw.get("source_type", "manual"),
        "seed_id": raw.get("seed_id", ""),
        "platform": raw.get("platform", ""),
        "url": raw.get("url", ""),
        "title": raw.get("title", ""),
        "creator": raw.get("creator", ""),
        "keyword": raw.get("keyword", ""),
        "local_file": raw.get("local_file", ""),
        "frame_dir": raw.get("frame_dir", ""),
        "analysis_file": raw.get("analysis_file", ""),
        "download_status": raw.get("download_status", ""),
        "download_error": raw.get("download_error", ""),
        "screenshot": raw.get("screenshot", ""),
        "metrics": metrics,
        "duration": raw.get("duration", ""),
        "published_at": raw.get("published_at", ""),
        "hook": raw.get("hook", ""),
        "main_selling_point": raw.get("main_selling_point", ""),
        "scene": raw.get("scene", ""),
        "cta": raw.get("cta", ""),
        "why_reference": raw.get("why_reference", ""),
        "notes": raw.get("notes", ""),
        "category_tags": raw.get("category_tags", []),
        "pattern_type": raw.get("pattern_type", ""),
        "seed_strength": raw.get("seed_strength", ""),
        "created_at": raw.get("created_at") or now_iso(),
    }
    return candidate


def read_candidates(project: Path) -> list[dict[str, Any]]:
    data = read_json(candidates_path(project), {"candidates": []})
    if isinstance(data, list):
        return [normalize_candidate(item) for item in data]
    return [normalize_candidate(item) for item in data.get("candidates", [])]


def write_candidates(project: Path, candidates: list[dict[str, Any]]) -> None:
    write_json(candidates_path(project), {"updated_at": now_iso(), "candidates": candidates})


def candidate_key(candidate: dict[str, Any]) -> str:
    url = str(candidate.get("url") or "").strip()
    if url:
        return f"url:{url}"
    return "title:" + "|".join(
        [
            str(candidate.get("platform") or ""),
            str(candidate.get("title") or ""),
            str(candidate.get("creator") or ""),
        ]
    )


def merge_candidates(existing: list[dict[str, Any]], incoming: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged = {candidate_key(item): item for item in existing}
    for item in incoming:
        key = candidate_key(item)
        if key in merged:
            current = merged[key]
            current.update({k: v for k, v in item.items() if v not in {"", None, {}}})
            current["metrics"] = {**(current.get("metrics") or {}), **(item.get("metrics") or {})}
        else:
            merged[key] = item
    return list(merged.values())


def command_add(args: argparse.Namespace) -> None:
    project = Path(args.project).expanduser().resolve()
    candidate = normalize_candidate(
        {
            "source_type": args.source_type,
            "platform": args.platform,
            "url": args.url,
            "title": args.title,
            "creator": args.creator,
            "keyword": args.keyword,
            "local_file": args.local_file,
            "screenshot": args.screenshot,
            "views": args.views,
            "likes": args.likes,
            "comments": args.comments,
            "shares": args.shares,
            "collects": args.collects,
            "duration": args.duration,
            "published_at": args.published_at,
            "hook": args.hook,
            "main_selling_point": args.main_selling_point,
            "scene": args.scene,
            "cta": args.cta,
            "why_reference": args.why_reference,
            "notes": args.notes,
        }
    )
    existing = read_candidates(project)
    candidates = merge_candidates(existing, [candidate])
    write_candidates(project, candidates)
    print(json.dumps({"candidates_file": str(candidates_path(project)), "candidate_count": len(candidates)}, ensure_ascii=False, indent=2))


def command_import_json(args: argparse.Namespace) -> None:
    project = Path(args.project).expanduser().resolve()
    source = Path(args.input).expanduser().resolve()
    data = read_json(source, [])
    raw_items = data.get("candidates", data) if isinstance(data, dict) else data
    if not isinstance(raw_items, list):
        raise SystemExit("input must be a JSON list or an object with candidates")
    incoming = [normalize_candidate(item) for item in raw_items]
    candidates = merge_candidates(read_candidates(project), incoming)
    write_candidates(project, candidates)
    print(json.dumps({"imported": len(incoming), "candidate_count": len(candidates), "candidates_file": str(candidates_path(project))}, ensure_ascii=False, indent=2))


def run_yt_dlp_search(query: str, count: int) -> list[dict[str, Any]]:
    yt_dlp = shutil.which("yt-dlp")
    if not yt_dlp:
        raise SystemExit("yt-dlp not found; install yt-dlp before running fetch-youtube")
    search = f"ytsearch{count}:{query}"
    proc = subprocess.run(
        [
            yt_dlp,
            "--dump-json",
            "--skip-download",
            "--no-warnings",
            "--playlist-items",
            f"1:{count}",
            search,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise SystemExit(proc.stderr.strip() or proc.stdout.strip() or f"yt-dlp failed with code {proc.returncode}")

    items: list[dict[str, Any]] = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line or not line.startswith("{"):
            continue
        try:
            items.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return items


def youtube_item_to_candidate(item: dict[str, Any], query: str, min_duration: int, max_duration: int) -> dict[str, Any] | None:
    duration = int(item.get("duration") or 0)
    if min_duration and duration and duration < min_duration:
        return None
    if max_duration and duration and duration > max_duration:
        return None

    url = item.get("webpage_url") or item.get("original_url") or ""
    title = item.get("title") or ""
    channel = item.get("channel") or item.get("uploader") or ""
    view_count = item.get("view_count")
    like_count = item.get("like_count")
    comment_count = item.get("comment_count")
    upload_date = item.get("upload_date") or ""
    published_at = ""
    if re.fullmatch(r"\d{8}", str(upload_date)):
        text = str(upload_date)
        published_at = f"{text[:4]}-{text[4:6]}-{text[6:8]}"

    why = "YouTube 公开搜索结果，已抓到播放/点赞/评论等公开指标。"
    if like_count is None:
        why = "YouTube 公开搜索结果，已抓到部分公开指标；点赞数未公开或未返回。"

    return normalize_candidate(
        {
            "source_type": "real_video",
            "platform": "YouTube",
            "url": url,
            "title": title,
            "creator": channel,
            "keyword": query,
            "metrics": {
                "views": view_count,
                "likes": like_count,
                "comments": comment_count,
                "shares": "",
                "collects": "",
            },
            "duration": duration,
            "published_at": published_at,
            "hook": title,
            "main_selling_point": "",
            "scene": "",
            "cta": "",
            "why_reference": why,
            "notes": "metadata fetched by yt-dlp; no video file downloaded",
        }
    )


def command_fetch_youtube(args: argparse.Namespace) -> None:
    project = Path(args.project).expanduser().resolve()
    state = read_json(project_state_path(project), {})
    if not state:
        raise SystemExit(f"project state not found: {project_state_path(project)}")

    query = args.query.strip()
    if not query:
        product = state.get("product") or {}
        name = product_text(product, "product_name", "product")
        category = product_text(product, "category", "")
        query = f"{name} {category} review shorts".strip()

    raw_items = run_yt_dlp_search(query, args.count)
    fetched: list[dict[str, Any]] = []
    filtered = 0
    for item in raw_items:
        candidate = youtube_item_to_candidate(item, query, args.min_duration, args.max_duration)
        if candidate is None:
            filtered += 1
            continue
        fetched.append(candidate)

    candidates = merge_candidates(read_candidates(project), fetched)
    write_candidates(project, candidates)

    raw_file = project / "references" / f"youtube_fetch_{stamp()}.json"
    write_json(
        raw_file,
        {
            "created_at": now_iso(),
            "query": query,
            "requested_count": args.count,
            "fetched_count": len(fetched),
            "filtered_count": filtered,
            "raw_count": len(raw_items),
            "items": raw_items,
        },
    )

    state["hot_video_search"] = {
        **(state.get("hot_video_search") or {}),
        "last_youtube_fetch_file": str(raw_file),
        "last_youtube_query": query,
        "last_youtube_fetched_count": len(fetched),
        "updated_at": now_iso(),
    }
    state["current_step"] = "hot_video_search"
    state["status"] = "running"
    state["updated_at"] = now_iso()
    write_json(project_state_path(project), state)

    print(
        json.dumps(
            {
                "query": query,
                "raw_file": str(raw_file),
                "fetched_count": len(fetched),
                "filtered_count": filtered,
                "candidates_file": str(candidates_path(project)),
                "top_fetched": fetched[: min(args.top, len(fetched))],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def run_json_command(command: list[str], error_label: str) -> dict[str, Any]:
    proc = subprocess.run(command, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise SystemExit(proc.stderr.strip() or proc.stdout.strip() or f"{error_label} failed with code {proc.returncode}")
    return json.loads(proc.stdout)


def media_probe(video_file: Path) -> dict[str, Any]:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        raise SystemExit("ffprobe not found; install ffmpeg before analyzing downloaded videos")
    return run_json_command(
        [
            ffprobe,
            "-v",
            "error",
            "-show_entries",
            "format=filename,duration,size:stream=index,codec_type,codec_name,width,height,r_frame_rate",
            "-of",
            "json",
            str(video_file),
        ],
        "ffprobe",
    )


def has_stream(probe: dict[str, Any], codec_type: str) -> bool:
    return any(stream.get("codec_type") == codec_type for stream in probe.get("streams") or [])


def extract_frames(video_file: Path, frame_dir: Path, frame_interval: int) -> int:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise SystemExit("ffmpeg not found; install ffmpeg before extracting frames")
    frame_dir.mkdir(parents=True, exist_ok=True)
    for old_frame in frame_dir.glob("frame_*.jpg"):
        old_frame.unlink()
    interval = max(frame_interval, 1)
    proc = subprocess.run(
        [
            ffmpeg,
            "-y",
            "-i",
            str(video_file),
            "-vf",
            f"fps=1/{interval},scale=360:-1",
            str(frame_dir / "frame_%03d.jpg"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise SystemExit(proc.stderr.strip() or proc.stdout.strip() or f"ffmpeg failed with code {proc.returncode}")
    return len(list(frame_dir.glob("frame_*.jpg")))


def selected_download_targets(project: Path, args: argparse.Namespace) -> list[dict[str, Any]]:
    if args.url:
        return [
            normalize_candidate(
                {
                    "source_type": args.source_type,
                    "platform": args.platform,
                    "url": args.url,
                    "title": args.title or args.url,
                }
            )
        ]

    ranking_file = Path(args.ranking).expanduser().resolve() if args.ranking else project / "analysis" / "hot_video_ranking.json"
    ranking = read_json(ranking_file, {})
    ranked = ranking.get("ranked") or []
    if not ranked:
        ranked = ranked_candidates(project).get("ranked") or []
    targets = [item for item in ranked if item.get("url") and item.get("source_type") != "built_in_seed"]
    return targets[: args.top]


def update_downloaded_candidate(project: Path, downloaded: dict[str, Any]) -> None:
    url = downloaded.get("url")
    candidates = read_candidates(project)
    updated = False
    for candidate in candidates:
        if url and candidate.get("url") == url:
            candidate["local_file"] = downloaded.get("local_file", "")
            candidate["frame_dir"] = downloaded.get("frame_dir", "")
            candidate["analysis_file"] = downloaded.get("analysis_file", "")
            candidate["download_status"] = downloaded.get("download_status", "")
            candidate["download_error"] = downloaded.get("download_error", "")
            candidate["notes"] = downloaded.get("notes", candidate.get("notes", ""))
            updated = True
    if not updated:
        candidates.append(normalize_candidate(downloaded))
    write_candidates(project, candidates)


def command_download(args: argparse.Namespace) -> None:
    project = Path(args.project).expanduser().resolve()
    yt_dlp = shutil.which("yt-dlp")
    if not yt_dlp:
        raise SystemExit("yt-dlp not found; install yt-dlp before downloading videos")

    targets = selected_download_targets(project, args)
    if not targets:
        raise SystemExit("no downloadable target found; provide --url or run rank with real video candidates first")

    videos_dir = project / "videos"
    videos_dir.mkdir(parents=True, exist_ok=True)
    downloaded_items: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []

    for index, target in enumerate(targets, start=1):
        url = str(target.get("url") or "").strip()
        if not url:
            continue
        title = str(target.get("title") or url)
        stem = safe_slug(args.output_name or title or f"video-{index}", f"video-{index}")
        output_template = str(videos_dir / f"{stem}.%(ext)s")
        command = [
            yt_dlp,
            "-f",
            args.format,
            "--merge-output-format",
            "mp4",
            "-o",
            output_template,
            url,
        ]
        proc = subprocess.run(command, capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            error = proc.stderr.strip() or proc.stdout.strip() or f"yt-dlp failed with code {proc.returncode}"
            failed = normalize_candidate({**target, "download_status": "failed", "download_error": error})
            update_downloaded_candidate(project, failed)
            errors.append({"url": url, "title": title, "error": error})
            if not args.keep_going:
                break
            continue

        files = sorted(videos_dir.glob(f"{stem}.*"), key=lambda path: path.stat().st_mtime, reverse=True)
        video_file = next((path for path in files if path.suffix.lower() in {".mp4", ".mov", ".webm", ".mkv", ".m4v"}), None)
        if video_file is None:
            error = "download command finished but output video file was not found"
            failed = normalize_candidate({**target, "download_status": "failed", "download_error": error})
            update_downloaded_candidate(project, failed)
            errors.append({"url": url, "title": title, "error": error})
            if not args.keep_going:
                break
            continue

        probe = media_probe(video_file)
        frame_dir = project / "frames" / video_file.stem
        frame_count = extract_frames(video_file, frame_dir, args.frame_interval) if has_stream(probe, "video") else 0
        audio_present = has_stream(probe, "audio")
        analysis_file = project / "analysis" / f"hot_video_media_{video_file.stem}.json"
        analysis = {
            "created_at": now_iso(),
            "source": {
                "platform": target.get("platform"),
                "source_type": target.get("source_type"),
                "url": url,
                "title": title,
            },
            "local_file": str(video_file),
            "probe": probe,
            "frame_dir": str(frame_dir) if frame_count else "",
            "frame_count": frame_count,
            "audio_present": audio_present,
            "analysis_scope": "visual_and_audio" if audio_present else "visual_only",
            "notes": [
                "下载成功后才允许做视频级拆解。",
                "本命令只抽帧和检查音轨；没有音轨时不能做口播转写。",
                "参考内容只学习结构、节奏和镜头语言，不复制素材。",
            ],
        }
        write_json(analysis_file, analysis)

        downloaded = normalize_candidate(
            {
                **target,
                "local_file": str(video_file),
                "frame_dir": str(frame_dir) if frame_count else "",
                "analysis_file": str(analysis_file),
                "download_status": "downloaded",
                "download_error": "",
                "notes": "downloaded and probed; visual frames extracted" if frame_count else "downloaded and probed; no frames extracted",
            }
        )
        update_downloaded_candidate(project, downloaded)
        downloaded_items.append(downloaded)

    state = read_json(project_state_path(project), {})
    if state:
        state["hot_video_search"] = {
            **(state.get("hot_video_search") or {}),
            "last_downloaded_count": len(downloaded_items),
            "last_download_errors": errors,
            "updated_at": now_iso(),
        }
        state["current_step"] = "reference_analysis" if downloaded_items else "hot_video_search"
        state["status"] = "running" if downloaded_items else state.get("status", "running")
        state["updated_at"] = now_iso()
        write_json(project_state_path(project), state)

    print(
        json.dumps(
            {
                "downloaded_count": len(downloaded_items),
                "errors": errors,
                "downloaded": downloaded_items,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def ranked_candidates(project: Path) -> dict[str, Any]:
    state = read_json(project_state_path(project), {})
    product = state.get("product") or {}
    ranked = []
    for candidate in read_candidates(project):
        heat = metric_score(candidate.get("metrics") or {})
        if candidate.get("source_type") == "built_in_seed" and heat <= 0:
            heat = min(parse_count(candidate.get("seed_strength")), 55.0)
        relevance = relevance_score(candidate, product)
        completeness = completeness_score(candidate)
        total = round(heat * 0.55 + relevance * 0.35 + completeness * 0.10, 2)
        item = dict(candidate)
        item["scores"] = {
            "heat": heat,
            "relevance": relevance,
            "completeness": completeness,
            "total": total,
        }
        item["metric_missing"] = [key for key in METRIC_WEIGHTS if parse_count((candidate.get("metrics") or {}).get(key)) <= 0]
        ranked.append(item)
    ranked.sort(key=lambda item: item["scores"]["total"], reverse=True)
    return {
        "created_at": now_iso(),
        "project": str(project),
        "score_rule": {
            "total": "heat * 0.55 + relevance * 0.35 + completeness * 0.10",
            "heat_metrics": METRIC_WEIGHTS,
            "built_in_seed_note": "内置种子没有真实热度数据；heat 使用 seed_strength 兜底，且最高限制为 55，真实平台数据应优先。",
        },
        "ranked": ranked,
    }


def command_rank(args: argparse.Namespace) -> None:
    project = Path(args.project).expanduser().resolve()
    result = ranked_candidates(project)
    output = Path(args.output).expanduser().resolve() if args.output else project / "analysis" / "hot_video_ranking.json"
    write_json(output, result)
    state = read_json(project_state_path(project), {})
    if state:
        state["hot_video_search"] = {
            **(state.get("hot_video_search") or {}),
            "ranking_file": str(output),
            "ranked_at": result["created_at"],
            "candidate_count": len(result["ranked"]),
        }
        state["current_step"] = "hot_video_search"
        state["updated_at"] = now_iso()
        write_json(project_state_path(project), state)
    print(json.dumps({"ranking_file": str(output), "candidate_count": len(result["ranked"]), "top": result["ranked"][: min(args.top, len(result["ranked"]))]}, ensure_ascii=False, indent=2))


def command_export_references(args: argparse.Namespace) -> None:
    project = Path(args.project).expanduser().resolve()
    ranking_file = Path(args.ranking).expanduser().resolve() if args.ranking else project / "analysis" / "hot_video_ranking.json"
    ranking = read_json(ranking_file, {})
    if not ranking:
        ranking = ranked_candidates(project)
        write_json(ranking_file, ranking)
    ranked = ranking.get("ranked") or []
    selected = ranked[: args.top]
    references = []
    for item in selected:
        references.append(
            {
                "platform": item.get("platform"),
                "source_type": item.get("source_type"),
                "seed_id": item.get("seed_id"),
                "url": item.get("url"),
                "local_file": item.get("local_file"),
                "screenshot": item.get("screenshot"),
                "title": item.get("title"),
                "hook": item.get("hook"),
                "main_selling_point": item.get("main_selling_point"),
                "why_reference": item.get("why_reference"),
                "pattern_type": item.get("pattern_type"),
                "hot_video_metrics": item.get("metrics"),
                "hot_video_scores": item.get("scores"),
                "created_at": now_iso(),
            }
        )
    output = project / "references" / "hot_video_references.json"
    write_json(output, {"created_at": now_iso(), "source_ranking": str(ranking_file), "references": references})

    state = read_json(project_state_path(project), {})
    if state:
        existing = state.setdefault("references", [])
        existing_keys = {candidate_key(ref) for ref in existing}
        for ref in references:
            key = candidate_key(ref)
            if key not in existing_keys:
                existing.append(ref)
                existing_keys.add(key)
        state["current_step"] = "reference_analysis"
        state["status"] = "running"
        state["updated_at"] = now_iso()
        write_json(project_state_path(project), state)

    print(json.dumps({"references_file": str(output), "exported": len(references)}, ensure_ascii=False, indent=2))


def seed_match_score(seed: dict[str, Any], product: dict[str, Any]) -> float:
    product_terms = keyword_terms(product)
    product_terms.extend(
        [
            product_text(product, "product_name", "").lower(),
            product_text(product, "category", "").lower(),
        ]
    )
    product_terms = dedupe_keep_order([term for term in product_terms if term])
    blob = " ".join(
        [
            str(seed.get("title") or ""),
            str(seed.get("hook") or ""),
            str(seed.get("main_selling_point") or ""),
            str(seed.get("scene") or ""),
            str(seed.get("why_reference") or ""),
            " ".join(str(tag) for tag in seed.get("category_tags") or []),
        ]
    ).lower()
    matched = [term for term in product_terms if term and term in blob]
    generic_bonus = 0.5 if "generic" in [str(tag).lower() for tag in seed.get("category_tags") or []] else 0.0
    product_name = product_text(product, "product_name", "").lower()
    exact_product_bonus = 2.0 if product_name and product_name in blob else 0.0
    return len(matched) + exact_product_bonus + generic_bonus


def command_seed(args: argparse.Namespace) -> None:
    project = Path(args.project).expanduser().resolve()
    state = read_json(project_state_path(project), {})
    if not state:
        raise SystemExit(f"project state not found: {project_state_path(project)}")

    library_path = Path(args.library).expanduser().resolve() if args.library else SEED_LIBRARY_PATH
    library = read_json(library_path, {})
    raw_seeds = library.get("seeds") or []
    if not raw_seeds:
        raise SystemExit(f"seed library is empty: {library_path}")

    product = state.get("product") or {}
    matching = []
    generic = []
    unmatched = []
    for raw in raw_seeds:
        seed = normalize_candidate({**raw, "source_type": "built_in_seed", "platform": raw.get("platform") or "内置种子库"})
        score = seed_match_score(seed, product)
        item = (score, parse_count(seed.get("seed_strength")), seed)
        tags = [str(tag).lower() for tag in seed.get("category_tags") or []]
        if score >= args.min_match_score and "generic" not in tags:
            matching.append(item)
        elif "generic" in tags:
            generic.append(item)
        else:
            unmatched.append(item)

    scored = matching + generic
    if args.include_unmatched:
        scored.extend(unmatched)
    scored.sort(key=lambda item: (item[0], item[1]), reverse=True)
    selected = [item[2] for item in scored[: args.count]]
    if not selected:
        raise SystemExit("no matching built-in seeds found; use --include-unmatched to import broad fallback seeds")

    candidates = merge_candidates(read_candidates(project), selected)
    write_candidates(project, candidates)

    import_file = project / "references" / "hot_video_seed_import.json"
    write_json(
        import_file,
        {
            "created_at": now_iso(),
            "library": str(library_path),
            "note": "这些是内置结构种子，不是真实抓取的高赞视频。",
            "selected": selected,
        },
    )

    state["hot_video_search"] = {
        **(state.get("hot_video_search") or {}),
        "seed_import_file": str(import_file),
        "seed_imported_at": now_iso(),
        "seed_count": len(selected),
    }
    state["current_step"] = "hot_video_search"
    state["status"] = "running"
    state["updated_at"] = now_iso()
    write_json(project_state_path(project), state)

    print(json.dumps({"seed_import_file": str(import_file), "seed_count": len(selected), "candidates_file": str(candidates_path(project))}, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Search workflow helpers for high-engagement product videos.")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("plan")
    p.add_argument("--project", required=True)
    p.add_argument("--product-name", default="")
    p.add_argument("--category", default="")
    p.add_argument("--platforms", default="")
    p.add_argument("--queries-per-platform", type=int, default=8)
    p.set_defaults(func=command_plan)

    p = sub.add_parser("add")
    p.add_argument("--project", required=True)
    p.add_argument("--source-type", default="manual")
    p.add_argument("--platform", default="")
    p.add_argument("--url", default="")
    p.add_argument("--title", default="")
    p.add_argument("--creator", default="")
    p.add_argument("--keyword", default="")
    p.add_argument("--local-file", default="")
    p.add_argument("--screenshot", default="")
    p.add_argument("--views", default="")
    p.add_argument("--likes", default="")
    p.add_argument("--comments", default="")
    p.add_argument("--shares", default="")
    p.add_argument("--collects", default="")
    p.add_argument("--duration", default="")
    p.add_argument("--published-at", default="")
    p.add_argument("--hook", default="")
    p.add_argument("--main-selling-point", default="")
    p.add_argument("--scene", default="")
    p.add_argument("--cta", default="")
    p.add_argument("--why-reference", default="")
    p.add_argument("--notes", default="")
    p.set_defaults(func=command_add)

    p = sub.add_parser("import-json")
    p.add_argument("--project", required=True)
    p.add_argument("--input", required=True)
    p.set_defaults(func=command_import_json)

    p = sub.add_parser("fetch-youtube")
    p.add_argument("--project", required=True)
    p.add_argument("--query", default="")
    p.add_argument("--count", type=int, default=8)
    p.add_argument("--min-duration", type=int, default=0)
    p.add_argument("--max-duration", type=int, default=1800)
    p.add_argument("--top", type=int, default=5)
    p.set_defaults(func=command_fetch_youtube)

    p = sub.add_parser("download")
    p.add_argument("--project", required=True)
    p.add_argument("--url", default="")
    p.add_argument("--title", default="")
    p.add_argument("--platform", default="")
    p.add_argument("--source-type", default="real_video")
    p.add_argument("--ranking", default="")
    p.add_argument("--top", type=int, default=1)
    p.add_argument("--format", default="bv*[height<=720]+ba/b[height<=720]/best[height<=720]/best")
    p.add_argument("--frame-interval", type=int, default=1)
    p.add_argument("--output-name", default="")
    p.add_argument("--keep-going", action="store_true")
    p.set_defaults(func=command_download)

    p = sub.add_parser("seed")
    p.add_argument("--project", required=True)
    p.add_argument("--count", type=int, default=6)
    p.add_argument("--library", default="")
    p.add_argument("--min-match-score", type=float, default=2.0)
    p.add_argument("--include-unmatched", action="store_true")
    p.set_defaults(func=command_seed)

    p = sub.add_parser("rank")
    p.add_argument("--project", required=True)
    p.add_argument("--output", default="")
    p.add_argument("--top", type=int, default=5)
    p.set_defaults(func=command_rank)

    p = sub.add_parser("export-references")
    p.add_argument("--project", required=True)
    p.add_argument("--ranking", default="")
    p.add_argument("--top", type=int, default=5)
    p.set_defaults(func=command_export_references)

    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
