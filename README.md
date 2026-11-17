# 直播第四防线（Abasthan 常驻版）+ 微博动态巡查

哨兵 4 个号（坏坏哦小号/板栗饼/余霜/小钰）每 2 分钟查一轮，12 个号每 10 分钟全查一轮，有人刚开播就发邮件提醒。微博 8 个号每 10 分钟查一轮（跟直播全量同一轮），有新帖发邮件提醒。

## 怎么跑

Abasthan 上建 Web Service：

- Runtime：Python 3.12
- Start Command：`python check_all_live_ab.py`
- 环境变量：`AB_LOOP=1`（常驻循环模式，哨兵每 2 分钟一轮、全量每 10 分钟一轮）、`ALERT_EMAIL`（收提醒的邮箱，必填，在仪表盘里设，不写进仓库）、`AB_WEIBO_SUB` / `AB_WEIBO_SUBP` / `AB_WEIBO_TWM`（微博登录态，仪表盘里设，不写进仓库；没设时微博巡查自动跳过，不影响直播）
- 脚本自带健康检查服务（`/` 和 `/health` 回 ok），供平台探活

为什么是 Web Service：仪表盘里没有 Cron Job 入口，定时任务建不了；Background Worker 也建不了——2026-11-17 两次提交都报平台错误 `E11000 duplicate key error ... subdomain_1 dup key: { subdomain: null }`，是平台的 bug，只能等它修或等删掉的应用记录清干净再试。Web Service 会分到一个真实子域名，绕开这个错。
- 套餐：Free（每账号只有 1 个免费名额）

## 文件

- `check_all_live_ab.py`：巡查脚本，纯标准库，不依赖第三方包
- `requirements.txt`：空的，只为让平台识别成 Python 项目

## 关键点

- 原理：先拿 ttwid，再调抖音 profile/other 接口读 live_status（1=开播，0=没播）。
- 状态记在脚本同目录的 `ab_live_state.json`，只在“刚开播”时发一次邮件，开着不重复发。
- 夜间 02:00–08:30（北京时间）不查，脚本里自带。
- 提醒走 formsubmit 发到 ALERT_EMAIL 里设的邮箱（该地址已在 LightVela 线激活过，直接通），标题 `AB开播提醒 <昵称>`。
- 提醒邮件已进现有处理流程：VM 上的 lv-alert-hook 查询已改成 LV/AB 两个标题都认，AB 的报「第四防线(Abasthan)」。
- 微博巡查（2026-11-17 22:36 加）：手机端 getIndex 接口查 8 个号最新帖 ID，只 SUB+SUBP 就够（不用短 token）；状态记 `ab_weibo_state.json`；有新帖发邮件，标题 `AB微博新帖提醒 <昵称>`；夜间 02:00–08:30 只查余霜/小钰；潮汐（ok=0）和 king（无帖子卡片）是账号本身问题，查不到就跳过。提醒邮件要进动态线处理流程（VM 上需建 lv-weibo-alert-hook 的 AB 版或把查询改成两个标题都认）。
- 测试开关（TEST/TEST_EMAIL/CLEAR_STATE）只能改代码里的常量，不读环境变量——Abasthan 删了的环境变量在容器里清不掉，2026-11-17 AB_TEST_EMAIL 因此每轮误发测试邮件。

## 本地试跑

```bash
python3 check_all_live_ab.py             # 只跑一轮全量（要测不发邮件，先把代码里 TEST 改成 True）
AB_LOOP=1 python3 check_all_live_ab.py   # 常驻循环
```
