# 数据库基础与 ORM 学习总结

这份文档总结了当前阶段和数据库相关的学习成果。到目前为止，已经完成了从数据库基础层级认知，到独立实验室中的配置、建库、建表、ORM 模型、CRUD、Session、事务与结果取值方式的第一轮学习。

## 本阶段学习目标

本阶段的目标不是把数据库所有高级特性学完，而是先建立：

1. PostgreSQL 的层级结构认知
2. 数据库配置、建库、schema、建表的完整路径
3. ORM 的基本思想
4. Session、CRUD、事务的第一层理解
5. 读懂项目里数据库相关代码所需的基础能力

## 一、PostgreSQL 的层级结构

通过 PyCharm 数据库面板和实验室练习，已经建立了这套层级认知：

1. 服务器实例
2. 数据库
3. schema
4. 表

结合当前环境，可以这样理解：

1. `postgres`、`ai_learning_coach`、`db_learning_lab` 是数据库
2. 每个数据库下面有多个 schema
3. schema 下面才是具体表

一句话记忆：

表不是直接挂在数据库下面的，表属于某个 schema，而 schema 属于某个数据库。

## 二、几个关键数据库对象

### 1. `postgres` 数据库

`postgres` 是 PostgreSQL 默认存在的数据库，一般无需手动创建。

它当前阶段最重要的作用是：

1. 作为默认可连接数据库
2. 作为管理入口，用于执行 `CREATE DATABASE` 这类操作

当前理解已经明确：

不是凭空创建数据库，而是先连接到一个已存在的数据库，再创建新数据库。

### 2. `public` schema

`public` 是默认 schema。  
如果不显式指定 schema，很多表默认会建在这里。

### 3. `information_schema`

这是标准化的数据库结构信息视图，用于查看：

1. 表
2. 列
3. 约束
4. 其他结构信息

### 4. `pg_catalog`

这是 PostgreSQL 的系统目录，保存系统级元数据和内部对象信息。

### 5. 自定义 schema：`lab`

实验室中创建的 `lab` schema 是自己的业务命名空间，当前表包括：

1. `lab.students`
2. `lab.wallets`
3. `lab.transfer_logs`

它的价值是：

1. 做逻辑分组
2. 和默认 `public` 隔离
3. 帮助理解 PostgreSQL 中 schema 的实际用途

## 三、独立数据库实验室的意义

为了不直接在项目业务库上学习，建立了独立实验室：

[tutorials/database_lab](/D:/Code/python/AILearningCoach/tutorials/database_lab)

它使用单独数据库：

`db_learning_lab`

这样做的好处是：

1. 不污染项目业务数据
2. 可以放心反复练习建库、建表、删数据
3. 可以先把数据库基础学透，再映射回项目

## 四、配置文件的理解

文件：
[config.py](/D:/Code/python/AILearningCoach/tutorials/database_lab/config.py)

目前已经理解这几类配置：

1. `DB_HOST`
2. `DB_PORT`
3. `DB_USER`
4. `DB_PASSWORD`
5. `ADMIN_DB`
6. `LAB_DB`
7. `LAB_SCHEMA`

### 1. `os.getenv()` 的意义

例如：

```python
DB_HOST = os.getenv("DB_LAB_HOST", "localhost")
```

意思是：

1. 优先读取系统环境变量
2. 如果没有，就使用后面的默认值

所以这套实验室代码即使没有额外 `.env` 文件，也能直接运行。

### 2. `ADMIN_DB` 和 `LAB_DB`

当前已经理清：

1. `ADMIN_DB = "postgres"`
用于连接默认数据库，执行“创建数据库”这类数据库级操作

2. `LAB_DB = "db_learning_lab"`
用于连接学习数据库，后续 schema、表和数据都在这里操作

一句话记忆：

先连接已有数据库创建新数据库，再连接新数据库做实验。

### 3. `LAB_SCHEMA`

`LAB_SCHEMA = "lab"` 表示在学习数据库中使用 `lab` 这个 schema。

schema 当前可以理解成：

数据库内部的逻辑分组 / 命名空间。

## 五、Engine 的理解

在建库和建表脚本里都出现了 `engine`。

当前已经建立的理解是：

1. `engine` 是数据库操作的总入口
2. 它类似一个数据库总客户端
3. 它知道连接哪个数据库、使用什么驱动、如何创建具体连接

你已经建立了一个很合适的类比：

`engine` 类似 OpenAI 的 client。

## 六、数据库连接 URL 的理解

例如：

```python
postgresql+psycopg2://postgres:postgres@localhost:5432/postgres
```

可以拆成：

1. `postgresql`
数据库类型

2. `psycopg2`
PostgreSQL 的 Python 驱动

3. `postgres:postgres`
用户名和密码

4. `localhost:5432`
数据库服务地址和端口

5. `/postgres`
连接目标数据库名

它的作用就是告诉 SQLAlchemy：

“用什么方式，连接哪个数据库。”

## 七、`AUTOCOMMIT` 的理解

在建库脚本中使用了：

```python
create_engine(..., isolation_level="AUTOCOMMIT")
```

目前已经理解：

1. 普通数据库写入通常放在事务里
2. 但 `CREATE DATABASE` 这类数据库级操作不适合走普通事务块
3. 因此这里使用 `AUTOCOMMIT`，让命令直接生效

这属于数据库级管理操作，而不是普通业务写入。

## 八、`engine.connect()` 和 `engine.begin()` 的区别

### 1. `engine.connect()`

表示：

拿到一条具体数据库连接来执行命令。

适合：

1. 简单管理操作
2. 原生 SQL 执行

### 2. `engine.begin()`

表示：

拿到一条连接，并自动开启事务。

适合：

1. 多步结构初始化
2. 希望多步操作要么一起成功，要么一起回滚

在建 schema 和建表场景下，它的意义是：

避免中途出错时留下半完成状态。

## 九、结果集对象和 `scalar`

在建库和查询示例中，已经理解：

1. `execute()` 返回的是结果集对象，不是直接值
2. 查询结果本质上可以看成二维结构：多行多列
3. 数据库工具中看到的小表格只是可视化渲染

例如一条一行一列的结果，大致可以看成：

```python
[(1,)]
```

经过 `.scalar()` 后得到：

```python
1
```

### 当前已经掌握的常见取值方式

1. `scalar()`
取第一行第一列

2. `scalar_one()`
要求恰好一条结果，否则报错

3. `scalar_one_or_none()`
要么返回一个结果，要么返回 `None`

4. `scalars()`
把每行第一列提取出来，形成一个可迭代结果

5. `all()`
一次性取出所有结果，返回列表

### 一个关键理解

例如：

```python
session.execute(select(User)).all()
```

返回结果更接近：

```python
[(User(...),), (User(...),)]
```

而：

```python
session.execute(select(User)).scalars().all()
```

返回结果更接近：

```python
[User(...), User(...)]
```

这表示：

1. `select(User)` 选中的是“整个 ORM 实体”
2. 每行只有一列，这一列是 `User` 对象
3. `scalars()` 的作用就是去掉每行外层的那一层包装，提取第一列对象

## 十、ORM 的基本思想

这一阶段已经建立了 ORM 的核心认知：

ORM = Object Relational Mapping，对象关系映射。

它的核心思想是：

1. 表 -> Python 类
2. 行 -> 类实例
3. 列 -> 类属性

目前已经理解：

1. `Student` 类对应 `lab.students` 表
2. 类中的字段定义，对应数据库表的列和约束
3. ORM 允许我们更多地用对象方式操作数据库，而不是手写 SQL

## 十一、`Base` 基类的意义

在 `models.py` 中：

```python
class Base(DeclarativeBase):
    pass
```

虽然看起来是空类，但它非常关键。

它的作用是：

1. 作为所有 ORM 模型的共同父类
2. 收集所有模型的元数据
3. 支持通过 `Base.metadata.create_all(...)` 一次性创建所有表

一句话记忆：

`Base` 是所有 ORM 模型的统一注册中心。

## 十二、模型文件中的关键导入

在 `models.py` 中学习了：

```python
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
```

目前的理解是：

1. `DeclarativeBase`
定义 ORM 基类

2. `Mapped`
给 ORM 属性做类型标注

3. `mapped_column`
定义数据库列

4. `relationship`
定义 ORM 层对象之间的关系导航

## 十三、`__repr__` 的理解

每个模型类里的 `__repr__` 已经理解清楚：

1. 它是对象的可读输出定义
2. 用来代替默认难读的对象地址表示
3. 类似 Java 里的 `toString()`

## 十四、外键的理解

当前已经理解：

外键是一张表中引用另一张表主键的字段。

它的作用是：

1. 表达表和表之间的关系
2. 保证引用的数据真实存在

在实验室中：

1. `from_wallet_id`
2. `to_wallet_id`

都引用 `wallets.id`

表示：

每条转账记录都必须关联真实存在的钱包。

## 十五、`relationship` 的第一层理解

这一部分已经建立了重要基础：

1. 外键属于数据库层约束
2. `relationship` 不是数据库层强制必须的
3. `relationship` 的主要价值是让 Python 代码更方便访问关联对象

例如：

1. `log.from_wallet`
2. `wallet.outgoing_logs`

### 当前已经理解到的点

1. `Mapped[list["TransferLog"]]` 表示一对多的一侧
2. `Mapped[Wallet]` 表示多对一的一侧
3. `back_populates` 是把双向关系两边配对起来
4. 关系不是必须写的，但写了之后对象导航更自然

一句话记忆：

`relationship` 的核心价值是把“表之间的关系”提升成“对象之间的导航能力”。

## 十六、Session 的理解

这是今天学习中一个重要进展。

当前已经理解：

1. `Session` 是 ORM 层最常用的数据库工作会话
2. 它负责查对象、改对象、提交事务和回滚事务
3. 它和 `engine`、`connection` 不同，属于更上层的 ORM 工作台

可以这样区分：

1. `engine`
数据库总入口

2. `connection`
更底层的具体连接

3. `session`
更上层的 ORM 工作上下文

## 十七、Session 和 ORM 的关系

目前已经建立了一个很核心的理解：

1. 很多数据库操作方法都会接收一个 `session`
2. 这表示该方法拿到了和数据库通信的当前工作上下文
3. 通过 `session` 查出来的 ORM 对象，会被它跟踪
4. 修改这些对象的属性后，ORM 会在 `commit()` 时把变化翻译成真正的 SQL

一句话记忆：

`session` 管理数据库会话和事务，ORM 负责把对象操作映射成 SQL。

## 十八、CRUD 的第一轮理解

通过 [03_crud_and_transaction_demo.py](/D:/Code/python/AILearningCoach/tutorials/database_lab/03_crud_and_transaction_demo.py)，已经把 CRUD 基本看懂。

### 1. Create

```python
session.add(obj)
session.add_all([obj1, obj2])
session.commit()
```

当前理解：

1. `add/add_all` 只是把对象加入当前事务
2. `commit()` 才真正把数据写入数据库

### 2. Read

```python
session.execute(select(Student)...)
```

当前理解：

1. `select(Model)` 表示查询模型对应的表
2. `.filter(...)` 添加条件
3. `session.execute(...)` 执行查询
4. 再通过 `scalar/scalars/all` 等方式取结果

### 3. Update

当前理解：

1. 先查出对象
2. 修改对象属性
3. `session.commit()` 时 ORM 自动生成 `UPDATE`

这是 ORM 的核心优势之一：对象状态跟踪。

### 4. Delete

```python
session.delete(obj)
session.commit()
```

当前理解：

1. `delete()` 标记删除对象
2. `commit()` 后才真正落库

## 十九、事务的第一轮理解

通过转账示例已经建立了事务的第一层理解：

1. 一次转账不是一个动作，而是一组动作
2. 至少包括：
   - 扣钱
   - 加钱
   - 写转账日志
3. 这组操作要么全部成功，要么全部失败

所以事务的核心意义是：

保证一组相关操作的原子性，防止业务数据出现半成功状态。

### 当前已经理解的关键操作

1. `commit()`
把当前事务正式提交到数据库

2. `rollback()`
在出错时撤销本次未提交的修改

你已经通过转账例子看懂：

失败后回滚，余额会恢复到失败前状态。

## 二十、当前阶段已经具备的能力

截至目前，数据库这条主线已经完成了第一轮基础搭建。你已经能够：

1. 解释 PostgreSQL 的层级结构
2. 解释数据库、schema、表之间的关系
3. 解释为什么要先连接默认库再创建新库
4. 解释配置文件里数据库参数的作用
5. 解释 `engine`、`connection`、`session` 的区别
6. 解释 `connect()` 和 `begin()` 的区别
7. 解释结果集对象与 `scalar/scalars/all` 的区别
8. 解释 ORM 是怎么把类映射成表的
9. 解释 `Base` 为什么重要
10. 解释外键和 `relationship` 的基本用途
11. 看懂大部分简单的 CRUD 代码
12. 对事务的作用建立直观理解

## 二十一、这些能力如何映射回项目

现在你已经能更自然地读懂项目中的这些文件：

1. [app/db/session.py](/D:/Code/python/AILearningCoach/app/db/session.py)
2. [app/core/deps.py](/D:/Code/python/AILearningCoach/app/core/deps.py)
3. [app/models/user.py](/D:/Code/python/AILearningCoach/app/models/user.py)
4. [app/api/v1/endpoints/auth.py](/D:/Code/python/AILearningCoach/app/api/v1/endpoints/auth.py)

尤其是在 `auth` 相关接口中，你已经能看懂大部分数据库相关代码。

## 二十二、下一阶段学习重点

数据库这部分接下来不再作为完全独立主题继续深挖，而是要进入“在项目业务中巩固”的阶段。

下一步最适合的是：

1. 以 [auth.py](/D:/Code/python/AILearningCoach/app/api/v1/endpoints/auth.py) 为基础
2. 学习 HTTP、JWT、令牌、鉴权、加密的最小必要知识
3. 在理解认证流程的同时，继续巩固数据库查询、对象创建、事务提交这些内容

等认证这一层打通之后，再继续进入其他主要 API 和 AI 主链路。
