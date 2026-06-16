# 重大错误检测模板

质检只判断“能不能继续用”。不要因为钩子弱、CTA 弱、广告感不强、节奏不够刺激而要求重试。

```json
{
  "overall": "pass / retry / manual_review",
  "review_mode": "major_defect_only",
  "checks": {
    "human_body_defect": {
      "result": "",
      "notes": "断手断脚、多手多指、脸崩、身体结构异常"
    },
    "product_mismatch": {
      "result": "",
      "notes": "商品颜色、形状、包装、材质不一致"
    },
    "human_inconsistent": {
      "result": "",
      "notes": "人物前后不一致"
    },
    "product_lost_or_deformed": {
      "result": "",
      "notes": "商品消失、遮挡、变形"
    },
    "visual_text_defect": {
      "result": "",
      "notes": "字幕乱码、画面严重模糊、闪烁、穿模"
    },
    "fabricated_claim": {
      "result": "",
      "notes": "编造价格、销量、成分、产地、认证、活动、医疗功效"
    }
  },
  "problems": [],
  "retry_targets": [
    {
      "shot_id": "shot_001",
      "problem_key": "",
      "problem": "",
      "change_needed": ""
    }
  ]
}
```

判定标准：

- 没有重大错误：`overall=pass`。
- 有上述任一重大错误：`overall=retry`，并填写对应 `retry_targets`。
- 商品事实、授权、成分、产地、认证、医疗功效、价格销量无法确认：`overall=manual_review`。
- 重试提示词只修失败点，保持原商品、人物、场景和脚本方向。
