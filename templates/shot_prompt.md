# 即梦镜头提示词模板

把选中的广告脚本拆成 3-8 个镜头。每个镜头单独生成，便于失败重试。

## 镜头表

```json
{
  "video_ratio": "9:16",
  "total_duration": "15-30s",
  "shots": [
    {
      "id": "shot_001",
      "duration": 5,
      "goal": "",
      "visual": "",
      "product": "",
      "person": "",
      "action": "",
      "subtitle": "",
      "dreamina_mode": "text2video / image2video / multimodal2video",
      "prompt": "",
      "negative_prompt": ""
    }
  ]
}
```

## 提示词要求

- 写清楚真实广告画面，不要写抽象营销词。
- 保持产品外观一致，商品图可用时优先作为参考图。
- 人物口播要自然，不要夸张表演。
- 字幕只保留核心句，不要堆满屏幕。
- 画面要有真实使用场景和产品近景。

## 默认即梦参数

- `ratio`: `9:16`
- `model_version`: `seedance2.0fast`
- `duration`: 单镜头 4-15 秒
- 样片阶段只生成 1 条主版本
