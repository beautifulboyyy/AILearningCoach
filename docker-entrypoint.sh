#!/bin/bash
# 应用入口脚本 - 启动前检查依赖

set -e

echo "=========================================="
echo "启动AI学习教练应用"
echo "=========================================="

# 等待初始化完成
INIT_MARKER="/tmp/init/.initialized"
max_wait=300  # 最多等待5分钟
elapsed=0

echo "等待初始化完成..."
while [ ! -f "$INIT_MARKER" ] && [ $elapsed -lt $max_wait ]; do
    echo -n "."
    sleep 5
    elapsed=$((elapsed + 5))
done

if [ ! -f "$INIT_MARKER" ]; then
    echo ""
    echo "⚠ 初始化未完成，但继续启动应用"
    echo "如遇到问题，请检查init容器日志"
fi

echo ""
echo "✓ 准备就绪，启动应用..."

# 执行传入的命令
exec "$@"
