#!/system/bin/sh
# ==============================================================================
# 脚本名称: scan_zeeho_token.sh
# 功能描述: 对极核 (com.cfmoto) App 数据目录进行全面扫描，
#           自动输出可能包含 Token / userId 的原始片段，便于后续人工挑选。
# 适用环境: Android Root (ZeroTermux / MT管理器 / 终端模拟器)
# 产物输出: /storage/emulated/0/Download/zeeho_scan_result.txt
# 使用方式: su 后执行 sh /path/to/scan_zeeho_token.sh
# 署名: life
# ==============================================================================

# 必须先获取 Root 权限
if [ "$(id -u)" -ne 0 ]; then
    echo "[-] 请先执行 'su' 获取 Root 权限后再运行本脚本！"
    exit 1
fi

DATA_DIR="/data/data/com.cfmoto"
OUT_FILE="/storage/emulated/0/Download/zeeho_scan_result.txt"

# 检查极核 App 是否已安装并至少打开过一次
if [ ! -d "$DATA_DIR" ]; then
    echo "[-] 未检测到极核 App 数据目录 ($DATA_DIR)，请先安装并打开一次极核 App。"
    exit 1
fi

# 清空旧结果
rm -f "$OUT_FILE"
mkdir -p "$OUT_FILE%/*" 2>/dev/null

echo "[+] 开始全面扫描极核 App 数据目录..."
echo "[提示] 如果刚打开过 App 的签到/核能量页面，效果会更好。"
echo ""

# --- 第一部分：目录结构概览 ---
echo "====== 1. 极核数据目录结构 (前200行) ======" >> "$OUT_FILE"
find "$DATA_DIR" -maxdepth 5 -type d 2>/dev/null | sort | head -n 200 >> "$OUT_FILE"
echo "" >> "$OUT_FILE"

# --- 第二部分：文件列表（定位数据库、缓存、LevelDB 等） ---
echo "====== 2. 关键文件列表 ======" >> "$OUT_FILE"
find "$DATA_DIR" -type f \( \
    -name "*.xml" -o -name "*.json" -o -name "*.ldb" \
    -o -name "*.log" -o -name "*.leveldb*" -o -name "*cookies*" \
    -o -name "*webview*" -o -name "*cache*" \) 2>/dev/null | sort >> "$OUT_FILE"
echo "" >> "$OUT_FILE"

# --- 第三部分：正则匹配 Token / userId 相关字段 ---
echo "====== 3. Token / userId 相关原始片段 (前300条) ======" >> "$OUT_FILE"
grep -Eroa '.{0,40}(Bearer|access_token|refresh_token|id_token|token|userId|user_id|user_info|userInfo|accountId|memberId|openId).{0,120}' \
    "$DATA_DIR" 2>/dev/null | head -n 300 >> "$OUT_FILE"
echo "" >> "$OUT_FILE"

# --- 第四部分：匹配标准 JWT 格式 (eyJxxx.yyy.zzz) ---
echo "====== 4. 疑似 JWT 字符串 (前50条) ======" >> "$OUT_FILE"
grep -Eroa 'eyJ[A-Za-z0-9_-]{6,}\.eyJ[A-Za-z0-9_-]{6,}\.[A-Za-z0-9_-]{6,}' \
    "$DATA_DIR" 2>/dev/null | head -n 50 >> "$OUT_FILE"
echo "" >> "$OUT_FILE"

# --- 第五部分：单独列出 WebView Local Storage 数据库内容 ---
echo "====== 5. WebView LocalStorage LevelDB 关键内容 ======" >> "$OUT_FILE"
grep -Eroa '.{0,80}(token|userId|user_id|userInfo).{0,120}' \
    "$DATA_DIR/app_webview/" 2>/dev/null | head -n 200 >> "$OUT_FILE"
echo "" >> "$OUT_FILE"

echo ""
echo "[✓] 扫描完成！"
echo "[✓] 结果文件路径: $OUT_FILE"
echo "[✓] 请直接在微信/飞书/QQ 里发送这个 .txt 文件给我。"
echo "[✓] 如果内容很长，你也可以在文件里查看。"
