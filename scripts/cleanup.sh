#!/bin/bash
# 清理脚本 - 停止所有相关容器并清理端口占用

echo "=========================================="
echo "清理旧容器和端口占用"
echo "=========================================="

# 停止并删除所有项目容器
echo "停止所有容器..."
docker-compose down -v 2>/dev/null || true

# 查找并停止占用关键端口的容器
echo "检查端口占用..."

ports=(5432 6379 8000 9000 9001 9091 19530)
for port in "${ports[@]}"; do
    container_id=$(docker ps -q --filter "publish=$port")
    if [ ! -z "$container_id" ]; then
        echo "发现占用端口$port的容器: $container_id"
        docker stop "$container_id" 2>/dev/null || true
        docker rm "$container_id" 2>/dev/null || true
        echo "✓ 已停止容器 $container_id"
    fi
done

# 清理所有停止的容器
echo "清理停止的容器..."
docker container prune -f 2>/dev/null || true

# 清理未使用的网络
echo "清理未使用的网络..."
docker network prune -f 2>/dev/null || true

echo ""
echo "✓ 清理完成！"
echo ""
echo "现在可以重新部署："
echo "  ./deploy.sh"
echo ""
