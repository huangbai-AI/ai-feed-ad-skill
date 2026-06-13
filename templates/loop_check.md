# Loop 循环检测模板

Loop 用在“已经生成样片或镜头片段之后”。它不重新发明整条广告，只根据质量检测结果修正失败镜头。

## 输入

- `project.json`
- `analysis/quality_check.json`
- 原镜头提示词，通常在 `shots/`
- 参考广告拆解和商品资料

## 判定

```json
{
  "overall": "pass / retry / manual_review",
  "problems": [],
  "retry_targets": [
    {
      "shot_id": "shot_001",
      "problem": "",
      "change_needed": ""
    }
  ]
}
```

## 规则

- `pass`：停止 Loop，进入交付或批量扩展。
- `retry`：只重写失败镜头提示词，默认最多重试 3 次。
- `manual_review`：涉及合规、商品事实、品牌授权或账号权限时暂停。
- 前 3 秒没有钩子、商品不清楚、画面不像信息流广告，必须重试。
- 即梦返回 `current account is not maestro vip` 时立即暂停，不要重复提交。
- 每轮 Loop 都要写入 `loop_runs/`，方便回看为什么重试。

## 执行

```bash
python scripts/quality_check.py --project . --video outputs/demo.mp4
# 填写 analysis/quality_check.json 后执行：
python scripts/loop_controller.py --project . --max-retries 3

# 如果要自动提交重试生成：
python scripts/loop_controller.py --project . --max-retries 3 --submit --duration 5
```
