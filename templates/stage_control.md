# 分阶段运行模板

分阶段运行用于“只做到某一步就停”，方便调试和复用中间产物。

## 常见 stop-at

- `production_type`：只整理商品资料并选择剧情广告 / 品牌大片 / 达人带货。
- `ad_script`：只生成广告脚本。
- `shot_prompt`：只生成即梦镜头提示词。
- `dreamina_generate`：生成样片后停，不自动 Loop。
- `async_query`：只查询已经提交的即梦任务，不重复提交。
- `quality_check`：生成质量检查后停，等人工确认。
- `batch_variants`：样片通过后，进入批量候选和择优。

可选参考阶段，只有用户明确要求搜索或复刻时才用：

- `reference_search`：只找参考广告，不写脚本。
- `hot_video_search`：只找同类高赞视频并排序，不写脚本。
- `reference_analysis`：只拆解参考广告。

## 执行

```bash
python scripts/workflow_stage.py plan --project . --stop-at shot_prompt
python scripts/workflow_stage.py mark --project . --stage product_brief --status complete
python scripts/workflow_stage.py next --project .
python scripts/workflow_stage.py status --project .
```

## 规则

- 到达 `stop_at` 后必须停下，不继续提交即梦生成。
- 每个阶段都要留下可复用产物，放在 `analysis/`、`scripts/`、`shots/` 或 `references/`。
- 用户只要求前半段时，不要擅自进入生成阶段。
- 默认不执行参考搜索或高赞视频抓取；抓取只作为用户明确要求时的可选阶段。
- 高赞视频只完成元数据抓取时，不要写成已完成视频级拆解；下载成功并抽帧后才进入画面分析。
- 即梦返回 `Queueing/querying` 时，记录 `submit_id` 和队列状态即可，不要重复提交同一条。
