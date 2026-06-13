# 信息流广告质量检测模板

对生成结果逐项检查，输出“通过 / 需要重试 / 需要人工确认”。

```json
{
  "overall": "pass / retry / manual_review",
  "checks": {
    "hook_first_3s": "",
    "product_visibility": "",
    "single_clear_selling_point": "",
    "feed_ad_feeling": "",
    "subtitle_readability": "",
    "visual_consistency": "",
    "cta": "",
    "policy_risk": ""
  },
  "problems": [],
  "retry_targets": [
    {
      "shot_id": "",
      "problem": "",
      "change_needed": ""
    }
  ]
}
```

判定标准：

- 前 3 秒没有钩子，必须重试。
- 看不清产品，必须重试。
- 像品牌大片而不是信息流广告，必须重试。
- 商品外观明显变形，必须重试。
- 夸大功效或有合规风险，必须人工确认。
