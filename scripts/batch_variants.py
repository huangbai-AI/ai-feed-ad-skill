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
    ("drama_scene_mismatch", "剧情广告", "场景错位短剧反转", "XQ-01", "强冲突、商品动作、场面反转、记忆点文案"),
    ("ai_tool_capability", "剧情广告", "AI 工具能力展示", "XQ-02", "创作难题、输入生成过程、多结果证明、工具口号"),
    ("brand_product_hero", "品牌大片", "产品英雄广告", "LV-05", "产品极近特写、感官卖点、正面定格"),
    ("brand_tv_spot", "品牌大片", "电影感 TV 广告", "LV-06", "强氛围世界观、角色体验、产品定格"),
    ("brand_sport_performance", "品牌大片", "运动性能品牌片", "XQ-03", "运动动作、性能细节、训练氛围、品牌短句"),
    ("brand_tech_accessory", "品牌大片", "科技配饰冷感品牌片", "XQ-04", "极简空间、产品佩戴、冷感城市、正面定格"),
    ("creator_handheld_ugc", "达人带货", "UGC 手持口播展示", "LV-01", "真人自拍、指出细节、推荐理由"),
    ("creator_food_sensory", "达人带货", "食品口感连击种草", "XQ-05", "场景痛点、商品名、口感特写连击、囤货理由"),
    ("creator_gift_unbox", "达人带货", "礼品心意开箱", "XQ-06", "送礼对象、开箱惊喜、质感细节、心意理由"),
    ("brand_lifestyle_follow", "品牌大片", "时尚生活方式跟拍", "LV-08", "真人跟拍、商品细节、生活方式定格"),
    ("creator_unboxing_reveal", "达人带货", "开箱揭晓", "LV-02", "包装开场、取出商品、同框定格"),
    ("creator_use_case_proof", "达人带货", "使用场景证明", "LV-03", "痛点场景、使用动作、结果证明"),
    ("creator_tryon_change", "达人带货", "试穿前后变化", "LV-04", "未上身、上身变化、细节判断"),
    ("creator_asmr_unbox", "达人带货", "俯拍 ASMR 开箱", "LV-07", "俯拍开盒、取出细节、仪式感定格"),
    ("creator_kit_checklist", "达人带货", "套装清单展示", "XQ-07", "清单焦虑、逐件展示、齐全省心、情绪价值"),
    ("creator_smart_scenarios", "达人带货", "智能小物场景连发", "XQ-08", "高频麻烦、一键解决、多场景连发、便利收尾"),
    ("creator_ingredient_offer", "达人带货", "成分背书促销", "XQ-09", "人群需求、成分工艺规格、活动信息、合规 CTA"),
    ("creator_sleep_ritual", "达人带货", "睡前仪式情绪种草", "XQ-10", "情绪共鸣、睡前仪式、使用过程、温和状态变化"),
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
REVIEW_FIELDS = ["usable", "major_defect", "product_consistent", "human_consistent", "manual_pick"]


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
            "review": {
                "usable": None,
                "major_defect": None,
                "product_consistent": None,
                "human_consistent": None,
                "manual_pick": None,
                "notes": "",
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
        "review_rule": {
            "fields": REVIEW_FIELDS,
            "usable": "能直接作为候选继续精修",
            "major_defect": "有重大错误则不能入选",
            "product_consistent": "商品颜色、形状、包装、材质一致",
            "human_consistent": "人物前后一致且没有身体结构问题",
            "manual_pick": "人工最终选中",
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


def bool_value(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    raw = str(value).strip().lower()
    if raw in {"true", "yes", "y", "1", "是", "通过", "可用", "选中"}:
        return True
    if raw in {"false", "no", "n", "0", "否", "不通过", "不可用", "未选"}:
        return False
    return None


def review_status(item: dict[str, Any]) -> tuple[str, int]:
    if not item.get("source_id_valid"):
        return "invalid_source", 0
    review = item.get("review") or {}
    usable = bool_value(review.get("usable"))
    major_defect = bool_value(review.get("major_defect"))
    product_consistent = bool_value(review.get("product_consistent"))
    human_consistent = bool_value(review.get("human_consistent"))
    manual_pick = bool_value(review.get("manual_pick"))

    if major_defect is True:
        return "major_defect", 1
    if product_consistent is False or human_consistent is False:
        return "inconsistent", 1
    if manual_pick is True:
        return "manual_pick", 4
    if usable is True and major_defect is False and product_consistent is True and human_consistent is True:
        return "usable", 3
    return "needs_review", 2


def command_rank(args: argparse.Namespace) -> None:
    project = Path(args.project).expanduser().resolve()
    variants_path = Path(args.variants).expanduser().resolve() if args.variants else project / "analysis" / "batch_variants.json"
    data = read_json(variants_path, {})
    variants = data.get("variants") or []
    if not variants:
        raise SystemExit(f"no variants found: {variants_path}")

    ranked: list[dict[str, Any]] = []
    for order, variant in enumerate(variants):
        item = dict(variant)
        item["source_id_valid"] = item.get("source_id") in SOURCE_IDS
        review = item.get("review") or {}
        status, priority = review_status(item)
        item["review_status"] = status
        item["review_priority"] = priority
        item["review_missing"] = [key for key in REVIEW_FIELDS if bool_value(review.get(key)) is None]
        item["_order"] = order
        ranked.append(item)

    ranked.sort(key=lambda item: (item["review_priority"], -item["_order"]), reverse=True)
    winner = next((item for item in ranked if item["review_status"] in {"manual_pick", "usable"}), None)
    for item in ranked:
        item.pop("_order", None)
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
                "winner_status": winner.get("review_status") if winner else "",
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
