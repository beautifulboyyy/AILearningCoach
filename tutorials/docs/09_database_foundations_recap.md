# 数据库基础学习总结

这份文档总结了本阶段的数据库学习内容。目标不是把数据库一次学完，而是先建立足够清晰的整体框架，方便后续继续学习 CRUD、事务、Session 和项目中的数据库实现。

## 本阶段学到了什么

这一阶段主要完成了三件事：

1. 建立数据库的整体层级认知
2. 通过独立实验理解配置、建库、schema、模型和建表
3. 开始理解 ORM 和表关系，但还没有深入 CRUD 与事务细节

## 一、数据库整体层级

目前已经建立了 PostgreSQL 的基本层级观：

1. 服务器实例
2. 数据库
3. schema
4. 表

结合你在 PyCharm 数据库面板里的观察，现在可以这样理解：

1. `postgres`、`ai_learning_coach`、`db_learning_lab` 是三个数据库
2. 每个数据库下面都有多个 schema
3. schema 下面才是具体表

一句话记忆：

数据库不是直接装表的，表属于某个 schema，schema 属于某个数据库。

## 二、PostgreSQL 中几个重要对象

### 1. `postgres` 数据库

`postgres` 是 PostgreSQL 默认存在的数据库，一般不需要手动创建。

它的作用可以理解成：

1. 一个默认可连接的数据库
2. 方便执行管理类操作，比如 `CREATE DATABASE`

它不是“全局管理信息库”，而是一个默认存在、方便连接的普通数据库。

### 2. `public` schema

`public` 是默认 schema。

如果你没有显式指定 schema，表通常就会建在 `public` 下面。

### 3. `information_schema`

这是标准化的数据库结构信息视图，主要用于查看：

1. 表
2. 列
3. 约束
4. 其他结构信息

它更像“数据库结构查询区”。

### 4. `pg_catalog`

这是 PostgreSQL 的系统目录，保存数据库内部系统对象和元数据。

它更像“PostgreSQL 内部系统区”。

### 5. 自定义 schema：`lab`

我们创建的 `lab` schema 是自己的业务分组，用于隔离学习实验中的表：

1. `lab.students`
2. `lab.wallets`
3. `lab.transfer_logs`

它的价值是：

1. 做逻辑分组
2. 和默认 `public` 隔离
3. 帮助理解 PostgreSQL 的命名空间机制

## 三、独立实验室的目标

为了不直接上项目复杂数据库逻辑，我们专门建立了一套独立实验：

目录：
[tutorials/database_lab](/D:/Code/python/AILearningCoach/tutorials/database_lab)

它使用独立数据库：

`db_learning_lab`

这样做的好处是：

1. 不污染项目业务库
2. 可以反复练习建库、建表和删数据
3. 有利于先学原理，再回到项目

## 四、配置文件的理解

文件：
[config.py](/D:/Code/python/AILearningCoach/tutorials/database_lab/config.py)

你已经理解了这几个最重要的配置：

1. `DB_HOST`
2. `DB_PORT`
3. `DB_USER`
4. `DB_PASSWORD`

它们决定如何连接 PostgreSQL。

### 1. `os.getenv()` 的意义

比如：

```python
DB_HOST = os.getenv("DB_LAB_HOST", "localhost")
```

意思是：

1. 先从系统环境变量中读取 `DB_LAB_HOST`
2. 如果没有，就使用默认值 `localhost`

所以这个实验室不依赖额外 `.env` 文件也能运行，因为已经给了默认值。

### 2. `ADMIN_DB` 和 `LAB_DB`

你已经理解这两个目标数据库的区别：

1. `ADMIN_DB = "postgres"`
用于连接默认数据库，执行“创建数据库”这类操作

2. `LAB_DB = "db_learning_lab"`
用于连接学习数据库，后续建 schema、建表、做 CRUD 都在这里完成

一句话记忆：

先连接已有库建新库，再连接新库做实验。

### 3. `LAB_SCHEMA`

`LAB_SCHEMA = "lab"` 表示我们在学习数据库里使用 `lab` 这个 schema。

schema 可以理解成：

数据库内部的逻辑分组 / 命名空间。

## 五、Engine 的理解

在创建数据库和建表时都出现了 `engine`。

你已经建立了一个很好的类比：

`engine` 类似一个数据库总客户端，像 OpenAI 的 client。

它的作用是：

1. 知道要连接哪个数据库
2. 知道用什么驱动连接
3. 负责创建具体连接
4. 管理数据库连接相关资源

一句话记忆：

`engine` 是数据库操作的总入口，不是某一条具体 SQL 的结果。

## 六、数据库连接 URL 的理解

比如：

```python
postgresql+psycopg2://postgres:postgres@localhost:5432/postgres
```

可以拆成：

1. `postgresql`
数据库类型

2. `psycopg2`
PostgreSQL Python 驱动

3. `postgres:postgres`
用户名和密码

4. `localhost:5432`
数据库服务地址和端口

5. `/postgres`
要连接的数据库名

这个 URL 的作用就是告诉 SQLAlchemy：

“用什么方式，去哪里，连接哪个数据库。”

## 七、`AUTOCOMMIT` 的理解

在建库脚本里用了：

```python
create_engine(..., isolation_level="AUTOCOMMIT")
```

目前已经理解：

1. 普通数据库操作经常放在事务里
2. 但 `CREATE DATABASE` 这类数据库级操作不适合走普通事务块
3. 所以这里用 `AUTOCOMMIT`，让命令直接生效

一句话记忆：

建库这种操作更像“管理命令”，不是普通业务事务写入。

## 八、`engine.connect()` 和 `engine.begin()` 的区别

### 1. `engine.connect()`

表示：

拿一条具体数据库连接来执行命令。

适合：

1. 简单管理操作
2. 普通执行 SQL

### 2. `engine.begin()`

表示：

拿一条连接，并自动开启事务。

适合：

1. 多步结构初始化
2. 希望多步操作要么一起成功，要么一起回滚

你已经理解了它在建 schema 和建表场景下的意义：

避免半途失败留下不完整结构。

## 九、结果集对象和 `scalar()`

在建库脚本中，学习了：

```python
connection.execute(...).scalar()
```

这里你已经建立了关键认知：

1. `execute()` 返回的是结果集对象，不是直接的值
2. 数据库结果本质上可以看成二维结构：多行多列
3. 图形工具里显示成“小表格”，只是可视化渲染
4. `.scalar()` 的作用是取结果中的第一行第一列

比如：

```python
[(1,)]
```

经过 `.scalar()` 后，得到：

```python
1
```

## 十、ORM 的基础理解

这一阶段已经开始接触 ORM。

ORM 的核心思想是：

把关系型数据库中的表，映射成 Python 类。

对应关系如下：

1. 表 -> 类
2. 行 -> 类实例
3. 列 -> 类属性

你现在已经理解：

1. `Student` 类对应 `lab.students` 表
2. 类里的字段定义，对应数据库表的列和约束
3. 这是用 Python 代码表达表结构的一种方式

## 十一、`Base` 基类的意义

你在 `models.py` 中注意到了一个非常重要的点：

```python
class Base(DeclarativeBase):
    pass
```

虽然这个类表面上什么都没做，但它非常关键。

它的作用是：

1. 作为所有 ORM 模型的共同父类
2. 统一收集所有模型的元数据
3. 让 SQLAlchemy 能通过 `Base.metadata.create_all(...)` 一次性创建所有表

这是 ORM 中非常重要的一种最佳实践。

一句话记忆：

`Base` 不是业务类，而是所有模型的统一注册中心。

## 十二、模型文件里几个关键导入

在 `models.py` 中，你学习了：

```python
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
```

目前的理解如下：

1. `DeclarativeBase`
定义 ORM 基类

2. `Mapped`
给 ORM 属性做类型标注

3. `mapped_column`
定义数据库列

4. `relationship`
定义 ORM 层对象之间的关系导航

## 十三、`__repr__` 的理解

你注意到每个模型类里都有 `__repr__`，这个理解也已经到位：

1. 它是对象的可读输出定义
2. 用来替代默认难读的对象地址表示
3. 类似 Java 里的 `toString()`

这在调试、打印、日志里非常有帮助。

## 十四、外键的基础理解

这一阶段也开始接触了外键。

外键可以理解成：

一张表中的某个字段，用来引用另一张表的主键。

它的作用有两个：

1. 表达表和表之间的关系
2. 保证引用的数据真实存在

例如在转账记录里：

1. `from_wallet_id`
2. `to_wallet_id`

都引用 `wallets.id`

这表示：

每条转账记录都必须对应真实存在的钱包。

## 十五、关系和 `relationship` 的初步理解

这是目前还在消化中的部分，但已经建立了第一层理解。

你已经理解：

1. 外键属于数据库层约束
2. `relationship` 不是必须的
3. `relationship` 的主要作用是让 Python 代码更方便访问关联对象

比如：

1. `log.from_wallet`
2. `wallet.outgoing_logs`

这类写法依赖 ORM 关系定义，而不是单纯依赖外键本身。

### 当前已经理解到的点

1. `Mapped[list["TransferLog"]]` 表示一个对象可以关联多个转账记录
2. 一条 `TransferLog` 对应一个 `from_wallet` 和一个 `to_wallet`
3. `back_populates` 是把双向关系两边配对起来

目前这部分已经建立基础，但仍需要结合 CRUD 实操继续加深。

## 十六、当前阶段还没有深入的内容

今天刻意没有深入学习：

1. Session 的完整机制
2. CRUD 的完整执行过程
3. 事务中的 `commit` 和 `rollback`
4. SQLAlchemy 查询结果的更多取值方式
5. 项目主业务库中的复杂模型关系

这些会在下一阶段专门学习。

## 十七、本阶段的知识成果

截至今天，你已经完成了数据库学习最关键的第一层搭建：

1. 知道 PostgreSQL 的层级结构
2. 知道数据库、schema、表之间的关系
3. 知道为什么要先连默认库再创建新库
4. 知道配置文件里各数据库参数的作用
5. 知道 `engine` 是数据库总入口
6. 知道 `connect()` 和 `begin()` 的区别
7. 知道查询结果不是直接值，而是结果集对象
8. 知道 ORM 是“用类映射表”
9. 知道 `Base` 基类为什么重要
10. 知道外键和 `relationship` 的基本用途

## 十八、下一阶段学习重点

下一步建议进入：

1. `03_crud_and_transaction_demo.py`

重点学习：

1. CRUD 的完整流程
2. `Session` 是什么
3. `add / commit / rollback / delete / query`
4. 为什么事务对业务一致性重要

等这条独立实验室主线学透之后，再回到项目中的：

[app/core/deps.py](/D:/Code/python/AILearningCoach/app/core/deps.py)
[app/db/session.py](/D:/Code/python/AILearningCoach/app/db/session.py)
[app/models/user.py](/D:/Code/python/AILearningCoach/app/models/user.py)
[app/api/v1/endpoints/auth.py](/D:/Code/python/AILearningCoach/app/api/v1/endpoints/auth.py)

去读项目里的真实数据库实现。
