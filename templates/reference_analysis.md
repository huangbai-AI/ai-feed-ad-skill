# 参考广告拆解模板

对每条参考广告输出以下内容。

```json
{
  "source": "",
  "duration": "",
  "hook_0_3s": "",
  "pain_or_desire": "",
  "product_reveal": "",
  "proof": "",
  "offer_or_cta": "",
  "inferred_prompt_pattern": {
    "primary_pattern": "",
    "secondary_pattern": "",
    "why_this_pattern": "",
    "opening_product_appearance": "",
    "core_camera_motion": "",
    "scene_and_props": "",
    "reusable_prompt_sentence": ""
  },
  "shot_rhythm": [
    {
      "time": "0-3s",
      "visual": "",
      "subtitle": "",
      "purpose": ""
    }
  ],
  "subtitle_style": "",
  "borrowable_patterns": [],
  "do_not_copy": []
}
```

视频参考必须读取 `templates/video_prompt_patterns.md`，把参考视频归入其中的模式；如果不属于任何模式，再新增“临时模式”，但不要直接照抄参考画面。

反推提示词时只抽象以下内容：

- 商品出现方式：手持、开箱、使用中、上身、宏观特写、礼盒展示。
- 场景类型：卧室、浴室、厨房、健身房、球场、街头、影棚、桌面俯拍。
- 镜头方式：自拍手持、俯拍、推进、环绕、跟拍、慢动作、跳切。
- 节奏结构：钩子、揭晓、证明、结果、行动引导。

不要抽象以下内容：

- 参考视频中的人物身份、脸、服装细节。
- 参考品牌、包装图案、商标、口号。
- 明确属于原视频的剧情或独特设定。

最后总结“可复用的广告公式”：

```text
钩子 -> 痛点 -> 产品解决方案 -> 证明 -> 行动引导
```

如果广告是纯展示型，也要转成信息流可用结构，不要只描述画面。
