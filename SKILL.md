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
3. 拆解参考广告
4. 重写原创广告脚本
5. 拆成镜头和即梦提示词
6. 调用 `dreamina` 生成样片
7. 检查结果，不合格就改提示词重试
8. 启用 Loop 时，自动复盘、重写失败镜头、限制重试次数
9. 启用定时任务时，按固定间隔检查项目并继续推进

不要把这个 Skill 用于短剧、漫剧或剧情长内容。

## 默认边界

- 默认中文输出，默认竖屏 `9:16`，默认 15-30 秒。
- 默认先做 1 条样片，用户确认后再批量生成。
- 默认优先使用低成本模型，符合 Seedance 2.0 mini / fast 适合批量生产的定位。
- Loop 默认最多重试 3 次；定时任务默认 15 分钟检查一次，但必须由用户明确要求才开启。
- 只处理公开可访问或用户授权的素材。不要绕过登录、付费、加密或平台下载限制。
- 参考广告只学习结构、节奏、卖点表达和镜头语言，不复制原文案、品牌素材或人物形象。

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

### 3. 参考拆解

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

### 4. 原创广告脚本

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

### 5. 镜头和提示词

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

### 6. 即梦生成

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

### 7. 质量检测和重试

读取 `templates/quality_check.md`。检查：

- 前 3 秒是否有钩子
- 商品是否清楚出现
- 痛点和卖点是否明确
- 是否像信息流广告，而不是普通宣传片
- 字幕是否适合手机快速浏览
- 画面是否和商品一致
- 是否有明确行动引导

不合格时读取 `templates/retry_prompt.md`，只改有问题的镜头或提示词，不重做整个项目。

### 8. Loop 循环检测

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

### 9. 定时任务

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

## 项目目录

每个商品项目使用固定结构：

```text
product/
references/
transcripts/
analysis/
scripts/
shots/
dreamina_tasks/
loop_runs/
schedule_runs/
outputs/
project.json
```

用 `scripts/project_state.py` 创建和更新项目状态。

## 脚本说明

- `scripts/project_state.py`：创建项目、记录步骤状态、保存参考广告条目。
- `scripts/ensure_dreamina.py`：检查即梦 CLI，缺失时用官方安装脚本自动安装。
- `scripts/transcribe.py`：从本地广告视频提取音频并转写，英文参考广告用 `--language en`。
- `scripts/dreamina_generate.py`：封装 `dreamina` 生成和查询，调用前会自动检查并安装 CLI。
- `scripts/quality_check.py`：生成质量检查表，便于人工或 Agent 逐项复核。
- `scripts/loop_controller.py`：读取质量检查结果，生成失败镜头重试提示词，可选自动提交即梦。
- `scripts/scheduler.py`：按固定间隔检查一个或多个商品项目，必要时触发 Loop。

脚本是辅助工具；复杂判断仍由 Agent 读取模板后完成。
