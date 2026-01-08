#!/bin/bash

# 天天象棋专用 Chrome 启动脚本
# 开启远程调试，方便自动提取棋谱

echo "启动天天象棋专用 Chrome..."

# 使用独立的用户数据目录，不影响主 Chrome
USER_DATA_DIR="$HOME/chrome_chess_debug"

/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir="$USER_DATA_DIR" \
  --no-first-run \
  --no-default-browser-check \
  "https://txqp.qq.com" &

echo "✅ Chrome 已启动（调试端口: 9222）"
echo "现在可以运行: python src/extract_chess_data.py"
