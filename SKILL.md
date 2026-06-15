---
name: ai-feed-ad-skill
description: Create product feed-ad workflows for AI agents. Use when the user wants information-flow ads, product ads, paid social creatives, TikTok/Douyin/Instagram-style vertical ads, Seedance/Dreamina batch ad generation, reference ad analysis, ad script rewriting, shot prompts, or loop-based ad quality checks. Do not use for short drama workflows.
---

# AI 信息流广告 Skill

## 核心目标

把“商品图 + 商品信息”变成一条可投放思路清晰的竖屏信息流广告样片。默认先生成 1 条样片，再扩展批量版本。

始终按这个顺序执行：

1. 整理商品资料
2. 搜索同类参考广告
3. 搜索同类高赞视频并排序
4. 拆解参考广告/高赞视频
5. 选择商品广告视频提示词模式
6. 重写原创广告脚本
7. 拆成镜头和即梦提示词
8. 调用 `dreamina` 生成样片
9. 检查结果，不合格就改提示词重试
10. 启用 Loop 时，自动复盘、重写失败镜头、限制重试次数
11. 启用定时任务时，按固定间隔检查项目并继续推进
12. 样片通过后，批量生成候选并评分择优

不要把这个 Skill 用于短剧、漫剧或剧情长内容。

## 默认边界

- 默认中文输出，默认竖屏 `9:16`，默认 15-30 秒。
- 当用户明确要求 5 秒、短变体、一次生成多条 5 秒视频时，不走 15-30 秒多镜头脚本，改用“5 秒单场景变体”：每条视频只完成一个清楚动作链。
- 默认先做 1 条样片，用户确认后再批量生成。
- 默认优先使用低成本模型，符合 Seedance 2.0 mini / fast 适合批量生产的定位。
- Loop 默认最多重试 3 次；定时任务默认 15 分钟检查一次，但必须由用户明确要求才开启。
- 支持 `stop_at` 分阶段运行。用户只要前半段时，必须停在指定阶段，不要擅自生成。
- 批量候选默认 9 个，评分后只精修 1-3 个最高分版本，避免平均消耗生成额度。
- 只处理公开可访问或用户授权的素材。不要绕过登录、付费、加密或平台下载限制。
- 参考广告只学习结构、节奏、卖点表达和镜头语言，不复制原文案、品牌素材或人物形象。
- 内部分析可以记录参考视频编号、文件名和来源；最终交给视频生成器的提示词不能出现“参考 xx”“Higgsfield”“照着某视频”等来源字样。
- 用户给定人物约束时，例如亚洲人、亚洲女生、年龄段、穿搭风格，必须作为全局约束继承到每条提示词，不能只写在第一条。

## 参考广告去哪找

按商品所在市场选择平台。无法登录或无法下载时，保存链接、截图、人工描述即可。

1. TikTok Creative Center / Top Ads
   - 海外首选。
   - 适合找高表现短视频广告、开场钩子、转化话术和镜头节奏。
   - 搜索：商品类目词、痛点词、竞品品牌、英文商品词。
   - 入口：`https://ads.tiktok.com/creative/creativeCenter`

2. 巨量创意
   - 国内首选。
   - 适合找抖音/巨量体系信息流广告、口播广告、商品种草、开箱测评。
   - 搜索：商品类目、功效词、痛点词、人群词、竞品词。
   - 入口：`https://cc.oceanengine.com/`

3. Meta Ads Library
   - 用于 Facebook / Instagram 正在投放广告。
   - 没有直接表现数据时，用持续投放时间、同主题变体数量、素材重复频率判断参考价值。
   - 搜索：品牌名、竞品名、官网域名、英文类目词。
   - 入口：`https://www.facebook.com/ads/library`

4. Google Ads Transparency Center
   - 用于查 Google / YouTube / 展示广告。
   - 适合补充竞品落地页话术、YouTube 广告和展示广告卖点。
   - 搜索：品牌名、官网域名、竞品名。
   - 入口：`https://adstransparency.google.com/`

5. 用户提供素材
   - 当平台搜索不足时，优先让用户提供本地视频、链接、截图或竞品名单。
   - 本地视频可以用 `scripts/transcribe.py` 转写。

## 执行流程

### 0. 分阶段运行

当用户要求“先做到某一步”“只跑生成前流程”“只生成提示词”“先不要调用即梦”等，读取 `templates/stage_control.md`。

可用脚本：

```bash
python scripts/workflow_stage.py plan --project . --stop-at shot_prompt
python scripts/workflow_stage.py mark --project . --stage product_brief --status complete
python scripts/workflow_stage.py next --project .
python scripts/workflow_stage.py status --project .
```

常用停止点：

- `reference_search`：只找同类参考广告。
- `hot_video_search`：只找同类高赞视频并排序。
- `reference_analysis`：只拆解参考广告。
- `ad_script`：只写广告脚本。
- `shot_prompt`：只写即梦镜头提示词。
- `dreamina_generate`：只生成样片，不自动 Loop。
- `quality_check`：只做质量检测，等人工确认。
- `batch_variants`：样片通过后，批量候选并择优。

到达 `stop_at` 后必须停下，不继续调用下一阶段。

### 1. 商品资料

读取 `templates/product_brief.md`。把用户输入整理成：

- 商品名
- 类目
- 目标人群
- 核心痛点
- 3-5 个卖点
- 使用场景
- 价格/优惠
- 禁用词和合规限制
- 投放平台

如果缺少商品图或核心卖点，先基于现有信息继续，不要卡住；在结果里标注缺口。

### 2. 参考搜索

读取 `templates/reference_search.md`。生成三组搜索词：

- 类目词：商品是什么
- 痛点词：解决什么问题
- 竞品词：谁在卖类似产品

默认收集 5-10 条参考广告。每条记录至少包含：

- 平台
- 链接
- 截图或视频文件路径
- 商品类目
- 时长
- 开场钩子
- 核心卖点
- 转化动作
- 为什么值得参考

### 3. 同类高赞视频搜索

当用户要求“高赞视频”“爆款视频”“同类热门内容”“找高互动参考”时，读取 `templates/hot_video_search.md`。

先明确边界：抖音、小红书、TikTok 等平台的点赞、收藏、分享和评论数据经常需要登录态或人工读取；不能绕过限制。无法自动读取时，保存链接、截图，并用脚本录入热度数据。

可用脚本：

```bash
python scripts/hot_video_search.py plan --project .
python scripts/hot_video_search.py fetch-youtube --project . --query "portable blender review" --count 8
python scripts/hot_video_search.py download --project . --top 1
python scripts/hot_video_search.py download --project . --url "https://..." --title "参考视频标题"
python scripts/hot_video_search.py seed --project . --count 6
python scripts/hot_video_search.py add --project . --platform 小红书 --url "..." --title "..." --likes 12000 --views 200000 --hook "..."
python scripts/hot_video_search.py import-json --project . --input references/manual_hot_videos.json
python scripts/hot_video_search.py rank --project .
python scripts/hot_video_search.py export-references --project . --top 5
```

输出：

- `references/hot_video_search_plan.json`
- `references/youtube_fetch_<timestamp>.json`
- `references/hot_video_seed_import.json`
- `references/hot_video_candidates.json`
- `analysis/hot_video_ranking.json`
- `videos/<video>.mp4`
- `frames/<video>/frame_001.jpg`
- `analysis/hot_video_media_<video>.json`
- `references/hot_video_references.json`

排序依据：

- 热度：点赞、播放、评论、分享、收藏。
- 相关度：商品词、类目词、痛点词、场景词是否匹配。
- 完整度：是否有标题、链接、截图、钩子、卖点和可借鉴说明。

如果平台搜索受限或暂时没有真实候选，先运行 `python scripts/hot_video_search.py seed --project . --count 6` 导入内置结构种子。内置种子必须标记为 `source_type=built_in_seed`，不能当作真实高赞数据。

已跑通的公开抓取方式：

```bash
python scripts/hot_video_search.py fetch-youtube --project . --query "商品英文词 review" --count 8
```

这条链路依赖本机 `yt-dlp`，只抓公开视频元数据，不下载视频文件。抓到的真实候选标记为 `source_type=real_video`，可用于排序和导出参考。

视频级拆解必须先下载本地文件：

```bash
python scripts/hot_video_search.py download --project . --top 1
```

下载成功后才允许按画面和口播做拆解。脚本会写入 `local_file`、`frame_dir`、`analysis_file`，并用 `ffprobe` 标记是否有音轨；没有音轨时只能做画面拆解，不能假装做了口播分析。下载失败、要求登录或平台限制时，保留链接和错误原因，只能做链接级参考。

已验证限制：TikTok 普通搜索页 `https://www.tiktok.com/search/video?q=...` 当前不能直接用 `yt-dlp` 抓，需登录态浏览、官方案例、用户提供链接或人工录入。

### 4. 参考拆解

读取 `templates/reference_analysis.md`。每条参考广告都拆成：

- 前 3 秒钩子
- 痛点/欲望
- 产品出现方式
- 证明方式
- 价格/优惠/行动引导
- 镜头节奏
- 字幕样式
- 可借鉴点
- 禁止复制点

如果参考素材是视频，必须额外反推“可复用提示词模式”：

- 属于哪个视频模式
- 开场 0-3 秒如何让商品出现
- 商品如何被手持、开箱、使用、试穿或宏观展示
- 镜头运动和场景是什么
- 哪些元素只能学习结构，不能复制

读取 `templates/video_prompt_patterns.md`，把参考视频归入 1-2 个模式，供后续脚本和镜头提示词使用。

如果用户提供本地参考视频目录，必须优先从本地视频抽帧或总览图中选择同类结构，不要只按通用模式乱写。选择参考时先按商品类目过滤，例如包袋优先选择开箱、上身试背、穿搭展示、街头跟拍、细节特写；不要把食品、饮料、电器的镜头结构硬套到包袋。

拆解记录和最终生成提示词必须分开：

- 拆解记录：可以写参考视频编号、文件名、对应结构。
- 最终提示词：只写画面、人物、商品、动作、镜头和限制，不写参考来源。

### 5. 商品广告视频提示词模式

生成脚本或镜头前，读取 `templates/video_prompt_patterns.md`。

默认从以下模式中选 1 个主模式：

- `ugc_handheld_demo`：真人手持口播展示。
- `unboxing_reveal`：开箱揭晓。
- `use_case_proof`：真实使用证明。
- `try_on_transformation`：试穿/前后变化。
- `macro_product_hero`：宏观产品英雄镜头。
- `cinematic_tv_spot`：电影感 TV 广告。
- `tutorial_step_demo`：步骤教学演示。
- `fashion_lifestyle_follow`：时尚生活方式跟拍。

除非商品确实需要，单条广告不要混合超过 2 个模式。

当用户要求 5 秒视频或 5 秒变体时，按 `templates/video_prompt_patterns.md` 中的“5 秒单场景变体规则”执行：

- 每条 5 秒视频只选 1 个场景和 1 个动作链。
- 每条必须写清 0-1 秒、1-3 秒、3-5 秒发生什么。
- 前 0.5 秒必须出现商品、包装、上身效果或明确结果。
- 同一批变体必须围绕同一个商品外观，不能改颜色、材质、结构和配件。
- 人物约束、地区约束、性别约束必须写进每条提示词。

### 6. 原创广告脚本

读取 `templates/ad_script.md`。默认生成 3 个方向：

- 痛点解决型
- 真人口播型
- 开箱测评型

每个方向输出：

- 标题
- 目标人群
- 15-30 秒脚本
- 分镜概览
- 开场钩子
- 转化话术

默认选择最适合商品和平台的一个方向进入生成。

### 7. 镜头和提示词

读取 `templates/shot_prompt.md`。把脚本拆成 3-8 个镜头。

每个镜头必须包含：

- 镜头编号
- 时长
- 画面
- 人物/商品
- 动作
- 字幕
- 即梦提示词
- 负面要求

如用户有商品图，优先用 `dreamina image2video` 或 `dreamina multimodal2video`；没有图片才用 `dreamina text2video`。

如果用户要求一次生成多条 5 秒商品视频，不拆成 3-8 个镜头，而是输出多条 `5s_single_scene_variants`。每条都是独立 5 秒完整场景，可单独调用一次 `dreamina image2video`。最终 prompt 里不要出现参考编号、参考平台名或“参考某视频”的描述。

### 8. 即梦生成

先确认本机有 `dreamina`；如果没有，自动安装官方 CLI：

```bash
python scripts/ensure_dreamina.py --install
dreamina user_credit
```

如果生成命令返回 `当前账号没有 dreamina_cli 使用权限: current account is not maestro vip`，立即停止生成，不要反复重试。说明当前账号能查看余额但没有 CLI 生成权限，需要用户升级/切换到有 `dreamina_cli` 权限的账号后再继续。

默认参数：

- `ratio=9:16`
- `duration=5-15`，按镜头长度决定
- `model_version=seedance2.0fast`
- 样片优先低成本，关键镜头再升级模型

可用脚本：

```bash
python scripts/dreamina_generate.py text2video --prompt-file shots/shot_001.txt --project . --duration 5
python scripts/dreamina_generate.py image2video --image product/main.png --prompt-file shots/shot_001.txt --project . --duration 5
python scripts/dreamina_generate.py query --submit-id <id> --project .
```

### 9. 质量检测和重试

读取 `templates/quality_check.md`。检查：

- 前 3 秒是否有钩子
- 商品是否清楚出现
- 痛点和卖点是否明确
- 是否像信息流广告，而不是普通宣传片
- 字幕是否适合手机快速浏览
- 画面是否和商品一致
- 是否有明确行动引导

不合格时读取 `templates/retry_prompt.md`，只改有问题的镜头或提示词，不重做整个项目。

### 10. Loop 循环检测

当用户要求 Loop、自动复盘、自动重试或 24 小时生产时，读取 `templates/loop_check.md`。

Loop 的职责：

- 根据 `analysis/quality_check.json` 判断 `pass / retry / manual_review`。
- `pass`：停止循环，进入交付或批量扩展。
- `retry`：只重写失败镜头的提示词，默认最多 3 次。
- `manual_review`：合规、商品事实、品牌授权、账号权限等问题，暂停等待用户确认。
- 每轮结果写入 `loop_runs/`，并同步更新 `project.json`。

可用脚本：

```bash
python scripts/quality_check.py --project . --video outputs/demo.mp4
python scripts/loop_controller.py --project . --max-retries 3
python scripts/loop_controller.py --project . --max-retries 3 --submit --duration 5
```

如果遇到 `current account is not maestro vip` 或“没有 dreamina_cli 使用权限”，Loop 必须暂停，不能反复提交。

### 11. 定时任务

当用户要求定时、持续跑、批量生产或 24 小时生产时，读取 `templates/scheduler.md`。

定时任务的职责：

- 默认每 15 分钟检查一次项目状态。
- 对有质量检查结果的项目运行 Loop。
- 对没有质量检查结果的项目只记录当前步骤，等待 Agent 继续创作、搜索或生成。
- 默认不自动提交即梦生成；只有用户明确允许时才加 `--submit-loop`。
- 已完成、已暂停、即梦 CLI 权限不足的项目默认跳过。

可用脚本：

```bash
python scripts/scheduler.py --project . --once
python scripts/scheduler.py --project . --interval-minutes 15
python scripts/scheduler.py --project-root /path/to/projects --interval-minutes 15
python scripts/scheduler.py --project . --interval-minutes 15 --submit-loop --max-retries 3
```

### 12. 批量候选和择优

样片通过后，读取 `templates/batch_variants.md`。批量不是简单复制，而是围绕可测试变量做候选：

- 开场钩子
- 主卖点角度
- 人物表达方式
- 结尾行动引导

默认先生成 9 个候选。看完候选视频后，按这些维度评分：

- 前 3 秒钩子
- 商品清晰度
- 单一卖点
- 信息流广告感
- 行动引导
- 合规风险

可用脚本：

```bash
python scripts/batch_variants.py plan --project . --count 9
python scripts/batch_variants.py rank --project .
```

择优后，只继续精修排名最高的 1-3 个候选。

## 项目目录

每个商品项目使用固定结构：

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

用 `scripts/project_state.py` 创建和更新项目状态。

## 脚本说明

- `scripts/project_state.py`：创建项目、记录步骤状态、保存参考广告条目。
- `scripts/ensure_dreamina.py`：检查即梦 CLI，缺失时用官方安装脚本自动安装。
- `scripts/transcribe.py`：从本地广告视频提取音频并转写，英文参考广告用 `--language en`。
- `scripts/hot_video_search.py`：规划同类高赞视频搜索、录入热度数据、排序、下载可访问视频、抽帧并导出参考。
- `scripts/dreamina_generate.py`：封装 `dreamina` 生成和查询，调用前会自动检查并安装 CLI。
- `scripts/quality_check.py`：生成质量检查表，便于人工或 Agent 逐项复核。
- `scripts/loop_controller.py`：读取质量检查结果，生成失败镜头重试提示词，可选自动提交即梦。
- `scripts/scheduler.py`：按固定间隔检查一个或多个商品项目，必要时触发 Loop。
- `scripts/workflow_stage.py`：管理分阶段运行，支持 `stop_at`。
- `scripts/batch_variants.py`：规划批量候选、生成候选提示词、评分排序。
- `templates/video_prompt_patterns.md`：商品广告视频提示词模式库，用于从参考视频反推可复用镜头和即梦提示词。

脚本是辅助工具；复杂判断仍由 Agent 读取模板后完成。
