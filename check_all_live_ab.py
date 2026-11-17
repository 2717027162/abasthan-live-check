# 直播第三防线（Abasthan 定时任务版）
# 12 个号一个脚本一次查完：哨兵 4 个先查，其余随后；开播才发邮件，没开播不发
# 原理：ttwid + profile/other 接口读 live_status（1=开播，0=没播）
# 状态记在脚本同目录的 ab_live_state.json；只在“刚开播”时发一次邮件，开着就不重复发
# 注意：Abasthan 定时任务每次跑可能是全新容器，状态文件不一定留得住；启动时会打印 state file 是否存在、几条
# 发邮件走 formsubmit 免注册接口，目标是 Aw 的新号 Gmail（该地址已在 LightVela 线激活过，直接通）
# formsubmit ajax 必须带 Referer 头（https://formsubmit.co/），不带会被拒（"HTML files" 报错）；Origin 头没用
# TEST 模式不写状态文件（免得测试把“在播”记进去，正式跑时漏发提醒）；CLEAR_STATE 一次性清掉旧状态
# 每号只查一次不重试，45 秒没查完就停下（已查的照常记状态、照常发邮件）
# 开关可用环境变量覆盖：AB_TEST=1 / AB_TEST_EMAIL=1 / AB_CLEAR_STATE=1
# AB_LOOP=1：常驻循环模式（后台 Worker 用，每 10 分钟查一轮）；不设则只跑一轮退出

TEST = False        # True：只打印、不真发邮件（测 12 个号能不能查完）；确认后改 False
TEST_EMAIL = False  # True：额外发一封测试邮件，验证发信通不通；确认后改 False
CLEAR_STATE = False  # True：本轮开始先清掉旧状态文件；正式跑时改 False

ALERT_EMAIL = ""  # 收提醒的邮箱：部署时在环境变量里设 ALERT_EMAIL，不写进仓库
TIME_BUDGET = 45    # 秒，查到这里就停

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

import json
import os
import time
import urllib.request
import urllib.error
import http.client
import http.cookiejar
from datetime import datetime, timezone, timedelta

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
START = time.time()

# 环境变量覆盖开关；状态文件放在脚本同目录
TEST = TEST or os.environ.get("AB_TEST", "") == "1"
TEST_EMAIL = TEST_EMAIL or os.environ.get("AB_TEST_EMAIL", "") == "1"
CLEAR_STATE = CLEAR_STATE or os.environ.get("AB_CLEAR_STATE", "") == "1"
STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ab_live_state.json")
ALERT_EMAIL = os.environ.get("ALERT_EMAIL", ALERT_EMAIL)
FORMSUBMIT_URL = "https://formsubmit.co/ajax/" + ALERT_EMAIL


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
        "来源": "Abasthan第三防线",
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


def main():
    now = datetime.now(timezone(timedelta(hours=8)))
    mins = now.hour * 60 + now.minute
    if 120 <= mins < 510:
        print("night pause, skip")
        return 0
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
    for douyin_id, sec_uid in ACCOUNTS:
        if time.time() - START > TIME_BUDGET:
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
    print("done: checked=%d live=%s emailed=%s elapsed=%.1fs" % (checked, live_now, emailed, time.time() - START))
    return 0


def run_loop():
    # 后台 Worker 常驻模式：每 10 分钟查一轮，单轮异常不杀进程
    print("worker start %s (loop every 600s)" % now_str(), flush=True)
    while True:
        try:
            main()
        except Exception as e:
            print("loop ERR %s: %s" % (type(e).__name__, str(e)[:200]), flush=True)
        print("sleep 600s, next run ~%s" % now_str(), flush=True)
        time.sleep(600)


if __name__ == "__main__":
    if os.environ.get("AB_LOOP", "") == "1":
        run_loop()
    else:
        raise SystemExit(main())
