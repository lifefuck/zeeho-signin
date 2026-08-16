#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""极核 ZEEHO APP 自动签到（青龙面板）

签名算法: sign = MD5( SHA1( data + "appId=<app_id>&nonce=<uuid>&timestamp=<毫秒>" + app_secret ) )

使用方法：
1. 复制本目录，把 zeeho_data.json 里的占位符替换成你自己的抓包值
2. 部署到青龙面板（见 README.md），或本地 `python3 zeeho_signin.py` 直接跑

登录态（token/cookie/user_id）过期后，重新抓包更新 zeeho_data.json 即可，
app_id / app_secret 是应用级固定值，一般不变。
"""
import hashlib
import json
import time
import uuid
import os
import requests

BASE = "https://h5.zeehoev.com"
NO_PROXY = {"http": None, "https": None}  # 强制直连，避免被本机抓包代理拦截

HERE = os.path.dirname(os.path.abspath(__file__))


def load_config():
    with open(os.path.join(HERE, "zeeho_data.json"), "r", encoding="utf-8") as f:
        return json.load(f)


def gen_sign(cfg, data=""):
    nonce = str(uuid.uuid4())
    ts = str(int(time.time() * 1000))
    raw = f"{data}appId={cfg['app_id']}&nonce={nonce}&timestamp={ts}{cfg['app_secret']}"
    sign = hashlib.md5(hashlib.sha1(raw.encode("utf-8")).hexdigest().encode("utf-8")).hexdigest()
    return nonce, ts, sign


def build_headers(cfg, data=""):
    nonce, ts, sign = gen_sign(cfg, data)
    dev_uuid = str(uuid.uuid4())
    # Zeeho-User-Agent 里的设备字段（系统版本/APP版本/机型/分辨率）按你的抓包设备修改
    zeeho_ua = f"MOBILE|Android|10|ZEEHO_APP|2.6.24|google Pixel XL|412*732|{dev_uuid}|4g|AndroidOS"
    referer = f"https://h5.zeehoev.com/activity/signin?hideNavigationBar=true&timeStamp={int(time.time() * 1000)}"
    return {
        "user_id": cfg["user_id"],
        "Authorization": cfg["authorization"],
        "Origin": "https://h5.zeehoev.com",
        "Cfmoto-X-Sign": sign,
        "Cfmoto-X-Param": f"appId={cfg['app_id']}&nonce={nonce}&timestamp={ts}",
        "Cfmoto-X-Sign-Type": "0",
        "Zeeho-User-Agent": zeeho_ua,
        "User-Agent": cfg["user_agent"],
        "Referer": referer,
        "Cookie": cfg["cookie"],
        "X-Requested-With": "com.cfmoto",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    }


def do_signin(cfg):
    headers = build_headers(cfg, "")
    return requests.post(f"{BASE}/cfmotoservermine/signin", headers=headers,
                         timeout=15, proxies=NO_PROXY)


def notify(content):
    """通过企业微信机器人推送结果，webhook 从环境变量 WECOM_WEBHOOK 读取"""
    webhook = os.getenv("WECOM_WEBHOOK", "").strip()
    if not webhook:
        print("ℹ️ 未配置 WECOM_WEBHOOK，跳过微信通知")
        return
    try:
        resp = requests.post(webhook, json={"msgtype": "text", "text": {"content": content}},
                             timeout=10, proxies=NO_PROXY)
        if resp.status_code == 200:
            rj = resp.json()
            if rj.get("errcode") == 0:
                print("✅ 企业微信通知已发送")
            else:
                print(f"⚠️ 微信通知失败: {rj.get('errmsg', resp.text)[:150]}")
        else:
            print(f"⚠️ 微信通知 HTTP {resp.status_code}")
    except Exception as e:
        print(f"⚠️ 微信通知异常: {e}")


def main():
    cfg = load_config()
    try:
        r = do_signin(cfg)
    except Exception as e:
        print(f"⛔️ 极核签到请求异常: {e}")
        notify(f"🔴 极核自动签到报告\n\n请求异常: {e}")
        return

    try:
        j = r.json()
        code = j.get("code")
        msg = j.get("message") or ""
        data = j.get("data") or {}
        nick = data.get("nickName") or cfg.get("user_id", "")

        if code == "10000":
            line = f"✅ 签到成功（{nick}）"
            title = "✅ 极核自动签到报告"
        elif code == "repeatedly_operation":
            line = "ℹ️ 今日已签到（或操作过快）"
            title = "✅ 极核自动签到报告"
        else:
            line = f"⚠️ 签到异常 code={code} msg={msg}"
            title = "🔴 极核自动签到报告"
            print("响应:", r.text[:300])
            line += f"\n响应: {r.text[:200]}"
        print(line)
        notify(f"{title}\n\n{line}")
    except Exception as e:
        print(f"⛔️ 极核签到解析失败: {e}")
        print("原始响应:", r.text[:300])
        notify(f"🔴 极核自动签到报告\n\n解析失败: {e}")


if __name__ == "__main__":
    main()
