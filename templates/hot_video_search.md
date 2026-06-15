# 同类高赞视频搜索模板

目标：为商品收集 5-20 条同类高赞短视频，用真实热度信号辅助广告脚本和镜头设计。

## 边界

- 只处理公开可访问或用户授权的内容。
- 不绕过登录、付费、加密、反爬或平台限制。
- 抖音、小红书、TikTok 的点赞、评论、收藏、分享等数据可能需要登录态；无法自动读取时，先保存链接、截图和人工录入的数据。
- 高赞视频只学习选题、节奏、钩子、场景和卖点表达，不复制原文案、人物形象、品牌素材或未授权音乐。

## 搜索顺序

1. 官方广告/创意库
   - TikTok Creative Center / Top Ads
   - 巨量创意
   - Meta Ads Library
   - Google Ads Transparency Center

2. 内容平台
   - 抖音：商品词、痛点词、场景词、竞品词。
   - 小红书：商品词 + 测评 / 好物 / 避坑 / 使用体验。
   - TikTok / Instagram / YouTube Shorts：英文商品词、痛点词、竞品词。

3. 用户提供
   - 本地视频、链接、截图、竞品账号、竞品商品页。

## 关键词

- 类目词：商品是什么。
- 痛点词：解决什么问题。
- 场景词：在哪里用。
- 人群词：谁会买。
- 竞品词：谁在卖类似产品。

## 记录字段

```json
{
  "platform": "",
  "url": "",
  "title": "",
  "creator": "",
  "keyword": "",
  "local_file": "",
  "frame_dir": "",
  "analysis_file": "",
  "screenshot": "",
  "metrics": {
    "views": "",
    "likes": "",
    "comments": "",
    "shares": "",
    "collects": ""
  },
  "duration": "",
  "published_at": "",
  "hook": "",
  "main_selling_point": "",
  "scene": "",
  "cta": "",
  "why_reference": "",
  "notes": ""
}
```

## 排序规则

优先级：

1. 热度高：点赞、播放、评论、分享、收藏。
2. 相关度高：标题、钩子、卖点、场景和商品一致。
3. 可借鉴：前 3 秒有钩子，商品露出清楚，节奏适合信息流广告。
4. 风险低：不依赖未授权人物、音乐、品牌素材或夸张功效表达。

使用脚本：

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

## 输出

- `references/hot_video_search_plan.json`
- `references/youtube_fetch_<timestamp>.json`
- `references/hot_video_seed_import.json`
- `references/hot_video_candidates.json`
- `analysis/hot_video_ranking.json`
- `videos/<video>.mp4`
- `frames/<video>/frame_001.jpg`
- `analysis/hot_video_media_<video>.json`
- `references/hot_video_references.json`

输出后进入 `reference_analysis` 阶段，拆解排名最高的 5-10 条。

## 已跑通的公开抓取

YouTube 公开搜索可以用 `yt-dlp` 抓元数据，不下载视频文件：

```bash
python scripts/hot_video_search.py fetch-youtube --project . --query "portable blender review" --count 8
python scripts/hot_video_search.py rank --project .
python scripts/hot_video_search.py export-references --project . --top 5
```

能抓到的字段通常包括：

- 链接
- 标题
- 作者
- 播放数
- 点赞数
- 评论数
- 时长
- 发布时间

这个链路适合作为公开参考的第一版验证。抖音、小红书、TikTok 普通内容页仍可能需要登录态，不能按 YouTube 的成功情况直接假设也能抓。

## 下载和视频级分析

真正拆解画面、节奏和口播前，必须先把视频下载到本地：

```bash
python scripts/hot_video_search.py download --project . --top 1
```

也可以直接下载用户给的公开链接：

```bash
python scripts/hot_video_search.py download --project . --url "https://..." --title "参考视频标题"
```

下载成功后输出：

- `videos/<video>.mp4`：本地视频文件。
- `frames/<video>/frame_001.jpg`：按间隔抽出的画面帧。
- `analysis/hot_video_media_<video>.json`：视频参数、帧数、是否有音轨、分析范围。

规则：

- `download_status=downloaded` 才能进入视频级拆解。
- 没有音轨时，`analysis_scope=visual_only`，只能做画面拆解。
- 下载失败、要求登录或平台限制时，记录错误原因，不能把链接级参考写成视频级分析。
- 下载的视频只作为参考拆解缓存，不等于获得素材授权。

已验证限制：

- `yt-dlp` 可以识别 TikTok 单条视频、用户页等提取器。
- `https://www.tiktok.com/search/video?q=...` 这种普通搜索页当前不能直接用 `yt-dlp` 抓，返回不支持该 URL。

## 内置种子库

当平台抓取失败、没有登录态，或商品还没有外部参考时，可以先导入内置结构种子：

```bash
python scripts/hot_video_search.py seed --project . --count 6
```

内置种子会写入 `references/hot_video_candidates.json`，并标记：

```json
{
  "source_type": "built_in_seed",
  "platform": "内置种子库"
}
```

内置种子不是实时高赞数据，只能作为脚本和镜头结构参考。后续录入真实平台链接和热度数据后，应以真实候选为准。
