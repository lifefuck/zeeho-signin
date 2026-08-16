# 极核 ZEEHO APP 自动签到

飞牛 NAS 青龙面板定时签到脚本，适用于春风动力旗下 ZEEHO 极核 APP 的「每日签到」功能（含补签卡、连续签到盲盒奖励体系）。

> ⚠️ 本脚本仅用于个人学习与自动化自己的账号，请勿用于任何违规用途。

## 功能特性

- 每日自动签到（`POST /cfmotoservermine/signin`）
- 完整还原请求签名（`Cfmoto-X-Sign`，`MD5(SHA1(...))` 算法）
- 支持企业微信机器人推送运行结果
- token 过期后只需更新配置，无需改代码

## 环境要求

- Python 3.x（本地测试或青龙容器内）
- 依赖：`requests`（`pip install requests`）
- （可选）`paramiko`（仅部署脚本需要）

## 配置说明

编辑 `zeeho_data.json`，填入你的抓包值：

| 字段 | 说明 | 获取方式 |
|---|---|---|
| `app_id` | 应用标识 | 固定值，一般不用改 |
| `app_secret` | 签名密钥 | 从极核 H5 前端 JS 提取（见下文） |
| `user_id` | 用户 ID | 抓包签到接口请求头 `user_id` |
| `authorization` | 登录令牌 | 抓包请求头 `Authorization`（保留 `Bearer ` 前缀） |
| `cookie` | 会话 Cookie | 抓包请求头 `Cookie` |
| `user_agent` | 设备 UA | 抓包请求头 `User-Agent` |

### 怎么抓包拿到配置？

1. 手机（需 root）装好 Reqable 证书，电脑开 Reqable 代理
2. 手机打开极核 APP 并登录，进入签到页，点一次「签到」
3. 在 Reqable 里找到 `POST h5.zeehoev.com/cfmotoservermine/signin` 请求
4. 右键「复制为 cURL」，把请求头里的 `user_id`、`Authorization`、`Cookie`、`User-Agent` 填进 `zeeho_data.json`

### `app_secret` 怎么获取？

`app_secret` 是应用级固定值，藏在极核签到页的 H5 前端 JS 里（签到是 H5 页面，签名逻辑在 JS 明文）：

1. 打开签到页 `https://h5.zeehoev.com/activity/signin`，查看网页源码，找到入口 JS（如 `app.xxx.js`）
2. 在 JS 里搜 `appSecret`，会看到它被存成「16 位二进制空格串」
3. 每个二进制 token 的**前 8 位**是 ASCII 码，逐个 `chr(int(bin,2))` 解码即得 40 位十六进制字符串

> 不同 APP 版本该值可能不同；若服务端更换密钥，需按上述步骤重新提取。

## 部署到青龙面板

### 方式一：一键部署脚本

编辑 `zeeho_deploy.py` 顶部「部署配置」的占位符（NAS IP、SSH 账号密码、青龙密码、本地脚本目录），然后运行：

```bash
pip install paramiko requests
python3 zeeho_deploy.py
```

脚本会自动：上传脚本到青龙 scripts 目录 → 装依赖 → 建 cron（每天 08:10）→ 触发测试 → 打印日志。

### 方式二：手动部署

1. 把 `zeeho_signin.py` 和 `zeeho_data.json` 上传到青龙 `scripts/zeeho/` 目录
2. 青龙面板「定时任务」新建任务：
   - 命令：`task zeeho/zeeho_signin.py`
   - 定时规则：`10 8 * * *`（每天 08:10，可自定义）
3. 运行一次测试，日志出现 `✅ 签到成功` 即成功

## 微信机器人通知（可选）

脚本从环境变量 `WECOM_WEBHOOK` 读取企业微信机器人 webhook：

1. 青龙「系统设置 → 环境变量」添加 `WECOM_WEBHOOK = https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=你的key`
2. 之后每次签到结果都会推送到对应群聊

## 本地测试

```bash
python3 zeeho_signin.py
```

输出 `✅ 签到成功（昵称）` 即接口连通；`ℹ️ 今日已签到` 表示当天已签过。

## 常见问题

**Q: 返回 `code=40000` 或「网络开小差」？**
A: 签名或登录态失效，重新抓包更新 `zeeho_data.json`。

**Q: 返回 `repeatedly_operation`？**
A: 短时间重复签到，属正常，当天已签过。

**Q: 提示 `⛔️ 请求异常` / SSL 报错？**
A: 脚本已强制直连（`proxies={}`）。若在本机有抓包代理，清掉 `http_proxy`/`https_proxy` 环境变量再跑。

**Q: token 多久过期？**
A: 一般几周到几月。过期后按「怎么抓包」重新抓一条 cURL，更新 `authorization`/`cookie`/`user_id` 即可，`app_id`/`app_secret` 不变。

## 免责声明

本脚本仅供学习研究，使用者需对自身账号行为负责。
