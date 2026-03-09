# 多阶段构建 - 优化镜像大小

# 构建阶段
FROM python:3.10-slim as builder

WORKDIR /app

# 安装编译依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖到本地目录
RUN pip install --user --no-cache-dir -r requirements.txt

# 运行阶段
FROM python:3.10-slim

WORKDIR /app

# 安装运行时依赖
RUN apt-get update && apt-get install -y \
    postgresql-client \
    redis-tools \
    curl \
    bash \
    && rm -rf /var/lib/apt/lists/*

# 从builder复制Python包
COPY --from=builder /root/.local /root/.local

# 确保脚本在PATH中
ENV PATH=/root/.local/bin:$PATH

# 复制应用代码
COPY . .

# 创建必要的目录
RUN mkdir -p logs alembic/versions

# 设置脚本执行权限
RUN chmod +x /app/docker-entrypoint.sh /app/scripts/docker_init.sh

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python scripts/healthcheck.py || exit 1

# 默认启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
