# AI 信息流广告 Skill

这个 Skill 用来把商品资料变成信息流广告工作流：搜索参考广告、拆解脚本、重写原创广告、生成即梦提示词，并支持 Loop 复盘和定时跑批。

## 一条命令安装

如果仓库是公开的：

```bash
curl -fsSL https://raw.githubusercontent.com/huangbai-AI/ai-feed-ad-skill/main/install.sh | bash
```

如果仓库还是私有的，需要对方先有仓库权限并登录 GitHub：

```bash
tmp="$(mktemp -d)" && gh repo clone huangbai-AI/ai-feed-ad-skill "$tmp/ai-feed-ad-skill" -- --depth 1 && bash "$tmp/ai-feed-ad-skill/install.sh"
```

默认安装到：

```text
~/.codex/skills/ai-feed-ad-skill
```

## 核心流程

1. 整理商品资料
2. 搜索同类参考广告
3. 搜索同类高赞视频并排序
4. 拆解参考广告/高赞视频
5. 重写原创广告脚本
6. 拆分镜头和即梦提示词
7. 调用即梦 CLI 生成样片
8. 质量检测，不合格则 Loop 重试
9. 需要持续生产时启用定时任务
10. 样片通过后批量生成候选并择优

## 主要文件

- `SKILL.md`：Skill 主说明
- `templates/`：商品资料、参考搜索、高赞视频搜索、脚本、镜头、Loop、定时任务、分阶段、批量候选模板
- `scripts/`：项目状态、同类高赞视频搜索、即梦生成、质量检测、Loop、定时任务、阶段控制、批量候选脚本
- `references/`：参考广告平台说明

## 常用命令

```bash
python scripts/project_state.py init --project ./demo --product-name "便携榨汁杯"
python scripts/workflow_stage.py plan --project ./demo --stop-at shot_prompt
python scripts/hot_video_search.py plan --project ./demo
python scripts/hot_video_search.py fetch-youtube --project ./demo --query "portable blender review" --count 8
python scripts/hot_video_search.py download --project ./demo --top 1
python scripts/hot_video_search.py download --project ./demo --url "https://..." --title "参考视频标题"
python scripts/hot_video_search.py seed --project ./demo --count 6
python scripts/hot_video_search.py add --project ./demo --platform 小红书 --url "..." --title "..." --likes 12000 --views 200000
python scripts/hot_video_search.py rank --project ./demo
python scripts/hot_video_search.py export-references --project ./demo --top 5
python scripts/quality_check.py --project ./demo --video ./demo/outputs/demo.mp4
python scripts/loop_controller.py --project ./demo --max-retries 3
python scripts/batch_variants.py plan --project ./demo --count 9
python scripts/batch_variants.py rank --project ./demo
python scripts/scheduler.py --project ./demo --interval-minutes 15
```

如果即梦返回 `current account is not maestro vip`，说明当前账号没有 CLI 生成权限，流程会暂停，不会反复重试。
