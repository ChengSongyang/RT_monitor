#!/bin/bash
# RT Monitor 启动脚本 (生产模式)
set -e

echo "🚀 启动 RT Monitor..."

# 杀掉旧进程
pkill -f "python3 api_server.py" 2>/dev/null || true
pkill -f "next start" 2>/dev/null || true
sleep 1

cd "$(dirname "$0")"

# 启动 API 服务器
echo "📡 API server (port 8001)..."
python3 api_server.py 8001 &
API_PID=$!
sleep 1

# 构建（如果需要）
if [ ! -d ".next" ] || [ "src/app/page.tsx" -nt ".next/BUILD_ID" ] 2>/dev/null; then
  echo "🔨 Building..."
  npm run build
fi

# 启动前端
echo "🌐 Frontend (port 3000)..."
PORT=3000 npx next start -p 3000 &
NEXT_PID=$!
sleep 2

echo "✅ Ready! http://47.77.216.151:24830"
trap "kill $API_PID $NEXT_PID 2>/dev/null; exit 0" INT TERM
wait
