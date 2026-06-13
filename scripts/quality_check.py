#!/usr/bin/env python3
"""Create a lightweight feed-ad quality checklist file."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


DEFAULT_CHECKS = {
    "hook_first_3s": "前 3 秒是否直接给出痛点、结果或反差",
    "product_visibility": "商品是否清楚出现，外观是否一致",
    "single_clear_selling_point": "是否只讲一个清晰主卖点",
    "feed_ad_feeling": "是否像真实信息流广告，而不是品牌宣传片",
    "subtitle_readability": "字幕是否短、清楚、适合手机刷到",
    "visual_consistency": "人物、商品、场景是否前后一致",
    "cta": "是否有明确行动引导",
    "policy_risk": "是否存在夸大功效、医疗化、绝对化等风险",
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Write a feed-ad quality checklist.")
    parser.add_argument("--project", required=True)
    parser.add_argument("--output", default="")
    parser.add_argument("--video", default="")
    args = parser.parse_args()

    project = Path(args.project).expanduser().resolve()
    output = Path(args.output).expanduser().resolve() if args.output else project / "analysis" / "quality_check.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "video": args.video,
        "overall": "manual_review",
        "checks": {key: {"question": value, "result": "", "notes": ""} for key, value in DEFAULT_CHECKS.items()},
        "problems": [],
        "retry_targets": [],
    }
    output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
