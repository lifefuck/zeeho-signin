#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ==============================================================================
# 脚本名称: zeeho_signin.py
# 功能描述: 极核 (ZEEHO / CFMOTO) 平台每日自动签到
# 来源项目: https://github.com/jixiaotong1999/zeeho-signin
# 修改说明: 保留原作者接口逻辑与签名算法，重命名并补全中文注释
# 署名: life
# 使用方式:
#   1. 填写同目录下的 zeeho_config.json
#   2. python3 zeeho_signin.py
# ==============================================================================

import os
import sys
import json
import time
import uuid
import hashlib
import urllib.parse

# 关闭 requests 的 SSL 警告
try:
    import requests
    requests.packages.urllib3.disable_warnings()
except Exception:
    pass


# ---------------------------- 配置文件加载 ----------------------------
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "zeeho_config.json")


def load_config():
    """加载配置文件，缺少时自动创建模板并提示用户填写。"""
    default_template = {
        "app_id": "Sw5F9uJi",
        "app_secret": "46870a8f678a09109468f5b0168818b91c292845",
        "user_id": "",
        "authorization": "",
        "cookie": "",
        "user_agent": "Mozilla/5.0 (Linux; Android 14; Mi 14 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
    }

    if not os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(default_template, f, indent=2, ensure_ascii=False)
        print(f"[-] 首次运行，已在 {CONFIG_PATH} 生成默认配置模板。")
        print("[-] 请填写 user_id / authorization / cookie 后重新运行。")
        sys.exit(1)

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    # 合并缺省字段，防止用户误删 key
    for k, v in default_template.items():
        cfg.setdefault(k, v)

    # 简单校验
    if not cfg.get("user_id") or not cfg.get("authorization"):
        print("[-] 配置不完整：user_id 或 authorization 为空。")
        sys.exit(1)

    # 统一 Authorization 前缀为 Bearer
    auth = cfg["authorization"]
    if not auth.lower().startswith("bearer "):
        cfg["authorization"] = "Bearer " + auth

    return cfg


# ---------------------------- 签名算法 ----------------------------
def gen_sign(data: str, app_id: str, app_secret: str) -> tuple[str, str, str]:
    """
    极核接口的签名算法：
    sign = MD5( SHA1( data + "appId=...&nonce=...&timestamp=..." + app_secret ) )
    其中 nonce 使用 UUID4，timestamp 为毫秒级时间戳。
    """
    nonce = str(uuid.uuid4())
    ts = str(int(time.time() * 1000))
    param = f"appId={app_id}&nonce={nonce}&timestamp={ts}"
    raw = f"{data}{param}{app_secret}"
    sign = hashlib.md5(hashlib.sha1(raw.encode("utf-8")).hexdigest().encode("utf-8")).hexdigest()
    return nonce, ts, sign


# ---------------------------- HTTP 请求函数 ----------------------------
NO_PROXY = {"http": None, "https": None}  # 直连，避免被本机代理抓包链干扰
BASE_HOST = "https://h5.zeehoev.com"


def build_headers(config, data=""):
    """构造请求头，包含登录态、签名、设备伪装等字段。"""
    nonce, ts, sign = gen_sign(data, config["app_id"], config["app_secret"])
    dev_uuid = str(uuid.uuid4())

    # 这里的设备信息可以按需修改为你自己的机型
    zeeho_ua = f"MOBILE|Android|14|ZEEHO_APP|2.6.24|Xiaomi Mi 14 Pro|420*945|{dev_uuid}|4g|AndroidOS"
    referer = f"https://h5.zeehoev.com/activity/signin?hideNavigationBar=true&timeStamp={ts}"

    return {
        "Host": "h5.zeehoev.com",
        "Authorization": config["authorization"],
        "user_id": config["user_id"],
        "Origin": "https://h5.zeehoev.com",
        "Cfmoto-X-Sign": sign,
        "Cfmoto-X-Param": f"appId={config['app_id']}&nonce={nonce}&timestamp={ts}",
        "Cfmoto-X-Sign-Type": "0",
        "Zeeho-User-Agent": zeeho_ua,
        "User-Agent": config["user_agent"],
        "Referer": referer,
        "Cookie": config["cookie"],
        "X-Requested-With": "com.cfmoto",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "Content-Type": "application/x-www-form-urlencoded",
    }


def do_signin(config):
    """调用极核签到主接口。"""
    headers = build_headers(config, "")
    try:
        resp = requests.post(
            f"{BASE_HOST}/cfmotoservermine/signin",
            headers=headers,
            timeout=20,
            proxies=NO_PROXY,
            verify=False
        )
        return resp
    except Exception as e:
        return None


def get_signin_info(config):
    """调用签到信息查询接口。"""
    headers = build_headers(config, "")
    try:
        resp = requests.get(
            f"{BASE_HOST}/cfmotoservermine/signin/info",
            headers=headers,
            params={"userId": config["user_id"]},
            timeout=20,
            proxies=NO_PROXY,
            verify=False
        )
        return resp
    except Exception as e:
        return None


# ---------------------------- 主入口 ----------------------------
def main():
    cfg = load_config()
    print("[+] 极核 (ZEEHO) 自动签到任务启动")
    print(f"[+] 用户 ID: {cfg['user_id']}")

    # 1. 查询签到信息
    print("[*] 正在查询签到信息...")
    info_resp = get_signin_info(cfg)
    if info_resp is not None:
        try:
            info = info_resp.json()
            print(json.dumps(info, ensure_ascii=False, indent=2))
        except Exception as e:
            print(f"[!] 查询接口解析失败: {e}, 原文: {info_resp.text[:200]}")
    else:
        print("[!] 查询请求失败")

    # 2. 执行签到
    print("[*] 正在执行签到...")
    resp = do_signin(cfg)
    if resp is None:
        print("[!] 签到请求失败")
        return

    try:
        result = resp.json()
        print(json.dumps(result, ensure_ascii=False, indent=2))

        code = result.get("code")
        msg = result.get("message") or ""

        if code == "10000":
            print("[✓] 签到成功！")
        elif code == "repeatedly_operation":
            print("[✓] 今日已签到，无需重复操作。")
        else:
            print(f"[!] 签到异常: code={code}, msg={msg}")
    except Exception as e:
        print(f"[!] 解析响应失败: {e}, 原文: {resp.text[:300]}")


if __name__ == "__main__":
    main()
