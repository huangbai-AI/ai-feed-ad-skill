---
name: ai-feed-ad-skill
description: AI Ads skill for product feed-ad workflows. Use when the user asks for AI Ads, AI product ads, e-commerce short videos, Xiaoyunque/Dreamina/Seedance ad generation, product promotion scripts, influencer-style selling videos, drama selling ads, brand films, prompt templates, async generation tracking, loop-based quality checks, or batch ad variants. Do not use for short drama workflows unrelated to product selling.
---

# AI 带货广告 Skill

## 核心目标

把“商品图 + 商品信息 + 可选参考素材”变成可直接交给小云雀 / 即梦 / Seedance 的带货广告提示词和样片任务。

默认不走平台抓取。搜索慢且不稳定，只在用户明确要求“搜索参考素材”时才启用。

## 默认流程

1. 整理商品资料：读取 `templates/product_brief.md`。
2. 选择生产类型和子类型：读取 `templates/reference_script_library.md`、`templates/video_prompt_patterns.md`、`templates/commerce_ad_subtypes.md`。
3. 写系统提示词：读取 `templates/commerce_ad_system_prompt.md`；没有来源编号和参考脚本的小类不能进入输出。
4. 写脚本和分镜：读取 `templates/ad_script.md`、`templates/shot_prompt.md`。
5. 提交生成：优先 `dreamina multimodal2video`，模型默认 `seedance2.0fast`。
6. 记录异步任务：提交成功后写入 `dreamina_tasks/` 和 `project.json`。
7. 查询结果：生成排队时只记录 `Queueing/querying`，不要反复提交。
8. 结果出来后做重大错误检测：读取 `templates/quality_check.md`。
9. 如需 Loop：只针对重大错误读取 `templates/loop_check.md` 并生成重试提示词。
10. 生成结果报告：运行 `scripts/result_report.py`。
11. 用户要批量时：读取 `templates/batch_variants.md`，出候选并用简单人工字段择优。

如果用户给本地视频或要求“扒脚本 / 反推参考”，必须做多模态分析：抽关键帧、看字幕/画面文字、转写口播、整理镜头结构。不能只提取音频。

## 3 大类 + 真实依据小类库

三类是一级分类，不是最终模板。每次创作必须继续选择一个有来源编号的小类，否则提示词会太泛，也容易变成瞎写。

正式小类必须已经写入 `templates/reference_script_library.md`。飞书文档里只出现名字、但还没有完成视频反推脚本的风格，先放“待反推”，不参与默认生成和批量候选。

### 1. 剧情广告

适合：需要强钩子、反转、戏剧冲突、短剧带货、情绪带货的商品。

正式小类：

- 情感反转剧情（LD-01）：低落情绪 + 商品触发状态变化 + 新场景定格。
- 场景错位短剧反转（XQ-01）：强冲突 + 商品动作 + 场面反转 + 记忆点文案。
- AI 工具能力展示（XQ-02）：创作难题 + 输入/生成过程 + 多结果证明 + 工具口号。

待反推，不进默认库：

- 霸总、重生等具体风格名。宫廷、武侠、审讯、现代服务错位场景已归入 XQ-01，不再作为独立小类。

### 2. 品牌大片

适合：视觉质感强、客单较高、需要高级感、氛围感、品牌调性的商品。

正式小类：

- 产品英雄广告（LV-05）：产品极近特写 + 感官卖点 + 正面定格。
- 电影感 TV 广告（LV-06）：强氛围世界观 + 角色体验 + 产品定格。
- 时尚生活方式跟拍（LV-08）：真人跟拍 + 商品细节 + 生活方式定格。
- AI 工具能力展示（XQ-02）：创作难题 + 输入/生成过程 + 多结果证明 + 工具口号。
- 运动性能品牌片（XQ-03）：运动动作 + 性能细节 + 训练氛围 + 品牌短句。
- 科技配饰冷感品牌片（XQ-04）：极简空间 + 产品佩戴 + 冷感城市 + 正面定格。

待反推，不进默认库：

- 冷暖科技风、动感潮流风、高级简约风。飞书文档截图出现过这些风格词，但当前只作为视觉风格词，不作为独立小类。

### 3. 达人带货

适合：大多数电商商品，尤其是美妆个护、服饰配饰、家居日用、食品饮料、数码配件、母婴宠物。

正式小类：

- UGC 手持口播展示（LV-01）：真人自拍 + 指出细节 + 推荐理由。
- 开箱揭晓（LV-02）：包装开场 + 取出商品 + 同框定格。
- 使用场景证明（LV-03）：痛点场景 + 使用动作 + 结果证明。
- 试穿前后变化（LV-04）：未上身 + 上身变化 + 细节判断。
- 俯拍 ASMR 开箱（LV-07）：俯拍开盒 + 取出细节 + 仪式感定格。
- 食品口感连击种草（XQ-05）：场景痛点 + 商品名 + 口感特写连击 + 囤货理由。
- 礼品心意开箱（XQ-06）：送礼对象 + 开箱惊喜 + 质感细节 + 心意理由。
- 套装清单展示（XQ-07）：清单焦虑 + 逐件展示 + 齐全省心 + 情绪价值。
- 智能小物场景连发（XQ-08）：高频麻烦 + 一键解决 + 多场景连发 + 便利收尾。
- 成分背书促销（XQ-09）：人群需求 + 成分/工艺/规格 + 活动信息 + 合规 CTA。
- 睡前仪式情绪种草（XQ-10）：情绪共鸣 + 睡前仪式 + 使用过程 + 温和状态变化。

待反推，不进默认库：

- 家居好物、穿搭单品、美妆护肤、母婴用品、宠物用品。这些是赛道，不是已经反推完成的小类；食品、智能小物、美容仪、成分背书已有正式 XQ 小类。

## 爆款表达结构

写脚本时可以从下面 6 个表达结构中选 1 个做钩子，不要全混在一起：

- 信息差：现状否定 + 工具/商品揭秘 + 方法讲解。
- 机遇焦虑：别人已跑通 + 你还在观望 + 立刻行动。
- 视觉震撼：先展示成片/效果 + 成本揭秘 + 工具或商品安利。
- 亲身经验：结果展示 + 关键经验 + 可复制步骤。
- 保姆级教程：分步演示 + 结果交付 + 收藏引导。
- 痛点共鸣：翻车现场 + 解决方案 + 干货总结。

## 参考素材策略

默认只用以下材料：

- 用户上传的商品图、商品视频、品牌素材。
- 用户提供的文档、脚本、参考链接、本地视频目录。
- 已经存在于项目目录里的参考素材。

只有用户明确要求搜索时，才读取：

- `templates/reference_search.md`
- `templates/reference_analysis.md`

如果搜索失败、平台要求登录、下载慢或队列不稳定，不要阻塞主流程；直接回到“生产类型 + 系统提示词 + 模板生成”。

## 即梦 / Seedance 生成规则

- 默认比例：`9:16`。
- 默认时长：15 秒；用户要求短视频时可以 5-10 秒。
- 默认模型：`seedance2.0fast`。当前 CLI 没有可直接传的 `seedance2.0mini` 参数。
- 商品图存在时，优先 `multimodal2video`；需要保持首帧构图时用 `image2video`。
- 生成命令返回 `Queueing/querying` 时，只记录任务 ID 并等待，不要重复提交。
- 遇到 `current account is not maestro vip` 或“没有 dreamina_cli 使用权限”时，立即暂停。

常用命令：

```bash
python3 scripts/dreamina_generate.py multimodal2video --project . --image product/main.png --prompt-file shots/shot_001.txt --duration 10 --ratio 9:16 --model-version seedance2.0fast --poll 60
python3 scripts/dreamina_generate.py query --project . --submit-id <id>
```

## 分阶段运行

默认阶段：

- `product_brief`
- `production_type`
- `ad_script`
- `shot_prompt`
- `dreamina_generate`
- `async_query`
- `quality_check`
- `loop_check`
- `result_report`
- `batch_variants`

可选阶段，仅用户明确要求参考搜索时使用：

- `reference_search`
- `reference_analysis`

## 项目目录

```text
product/
references/
videos/
frames/
transcripts/
analysis/
scripts/
shots/
dreamina_tasks/
loop_runs/
schedule_runs/
workflow_runs/
batch_runs/
outputs/
project.json
```

## 关键文件

- `templates/commerce_ad_system_prompt.md`：三类带货广告系统提示词和模板。
- `templates/reference_script_library.md`：真实视频依据和参考脚本库。
- `templates/video_prompt_patterns.md`：三大类生产类型库。
- `templates/commerce_ad_subtypes.md`：子类型和可套用提示词模板库。
- `templates/ad_script.md`：脚本结构。
- `templates/shot_prompt.md`：即梦提示词结构。
- `scripts/dreamina_generate.py`：提交和查询即梦任务。
- `scripts/workflow_stage.py`：分阶段状态。
- `scripts/quality_check.py`：重大错误检测表。
- `scripts/result_report.py`：结果报告。
- `scripts/batch_variants.py`：批量候选和简单择优。
