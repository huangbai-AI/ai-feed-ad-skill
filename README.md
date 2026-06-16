# AI 信息流广告 Skill

这个 Skill 用来把商品资料变成 AI 带货广告工作流：选择剧情广告 / 品牌大片 / 达人带货及其有真实视频依据的小类，重写脚本，生成即梦提示词，并支持 Loop 复盘和定时跑批。

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
2. 选择生产大类和有来源编号的小类
3. 重写原创广告脚本
4. 拆分镜头和即梦提示词
5. 调用即梦 CLI 生成样片
6. 生成排队时记录任务并异步查询
7. 质量检测，不合格则 Loop 重试
8. 需要持续生产时启用定时任务
9. 样片通过后批量生成候选并择优

参考搜索和高赞视频抓取已改为可选流程，只有用户明确要求时才跑。

正式小类必须先在 `templates/reference_script_library.md` 里有真实素材依据和参考脚本。当前默认库：

- 剧情广告：情感反转剧情（LD-01）
- 品牌大片：产品英雄广告（LV-05）、电影感 TV 广告（LV-06）、时尚生活方式跟拍（LV-08）
- 达人带货：UGC 手持口播展示（LV-01）、开箱揭晓（LV-02）、使用场景证明（LV-03）、试穿前后变化（LV-04）、俯拍 ASMR 开箱（LV-07）

飞书文档中出现但还没有完成视频反推的“宫廷斗心机、霸总、重生、武侠、宫斗”等，只能作为待反推方向，不进入默认生成。

## 主要文件

- `SKILL.md`：Skill 主说明
- `templates/`：商品资料、真实视频参考脚本库、参考搜索、高赞视频搜索、脚本、镜头、Loop、定时任务、分阶段、批量候选模板
- `scripts/`：项目状态、同类高赞视频搜索、即梦生成、质量检测、Loop、定时任务、阶段控制、批量候选脚本
- `references/`：参考广告平台说明

## 常用命令

```bash
python scripts/project_state.py init --project ./demo --product-name "便携榨汁杯"
python scripts/workflow_stage.py plan --project ./demo --stop-at shot_prompt
python scripts/dreamina_generate.py multimodal2video --project ./demo --image ./demo/product/main.png --prompt-file ./demo/shots/shot_001.txt --duration 10 --ratio 9:16 --model-version seedance2.0fast
python scripts/dreamina_generate.py query --project ./demo --submit-id "<id>"
python scripts/quality_check.py --project ./demo --video ./demo/outputs/demo.mp4
python scripts/loop_controller.py --project ./demo --max-retries 3
python scripts/batch_variants.py plan --project ./demo --count 9
python scripts/batch_variants.py rank --project ./demo
python scripts/scheduler.py --project ./demo --interval-minutes 15
```

如果即梦返回 `current account is not maestro vip`，说明当前账号没有 CLI 生成权限，流程会暂停，不会反复重试。
