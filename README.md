# AI 信息流广告 Skill

这个 Skill 用来把商品资料变成信息流广告工作流：搜索参考广告、拆解脚本、重写原创广告、生成即梦提示词，并支持 Loop 复盘和定时跑批。

## 核心流程

1. 整理商品资料
2. 搜索同类参考广告
3. 拆解参考广告
4. 重写原创广告脚本
5. 拆分镜头和即梦提示词
6. 调用即梦 CLI 生成样片
7. 质量检测，不合格则 Loop 重试
8. 需要持续生产时启用定时任务
9. 样片通过后批量生成候选并择优

## 主要文件

- `SKILL.md`：Skill 主说明
- `templates/`：商品资料、参考搜索、脚本、镜头、Loop、定时任务、分阶段、批量候选模板
- `scripts/`：项目状态、即梦生成、质量检测、Loop、定时任务、阶段控制、批量候选脚本
- `references/`：参考广告平台说明

## 常用命令

```bash
python scripts/project_state.py init --project ./demo --product-name "便携榨汁杯"
python scripts/workflow_stage.py plan --project ./demo --stop-at shot_prompt
python scripts/quality_check.py --project ./demo --video ./demo/outputs/demo.mp4
python scripts/loop_controller.py --project ./demo --max-retries 3
python scripts/batch_variants.py plan --project ./demo --count 9
python scripts/batch_variants.py rank --project ./demo
python scripts/scheduler.py --project ./demo --interval-minutes 15
```

如果即梦返回 `current account is not maestro vip`，说明当前账号没有 CLI 生成权限，流程会暂停，不会反复重试。
