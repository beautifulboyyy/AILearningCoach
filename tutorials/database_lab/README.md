# Database Learning Lab

这个实验室和项目业务库分开，复用同一个 PostgreSQL 服务，但会创建一个单独的学习数据库：`db_learning_lab`。

这样做的好处是：

1. 不会污染项目本身的数据
2. 你可以放心反复练习建库、建表、删数据
3. 更适合用费曼学习法做小实验

## 这个实验室会带你做什么

你会按顺序完成这条主线：

1. 配置数据库连接
2. 创建 PostgreSQL 数据库
3. 创建 schema
4. 定义 ORM 模型
5. 建表
6. 插入、查询、更新、删除
7. 理解事务的 `commit` 和 `rollback`

## 文件说明

- [config.py](/D:/Code/python/AILearningCoach/tutorials/database_lab/config.py)
作用：集中管理连接数据库需要的配置

- [models.py](/D:/Code/python/AILearningCoach/tutorials/database_lab/models.py)
作用：定义实验用的表结构，包括 `students`、`wallets`、`transfer_logs`

- [01_create_database.py](/D:/Code/python/AILearningCoach/tutorials/database_lab/01_create_database.py)
作用：创建独立学习数据库 `db_learning_lab`

- [02_create_schema_and_tables.py](/D:/Code/python/AILearningCoach/tutorials/database_lab/02_create_schema_and_tables.py)
作用：在学习库中创建 `lab` schema，并基于模型建表

- [03_crud_and_transaction_demo.py](/D:/Code/python/AILearningCoach/tutorials/database_lab/03_crud_and_transaction_demo.py)
作用：演示 CRUD 和事务回滚

## 实践顺序

请在项目根目录按顺序执行：

```powershell
python tutorials/database_lab/01_create_database.py
python tutorials/database_lab/02_create_schema_and_tables.py
python tutorials/database_lab/03_crud_and_transaction_demo.py
```

不要并行执行。  
因为第 2 步依赖第 1 步创建好的数据库，第 3 步依赖第 2 步创建好的表。

## 每一步你应该观察什么

### 第 1 步：创建数据库

目标：

1. 理解“数据库”和“表”不是一回事
2. 先有数据库，后有 schema 和表

预期现象：

1. 如果数据库不存在，会提示创建成功
2. 如果数据库已存在，会提示已存在

### 第 2 步：创建 schema 和表

目标：

1. 理解 PostgreSQL 里的 `schema` 是什么
2. 理解 Python ORM 模型如何映射成数据库表

预期现象：

1. 创建 `lab` schema
2. 创建 `lab.students`
3. 创建 `lab.wallets`
4. 创建 `lab.transfer_logs`

### 第 3 步：CRUD 和事务

目标：

1. 看懂插入、查询、更新、删除
2. 看懂 `commit` 的意义
3. 看懂事务回滚 `rollback`

预期现象：

1. 插入学生 Alice 和 Bob
2. 查询学生
3. 更新 Alice 的学习目标
4. 删除 Bob
5. 做一次成功转账
6. 做一次失败转账并回滚
7. 看到失败转账后余额没有被错误修改

## 默认连接配置

实验默认连接：

- host: `localhost`
- port: `5432`
- user: `postgres`
- password: `postgres`
- admin database: `postgres`
- lab database: `db_learning_lab`

如果你的本地配置不同，先设置环境变量：

```powershell
$env:DB_LAB_HOST="localhost"
$env:DB_LAB_PORT="5432"
$env:DB_LAB_USER="postgres"
$env:DB_LAB_PASSWORD="postgres"
$env:DB_LAB_ADMIN_DB="postgres"
$env:DB_LAB_NAME="db_learning_lab"
```

## 学完之后怎么映射回项目

学完这套实验后，再回头看项目时可以这样对照：

1. [config.py](/D:/Code/python/AILearningCoach/tutorials/database_lab/config.py) 对应 [app/core/config.py](/D:/Code/python/AILearningCoach/app/core/config.py)
2. [models.py](/D:/Code/python/AILearningCoach/tutorials/database_lab/models.py) 对应 [app/models/user.py](/D:/Code/python/AILearningCoach/app/models/user.py) 等模型
3. `Session` 的使用方式，对应 [app/core/deps.py](/D:/Code/python/AILearningCoach/app/core/deps.py)
4. “建表”这个动作，对应项目里的 Alembic 迁移和初始化逻辑
