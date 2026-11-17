# 直播第三防线（Abasthan 后台 Worker 版）

每 10 分钟查 12 个抖音号有没有开播，有人刚开播就发邮件提醒。

## 怎么跑

Abasthan 上建 Background Worker（仪表盘里没有 Cron Job 入口，定时任务建不了）：

- Runtime：Python 3.12
- Start Command：`python check_all_live_ab.py`
- 环境变量：`AB_LOOP=1`（常驻循环模式，每 10 分钟查一轮）、`ALERT_EMAIL`（收提醒的邮箱，必填，在仪表盘里设，不写进仓库）
- 套餐：Free（每账号只有 1 个免费名额）

## 文件

- `check_all_live_ab.py`：巡查脚本，纯标准库，不依赖第三方包
- `requirements.txt`：空的，只为让平台识别成 Python 项目

## 关键点

- 原理：先拿 ttwid，再调抖音 profile/other 接口读 live_status（1=开播，0=没播）。
- 状态记在脚本同目录的 `ab_live_state.json`，只在“刚开播”时发一次邮件，开着不重复发。
- 夜间 02:00–08:30（北京时间）不查，脚本里自带。
- 提醒走 formsubmit 发到 ALERT_EMAIL 里设的邮箱（该地址已在 LightVela 线激活过，直接通），标题 `AB开播提醒 <昵称>`。
- 提醒邮件要进现有处理流程：VM 上的 lv-alert-hook 目前只认 `LV开播提醒` 标题，AB 上线后要把查询改成两个标题都认，并按邮件正文的“来源”字段报第几防线。
- 开关可用环境变量覆盖：AB_TEST=1（只打印不发邮件）、AB_TEST_EMAIL=1（多发一封测试邮件）、AB_CLEAR_STATE=1（清掉旧状态）。

## 本地试跑

```bash
AB_TEST=1 python3 check_all_live_ab.py   # 只跑一轮，不发邮件
AB_LOOP=1 python3 check_all_live_ab.py   # 常驻循环
```
