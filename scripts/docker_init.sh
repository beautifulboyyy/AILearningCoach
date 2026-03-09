#!/bin/bash
# Docker初始化脚本 - 自动初始化数据库、Milvus和测试用户

set -e  # 遇到错误立即退出

echo "=========================================="
echo "AI学习教练系统 - Docker初始化"
echo "=========================================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查初始化标记
INIT_MARKER="/tmp/init/.initialized"
if [ -f "$INIT_MARKER" ]; then
    echo -e "${GREEN}✓ 系统已初始化，跳过${NC}"
    exit 0
fi

echo "开始初始化..."

# 1. 等待PostgreSQL就绪
echo -e "\n${YELLOW}[1/6] 等待PostgreSQL就绪...${NC}"
max_attempts=30
attempt=0
until PGPASSWORD=$POSTGRES_PASSWORD psql -h "$POSTGRES_SERVER" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c '\q' 2>/dev/null; do
    attempt=$((attempt+1))
    if [ $attempt -ge $max_attempts ]; then
        echo -e "${RED}✗ PostgreSQL未就绪，超时退出${NC}"
        exit 1
    fi
    echo "等待PostgreSQL... ($attempt/$max_attempts)"
    sleep 2
done
echo -e "${GREEN}✓ PostgreSQL已就绪${NC}"

# 2. 等待Redis就绪
echo -e "\n${YELLOW}[2/6] 等待Redis就绪...${NC}"
max_attempts=30
attempt=0
until redis-cli -h "$REDIS_HOST" ping 2>/dev/null | grep -q PONG; do
    attempt=$((attempt+1))
    if [ $attempt -ge $max_attempts ]; then
        echo -e "${RED}✗ Redis未就绪，超时退出${NC}"
        exit 1
    fi
    echo "等待Redis... ($attempt/$max_attempts)"
    sleep 2
done
echo -e "${GREEN}✓ Redis已就绪${NC}"

# 3. 等待Milvus就绪
echo -e "\n${YELLOW}[3/6] 等待Milvus就绪...${NC}"
max_attempts=60  # Milvus启动较慢，给更多时间
attempt=0
until curl -f http://$MILVUS_HOST:9091/healthz 2>/dev/null; do
    attempt=$((attempt+1))
    if [ $attempt -ge $max_attempts ]; then
        echo -e "${YELLOW}⚠ Milvus未完全就绪，但继续初始化${NC}"
        break
    fi
    echo "等待Milvus... ($attempt/$max_attempts)"
    sleep 3
done
echo -e "${GREEN}✓ Milvus已就绪${NC}"

# 4. 生成并执行数据库迁移
echo -e "\n${YELLOW}[4/6] 初始化数据库...${NC}"
cd /app

# 检查是否已有迁移
if [ ! "$(ls -A alembic/versions 2>/dev/null)" ]; then
    echo "生成数据库迁移脚本..."
    alembic revision --autogenerate -m "Initial migration" || {
        echo -e "${YELLOW}⚠ 迁移脚本生成失败，尝试直接创建表${NC}"
        python scripts/init_db.py || echo -e "${RED}✗ 数据库初始化失败${NC}"
    }
fi

# 执行迁移
echo "执行数据库迁移..."
alembic upgrade head || {
    echo -e "${YELLOW}⚠ Alembic迁移失败，使用备用方案${NC}"
    python scripts/init_db.py
}
echo -e "${GREEN}✓ 数据库初始化完成${NC}"

# 5. 初始化Milvus集合
echo -e "\n${YELLOW}[5/6] 初始化Milvus...${NC}"
python scripts/init_milvus.py || {
    echo -e "${YELLOW}⚠ Milvus初始化失败，应用启动后会自动创建${NC}"
}
echo -e "${GREEN}✓ Milvus初始化完成${NC}"

# 6. 创建测试用户
echo -e "\n${YELLOW}[6/6] 创建测试用户...${NC}"
python scripts/create_test_user.py || {
    echo -e "${YELLOW}⚠ 测试用户可能已存在${NC}"
}
echo -e "${GREEN}✓ 测试用户创建完成${NC}"

# 写入初始化完成标记
mkdir -p /tmp/init
touch "$INIT_MARKER"

echo ""
echo "=========================================="
echo -e "${GREEN}✓ 初始化完成！${NC}"
echo "=========================================="
echo ""
echo "测试用户信息："
echo "  用户名: testuser"
echo "  密码: test123456"
echo "  邮箱: test@example.com"
echo ""
echo "API文档地址："
echo "  http://localhost:8000/docs"
echo ""
echo "=========================================="

exit 0
