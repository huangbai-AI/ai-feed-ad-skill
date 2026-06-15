# 即梦镜头提示词模板

把选中的广告脚本拆成 3-8 个镜头。每个镜头单独生成，便于失败重试。

拆镜头前先读取 `templates/video_prompt_patterns.md`，为整条广告选择 1 个主模式、最多 1 个辅助模式。模式必须服务商品卖点，不要为了炫技混搭。

如果用户要求 5 秒视频、5 秒提示词、一次生成多条短视频，不使用 3-8 个镜头表。改用 `5s_single_scene_variants`：每条都是一个独立 5 秒完整场景，可单独调用一次视频生成。

参考来源只允许写在内部字段，最终 `prompt` 不能出现“参考 xx”“某平台视频”“Higgsfield”等来源字样。

## 镜头表

```json
{
  "video_ratio": "9:16",
  "total_duration": "15-30s",
  "primary_prompt_pattern": "ugc_handheld_demo / unboxing_reveal / use_case_proof / try_on_transformation / macro_product_hero / cinematic_tv_spot / tutorial_step_demo / fashion_lifestyle_follow",
  "secondary_prompt_pattern": "",
  "shots": [
    {
      "id": "shot_001",
      "duration": 5,
      "prompt_pattern": "",
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

## 5 秒单场景变体表

用于一次生成多条 5 秒商品视频。每条视频只完成一个具体场景，不拆镜头。

```json
{
  "video_ratio": "9:16",
  "total_duration": "5s_each",
  "generation_plan": "one_prompt_one_video",
  "product_lock": {
    "name": "",
    "color": "",
    "material": "",
    "fixed_details": []
  },
  "global_person_constraint": "",
  "global_negative_prompt": "不要品牌字，不要字幕，不要水印，不要改变商品颜色、形状、材质和配件",
  "variants": [
    {
      "id": "variant_01",
      "duration": 5,
      "internal_reference_note": "",
      "prompt_pattern": "unboxing_reveal / ugc_handheld_demo / try_on_transformation / fashion_lifestyle_follow / macro_product_hero / cinematic_tv_spot / tutorial_step_demo",
      "scene_type": "",
      "dreamina_mode": "image2video / multimodal2video / text2video",
      "prompt": "",
      "negative_prompt": ""
    }
  ]
}
```

`internal_reference_note` 可以记录“来自本地第几条视频的结构”，但不能复制到 `prompt` 中。

5 秒 `prompt` 写法：

```text
5 秒竖屏{场景类型}视频。0-1 秒，{商品或包装已经出现，人物和场景明确}。1-3 秒，{人物完成核心动作，商品始终清楚可见}。3-5 秒，{商品近景、上身效果或结果定格，突出一个细节}。
```

## 提示词要求

- 写清楚真实广告画面，不要写抽象营销词。
- 保持产品外观一致，商品图可用时优先作为参考图。
- 用户指定的人物约束必须写进每条提示词，例如亚洲女生、年龄段、穿搭风格。
- 人物口播要自然，不要夸张表演。
- 字幕只保留核心句，不要堆满屏幕。
- 画面要有真实使用场景和产品近景。
- 第一镜头 1 秒内必须出现商品、包装、上身效果或明确结果；5 秒视频必须在前 0.5 秒出现。
- 每条广告至少 1 个商品近景，至少 1 个真实使用/手部动作/上身展示镜头。
- 功能型商品优先套用 `use_case_proof`；服饰配饰优先套用 `try_on_transformation` 或 `fashion_lifestyle_follow`；包装强的食品饮料优先套用 `macro_product_hero`。
- 如果参考视频来自竞品，只复用镜头结构，不复用人物、品牌、包装、台词和具体场景。
- 最终 `prompt` 不写参考编号、参考平台、参考文件名，只保留画面执行指令。

## 常用镜头组合

### 5 秒女包变体

```text
variant_01: 桌面开箱，礼盒打开，包取出，商品和包装同框。
variant_02: 床上礼盒开包，防尘袋取出包，手持完整展示。
variant_03: 俯拍开箱，双手整理肩带、扣件、挂件，最后整齐摆放。
variant_04: 自拍手持展示，女生把包举近镜头，打开包口展示容量。
variant_05: 卧室变装试背，手遮镜头跳切，包已斜挎上身。
variant_06: 穿搭完成版，调整肩带，全身到包近景。
variant_07: 街头时尚跟拍，走动中包自然摆动，切包身细节。
variant_08: 卧室包袋上身展示，手持包、斜挎、皮革和五金近景、全身定格。
```

### UGC 快速种草

```text
shot_001: 真人手持商品近镜头，直接给钩子。
shot_002: 商品细节近景，手指指向核心卖点。
shot_003: 真实使用动作，证明卖点。
shot_004: 人物满意反应或商品定格，加短 CTA。
```

### 开箱到使用

```text
shot_001: 包装盒/快递箱占满画面，双手准备打开。
shot_002: 取出商品，商品完整亮相。
shot_003: 立刻进入使用场景，展示关键动作。
shot_004: 商品和结果同框，给购买理由。
```

### 试穿变化

```text
shot_001: 人物手持未穿戴商品。
shot_002: 转身、手遮镜头或跳切完成变化。
shot_003: 全身/上脚/佩戴效果展示。
shot_004: 材质、版型、搭配细节近景。
```

### 宏观产品大片

```text
shot_001: 商品极近特写，突出材质或包装。
shot_002: 商品旋转、悬浮、穿越或慢动作落位。
shot_003: 卖点相关元素围绕商品出现。
shot_004: 商品正面定格，干净收尾。
```

## 默认即梦参数

- `ratio`: `9:16`
- `model_version`: `seedance2.0fast`
- `duration`: 单镜头 4-15 秒
- 样片阶段只生成 1 条主版本
