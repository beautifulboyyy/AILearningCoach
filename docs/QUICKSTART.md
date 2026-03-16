# 🚀 快速开始指南

## 5分钟快速部署

### 第一步：准备环境

确保已安装：
- ✅ Docker 20.10+
- ✅ Docker Compose 2.0+

验证安装：
```bash
docker --version
docker compose version
```

### 第二步：配置环境变量

```bash
# 1. 复制环境变量模板
cp .env.example .env

# 2. 编辑 .env 文件（必填项）
nano .env  # 或使用其他编辑器
```

**最少需要配置以下3项：**

```bash
# 数据库密码（自己设置一个强密码）
POSTGRES_PASSWORD=your_strong_password_here

# JWT密钥（运行以下命令生成）
# python -c "import secrets; print(secrets.token_urlsafe(32))"
SECRET_KEY=your_jwt_secret_key_here

# OpenAI API密钥（从 https://platform.openai.com/api-keys 获取）
OPENAI_API_KEY=sk-your-api-key-here
```

### 第三步：一键部署

```bash
# 给脚本添加执行权限
chmod +x deploy.sh

# 执行部署
./deploy.sh
```

等待 3-5 分钟，看到以下信息表示部署成功：

```
╔════════════════════════════════════════════════════════════╗
║                     🎉 部署成功！🎉                         ║
╚════════════════════════════════════════════════════════════╝

📱 前端应用:
   http://localhost:3000

🔧 后端 API:
   http://localhost:8000
   API 文档: http://localhost:8000/docs
```

### 第四步：开始使用

1. 访问 http://localhost:3000
2. 点击"注册"创建账号
3. 登录后开始使用！

## 常见问题

### Q: 端口被占用怎么办？

```bash
# 查看端口占用
lsof -i :3000
lsof -i :8000

# 停止占用端口的进程
kill -9 <PID>
```

### Q: 构建失败怎么办？

```bash
# 清理并重新部署
./deploy.sh --clean
```

### Q: 如何查看日志？

```bash
# 查看所有服务日志
./deploy.sh --logs

# 查看特定服务日志
docker compose logs -f app      # 后端
docker compose logs -f frontend  # 前端
```

### Q: 如何停止服务？

```bash
./deploy.sh --stop
```

### Q: 忘记配置环境变量了？

```bash
# 停止服务
./deploy.sh --stop

# 编辑 .env
nano .env

# 重新部署
./deploy.sh
```

## 下一步

- 📖 查看完整的 [部署文档](DEPLOYMENT.md)
- 🎯 了解 [功能特性](README.md#-功能特性)
- 🔧 学习 [开发指南](README.md#-开发指南)

## 需要帮助？

- 查看部署脚本帮助: `./deploy.sh --help`
- 健康检查: `./deploy.sh --health`
- 查看日志: `./deploy.sh --logs`

---

**祝您使用愉快！** 🎉
