# 通用知识摄取系统设计方案

**设计日期：** 2026-03-21

**适用范围：** AI Learning Coach 项目的通用知识文档导入、切分、向量化、持久化与溯源能力

## 1. 背景与目标

当前项目中的 [`scripts/ingest.py`](/D:/Code/python/AILearningCoach/scripts/ingest.py) 仅支持单一 Markdown 文件导入，并且处理流程、元数据提取、文本切分与持久化逻辑高度耦合，主要面向课程讲义场景，已经无法满足后续通用知识库建设需求。

本方案的目标是将现有导入能力升级为一套面向通用知识文档的摄取系统，支持多种常见文件格式，并为 RAG（Retrieval-Augmented Generation，检索增强生成）问答提供稳定的检索与出处溯源能力。

第一版目标如下：

- 支持 `txt`、`docx`、`md`、`pdf` 四类文件导入。
- 为 `txt`、`docx`、`md` 使用 LangChain 体系完成加载。
- 为 `pdf` 使用 MinerU 完成解析。
- 将文档、文本块、图片资产等主数据统一持久化到 PostgreSQL。
- 将向量索引写入 Milvus。
- 支持基于文件哈希的去重与文档级增量更新。
- 支持回答时回溯文档来源、页码与关联图片。

明确不纳入第一版的内容如下：

- 不处理 `html` 文件。
- 不实现图片独立向量化检索。
- 不实现块级差异比对式增量更新。

## 2. 设计原则

本方案遵循以下设计原则：

- **通用优先：** 不再围绕“课程讲义”建模，而是围绕“通用知识文档”建模。
- **职责单一：** 解析、切分、向量化、持久化分别由独立组件负责。
- **PostgreSQL 为主：** PostgreSQL 保存事实数据，Milvus 仅承担向量索引职责。
- **离线维护：** 文档导入是离线维护操作，导入期间不保证检索可用。
- **可追溯：** 每个 chunk 都应能追溯到原始文档、页码以及相关资产。
- **可扩展：** 新增文件类型时，仅需新增 loader 并注册。
- **渐进演进：** 第一版优先完成稳定链路，不引入过度设计。

## 3. 目标架构

### 3.1 处理流程

统一摄取流程如下：

1. 扫描输入目录中的候选文件。
2. 根据文件扩展名从注册中心选择合适的 loader。
3. 将原始文件解析为统一的文档对象。
4. 将统一文档对象交由切分器生成 chunk。
5. 调用 embedding 服务生成向量。
6. 将文档、chunk、资产与关系信息写入 PostgreSQL。
7. 将向量索引写入 Milvus。
8. 记录导入任务状态、异常信息与更新时间。

### 3.2 组件划分

建议新增如下模块：

```text
app/ai/rag/ingest/
  base.py
  registry.py
  models.py
  splitter.py
  pipeline.py
  persistence.py
  loaders/
    langchain_loader.py
    mineru_pdf_loader.py
```

各模块职责如下：

- `base.py`
  - 定义基础接口，例如 `BaseDocumentLoader`。
- `registry.py`
  - 维护文件扩展名与 loader 的映射关系。
- `models.py`
  - 定义 ingest 过程中的统一数据结构。
- `splitter.py`
  - 提供统一的文本切分能力。
- `pipeline.py`
  - 串联扫描、加载、切分、向量化与持久化。
- `persistence.py`
  - 封装 PostgreSQL 与 Milvus 的写入、任务状态记录与清理逻辑。
- `loaders/langchain_loader.py`
  - 负责 `txt`、`docx`、`md` 文件解析。
- `loaders/mineru_pdf_loader.py`
  - 负责 `pdf` 文件解析及 PDF 资产提取。

## 4. Loader 设计

### 4.1 Loader 分类

第一版采用两类 loader：

- `LangChainDocumentLoader`
  - 支持：`txt`、`docx`、`md`
  - 内部根据扩展名选择对应的 LangChain loader
- `MinerUPdfLoader`
  - 支持：`pdf`
  - 调用 MinerU 解析 PDF 文本、结构与图片资产

不再为 Markdown 保留旧版专用处理逻辑，后续 Markdown 文档统一走 `LangChainDocumentLoader`。

### 4.2 Loader 接口

建议统一接口如下：

```python
class BaseDocumentLoader(ABC):
    supported_extensions: set[str]

    def can_handle(self, path: Path) -> bool:
        ...

    async def load(self, path: Path) -> list[IngestedDocument]:
        ...
```

采用 `list[IngestedDocument]` 作为返回值，而不是单个对象，原因如下：

- 某些格式后续可能天然拆解为多个逻辑文档。
- MinerU 的结构化输出未来可能扩展为章节级或页面级结果。
- 统一接口后更易扩展。

### 4.3 统一中间数据模型

建议在 ingest 层定义两类核心结构：

```python
@dataclass
class IngestedDocument:
    source_path: str
    file_name: str
    file_type: str
    content: str
    loader_name: str
    page_start: int | None = None
    page_end: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    assets: list["IngestedAsset"] = field(default_factory=list)
```

```python
@dataclass
class IngestedChunk:
    chunk_id: str
    source_path: str
    file_type: str
    chunk_index: int
    content: str
    page_start: int | None = None
    page_end: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    related_asset_keys: list[str] = field(default_factory=list)
```

图片等资产建议使用独立结构：

```python
@dataclass
class IngestedAsset:
    asset_key: str
    asset_type: str
    page_idx: int | None
    asset_path: str
    caption: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
```

说明如下：

- `chunk_id`、`asset_key` 等跨系统关联标识由应用层生成，避免依赖数据库自增主键串联 PostgreSQL 与 Milvus。
- `source_path` 在进入 ingest 流程前应先规范化，默认以项目工作目录为基准保存相对路径；若文件不在工作目录内，则保存规范化绝对路径。

## 5. 文本切分策略

### 5.1 切分职责

切分逻辑不应内置于 loader 中，而应由统一的 `Splitter` 组件负责。原因如下：

- 不同 loader 负责“解析”，不负责“索引策略”。
- 后续若要针对不同来源配置不同切分策略，可在 pipeline 层分发。
- 切分逻辑集中后，更容易测试与迭代。

### 5.2 第一版切分策略

第一版建议采用统一文本切分方案：

- 优先使用 LangChain 的文本切分器。
- 支持配置 `chunk_size` 与 `chunk_overlap`。
- 保留页码、文档标题、章节标题等上游元数据。
- 对含图片的 PDF 文本，在必要时可插入轻量语义占位，如：
  - `[图示] 图 1：RAG 系统架构图`

这里强调：

- 不向原始 Markdown 文件反写数据库定位信息。
- 不将 `![](images/xxx.png)` 这类纯路径文本直接作为检索语义核心。
- 图片语义主要来自 caption、相邻正文与页码信息。

## 6. 持久化策略

### 6.1 总体原则

持久化采用“双库分工”策略：

- PostgreSQL 是事实来源库（source of truth）
- Milvus 是向量索引库

PostgreSQL 负责保存：

- 文档主记录
- chunk 正文
- 资产信息
- 导入状态
- 文件哈希
- 溯源信息

Milvus 负责保存：

- 向量
- 向量与 chunk 的映射
- 少量筛选字段

### 6.2 双库一致性与离线导入策略

由于 PostgreSQL 与 Milvus 无法构成单一事务，而当前场景明确为离线导入，因此第一版不为在线实时切换设计版本化激活机制。

第一版的一致性处理原则如下：

- 导入是离线维护操作，导入期间默认不保证检索可用。
- PostgreSQL 与 Milvus 不做跨库原子切换。
- 失败恢复依赖“清理后重跑”，而不是版本回切。
- 系统保留轻量级导入任务状态记录，用于追踪 `running`、`succeeded`、`failed` 等状态。

建议新增轻量任务记录语义，可通过独立的 `ingest_jobs` 表实现，或在等价位置记录导入状态。该任务记录至少应包含：

- `job_id`
- `source_path`
- `file_hash`
- `status`
- `error_message`
- `started_at`
- `finished_at`

导入约束如下：

1. 开始导入前，为目标文件创建一条任务记录，状态为 `running`。
2. 导入时允许先清理旧的 PostgreSQL 与 Milvus 数据，再整批重建。
3. 若任一阶段失败，任务状态标记为 `failed`，并保留错误信息。
4. 失败后允许通过再次清理并重新执行导入恢复一致性。
5. 只有导入链路全部完成后，任务状态才标记为 `succeeded`。

该策略适用于当前离线维护场景，避免在第一版引入不必要的在线版本切换复杂度。

### 6.3 为什么不继续双份完整存储 chunk 正文

旧实现中，Milvus 与 PostgreSQL 都保存了 chunk 文本，这种做法适合快速原型，但不适合作为长期方案。主要问题如下：

- 同一份正文存在两份事实来源，容易产生不一致。
- 文档更新后，两边同步成本高。
- 后续加入资产关联、文档状态管理、增量更新后，Milvus 不适合作为主业务存储。
- 若将来替换向量库，业务数据迁移成本过高。

因此，本方案建议：

- PostgreSQL 保存完整正文。
- Milvus 不再保存完整正文作为权威副本。
- Milvus 可选保存短 `preview_text` 以便调试与快速检查召回质量。

### 6.4 性能考量

Milvus 检索后回查 PostgreSQL 不会成为主要性能瓶颈，原因如下：

- RAG 一般只取 Top K 条结果，数量通常较小。
- PostgreSQL 可通过 `chunk_id IN (...)` 一次性批量回表。
- 主要耗时通常集中在 embedding、重排序与大模型推理，而不是回查少量 chunk。

因此，为了保证数据一致性与系统可维护性，优先选择“PostgreSQL 主存储 + Milvus 轻索引”的模式。

## 7. 数据模型设计

### 7.1 文档表：`knowledge_documents`

建议新增文档级模型，字段如下：

| 字段名 | 类型 | 说明 |
|---|---|---|
| `id` | UUID / 字符串主键 | 文档 ID，由应用层生成 |
| `source_path` | 字符串 | 规范化后的来源路径 |
| `file_name` | 字符串 | 文件名 |
| `file_type` | 字符串 | 文件类型，如 `pdf`、`md` |
| `loader_name` | 字符串 | 使用的 loader 名称 |
| `file_hash` | 字符串 | 原文件哈希，用于去重与增量更新 |
| `status` | 枚举 | 文档处理状态，如 `processing`、`processed`、`failed` |
| `meta_info` | JSON | 文档级扩展元数据 |
| `created_at` | 时间 | 创建时间 |
| `updated_at` | 时间 | 更新时间 |

### 7.2 Chunk 表：`knowledge_chunks`

建议保留 `KnowledgeChunk` 概念，但语义升级为通用文档 chunk：

| 字段名 | 类型 | 说明 |
|---|---|---|
| `id` | UUID / 字符串主键 | chunk ID，由应用层生成 |
| `document_id` | 外键 | 所属文档 |
| `chunk_index` | 整数 | 文档内 chunk 顺序 |
| `content` | 文本 | chunk 正文 |
| `vector_id` | 字符串 | 对应 Milvus 向量 ID |
| `page_start` | 整数，可空 | 起始页码 |
| `page_end` | 整数，可空 | 结束页码 |
| `meta_info` | JSON | chunk 级扩展元数据 |
| `created_at` | 时间 | 创建时间 |
| `updated_at` | 时间 | 更新时间 |

### 7.3 资产表：`knowledge_assets`

建议第一版即引入资产表，用于记录 PDF 图片等可追溯对象：

| 字段名 | 类型 | 说明 |
|---|---|---|
| `id` | UUID / 字符串主键 | 资产 ID，由应用层生成 |
| `document_id` | 外键 | 所属文档 |
| `asset_type` | 字符串 | 资产类型，第一版重点为 `image` |
| `page_idx` | 整数，可空 | 所在页码 |
| `asset_path` | 字符串 | 资产相对存储路径，不保存临时绝对路径 |
| `caption` | 文本，可空 | 图片说明 |
| `meta_info` | JSON | 结构化扩展信息，如 bbox |
| `created_at` | 时间 | 创建时间 |
| `updated_at` | 时间 | 更新时间 |

### 7.4 Chunk 与资产关系表：`knowledge_chunk_assets`

为保证回答阶段能够准确返回“命中 chunk 关联的图片”，第一版建议显式引入关系表，而不是仅依赖文档级资产归属。

建议字段如下：

| 字段名 | 类型 | 说明 |
|---|---|---|
| `id` | UUID / 字符串主键 | 关系 ID |
| `chunk_id` | 外键 | 所属 chunk |
| `asset_id` | 外键 | 所属资产 |
| `relation_type` | 字符串 | 关系类型，如 `adjacent`、`same_page` |
| `sort_order` | 整数 | 展示顺序 |
| `meta_info` | JSON | 关系级补充信息 |

`knowledge_chunks.meta_info` 中可冗余缓存 `related_asset_ids`，用于快速调试，但系统的权威关系来源应为 `knowledge_chunk_assets`。

### 7.5 导入任务表：`ingest_jobs`

为记录离线导入过程，建议新增轻量级任务表：

| 字段名 | 类型 | 说明 |
|---|---|---|
| `id` | UUID / 字符串主键 | 任务 ID |
| `source_path` | 字符串 | 规范化后的来源路径 |
| `file_hash` | 字符串 | 本次导入的文件哈希 |
| `status` | 枚举 | `running`、`succeeded`、`failed` |
| `error_message` | 文本，可空 | 失败原因 |
| `meta_info` | JSON | 导入参数、统计信息等 |
| `started_at` | 时间 | 开始时间 |
| `finished_at` | 时间，可空 | 结束时间 |

### 7.6 与现有模型的关系

现有 [`KnowledgeChunk`](/D:/Code/python/AILearningCoach/app/models/knowledge.py) 中的 `lecture_number` 与 `section` 具有明显讲义语义，不再适合作为通用知识摄取模型的核心字段。

本方案建议直接引入新的通用表结构与查询链路，彻底替换旧讲义语义，而不是在旧模型上继续兼容扩展。

## 8. 去重与增量更新

### 8.1 去重规则

第一版采用基于文件哈希的文档级去重：

- 读取文件内容后计算 `file_hash`。
- 若同一规范化 `source_path` 与同一哈希已存在，则跳过导入。
- 若同一路径存在，但哈希不同，则视为文档更新。
- 若路径不同但哈希相同，是否视为重复暂不强制处理，默认按不同来源文档入库。

### 8.2 增量更新规则

文档更新时，采用“文档级重建”策略：

1. 查出同一 `source_path` 的已有文档数据。
2. 清理旧的 PostgreSQL 记录、Milvus 向量与资产目录。
3. 基于新文件重新解析、切分并写入 PostgreSQL。
4. 将新向量写入 Milvus。
5. 导入成功后更新文档与任务状态。

本策略的优点如下：

- 实现复杂度低。
- 逻辑一致性强。
- 易于调试与回滚。
- 适合当前离线整批维护场景。

本策略的限制如下：

- 更新一个文档时，需要重建该文档全部 chunk。
- 导入期间默认不保证检索可用。

该限制在第一版可接受，后续若有必要，再评估块级差异更新。

## 9. PDF 资产追踪设计

### 9.1 数据来源

MinerU 解析 PDF 后，会产出结构化结果与图片目录。程序化处理时，应优先消费结构化结果，而不是仅依赖最终 Markdown 文本。

第一版中，图片资产主要记录以下信息：

- `asset_path`
- `caption`
- `page_idx`
- 结构化位置信息（如可用）

资产存储约定如下：

- 所有抽取资产应落到稳定目录，而非临时运行目录。
- 建议目录形式为 `data/knowledge_assets/<document_id>/<job_id>/...`，或使用等价的时间戳目录。
- 数据库中仅保存相对路径或对象存储 key，不保存临时绝对路径。
- 当旧数据被清理后，对应的历史资产目录由异步清理任务回收。

### 9.2 关联策略

chunk 与图片资产的关联采用“2 + 1”策略：

- **优先邻近块关联**
  - 图片前后相邻的正文块优先绑定该图片
- **退回同页关联**
  - 若无法建立稳定邻近关系，则回退为同页关联

该策略兼顾实现成本与结果质量，适合作为第一版默认规则。

### 9.3 回答阶段的使用方式

图片在第一版中的角色不是独立检索对象，而是文本命中后的辅助证据。

推荐流程如下：

1. 用户提问后，Milvus 返回命中的 chunk。
2. 系统根据 `chunk_id` 回查 PostgreSQL。
3. 若 chunk 关联图片资产，则同时取出相关图片。
4. 回答层在展示 citation 时附带图片信息。

这意味着：

- 检索主通道仍然是文本检索。
- 图片用于增强解释与出处展示。
- 第一版不做图片 embedding 与图片独立召回。

## 10. 检索与引用链路

推荐的 RAG 检索链路如下：

1. 将用户问题向量化。
2. 通过 Milvus 检索候选 chunk，返回 `vector_id`、`chunk_id`、`document_id` 等字段。
3. 使用 PostgreSQL 一次性批量回查 chunk 正文、文档信息、关系表与资产信息。
4. 将结果组装为 RAG 上下文。
5. 将 citation 信息一并传递给回答层。

建议回答层消费的 citation 结构至少包含：

- 文档名
- 文件类型
- chunk 文本
- 页码
- 原始来源路径
- 关联图片资产列表

## 11. 非目标与后续扩展

本方案明确不纳入第一版的内容如下：

- `html` 文件摄取
- 图片独立召回
- 多模态 embedding
- 表格与公式的专门索引策略
- 块级差异增量更新

后续可沿以下方向扩展：

- 新增 `pptx`、`xlsx` 等格式 loader
- 支持表格结构化入库
- 支持图像 caption 自动增强
- 支持多模态检索
- 支持块级差异更新

## 12. 实施建议

实施时建议按以下顺序推进：

1. 定义新的 PostgreSQL 模型与迁移脚本。
2. 定义统一 ingest 数据结构。
3. 完成 `LoaderRegistry` 与 `BaseDocumentLoader`。
4. 实现 `LangChainDocumentLoader`。
5. 实现 `MinerUPdfLoader`。
6. 实现统一 `Splitter`。
7. 实现 `PersistenceService`。
8. 重写导入主入口，替代旧版 [`scripts/ingest.py`](/D:/Code/python/AILearningCoach/scripts/ingest.py) 主流程。
9. 调整检索链路以适配新表结构与 citation 输出。

## 13. 结论

本方案将项目中的知识导入能力从“讲义 Markdown 导入脚本”升级为“通用知识摄取系统”，核心变化如下：

- 从单一格式导入转向多格式导入。
- 从讲义语义建模转向通用知识文档建模。
- 从 Milvus 与 PostgreSQL 双份完整正文存储，转向 PostgreSQL 主存储与 Milvus 轻索引分工。
- 从纯文本检索，升级为支持出处与图片资产溯源的 RAG 基础设施。

该方案在第一版中控制了复杂度，同时为后续格式扩展、资产增强与多模态能力预留了清晰边界。
