# 定时任务模板

定时任务用于“持续生产”和“持续复盘”，不是默认开启。只有用户明确说要定时、持续跑、24 小时生产时才启动。

## 默认设置

- 默认每 15 分钟检查一次。
- 默认只推进没有完成、没有暂停的项目。
- 默认不自动提交即梦生成；需要自动提交时加 `--submit-loop`。
- 遇到账号权限、合规风险、商品事实不确定时暂停。
- 同一份重大错误检测已经处理过后，等待新生成结果或新的检测文件，不重复消耗重试次数。

## 适合做什么

- 定时检查某个商品项目是否有新的重大错误检测结果。
- 有重大错误 `retry` 结果时，自动生成重试提示词。
- 用户允许时，自动提交失败镜头重新生成。
- 多商品项目放在一个目录里时，按队列逐个检查。

## 不适合做什么

- 不绕过平台登录或下载限制。
- 不在没有商品资料、没有参考广告、没有重大错误检测结果时硬跑生成。
- 不在即梦账号没有 CLI 权限时反复提交。

## 执行

单次检查：

```bash
python scripts/scheduler.py --project . --once
```

每 15 分钟持续检查：

```bash
python scripts/scheduler.py --project . --interval-minutes 15
```

检查一个项目目录下的多个商品：

```bash
python scripts/scheduler.py --project-root /path/to/projects --interval-minutes 15
```

允许 Loop 自动提交重试生成：

```bash
python scripts/scheduler.py --project . --interval-minutes 15 --submit-loop --max-retries 3
```
