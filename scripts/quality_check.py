#!/usr/bin/env python3
"""Create a major-defect checklist for generated ad videos."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


DEFAULT_CHECKS = {
    "human_body_defect": "是否有断手断脚、多手多指、脸崩、身体结构异常",
    "product_mismatch": "商品颜色、形状、包装、材质是否与商品资料不一致",
    "human_inconsistent": "人物是否前后不一致",
    "product_lost_or_deformed": "商品是否消失、被严重遮挡、变形",
    "visual_text_defect": "是否有字幕乱码、画面严重模糊、闪烁、穿模",
    "fabricated_claim": "是否编造价格、销量、认证、医疗功效",
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Write a major-defect checklist.")
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
        "review_mode": "major_defect_only",
        "checks": {key: {"question": value, "result": "", "notes": ""} for key, value in DEFAULT_CHECKS.items()},
        "problems": [],
        "retry_targets": [],
    }
    output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
