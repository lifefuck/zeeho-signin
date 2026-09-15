# 极核 ZEEHO APP 自动签到

> ✅ 本项目 fork 自 [jixiaotong1999/zeeho-signin](https://github.com/jixiaotong1999/zeeho-signin)，感谢原作者提供签名算法与青龙面板适配版本。
> 本 fork 在原项目基础上新增了 **免抓包 token 提取** 与 **呆呆面板（D2550）** 适配方案，署名 `life`。

飞牛 NAS 青龙面板 / D2550 呆呆面板 定时签到脚本，适用于春风动力旗下 ZEEHO 极核 APP 的「每日签到」功能（含补签卡、连续签到盲盒奖励体系）。

> ⚠️ 本脚本仅用于个人学习与自动化自己的账号，请勿用于任何违规用途。

## 功能特性

- 每日自动签到（`POST /cfmotoservermine/signin`）
- 完整还原请求签名（`Cfmoto-X-Sign`，`MD5(SHA1(...))` 算法）
- 原青龙版本：支持企业微信机器人推送运行结果
- **呆呆面板版本**：无需抓包，Root 手机一键扫描本地 WebView 缓存提取 token

## 文件说明

| 文件 | 说明 |
|---|---|
| `zeeho_signin.py` | 原青龙面板版本（保留原作者代码风格） |
| `zeeho_data.json` | 原青龙版本配置文件 |
| `zeeho_signin_daidai.py` | 呆呆面板版本签到脚本（署名 life，带中文注释） |
| `zeeho_config_daidai.json` | 呆呆面板版本配置文件 |
| `scan_zeeho_token.sh` | Android Root 手机端扫描脚本，一键提取 token / user_id |
| `zeeho_deploy.py` | 原青龙一键部署脚本 |

## 环境要求

- Python 3.x
- 依赖：`requests`（`pip install requests`）
- （可选）`paramiko`（仅原青龙部署脚本需要）

## 呆呆面板部署（推荐：无需抓包）

### 1. 获取 token

在已 Root 的 Android 手机上：

1. 安装 ZeroTermux 或 MT 管理器终端；
2. 把本仓库的 `scan_zeeho_token.sh` 放到手机 `/storage/emulated/0/Download/`；
3. 打开极核 App 并进入签到页等待 3 秒；
4. 终端执行：
   ```bash
   su
   sh /storage/emulated/0/Download/scan_zeeho_token.sh
   ```
5. 结果会保存到 `/storage/emulated/0/Download/zeeho_scan_result.txt`，从中找到 `token` 与 `user_id`。

### 2. 配置签到脚本

编辑 `zeeho_config_daidai.json`：

```json
{
  "app_id": "Sw5F9uJi",
  "app_secret": "46870a8f678a09109468f5b0168818b91c292845",
  "user_id": "你的 user_id",
  "authorization": "Bearer 你的 token",
  "cookie": "",
  "user_agent": "Mozilla/5.0 (Linux; Android 14; Mi 14 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
}
```

### 3. 创建面板定时任务

在呆呆面板新建任务：

- **名称**：`[xy]极核ZEEHO每日签到`
- **命令**：`python3 data/scripts/xy/zeeho_signin_daidai.py`
- **定时**：`30 4 * * *`（每天早上 4:30）
- 把 `zeeho_signin_daidai.py` 与 `zeeho_config_daidai.json` 放到面板 `data/scripts/xy/` 目录下

## 青龙面板部署

### 方式一：一键部署脚本

编辑 `zeeho_deploy.py` 顶部「部署配置」的占位符，然后运行：

```bash
pip install paramiko requests
python3 zeeho_deploy.py
```

### 方式二：手动部署

1. 把 `zeeho_signin.py` 和 `zeeho_data.json` 上传到青龙 `scripts/zeeho/` 目录
2. 青龙面板「定时任务」新建任务：
   - 命令：`task zeeho/zeeho_signin.py`
   - 定时规则：`10 8 * * *`（每天 08:10，可自定义）

## 微信机器人通知（青龙版）

脚本从环境变量 `WECOM_WEBHOOK` 读取企业微信机器人 webhook：

青龙「系统设置 → 环境变量」添加：

```
WECOM_WEBHOOK = https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=你的key
```

## 本地测试

**呆呆面板版：**

```bash
python3 zeeho_signin_daidai.py
```

**青龙面板版：**

```bash
python3 zeeho_signin.py
```

输出 `签到成功` 即接口连通；`今日已签到` 表示当天已签过。

## 常见问题

**Q: 返回 `code=40000` 或「网络开小差」？**
A: 签名或登录态失效，重新运行 `scan_zeeho_token.sh` 提取更新。

**Q: 返回 `repeatedly_operation`？**
A: 当天已签过，属正常提示。

**Q: 提示 SSL / 代理报错？**
A: 脚本已强制直连（`proxies={}`）。若本机有 `http_proxy` 环境变量，请清除后再跑。

**Q: token 多久过期？**
A: 一般数天到数月。过期后重新用 `scan_zeeho_token.sh` 扫描一次更新即可，`app_id`/`app_secret` 不变。

## 免责声明

本脚本仅供学习研究，使用者需对自身账号行为负责。
