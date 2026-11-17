# 直播第四防线（Abasthan 常驻版）+ 微博动态巡查（2026-11-17 22:36 加，Aw 令“都试试”第二项）
# 12 个号一个脚本查完：哨兵 4 个（坏坏哦小号/板栗饼/余霜/小钰）每 2 分钟查一轮，12 个号每 10 分钟全查一轮；开播才发邮件，没开播不发
# 微博：8 个号每 10 分钟查一轮（跟直播全量同一轮），手机端 getIndex 接口，只 SUB+SUBP 就够；有新帖发邮件提醒
# 原理：ttwid + profile/other 接口读 live_status（1=开播，0=没播）
# 状态记在脚本同目录的 ab_live_state.json；只在“刚开播”时发一次邮件，开着就不重复发
# 注意：状态记在容器里的 ab_live_state.json；服务重启/重新部署后状态可能丢，启动时会打印 state file 是否存在、几条
# 发邮件走 formsubmit 免注册接口，目标是 Aw 的新号 Gmail（该地址已在 LightVela 线激活过，直接通）
# formsubmit ajax 必须带 Referer 头（https://formsubmit.co/），不带会被拒（"HTML files" 报错）；Origin 头没用
# TEST 模式不写状态文件（免得测试把“在播”记进去，正式跑时漏发提醒）；CLEAR_STATE 一次性清掉旧状态
# 每号只查一次不重试，每轮 300 秒没查完就停下（已查的照常记状态、照常发邮件）
# 测试开关（TEST/TEST_EMAIL/CLEAR_STATE）只能改上面代码里的常量，不读环境变量——
# Abasthan 删了的环境变量在容器里清不掉，2026-11-17 AB_TEST_EMAIL 因此每轮误发测试邮件
# AB_LOOP=1：常驻循环模式（Web Service 用，哨兵每 2 分钟一轮、全量每 10 分钟一轮）；不设则只跑一轮全量退出
# 循环模式会同时起一个极简 HTTP 健康检查服务（0.0.0.0:$PORT，默认 8080，/ 和 /health 返回 ok），供平台探活；单轮模式不起
# 微博 SUB/SUBP/_T_WM 从环境变量 AB_WEIBO_SUB / AB_WEIBO_SUBP / AB_WEIBO_TWM 读，绝不写进代码（仓库是公开的）

TEST = False        # True：只打印、不真发邮件（测 12 个号能不能查完）；确认后改 False
TEST_EMAIL = False  # True：额外发一封测试邮件，验证发信通不通；确认后改 False
CLEAR_STATE = False  # True：本轮开始先清掉旧状态文件；正式跑时改 False

ALERT_EMAIL = ""  # 收提醒的邮箱：部署时在环境变量里设 ALERT_EMAIL，不写进仓库
TIME_BUDGET = 300   # 秒，每轮查到这里就停（单轮模式沿用 LightVela 的 45 秒太紧，循环模式无 60 秒硬上限）

ACCOUNTS = [
    ("bkppszd111_", "MS4wLjABAAAAZj_-JgiSed_n6TT0vCDCzN06lOOZlEwRFcT696-5d7k"),
    ("zrdxg194", "MS4wLjABAAAAd4ep3zsH7R4v5qVdTIjuShPkbcEY3wQzVnZIOL96MNgp9gJHLGLKG7wG0WaVtLUI"),
    ("233233yushuang", "MS4wLjABAAAAVrH2D40qUk3Uc3sHeX9nUXRSpQJ0b_1gOxombYt5H1g"),
    ("364604220", "MS4wLjABAAAA33EKT7bm7FbBCsw4kZ3qIW6-nVI2PLTt-mmhpK81nxI"),
    ("ychyyds", "MS4wLjABAAAAeuxccY16kVoMGC5Nq1SWGp849NPND1N21TVzzlf8W_Y"),
    ("98476067049", "MS4wLjABAAAAHi-j0z1onA6Du9acM9eCjatspsk3CxnmC2nnpo3TXPIIGB3Oov1p7Pbno9prnGEl"),
    ("kkiou", "MS4wLjABAAAAI6YGBRshI6QNbur7Wy7eIQ_ddUPWDE0H0J3_ElUfHbM"),
    ("lllita0999", "MS4wLjABAAAAoTrb7XTjFGF2d0NYxYb3Uhi8KNNxjzD6iABNGeE5414"),
    ("Fffc_729", "MS4wLjABAAAAUe0a32ru2B0xO8fQcEczLfYJhT2Kl0kiYID1Lw_rhdk"),
    ("GuGu614", "MS4wLjABAAAAc9xJBu_GI5mOuVOokDa6G3oFAZGZrkL-b55VAyuO54PYONCa8-vVr6aebYs59hKz"),
    ("921065800t", "MS4wLjABAAAADmLktPKlMQ1Cp_00rNSXlE5862hvN7UnnC_FUxNW_qZ9hGTyRhUmrZbKAjanVnBX"),
    ("27026498843", "MS4wLjABAAAAFelfAwyh8sp0mFd4xfLeBGzT2zr1JBLRWlzjux3Taz4LZFdow7VLeOfptuQZQYpc"),
]

REGISTER_URL = "https://ttwid.bytedance.com/ttwid/union/register/"
FORMSUBMIT_URL = "https://formsubmit.co/ajax/" + ALERT_EMAIL

# 微博动态巡查（2026-11-17 22:36 加）：8 个号，手机端 getIndex 接口
WEIBO_ACCOUNTS = [
    ("余霜YSCandice", "1907518591"),
    ("小钰_Hilda", "1779654914"),
    ("解说Kitty", "7596025298"),
    ("潮汐海灵小桃人", "6911598452"),
    ("小珠桃子一米七", "1885411364"),
    ("柏崎奈肉", "8330657003"),
    ("宝石之星露比拉布拉", "6649052727"),
    ("喵喵喵喵king", "7544111288"),
]
WEIBO_NIGHT_ONLY = {"1907518591", "1779654914"}  # 夜间 02:00-08:30 只查余霜/小钰（跟动态线夜里规则一致）
WEIBO_UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
WEIBO_TIME_BUDGET = 45  # 秒，微博一轮查到这里就停

import json
import os
import time
import urllib.request
import urllib.error
import http.client
import http.cookiejar
from datetime import datetime, timezone, timedelta

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

# 状态文件放在脚本同目录；ALERT_EMAIL / AB_LOOP 仍走环境变量（部署时设，不写进仓库）
STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ab_live_state.json")
ALERT_EMAIL = os.environ.get("ALERT_EMAIL", ALERT_EMAIL)
FORMSUBMIT_URL = "https://formsubmit.co/ajax/" + ALERT_EMAIL

# 微博状态文件 + 登录态（环境变量，绝不写进代码；没设 AB_WEIBO_SUB 时微博巡查自动跳过，不影响直播）
WEIBO_STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ab_weibo_state.json")
WB_SUB = os.environ.get("AB_WEIBO_SUB", "")
WB_SUBP = os.environ.get("AB_WEIBO_SUBP", "")
WB_TWM = os.environ.get("AB_WEIBO_TWM", "")
WB_COOKIE = "SUB=%s; SUBP=%s; _T_WM=%s" % (WB_SUB, WB_SUBP, WB_TWM) if WB_SUB else ""


def now_str():
    return datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S")


def read_body(resp):
    try:
        return resp.read()
    except http.client.IncompleteRead as e:
        return e.partial


def get_ttwid(opener, jar):
    for _ in range(2):
        try:
            req = urllib.request.Request(
                REGISTER_URL,
                data=json.dumps({"service": "www.douyin.com", "union": True, "aid": 6383}).encode(),
                headers={"Content-Type": "application/json", "User-Agent": UA},
                method="POST")
            with opener.open(req, timeout=10) as r:
                d = json.loads(read_body(r).decode("utf-8", "ignore"))
            redir = d.get("redirect_url") or ""
            if not redir:
                continue
            req2 = urllib.request.Request(redir, headers={"User-Agent": UA})
            with opener.open(req2, timeout=10) as r2:
                read_body(r2)
            if any(c.name == "ttwid" for c in jar):
                return True
        except Exception:
            time.sleep(2)
    return False


def check_one(opener, sec_uid):
    url = ("https://www.douyin.com/aweme/v1/web/user/profile/other/"
           "?device_platform=webapp&aid=6383&channel=channel_pc_web&sec_user_id=" + sec_uid)
    req = urllib.request.Request(
        url, headers={"User-Agent": UA, "Referer": "https://www.douyin.com/user/" + sec_uid})
    with opener.open(req, timeout=6) as r:
        body = read_body(r)
    if not body:
        raise ValueError("empty body")
    d = json.loads(body.decode("utf-8", "ignore"))
    u = d.get("user") or {}
    if "live_status" not in u:
        raise ValueError("no live_status (status_code=%s)" % d.get("status_code"))
    return u.get("live_status"), u.get("nickname")


def load_state():
    try:
        with open(STATE_FILE) as f:
            s = json.load(f)
        return s if isinstance(s, dict) else {}
    except Exception:
        return {}


def save_state(state):
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, ensure_ascii=False)
    except Exception as e:
        print("save state ERR: %s" % e)


def send_alert(nick, douyin_id, test=False):
    subject = "AB开播提醒 %s" % ("测试" if test else nick)
    payload = {
        "_subject": subject,
        "_template": "table",
        "昵称": nick,
        "抖音号": douyin_id,
        "发现时间": now_str(),
        "来源": "Abasthan第四防线",
    }
    if test:
        payload["备注"] = "这是一封测试邮件，验证发信通不通，不是真开播"
    req = urllib.request.Request(
        FORMSUBMIT_URL,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": UA,
                 "Referer": "https://formsubmit.co/"},
        method="POST")
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.status, read_body(r).decode("utf-8", "ignore")[:200]


def load_weibo_state():
    try:
        with open(WEIBO_STATE_FILE) as f:
            s = json.load(f)
        return s if isinstance(s, dict) else {}
    except Exception:
        return {}


def save_weibo_state(state):
    try:
        with open(WEIBO_STATE_FILE, "w") as f:
            json.dump(state, f, ensure_ascii=False)
    except Exception as e:
        print("save weibo state ERR: %s" % e)


def check_weibo_one(uid):
    """手机端 getIndex，返回最新 10 条帖 ID 列表。ok=0（潮汐）或无帖子卡片（king）抛 ValueError 由调用方跳过；418/截断重试 1 次。"""
    url = "https://m.weibo.cn/api/container/getIndex?type=uid&value=%s&containerid=107603%s" % (uid, uid)
    headers = {"User-Agent": WEIBO_UA, "Referer": "https://m.weibo.cn/", "Cookie": WB_COOKIE,
               "Accept": "application/json, text/plain, */*"}
    for attempt in range(2):
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=8) as r:
                body = read_body(r)
        except urllib.error.HTTPError as e:
            if e.code == 418 and attempt == 0:
                time.sleep(5)
                continue
            raise
        try:
            d = json.loads(body.decode("utf-8", "ignore"))
        except json.JSONDecodeError:
            # 响应被截断（大包偶发），重试一次
            if attempt == 0:
                time.sleep(2)
                continue
            raise
        if d.get("ok") != 1:
            raise ValueError("ok=%s msg=%s" % (d.get("ok"), (d.get("msg") or "")[:20]))
        cards = (d.get("data") or {}).get("cards") or []
        ids = []
        for c in cards:
            m = c.get("mblog") or {}
            mid = m.get("id")
            if mid:
                ids.append(str(mid))
            if len(ids) >= 10:
                break
        if not ids:
            raise ValueError("no mblog ids in cards")
        return ids
    raise ValueError("418 retry failed")


def send_weibo_alert(nick, uid, post_id):
    subject = "AB微博新帖提醒 %s" % nick
    payload = {
        "_subject": subject,
        "_template": "table",
        "昵称": nick,
        "微博UID": uid,
        "新帖ID": post_id,
        "帖子链接": "https://weibo.com/%s/%s" % (uid, post_id),
        "发现时间": now_str(),
        "来源": "Abasthan微博巡查",
    }
    req = urllib.request.Request(
        FORMSUBMIT_URL,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": UA,
                 "Referer": "https://formsubmit.co/"},
        method="POST")
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.status, read_body(r).decode("utf-8", "ignore")[:200]


def weibo_main():
    """微博动态巡查一轮：查 8 个号最新帖 ID，有新帖发邮件。没设 AB_WEIBO_SUB 时跳过（不报错，不影响直播）。"""
    if not WB_SUB:
        print("[weibo] skipped: AB_WEIBO_SUB not set")
        return 0
    if not ALERT_EMAIL and not TEST:
        print("[weibo] FAIL: ALERT_EMAIL env not set")
        return 1
    now = datetime.now(timezone(timedelta(hours=8)))
    mins = now.hour * 60 + now.minute
    night = 120 <= mins < 510
    accounts = [(n, u) for (n, u) in WEIBO_ACCOUNTS if (not night or u in WEIBO_NIGHT_ONLY)]
    if night:
        print("[weibo] night mode: only 2 accounts")
    wb_start = time.time()
    state = load_weibo_state()
    checked = 0
    new_posts = []
    emailed = []
    for i, (nick, uid) in enumerate(accounts):
        if time.time() - wb_start > WEIBO_TIME_BUDGET:
            print("[weibo] time budget hit, stopped after %d accounts" % checked)
            break
        if i > 0:
            time.sleep(1.5)  # 号与号之间停一下，防 418
        try:
            ids = check_weibo_one(uid)
        except Exception as e:
            print("[weibo] %s: check ERR %s: %s" % (nick, type(e).__name__, str(e)[:60]))
            continue
        checked += 1
        latest = ids[0]
        prev = state.get(uid) or {}
        watermark = prev.get("latest") or ""
        if not watermark:
            state[uid] = {"latest": latest, "nick": nick, "updated": now_str()}
            print("[weibo] %s: baseline %s" % (nick, latest))
        elif latest != watermark and int(latest) > int(watermark):
            new_posts.append((nick, uid, latest))
            if TEST:
                print("[weibo] %s: NEW %s (would email, TEST mode)" % (nick, latest))
            else:
                try:
                    code, resp = send_weibo_alert(nick, uid, latest)
                    print("[weibo] %s: NEW %s, email sent code=%s" % (nick, latest, code))
                    emailed.append(nick)
                except Exception as e:
                    print("[weibo] %s: NEW %s, email ERR %s: %s" % (nick, latest, type(e).__name__, str(e)[:80]))
            state[uid] = {"latest": latest, "nick": nick, "updated": now_str()}
        else:
            state[uid] = {"latest": latest, "nick": nick, "updated": now_str()}
            print("[weibo] %s: no new (%s)" % (nick, latest))
        if not TEST:
            save_weibo_state(state)
    print("[weibo] done: checked=%d new=%s emailed=%s elapsed=%.1fs" % (checked, [n for n, _, _ in new_posts], emailed, time.time() - wb_start))
    return 0


def main(sentinel_only=False):
    now = datetime.now(timezone(timedelta(hours=8)))
    mins = now.hour * 60 + now.minute
    if 120 <= mins < 510:
        print("night pause, skip")
        return 0
    round_start = time.time()  # 每轮重设计时（循环模式下不能用进程启动时间，否则第二轮起还没查就超预算）
    if not TEST and not ALERT_EMAIL:
        print("FAIL: ALERT_EMAIL env not set")
        return 1
    if CLEAR_STATE:
        try:
            os.remove(STATE_FILE)
            print("state cleared")
        except FileNotFoundError:
            print("state cleared (no old file)")
        except Exception as e:
            print("clear state ERR: %s" % e)
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    if not get_ttwid(opener, jar):
        print("FAIL: no ttwid")
        return 1
    state = load_state()
    print("state file: exists=%s entries=%d" % (os.path.exists(STATE_FILE), len(state)))
    checked = 0
    live_now = []
    emailed = []
    accounts = ACCOUNTS[:4] if sentinel_only else ACCOUNTS
    for douyin_id, sec_uid in accounts:
        if time.time() - round_start > TIME_BUDGET:
            print("time budget hit, stopped after %d accounts" % checked)
            break
        try:
            live, nick = check_one(opener, sec_uid)
        except Exception as e:
            print("%s: check ERR %s: %s" % (douyin_id, type(e).__name__, str(e)[:60]))
            continue
        checked += 1
        prev = state.get(douyin_id) or {}
        was_live = prev.get("live") is True
        if live == 1:
            live_now.append(nick or douyin_id)
            if not was_live and not prev.get("alerted"):
                if TEST:
                    print("%s: LIVE (would email, TEST mode)" % (nick or douyin_id))
                else:
                    try:
                        code, resp = send_alert(nick or douyin_id, douyin_id)
                        print("%s: LIVE, email sent code=%s resp=%s" % (nick or douyin_id, code, resp[:100]))
                        emailed.append(nick or douyin_id)
                        state[douyin_id] = {"live": True, "alerted": True, "nick": nick, "updated": now_str()}
                    except Exception as e:
                        print("%s: LIVE, email ERR %s: %s" % (nick or douyin_id, type(e).__name__, str(e)[:80]))
                        state[douyin_id] = {"live": True, "alerted": False, "nick": nick, "updated": now_str()}
                    save_state(state)
                    continue
            state[douyin_id] = {"live": True, "alerted": prev.get("alerted", False), "nick": nick, "updated": now_str()}
        else:
            state[douyin_id] = {"live": False, "alerted": False, "nick": nick, "updated": now_str()}
        if not TEST:
            save_state(state)
        print("%s: %s" % (nick or douyin_id, "LIVE" if live == 1 else "not live"))
    if TEST_EMAIL:
        try:
            code, resp = send_alert("测试", "test", test=True)
            print("test email: code=%s resp=%s" % (code, resp[:200]))
        except Exception as e:
            print("test email ERR %s: %s" % (type(e).__name__, str(e)[:120]))
    print("done: [%s] checked=%d live=%s emailed=%s elapsed=%.1fs" % ("sentinel" if sentinel_only else "full", checked, live_now, emailed, time.time() - round_start))
    return 0


def start_health_server():
    # 极简探活服务：只回 ok，让平台知道进程还活着（Web Service 形态部署时需要）
    import threading
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    port = int(os.environ.get("PORT", "8080"))

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            body = b"ok"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    srv = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    print("health server on :%d" % port, flush=True)


def run_loop():
    # 常驻循环模式：每 120 秒一轮；第 0/5/10…轮全查 12 个号，其余轮只查哨兵 4 个号；单轮异常不杀进程
    # 微博巡查跟直播全量同一轮（第 0/5/10…轮，每 10 分钟一次），没设 AB_WEIBO_SUB 时自动跳过
    print("worker start %s (loop: sentinels every 120s, full every 600s)" % now_str(), flush=True)
    start_health_server()
    round_no = 0
    while True:
        try:
            is_full = (round_no % 5 == 0)
            main(sentinel_only=(not is_full))
            if is_full:
                weibo_main()
        except Exception as e:
            print("loop ERR %s: %s" % (type(e).__name__, str(e)[:200]), flush=True)
        round_no += 1
        print("sleep 120s, next run ~%s" % now_str(), flush=True)
        time.sleep(120)


if __name__ == "__main__":
    if os.environ.get("AB_LOOP", "") == "1":
        run_loop()
    else:
        rc = main()
        # 单轮模式也跑一轮微博（测接口通不通；没设 AB_WEIBO_SUB 时自动跳过）
        if rc == 0:
            rc = weibo_main()
        raise SystemExit(rc)
