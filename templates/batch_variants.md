# 批量候选和择优模板

样片通过后，再进入批量候选。不要一次性随机生成很多条，而是围绕“子类型、钩子、主卖点、表达方式、行动引导”做可比较的候选。

默认变体必须从 `templates/reference_script_library.md` 的正式小类里选，不允许使用待反推小类。

默认变体：

- 3 个开场钩子
- 3-9 个有来源编号的生产小类
- 2 个主卖点角度
- 2 种结尾行动引导

默认先生成 9 个候选，跑完后打分排序，选出 1-3 个继续精修。

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
      "scores": {
        "hook": null,
        "product_visibility": null,
        "selling_point": null,
        "feed_ad_feeling": null,
        "cta": null,
        "policy_risk": null
      }
    }
  ]
}
```

## 评分规则

- `hook`：前 3 秒是否有痛点、结果或反差。
- `product_visibility`：商品是否清楚出现，外观是否一致。
- `selling_point`：是否只讲一个主卖点。
- `feed_ad_feeling`：是否像真实信息流广告。
- `cta`：行动引导是否清楚。
- `policy_risk`：风险分，越高越差。
- `source_id_valid`：是否能在 `reference_script_library.md` 中找到对应来源编号。找不到直接淘汰。

总分：

```text
hook * 0.25
+ product_visibility * 0.25
+ selling_point * 0.20
+ feed_ad_feeling * 0.20
+ cta * 0.10
- policy_risk * 0.30
```

## 执行

```bash
python scripts/batch_variants.py plan --project . --count 9
# 人工或 Agent 看完候选视频后，填写 analysis/batch_variants.json 里的 scores
python scripts/batch_variants.py rank --project .
```

择优后，只继续精修分数最高的 1-3 个候选，不要平均消耗生成额度。
