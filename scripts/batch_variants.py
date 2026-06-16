#!/usr/bin/env python3
"""Plan and rank batch feed-ad variants."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


HOOK_PATTERNS = [
    ("pain", "痛点反差", "先说用户正在遇到的麻烦，再立刻展示解决后效果"),
    ("result", "结果前置", "第一秒直接展示理想结果，再解释商品怎么做到"),
    ("scenario", "场景共鸣", "从高频使用场景切入，让用户觉得和自己有关"),
    ("test", "测评挑战", "用一个小测试证明商品的主卖点"),
    ("offer", "优惠刺激", "把价格、优惠或限时权益放到结尾强化转化"),
]

PRODUCTION_SUBTYPES = [
    ("drama_emotional_turn", "剧情广告", "情感反转剧情", "LD-01", "情绪低点、商品触发变化、新状态定格"),
    ("brand_product_hero", "品牌大片", "产品英雄广告", "LV-05", "产品极近特写、感官卖点、正面定格"),
    ("brand_tv_spot", "品牌大片", "电影感 TV 广告", "LV-06", "强氛围世界观、角色体验、产品定格"),
    ("brand_lifestyle_follow", "品牌大片", "时尚生活方式跟拍", "LV-08", "真人跟拍、商品细节、生活方式定格"),
    ("creator_handheld_ugc", "达人带货", "UGC 手持口播展示", "LV-01", "真人自拍、指出细节、推荐理由"),
    ("creator_unboxing_reveal", "达人带货", "开箱揭晓", "LV-02", "包装开场、取出商品、同框定格"),
    ("creator_use_case_proof", "达人带货", "使用场景证明", "LV-03", "痛点场景、使用动作、结果证明"),
    ("creator_tryon_change", "达人带货", "试穿前后变化", "LV-04", "未上身、上身变化、细节判断"),
    ("creator_asmr_unbox", "达人带货", "俯拍 ASMR 开箱", "LV-07", "俯拍开盒、取出细节、仪式感定格"),
]

SOURCE_IDS = {item[3] for item in PRODUCTION_SUBTYPES}

PERSONA_PATTERNS = [
    ("real_talk", "真人口播", "真人自然口播，语气像朋友推荐"),
    ("unbox", "开箱测评", "开箱、拿起、使用、展示结果"),
    ("first_person", "第一视角", "只露手和商品，突出真实使用动作"),
]

CTA_PATTERNS = [
    ("learn_more", "点击了解", "结尾提示点击了解更多"),
    ("claim_offer", "领取优惠", "结尾提示领取当前优惠"),
    ("try_now", "现在试试", "结尾提示马上试试或下单"),
]

SCORE_WEIGHTS = {
    "hook": 0.25,
    "product_visibility": 0.25,
    "selling_point": 0.20,
    "feed_ad_feeling": 0.20,
    "cta": 0.10,
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


def product_name(product: dict[str, Any]) -> str:
    return str(product.get("product_name") or product.get("name") or product.get("商品名") or "商品")


def selling_points(product: dict[str, Any]) -> list[str]:
    raw = product.get("selling_points") or product.get("卖点") or []
    if isinstance(raw, list):
        points = [str(item).strip() for item in raw if str(item).strip()]
    elif raw:
        points = [part.strip() for part in str(raw).replace("，", ",").split(",") if part.strip()]
    else:
        points = []
    return points or ["核心卖点清楚", "使用方便", "适合日常场景"]


def target_audience(product: dict[str, Any]) -> str:
    raw = product.get("target_audience") or product.get("目标人群") or ""
    if isinstance(raw, list):
        return "、".join(str(item) for item in raw)
    return str(raw or "目标用户")


def build_variant_prompt(product: dict[str, Any], variant: dict[str, Any]) -> str:
    name = product_name(product)
    audience = target_audience(product)
    return (
        f"竖屏 9:16 AI 带货广告，商品是{name}。\n"
        f"目标人群：{audience}。\n"
        f"生产类型：{variant['production_type']} / {variant['production_subtype']}。\n"
        f"子类型结构：{variant['subtype_rule']}。\n"
        f"主卖点角度：{variant['selling_point']}。\n"
        f"开场钩子：{variant['hook']}。\n"
        f"人物表达：{variant['persona']}。\n"
        f"行动引导：{variant['cta']}。\n"
        "画面要求：第一秒必须出现商品、结果、冲突或主视觉；商品清楚出现；只讲一个主卖点；字幕短；结尾有明确点击、收藏、领券或下单动作。\n"
        "负面要求：不要夸大功效，不要医疗化表达，不要改变商品外观，不要复制真实影视剧角色、台词、音乐或服化道。\n"
    )


def command_plan(args: argparse.Namespace) -> None:
    project = Path(args.project).expanduser().resolve()
    state = read_json(project_state_path(project), {})
    if not state:
        raise SystemExit(f"project state not found: {project_state_path(project)}")

    product = state.get("product") or {}
    points = selling_points(product)

    variants: list[dict[str, Any]] = []
    variant_dir = project / "shots" / "variants"
    variant_dir.mkdir(parents=True, exist_ok=True)

    for index in range(1, args.count + 1):
        subtype = PRODUCTION_SUBTYPES[(index - 1) % len(PRODUCTION_SUBTYPES)]
        point = points[(index - 1) % len(points)]
        hook = HOOK_PATTERNS[(index - 1) % len(HOOK_PATTERNS)]
        persona = PERSONA_PATTERNS[(index - 1) % len(PERSONA_PATTERNS)]
        cta = CTA_PATTERNS[(index - 1) % len(CTA_PATTERNS)]
        variant_id = f"v{index:03d}"
        variant = {
            "variant_id": variant_id,
            "production_type": subtype[1],
            "production_subtype": subtype[2],
            "subtype_type": subtype[0],
            "source_id": subtype[3],
            "source_id_valid": True,
            "subtype_rule": subtype[4],
            "selling_point": point,
            "hook_type": hook[0],
            "hook": f"{hook[1]}：{hook[2]}",
            "persona_type": persona[0],
            "persona": f"{persona[1]}：{persona[2]}",
            "cta_type": cta[0],
            "cta": f"{cta[1]}：{cta[2]}",
            "main_change": "只改开场、表达方式和行动引导，保持商品事实一致。",
            "shots_to_regenerate": ["shot_001"],
            "expected_use": "用于批量测试开场钩子和转化话术",
            "prompt_file": "",
            "scores": {
                "hook": None,
                "product_visibility": None,
                "selling_point": None,
                "feed_ad_feeling": None,
                "cta": None,
                "policy_risk": None,
            },
        }
        prompt_path = variant_dir / f"{variant_id}_prompt.txt"
        prompt_path.write_text(build_variant_prompt(product, variant), encoding="utf-8")
        variant["prompt_file"] = str(prompt_path)
        variants.append(variant)

    data = {
        "created_at": now_iso(),
        "project": str(project),
        "product": product,
        "variant_count": len(variants),
        "score_rule": {
            "scale": "0-10，分数越高越好；policy_risk 是风险分，越高风险越大",
            "weights": SCORE_WEIGHTS,
            "policy_risk_penalty": "policy_risk * 0.30",
        },
        "variants": variants,
    }

    output = Path(args.output).expanduser().resolve() if args.output else project / "analysis" / "batch_variants.json"
    write_json(output, data)

    state.setdefault("batch_runs", []).append(
        {
            "created_at": data["created_at"],
            "type": "plan",
            "variant_count": len(variants),
            "file": str(output),
        }
    )
    state["current_step"] = "batch_variants"
    state["status"] = "running"
    state["updated_at"] = now_iso()
    write_json(project_state_path(project), state)

    print(json.dumps({"project": str(project), "variants_file": str(output), "variant_count": len(variants)}, ensure_ascii=False, indent=2))


def number(value: Any) -> float:
    if value is None or value == "":
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def total_score(scores: dict[str, Any]) -> float:
    total = 0.0
    for key, weight in SCORE_WEIGHTS.items():
        total += number(scores.get(key)) * weight
    total -= number(scores.get("policy_risk")) * 0.30
    return round(total, 2)


def command_rank(args: argparse.Namespace) -> None:
    project = Path(args.project).expanduser().resolve()
    variants_path = Path(args.variants).expanduser().resolve() if args.variants else project / "analysis" / "batch_variants.json"
    data = read_json(variants_path, {})
    variants = data.get("variants") or []
    if not variants:
        raise SystemExit(f"no variants found: {variants_path}")

    ranked: list[dict[str, Any]] = []
    for variant in variants:
        item = dict(variant)
        scores = item.get("scores") or {}
        item["source_id_valid"] = item.get("source_id") in SOURCE_IDS
        item["total_score"] = total_score(scores)
        if not item["source_id_valid"]:
            item["total_score"] = -999
        item["score_missing"] = [key for key in [*SCORE_WEIGHTS.keys(), "policy_risk"] if scores.get(key) in {None, ""}]
        ranked.append(item)

    ranked.sort(key=lambda item: item["total_score"], reverse=True)
    winner = ranked[0] if ranked else None
    result = {
        "created_at": now_iso(),
        "project": str(project),
        "variants_file": str(variants_path),
        "winner": winner,
        "ranked": ranked,
    }

    output = Path(args.output).expanduser().resolve() if args.output else project / "analysis" / "batch_ranking.json"
    write_json(output, result)

    state = read_json(project_state_path(project), {})
    if state:
        state.setdefault("batch_runs", []).append(
            {
                "created_at": result["created_at"],
                "type": "rank",
                "file": str(output),
                "winner": winner.get("variant_id") if winner else "",
                "winner_score": winner.get("total_score") if winner else None,
            }
        )
        state["selected_variant"] = winner.get("variant_id") if winner else ""
        state["updated_at"] = now_iso()
        write_json(project_state_path(project), state)

    print(json.dumps({"ranking_file": str(output), "winner": result["winner"]}, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Plan and rank AI feed-ad batch variants.")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("plan")
    p.add_argument("--project", required=True)
    p.add_argument("--count", type=int, default=9)
    p.add_argument("--output", default="")
    p.set_defaults(func=command_plan)

    p = sub.add_parser("rank")
    p.add_argument("--project", required=True)
    p.add_argument("--variants", default="")
    p.add_argument("--output", default="")
    p.set_defaults(func=command_rank)

    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
