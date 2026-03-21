# 通用知识摄取系统实现计划

> **面向 AI 代理的工作说明：** 建议使用 `superpowers:executing-plans` 或 `superpowers:subagent-driven-development` 按任务顺序执行。每个步骤使用复选框（`- [ ]`）跟踪进度。
>
> **目标：** 将现有单一 Markdown 导入脚本升级为支持 `txt`、`docx`、`md`、`pdf` 的通用知识摄取系统，并完成 PostgreSQL 主存储、Milvus 轻索引、图片资产关联与检索侧引用适配。
>
> **架构：** 新增统一 ingest 模块，按 `LoaderRegistry -> Loader -> Splitter -> PersistenceService` 组织导入流程；使用 PostgreSQL 保存文档、chunk、资产与关系，使用 Milvus 保存向量索引与轻量检索字段；离线导入通过 `ingest_jobs` 记录执行状态。
>
> **技术栈：** Python、FastAPI、SQLAlchemy、Alembic、LangChain、MinerU、PostgreSQL、Milvus、Pytest

---

## 文件结构

- 创建：`D:/Code/python/AILearningCoach/app/ai/rag/ingest/__init__.py`
- 创建：`D:/Code/python/AILearningCoach/app/ai/rag/ingest/base.py`
- 创建：`D:/Code/python/AILearningCoach/app/ai/rag/ingest/models.py`
- 创建：`D:/Code/python/AILearningCoach/app/ai/rag/ingest/registry.py`
- 创建：`D:/Code/python/AILearningCoach/app/ai/rag/ingest/splitter.py`
- 创建：`D:/Code/python/AILearningCoach/app/ai/rag/ingest/persistence.py`
- 创建：`D:/Code/python/AILearningCoach/app/ai/rag/ingest/pipeline.py`
- 创建：`D:/Code/python/AILearningCoach/app/ai/rag/ingest/loaders/__init__.py`
- 创建：`D:/Code/python/AILearningCoach/app/ai/rag/ingest/loaders/langchain_loader.py`
- 创建：`D:/Code/python/AILearningCoach/app/ai/rag/ingest/loaders/mineru_pdf_loader.py`
- 修改：`D:/Code/python/AILearningCoach/app/models/knowledge.py`
- 修改：`D:/Code/python/AILearningCoach/app/models/__init__.py`
- 创建：`D:/Code/python/AILearningCoach/alembic/versions/<timestamp>_refactor_knowledge_ingest_schema.py`
- 修改：`D:/Code/python/AILearningCoach/app/ai/rag/milvus_client.py`
- 修改：`D:/Code/python/AILearningCoach/app/ai/rag/retriever.py`
- 修改：`D:/Code/python/AILearningCoach/app/ai/rag/generator.py`
- 修改：`D:/Code/python/AILearningCoach/scripts/ingest.py`
- 创建：`D:/Code/python/AILearningCoach/tests/ai/rag/test_ingest_registry.py`
- 创建：`D:/Code/python/AILearningCoach/tests/ai/rag/test_splitter.py`
- 创建：`D:/Code/python/AILearningCoach/tests/ai/rag/test_persistence.py`
- 创建：`D:/Code/python/AILearningCoach/tests/ai/rag/test_retriever_citations.py`

## 任务 1：重构知识库数据模型

**文件：**

- 修改：`D:/Code/python/AILearningCoach/app/models/knowledge.py`
- 修改：`D:/Code/python/AILearningCoach/app/models/__init__.py`
- 创建：`D:/Code/python/AILearningCoach/alembic/versions/<timestamp>_refactor_knowledge_ingest_schema.py`
- 测试：`D:/Code/python/AILearningCoach/tests/ai/rag/test_persistence.py`

- [ ] **步骤 1：为新知识模型编写失败测试与最小断言**

```python
def test_knowledge_models_expose_document_chunk_asset_relationships():
    ...
```

- [ ] **步骤 2：运行目标测试并确认当前失败**

运行：

```bash
pytest tests/ai/rag/test_persistence.py -q
```

预期：

- 因模型不存在或字段不匹配而失败。

- [ ] **步骤 3：重写知识模型**

实现以下模型与字段：

- `KnowledgeDocument`
- `KnowledgeChunk`
- `KnowledgeAsset`
- `KnowledgeChunkAsset`
- `IngestJob`

实现要求：

- 使用应用层生成的字符串主键或 UUID 字段。
- `source_path` 使用规范化路径语义。
- `KnowledgeChunk` 保存 `vector_id`、页码与 `meta_info`。
- `KnowledgeChunkAsset` 明确表达 chunk 与图片的关系。

- [ ] **步骤 4：编写 Alembic 迁移**

迁移应完成：

- 移除旧讲义语义字段。
- 创建新知识库相关表。
- 添加必要索引与外键。

- [ ] **步骤 5：运行模型与迁移相关测试**

运行：

```bash
pytest tests/ai/rag/test_persistence.py -q
```

预期：

- 测试通过。

- [ ] **步骤 6：提交阶段性变更**

```bash
git add app/models/knowledge.py app/models/__init__.py alembic/versions/<timestamp>_refactor_knowledge_ingest_schema.py tests/ai/rag/test_persistence.py
git commit -m "refactor: redesign knowledge ingest schema"
```

## 任务 2：建立统一 ingest 基础设施

**文件：**

- 创建：`D:/Code/python/AILearningCoach/app/ai/rag/ingest/base.py`
- 创建：`D:/Code/python/AILearningCoach/app/ai/rag/ingest/models.py`
- 创建：`D:/Code/python/AILearningCoach/app/ai/rag/ingest/registry.py`
- 创建：`D:/Code/python/AILearningCoach/app/ai/rag/ingest/splitter.py`
- 创建：`D:/Code/python/AILearningCoach/app/ai/rag/ingest/__init__.py`
- 测试：`D:/Code/python/AILearningCoach/tests/ai/rag/test_ingest_registry.py`
- 测试：`D:/Code/python/AILearningCoach/tests/ai/rag/test_splitter.py`

- [ ] **步骤 1：为 registry 与 splitter 编写失败测试**

测试应覆盖：

- 按扩展名选择 loader
- 不支持文件类型时报错
- splitter 生成稳定 chunk 顺序
- splitter 保留元数据与关联资产键

- [ ] **步骤 2：运行测试并确认失败**

运行：

```bash
pytest tests/ai/rag/test_ingest_registry.py tests/ai/rag/test_splitter.py -q
```

预期：

- 因模块缺失而失败。

- [ ] **步骤 3：实现基础接口与中间数据模型**

实现内容：

- `BaseDocumentLoader`
- `IngestedDocument`
- `IngestedChunk`
- `IngestedAsset`

要求：

- `chunk_id`、`asset_key` 由应用层生成。
- 所有文件读取接口默认按 UTF-8 处理；若三方 loader 内部负责读取，则在调用边界显式声明 UTF-8 前提。

- [ ] **步骤 4：实现 `LoaderRegistry` 与统一 `Splitter`**

要求：

- `LoaderRegistry` 支持按扩展名注册与查找。
- `Splitter` 使用 LangChain 文本切分器或等价实现。
- `Splitter` 输出与存储模型兼容的稳定 chunk 序列。

- [ ] **步骤 5：运行测试**

运行：

```bash
pytest tests/ai/rag/test_ingest_registry.py tests/ai/rag/test_splitter.py -q
```

预期：

- 测试通过。

- [ ] **步骤 6：提交阶段性变更**

```bash
git add app/ai/rag/ingest/base.py app/ai/rag/ingest/models.py app/ai/rag/ingest/registry.py app/ai/rag/ingest/splitter.py app/ai/rag/ingest/__init__.py tests/ai/rag/test_ingest_registry.py tests/ai/rag/test_splitter.py
git commit -m "feat: add ingest foundation modules"
```

## 任务 3：实现 LangChain 文档加载器

**文件：**

- 创建：`D:/Code/python/AILearningCoach/app/ai/rag/ingest/loaders/langchain_loader.py`
- 创建：`D:/Code/python/AILearningCoach/app/ai/rag/ingest/loaders/__init__.py`
- 测试：`D:/Code/python/AILearningCoach/tests/ai/rag/test_ingest_registry.py`

- [ ] **步骤 1：为 `txt/docx/md` 加载行为补充失败测试**

测试应覆盖：

- 支持的扩展名集合
- 按扩展名选择对应 LangChain loader
- 输出统一 `IngestedDocument`

- [ ] **步骤 2：运行测试并确认失败**

运行：

```bash
pytest tests/ai/rag/test_ingest_registry.py -q
```

- [ ] **步骤 3：实现 `LangChainDocumentLoader`**

要求：

- 支持 `txt`、`docx`、`md`
- 保留文件名、来源路径、基础 metadata
- 不在 loader 中做切分和持久化

- [ ] **步骤 4：运行测试**

运行：

```bash
pytest tests/ai/rag/test_ingest_registry.py -q
```

- [ ] **步骤 5：提交阶段性变更**

```bash
git add app/ai/rag/ingest/loaders/langchain_loader.py app/ai/rag/ingest/loaders/__init__.py tests/ai/rag/test_ingest_registry.py
git commit -m "feat: add langchain document loader"
```

## 任务 4：实现 MinerU PDF 加载器与资产提取

**文件：**

- 创建：`D:/Code/python/AILearningCoach/app/ai/rag/ingest/loaders/mineru_pdf_loader.py`
- 测试：`D:/Code/python/AILearningCoach/tests/ai/rag/test_persistence.py`

- [ ] **步骤 1：为 PDF 资产提取与关联规则编写失败测试**

测试应覆盖：

- MinerU 输出解析为文本与图片资产
- 资产路径保存为相对路径
- 生成 `related_asset_keys`
- 使用“邻近块优先，同页回退”的关联规则

- [ ] **步骤 2：运行测试并确认失败**

运行：

```bash
pytest tests/ai/rag/test_persistence.py -q
```

- [ ] **步骤 3：实现 `MinerUPdfLoader`**

要求：

- 优先消费 MinerU 的结构化结果
- 解析图片 caption、页码、路径与结构化位置
- 资产落到稳定目录 `data/knowledge_assets/<document_id>/<job_id>/...`
- 数据库存储相对路径或对象存储 key

- [ ] **步骤 4：实现 chunk 与 asset 的关联计算**

要求：

- 优先邻近块关联
- 找不到稳定邻近关系时回退同页关联

- [ ] **步骤 5：运行测试**

运行：

```bash
pytest tests/ai/rag/test_persistence.py -q
```

- [ ] **步骤 6：提交阶段性变更**

```bash
git add app/ai/rag/ingest/loaders/mineru_pdf_loader.py tests/ai/rag/test_persistence.py
git commit -m "feat: add mineru pdf loader and asset extraction"
```

## 任务 5：实现离线持久化与导入主流程

**文件：**

- 创建：`D:/Code/python/AILearningCoach/app/ai/rag/ingest/persistence.py`
- 创建：`D:/Code/python/AILearningCoach/app/ai/rag/ingest/pipeline.py`
- 修改：`D:/Code/python/AILearningCoach/app/ai/rag/milvus_client.py`
- 修改：`D:/Code/python/AILearningCoach/scripts/ingest.py`
- 测试：`D:/Code/python/AILearningCoach/tests/ai/rag/test_persistence.py`

- [ ] **步骤 1：为离线导入状态与双库写入补充失败测试**

测试应覆盖：

- 创建 `ingest_jobs`
- 整批清理旧数据再重建
- Milvus 保存 `chunk_id/document_id/vector_id`
- 导入失败时任务状态变为 `failed`

- [ ] **步骤 2：运行测试并确认失败**

运行：

```bash
pytest tests/ai/rag/test_persistence.py -q
```

- [ ] **步骤 3：扩展 `MilvusClient`**

要求：

- 支持插入 `chunk_id`、`document_id`、`file_type`、`page_idx`、`preview_text`
- 支持按 `document_id` 或 `source_path` 清理旧索引

- [ ] **步骤 4：实现 `PersistenceService`**

要求：

- 写入文档、chunk、资产、关系与任务状态
- 导入前可清理旧 PG 与 Milvus 数据
- 成功后任务标记为 `succeeded`
- 失败后任务标记为 `failed`

- [ ] **步骤 5：实现 `IngestPipeline` 与重写 `scripts/ingest.py`**

要求：

- 主入口负责扫描目录并调用 registry
- 不再沿用旧版 `DocumentProcessor`
- 统一使用新 ingest 模块完成导入

- [ ] **步骤 6：运行测试**

运行：

```bash
pytest tests/ai/rag/test_persistence.py -q
```

- [ ] **步骤 7：提交阶段性变更**

```bash
git add app/ai/rag/ingest/persistence.py app/ai/rag/ingest/pipeline.py app/ai/rag/milvus_client.py scripts/ingest.py tests/ai/rag/test_persistence.py
git commit -m "feat: implement offline ingest pipeline"
```

## 任务 6：适配检索与引用输出

**文件：**

- 修改：`D:/Code/python/AILearningCoach/app/ai/rag/retriever.py`
- 修改：`D:/Code/python/AILearningCoach/app/ai/rag/generator.py`
- 测试：`D:/Code/python/AILearningCoach/tests/ai/rag/test_retriever_citations.py`

- [ ] **步骤 1：为新的 citation 结构编写失败测试**

测试应覆盖：

- 检索结果通过 `chunk_id` 回查 PostgreSQL
- citation 返回文档名、文件类型、页码、来源路径
- 若有关联图片，则 citation 带资产列表

- [ ] **步骤 2：运行测试并确认失败**

运行：

```bash
pytest tests/ai/rag/test_retriever_citations.py -q
```

- [ ] **步骤 3：重写 `RAGRetriever`**

要求：

- 不再依赖旧讲义字段 `lecture_number/section`
- 从 Milvus 取回 `chunk_id/document_id`
- 回 PostgreSQL 批量查询 chunk、文档、关系与资产
- 生成新的上下文与 citation 信息

- [ ] **步骤 4：调整 `RAGGenerator`**

要求：

- 使用新的来源结构
- 保持非流式与流式接口兼容
- 无图片时返回空资产列表，不报错

- [ ] **步骤 5：运行测试**

运行：

```bash
pytest tests/ai/rag/test_retriever_citations.py -q
```

- [ ] **步骤 6：提交阶段性变更**

```bash
git add app/ai/rag/retriever.py app/ai/rag/generator.py tests/ai/rag/test_retriever_citations.py
git commit -m "refactor: adapt rag retrieval to new knowledge schema"
```

## 任务 7：端到端验证与清理

**文件：**

- 修改：`D:/Code/python/AILearningCoach/docs/superpowers/specs/2026-03-21-unified-knowledge-ingest-design.md`（仅在实现偏差时）
- 修改：相关测试文件（如需）

- [ ] **步骤 1：执行后端核心测试**

运行：

```bash
pytest tests/ai/rag -q
```

预期：

- 新增的 ingest 与检索相关测试全部通过。

- [ ] **步骤 2：执行导入脚本冒烟验证**

运行：

```bash
python scripts/ingest.py <sample_data_dir>
```

预期：

- 离线导入成功。
- PostgreSQL 与 Milvus 中生成对应记录。
- `ingest_jobs` 状态为 `succeeded`。

- [ ] **步骤 3：执行 RAG 检索冒烟验证**

运行：

```bash
pytest tests/ai/rag/test_retriever_citations.py -q
```

预期：

- citation 中包含文档来源与图片资产信息。

- [ ] **步骤 4：检查实现与 spec 是否一致**

核对内容：

- 是否仍为离线导入语义
- 是否保留稳定 ID
- 是否存在 `knowledge_chunk_assets`
- 是否使用规范化 `source_path`
- 是否将资产落到稳定目录

- [ ] **步骤 5：提交最终集成变更**

```bash
git add .
git commit -m "feat: ship unified knowledge ingest system"
```

## 风险与注意事项

- 当前项目运行在 Windows native + PowerShell 环境，读取本地文本文件时默认显式使用 UTF-8。
- `docx` 与 `pdf` 依赖三方工具链，测试中应尽量使用 mock 或最小样例，避免把外部工具不稳定性带入单元测试。
- 旧 `retriever.py` 与 `generator.py` 强依赖讲义语义，改造时要一次性替换来源格式，避免新旧字段混用。
- `MilvusClient` 的字段调整将影响现有集合 schema，必要时需要明确重建集合策略。
- 若 Alembic 无法平滑迁移旧数据，优先保证新结构正确，再决定是否提供一次性数据清理脚本。
