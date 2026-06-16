# 批量候选和择优模板

样片通过后，再进入批量候选。候选只做可比较的方向变化，不做复杂评分。

默认变体必须从 `templates/reference_script_library.md` 的正式小类里选，不允许使用待反推小类。

默认先生成 6-9 个候选。看完候选后，只填写下面五个字段：

- `usable`：能否继续精修或投放测试。
- `major_defect`：是否存在重大错误。
- `product_consistent`：商品颜色、形状、包装、材质是否一致。
- `human_consistent`：人物是否前后一致，身体结构是否正常。
- `manual_pick`：人工是否选中。

输出格式：

```json
{
  "base_script": "",
  "variants": [
    {
      "variant_id": "v001",
      "production_type": "剧情广告 / 品牌大片 / 达人带货",
      "production_subtype": "",
      "source_id": "",
      "hook": "",
      "main_change": "",
      "shots_to_regenerate": [],
      "expected_use": "",
      "prompt_file": "",
      "review": {
        "usable": null,
        "major_defect": null,
        "product_consistent": null,
        "human_consistent": null,
        "manual_pick": null,
        "notes": ""
      }
    }
  ]
}
```

择优规则：

- `manual_pick=true` 且没有重大错误，优先入选。
- 没有人工选择时，选 `usable=true`、`major_defect=false`、`product_consistent=true`、`human_consistent=true` 的候选。
- `source_id` 找不到真实参考脚本来源时直接淘汰。
- 有重大错误的候选不进入精修。

## 执行

```bash
python scripts/batch_variants.py plan --project . --count 9
# 人工或 Agent 看完候选视频后，填写 analysis/batch_variants.json 里的 review
python scripts/batch_variants.py rank --project .
```
