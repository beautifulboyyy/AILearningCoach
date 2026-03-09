# API接口测试方案

## 📋 测试概览

**测试对象**：AI学习教练系统 API v1.0.0  
**测试地址**：http://localhost:8000  
**测试端点数量**：32个（含健康检查）  
**测试方法**：自动化测试脚本（Python + requests）  
**预计测试时间**：5-10分钟  

---

## 🎯 测试目标

1. ✅ 验证所有API端点可访问
2. ✅ 验证API响应符合OpenAPI规范
3. ✅ 验证业务逻辑正确性
4. ✅ 验证错误处理机制
5. ✅ 验证Multi-Agent路由功能
6. ✅ 生成详细的测试报告

---

## 📊 API端点清单

### 系统健康（3个）

| 方法 | 端点 | 说明 | 认证 |
|-----|------|------|------|
| GET | / | 根路径 | ❌ |
| GET | /health | 健康检查 | ❌ |
| GET | /ready | 就绪检查 | ❌ |

### 认证模块（4个）

| 方法 | 端点 | 说明 | 认证 | 依赖 |
|-----|------|------|------|------|
| POST | /api/v1/auth/register | 用户注册 | ❌ | - |
| POST | /api/v1/auth/login | 用户登录 | ❌ | - |
| POST | /api/v1/auth/refresh | 刷新Token | ❌ | login |
| GET | /api/v1/auth/me | 获取当前用户 | ✅ | login |

### Agent管理（2个）

| 方法 | 端点 | 说明 | 认证 | 依赖 |
|-----|------|------|------|------|
| GET | /api/v1/agents/list | 获取Agent列表 | ✅ | login |
| POST | /api/v1/agents/intent | 意图识别测试 | ✅ | login |

### 对话模块（3个）

| 方法 | 端点 | 说明 | 认证 | 依赖 |
|-----|------|------|------|------|
| POST | /api/v1/chat/ | 发送消息 | ✅ | login |
| POST | /api/v1/chat/stream | 流式对话 | ✅ | login |
| GET | /api/v1/chat/history/{session_id} | 获取历史 | ✅ | chat |

### 用户画像（3个）

| 方法 | 端点 | 说明 | 认证 | 依赖 |
|-----|------|------|------|------|
| GET | /api/v1/profile/ | 获取画像 | ✅ | login |
| PUT | /api/v1/profile/ | 更新画像 | ✅ | login |
| POST | /api/v1/profile/generate | 生成画像 | ✅ | login |

### 记忆管理（5个）

| 方法 | 端点 | 说明 | 认证 | 依赖 |
|-----|------|------|------|------|
| GET | /api/v1/memories/ | 获取记忆列表 | ✅ | login |
| GET | /api/v1/memories/{memory_id} | 获取单个记忆 | ✅ | memories |
| DELETE | /api/v1/memories/{memory_id} | 删除记忆 | ✅ | memories |
| POST | /api/v1/memories/search | 搜索记忆 | ✅ | login |
| POST | /api/v1/memories/export | 导出记忆 | ✅ | login |

### 学习路径（4个）

| 方法 | 端点 | 说明 | 认证 | 依赖 |
|-----|------|------|------|------|
| POST | /api/v1/learning-path/generate | 生成路径 | ✅ | login |
| GET | /api/v1/learning-path/active | 获取当前路径 | ✅ | generate |
| GET | /api/v1/learning-path/{path_id} | 获取指定路径 | ✅ | generate |
| PUT | /api/v1/learning-path/{path_id} | 更新路径 | ✅ | generate |

### 任务管理（6个）

| 方法 | 端点 | 说明 | 认证 | 依赖 |
|-----|------|------|------|------|
| POST | /api/v1/tasks/ | 创建任务 | ✅ | login |
| GET | /api/v1/tasks/ | 获取任务列表 | ✅ | login |
| GET | /api/v1/tasks/{task_id} | 获取单个任务 | ✅ | create |
| PUT | /api/v1/tasks/{task_id} | 更新任务 | ✅ | create |
| POST | /api/v1/tasks/{task_id}/complete | 完成任务 | ✅ | create |
| DELETE | /api/v1/tasks/{task_id} | 删除任务 | ✅ | create |

### 学习进度（3个）

| 方法 | 端点 | 说明 | 认证 | 依赖 |
|-----|------|------|------|------|
| GET | /api/v1/progress/stats | 获取进度统计 | ✅ | login |
| PUT | /api/v1/progress/{module_name} | 更新模块进度 | ✅ | login |
| GET | /api/v1/progress/report/weekly | 获取周报 | ✅ | login |

---

## 🔄 测试流程设计

### 阶段1：基础验证（无需认证）

```
1. GET /             → 验证服务可访问
2. GET /health       → 验证健康状态
3. GET /ready        → 验证就绪状态
```

**预期结果**：
- 状态码：200
- 健康检查返回 "healthy"
- 就绪检查返回 "ready": true

---

### 阶段2：认证流程测试

```
4. POST /api/v1/auth/register  → 注册新用户
   - 测试正常注册
   - 测试重复注册（应失败）
   
5. POST /api/v1/auth/login     → 登录获取Token
   - 使用testuser登录
   - 使用新注册用户登录
   - 测试错误密码（应失败）
   
6. POST /api/v1/auth/refresh   → 刷新Token
   - 使用refresh_token刷新
   
7. GET /api/v1/auth/me         → 获取当前用户信息
   - 验证返回正确用户信息
```

**保存的数据**：
- `access_token` - 用于后续请求
- `refresh_token` - 用于token刷新
- `user_id` - 用户ID

---

### 阶段3：Agent系统测试

```
8. GET /api/v1/agents/list     → 获取Agent列表
   - 验证返回4个Agent
   - 验证Agent信息完整
   
9. POST /api/v1/agents/intent  → 测试意图识别
   - 测试技术问题 → QA Agent
   - 测试规划问题 → Planner Agent
   - 测试项目问题 → Coach Agent
   - 测试进度问题 → Analyst Agent
```

**验证点**：
- Agent数量 = 4
- 意图识别准确性

---

### 阶段4：对话功能测试

```
10. POST /api/v1/chat/         → 发送对话消息
    - 测试技术问答
    - 测试学习规划
    - 验证Agent路由
    - 验证响应质量
    
11. POST /api/v1/chat/stream   → 测试流式对话
    - 验证SSE流式输出
    
12. GET /api/v1/chat/history/{session_id}  → 获取历史
    - 验证对话历史记录
```

**保存的数据**：
- `session_id` - 对话会话ID

---

### 阶段5：用户画像测试

```
13. GET /api/v1/profile/       → 获取用户画像
    - 验证初始画像结构
    
14. PUT /api/v1/profile/       → 更新用户画像
    - 更新学习目标
    - 更新技术栈
    - 更新学习风格
    
15. POST /api/v1/profile/generate  → 从对话生成画像
    - 验证自动生成功能
```

**验证点**：
- 画像字段完整性
- 更新成功

---

### 阶段6：学习路径测试

```
16. POST /api/v1/learning-path/generate  → 生成学习路径
    - 测试求职目标
    - 测试技能提升目标
    - 测试兴趣探索目标
    
17. GET /api/v1/learning-path/active     → 获取当前路径
    - 验证返回最新路径
    
18. GET /api/v1/learning-path/{path_id}  → 获取指定路径
    - 验证路径详情
    
19. PUT /api/v1/learning-path/{path_id}  → 更新路径
    - 更新学习进度
```

**保存的数据**：
- `learning_path_id` - 学习路径ID

---

### 阶段7：任务管理测试

```
20. POST /api/v1/tasks/        → 创建任务
    - 创建高优先级任务
    - 创建中优先级任务
    - 创建低优先级任务
    
21. GET /api/v1/tasks/         → 获取任务列表
    - 验证任务列表
    - 测试分页
    - 测试过滤
    
22. GET /api/v1/tasks/{task_id}     → 获取单个任务
    - 验证任务详情
    
23. PUT /api/v1/tasks/{task_id}     → 更新任务
    - 修改标题
    - 修改优先级
    - 修改截止日期
    
24. POST /api/v1/tasks/{task_id}/complete  → 完成任务
    - 标记任务完成
    
25. DELETE /api/v1/tasks/{task_id}  → 删除任务
    - 删除已完成任务
```

**保存的数据**：
- `task_id_list` - 创建的任务ID列表

---

### 阶段8：学习进度测试

```
26. GET /api/v1/progress/stats           → 获取进度统计
    - 验证初始统计数据
    
27. PUT /api/v1/progress/{module_name}   → 更新模块进度
    - 更新RAG模块进度
    - 更新Agent模块进度
    - 更新Memory模块进度
    
28. GET /api/v1/progress/report/weekly   → 获取周报
    - 验证周报生成
```

---

### 阶段9：记忆系统测试

```
29. GET /api/v1/memories/      → 获取记忆列表
    - 验证对话后的记忆
    
30. POST /api/v1/memories/search  → 搜索记忆
    - 语义搜索
    - 关键词搜索
    
31. GET /api/v1/memories/{memory_id}  → 获取单个记忆
    - 验证记忆详情
    
32. POST /api/v1/memories/export  → 导出记忆
    - 验证导出功能
    
33. DELETE /api/v1/memories/{memory_id}  → 删除记忆
    - 删除测试记忆
```

---

## ✅ 成功标准

### 响应状态码

| 操作类型 | 预期状态码 |
|---------|-----------|
| 成功查询 | 200 |
| 成功创建 | 200/201 |
| 成功更新 | 200 |
| 成功删除 | 200/204 |
| 请求错误 | 400 |
| 未认证 | 401 |
| 无权限 | 403 |
| 未找到 | 404 |
| 服务器错误 | 500 |

### 响应数据验证

1. **结构完整**：响应包含所有必需字段
2. **类型正确**：字段类型符合OpenAPI定义
3. **逻辑正确**：业务逻辑符合预期
4. **性能达标**：响应时间 < 5秒（LLM调用除外）

---

## 🧪 测试数据准备

### 用户数据

```python
test_users = [
    {
        "username": "test_api_user",
        "email": "test_api@example.com",
        "password": "TestPass123!",
        "full_name": "API测试用户"
    }
]

existing_user = {
    "username": "testuser",
    "password": "test123456"
}
```

### 测试消息

```python
test_messages = {
    "qa_question": "什么是RAG？",
    "planner_question": "帮我规划一下学习AI的路径",
    "coach_question": "我的RAG系统检索不准确，怎么优化？",
    "analyst_question": "我的学习进度如何？"
}
```

### 任务数据

```python
test_tasks = [
    {
        "title": "学习RAG系统",
        "description": "学习检索增强生成",
        "priority": "high",
        "due_date": "2026-02-15T00:00:00"
    },
    {
        "title": "实现Multi-Agent",
        "description": "实现多智能体协作",
        "priority": "medium",
        "due_date": "2026-02-20T00:00:00"
    }
]
```

---

## 📝 测试报告格式

```
======================================
API接口测试报告
======================================

测试时间：2026-01-28 15:30:00
测试端点：32个
成功：30个
失败：2个
跳过：0个
成功率：93.75%

--------------------------------------
详细结果：
--------------------------------------

[✅] GET  /                          (50ms)
[✅] GET  /health                    (45ms)
[✅] GET  /ready                     (42ms)
[✅] POST /api/v1/auth/register      (320ms)
[✅] POST /api/v1/auth/login         (280ms)
[✅] POST /api/v1/auth/refresh       (150ms)
[✅] GET  /api/v1/auth/me            (95ms)
[✅] GET  /api/v1/agents/list        (120ms)
[✅] POST /api/v1/agents/intent      (450ms)
[✅] POST /api/v1/chat/              (2500ms)  
     → Agent: QA Agent
     → Response: [RAG是检索增强生成...]
[✅] POST /api/v1/chat/stream        (2800ms)
[✅] GET  /api/v1/chat/history/xxx   (110ms)
[✅] GET  /api/v1/profile/           (85ms)
[✅] PUT  /api/v1/profile/           (180ms)
[✅] POST /api/v1/profile/generate   (3200ms)
[✅] POST /api/v1/learning-path/generate  (4500ms)
[✅] GET  /api/v1/learning-path/active    (95ms)
[✅] GET  /api/v1/learning-path/{id}      (88ms)
[✅] PUT  /api/v1/learning-path/{id}      (150ms)
[✅] POST /api/v1/tasks/             (120ms)
[✅] GET  /api/v1/tasks/             (90ms)
[✅] GET  /api/v1/tasks/{id}         (75ms)
[✅] PUT  /api/v1/tasks/{id}         (110ms)
[✅] POST /api/v1/tasks/{id}/complete (95ms)
[✅] DELETE /api/v1/tasks/{id}       (85ms)
[✅] GET  /api/v1/progress/stats     (105ms)
[✅] PUT  /api/v1/progress/{module}  (120ms)
[✅] GET  /api/v1/progress/report/weekly  (250ms)
[✅] GET  /api/v1/memories/          (100ms)
[✅] POST /api/v1/memories/search    (180ms)
[✅] GET  /api/v1/memories/{id}      (70ms)
[❌] POST /api/v1/memories/export    (0ms)
     → Error: 500 Internal Server Error
     → Message: Export功能未实现
[✅] DELETE /api/v1/memories/{id}    (90ms)

--------------------------------------
性能统计：
--------------------------------------

平均响应时间：328ms
最快响应：42ms (GET /ready)
最慢响应：4500ms (POST /learning-path/generate)
超时次数：0

--------------------------------------
Multi-Agent路由测试：
--------------------------------------

[✅] 技术问题 → QA Agent (100%)
[✅] 规划问题 → Planner Agent (100%)
[✅] 项目问题 → Coach Agent (100%)
[✅] 进度问题 → Analyst Agent (100%)

路由准确率：100%

--------------------------------------
失败详情：
--------------------------------------

1. POST /api/v1/memories/export
   - 状态码：500
   - 错误信息：Export功能未完全实现
   - 建议：补充导出逻辑

--------------------------------------
总结：
--------------------------------------

✅ 核心功能全部正常
✅ Multi-Agent路由准确
✅ 认证授权正常
✅ CRUD操作正常
⚠️  部分增强功能待完善

整体评估：生产可用 ✅

======================================
```

---

## 🛠️ 测试工具选择

### 方案1：Python脚本（推荐）

**优点**：
- 灵活性高
- 易于调试
- 可生成详细报告
- 支持复杂逻辑

**实现**：
```python
import requests
import json
from datetime import datetime

class APITester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.token = None
        self.results = []
    
    def test_endpoint(self, method, path, **kwargs):
        # 测试逻辑
        pass
    
    def generate_report(self):
        # 生成报告
        pass
```

### 方案2：Pytest（推荐用于CI/CD）

**优点**：
- 标准测试框架
- 丰富的插件
- 易于集成CI/CD
- 生成标准报告

### 方案3：Postman Collection

**优点**：
- 图形化界面
- 易于分享
- 支持环境变量

---

## ⏱️ 测试时间估算

| 阶段 | 端点数 | 估计时间 |
|-----|-------|---------|
| 基础验证 | 3 | 10秒 |
| 认证流程 | 4 | 30秒 |
| Agent系统 | 2 | 1分钟 |
| 对话功能 | 3 | 2分钟 |
| 用户画像 | 3 | 1分钟 |
| 学习路径 | 4 | 1.5分钟 |
| 任务管理 | 6 | 1分钟 |
| 学习进度 | 3 | 30秒 |
| 记忆系统 | 5 | 1分钟 |

**总计**：约8-10分钟

---

## 🎯 测试优先级

### P0（必须通过）
- ✅ 健康检查
- ✅ 认证登录
- ✅ 对话功能
- ✅ Multi-Agent路由

### P1（重要）
- ✅ 用户画像
- ✅ 学习路径
- ✅ 任务管理
- ✅ 学习进度

### P2（增强）
- ✅ 记忆导出
- ✅ 流式对话
- ✅ 周报生成

---

## 📋 测试检查清单

- [ ] 所有端点可访问
- [ ] 认证机制正常
- [ ] Token刷新正常
- [ ] Multi-Agent路由准确
- [ ] LLM响应质量好
- [ ] CRUD操作正常
- [ ] 错误处理正确
- [ ] 响应时间达标
- [ ] 数据持久化正常
- [ ] 并发请求稳定

---

## 🚀 开始测试

### 自动化测试

```bash
# 运行测试脚本
python tests/test_all_apis.py

# 生成HTML报告
python tests/test_all_apis.py --report html

# 只测试P0功能
python tests/test_all_apis.py --priority P0
```

### 手动测试

```bash
# 访问Swagger UI
open http://localhost:8000/docs

# 按照本方案逐个测试
```

---

## 📊 预期结果

- **成功率**：≥ 95%
- **平均响应时间**：< 500ms（不含LLM调用）
- **LLM调用时间**：< 5秒
- **无500错误**（除已知未实现功能）
- **Multi-Agent路由准确率**：100%

---

**测试方案版本**：v1.0  
**设计时间**：2026-01-28  
**设计人**：AI Assistant  
**审核状态**：待审核
