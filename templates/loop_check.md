# Loop 循环检测模板

Loop 只处理重大错误，不负责提升广告表现。它不重新发明整条广告，只根据重大错误检测结果修正失败镜头。

## 输入

- `project.json`
- `analysis/quality_check.json`
- 原镜头提示词，通常在 `shots/`
- 商品资料和已选广告类型

## 判定

```json
{
  "overall": "pass / retry / manual_review",
  "review_mode": "major_defect_only",
  "retry_targets": [
    {
      "shot_id": "shot_001",
      "problem_key": "human_body_defect / product_mismatch / human_inconsistent / product_lost_or_deformed / visual_text_defect / fabricated_claim",
      "problem": "",
      "change_needed": ""
    }
  ]
}
```

## 规则

- `pass`：停止 Loop，进入交付或批量扩展。
- `retry`：只重写失败镜头提示词，默认最多重试 3 次。
- `manual_review`：涉及商品事实、授权、价格销量、认证、医疗功效或账号权限时暂停。
- 弱钩子、弱 CTA、广告感不强、卖点不够锋利，不触发自动重试。
- 重试提示词只修失败点，保持原商品、人物、场景和脚本方向。
- 同一份重大错误检测已经处理过时，等待新视频或新检测；需要强制重跑才加 `--force`。
- 即梦返回 `current account is not maestro vip` 时立即暂停，不要重复提交。
- 每轮 Loop 都要写入 `loop_runs/`，并刷新 `analysis/result_report.json`。

## 执行

```bash
python scripts/quality_check.py --project . --video outputs/demo.mp4
# 填写 analysis/quality_check.json 后执行：
python scripts/loop_controller.py --project . --max-retries 3

# 如果要自动提交重试生成：
python scripts/loop_controller.py --project . --max-retries 3 --submit --duration 10
```
