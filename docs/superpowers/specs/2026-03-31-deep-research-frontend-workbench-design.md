# Deep Research 前端工作台设计文档

> Goal: 为 Deep Research 后端提供一套高信息密度的单页研究工作台，承接“创建任务 -> 生成分析师 -> 人工确认 -> 运行进度 -> 查看最终报告”的完整流程。

## 设计结论

本次前端不复用通用任务看板 [TasksView.vue](D:/Code/python/AILearningCoach/.worktrees/feature-deep-research/frontend/src/views/tasks/TasksView.vue) 的四列管理方式，而是新增一套专门的 Deep Research 工作台。页面采用双栏结构：

1. 左栏负责任务轨道和新建任务。
2. 右栏负责当前任务的步骤化工作区。
3. 所有关键操作都在同一页面完成，避免列表页和详情页频繁跳转。

## 目标用户体验

用户进入页面后，应当能在一个视图里完成以下动作：

1. 创建研究任务。
2. 查看任务列表并切换当前任务。
3. 生成分析师并阅读分析师卡片。
4. 输入自然语言反馈重新生成分析师，或确认后开始研究。
5. 观察当前任务正在执行的阶段，例如检索中、讨论中、写报告中。
6. 在任务完成后直接阅读最终报告和引用链接。

## 页面信息架构

### 总体布局

- 左栏宽度约 `320px`
- 右栏为自适应主工作区
- 页面在桌面端保持双栏
- 平板和窄屏设备切换为“顶部任务抽屉 + 下方工作区”

### 左栏

左栏由上到下分为三段：

1. **新建任务区**
   - `topic`
   - `max_analysts`
   - 可选的分析师方向输入
   - 创建按钮

2. **任务列表区**
   - 展示已有 deep research 任务
   - 任务项显示主题、状态、更新时间
   - 支持按状态筛选

3. **危险操作区**
   - 删除当前任务

### 右栏

右栏由上到下分为三层：

1. **任务头部**
   - 主题
   - 状态
   - 分析师数量
   - 当前进度摘要

2. **流程工作区**
   - `pending` 时显示引导和“生成分析师”按钮
   - `awaiting_feedback` 时显示分析师确认面板
   - `running` 时显示运行时进度面板
   - `failed` 时显示失败说明和“删除重建”引导

3. **报告阅读区**
   - `completed` 时展示最终报告
   - 支持引言、主体、结论、引用的快速跳转

## 交互流程

### 1. 创建任务

- 用户在左栏填写主题和分析师数量
- 提交后创建任务并自动选中
- 创建成功后右栏进入 `pending` 引导态

### 2. 生成分析师

- 用户点击“生成分析师”
- 页面调用 `POST /tasks/{thread_id}/analysts`
- 成功后任务进入 `awaiting_feedback`
- 页面展示分析师卡片列表和确认区

### 3. 分析师确认

在 `awaiting_feedback` 态，页面提供两条主路径：

1. **确认并开始研究**
   - 调用 `POST /tasks/{thread_id}/feedback`
   - 请求体：`{ "action": "approve" }`

2. **根据反馈重新生成**
   - 用户输入自然语言反馈
   - 调用 `POST /tasks/{thread_id}/feedback`
   - 请求体：`{ "action": "regenerate", "feedback": "..." }`

### 4. 运行中展示

- 页面轮询：
  - `GET /tasks/{thread_id}`
  - `GET /tasks/{thread_id}/progress`
- 页面使用进度阶段和消息展示当前正在做的工作
- 任务进入 `completed` 或 `failed` 后停止轮询

### 5. 查看最终报告

- 任务完成后，从任务详情中的 `final_report` 渲染报告
- 引用区展示 URL 列表，并支持直接打开

## 组件拆分

### 页面组件

- `frontend/src/views/deep-research/DeepResearchWorkbench.vue`

职责：

- 组织整页布局
- 管理选中任务
- 控制各工作区显示逻辑

### 左栏组件

- `frontend/src/components/deep-research/ResearchComposer.vue`
- `frontend/src/components/deep-research/TaskRail.vue`

职责：

- 创建任务
- 展示任务列表
- 发出切换任务和删除任务事件

### 右栏组件

- `frontend/src/components/deep-research/TaskHeader.vue`
- `frontend/src/components/deep-research/AnalystReviewPanel.vue`
- `frontend/src/components/deep-research/ResearchProgressPanel.vue`
- `frontend/src/components/deep-research/ReportViewer.vue`

职责：

- 展示任务摘要
- 展示分析师确认界面
- 展示运行进度
- 渲染最终报告

## 状态设计

前端只维护与页面交互直接相关的状态，不增加复杂缓存层。

建议 store 字段：

- `tasks`
- `selectedTaskId`
- `currentTask`
- `progress`
- `listLoading`
- `actionLoading`
- `progressPolling`

轮询策略：

- `pending` 和 `awaiting_feedback` 时低频刷新任务详情
- `running` 时轮询详情和进度
- `completed` 和 `failed` 时停止轮询

## 接口映射

工作台只依赖以下正式接口：

- `POST /api/v1/deep-research/tasks`
- `GET /api/v1/deep-research/tasks`
- `GET /api/v1/deep-research/tasks/{thread_id}`
- `GET /api/v1/deep-research/tasks/{thread_id}/progress`
- `POST /api/v1/deep-research/tasks/{thread_id}/analysts`
- `POST /api/v1/deep-research/tasks/{thread_id}/feedback`
- `DELETE /api/v1/deep-research/tasks/{thread_id}`

## 视觉设计原则

本页不沿用传统后台“多列表格 + 大量按钮”的通用管理界面，而采用更像研究控制台的视觉语言。

### 视觉方向

- 左栏更沉稳，使用深灰蓝背景
- 右栏使用暖白或浅灰背景，提升阅读舒适度
- 主强调色使用钴蓝
- 次强调色使用琥珀橙
- 不使用紫色作为品牌重点色

### 阅读体验

- 报告区采用文档化排版
- 标题层级明显
- 引用区与正文视觉区分
- 进度区采用时间线或状态带，不做复杂图表

### 动效策略

- 页面初始加载使用轻量淡入和位移
- 状态切换使用短时过渡
- 不添加装饰性动画

## 响应式策略

### 桌面端

- 左右双栏并行展示
- 报告区支持长文滚动阅读

### 平板端

- 左栏收窄
- 任务列表允许折叠

### 手机端

- 左栏转为抽屉
- 工作区垂直堆叠
- 报告目录跳转改为顶部锚点按钮

## 代码落点

预计新增和修改的前端文件如下：

### 新增

- `frontend/src/views/deep-research/DeepResearchWorkbench.vue`
- `frontend/src/components/deep-research/ResearchComposer.vue`
- `frontend/src/components/deep-research/TaskRail.vue`
- `frontend/src/components/deep-research/TaskHeader.vue`
- `frontend/src/components/deep-research/AnalystReviewPanel.vue`
- `frontend/src/components/deep-research/ResearchProgressPanel.vue`
- `frontend/src/components/deep-research/ReportViewer.vue`
- `frontend/src/api/deepResearch.ts`
- `frontend/src/stores/deepResearch.ts`
- `frontend/src/types/deepResearch.d.ts`

### 修改

- `frontend/src/router/index.ts`
- `frontend/src/components/common/AppSidebar.vue`

### 清理

- 删除历史上的 deep research 前端草稿文件
- 不删除与其他业务共用的通用任务模块

## 错误处理

### 前端需覆盖的状态

- 创建任务失败
- 生成分析师失败
- 反馈提交失败
- 任务删除失败
- 轮询超时或接口报错

### 页面处理方式

- 使用靠近操作位置的错误提示
- 长流程中保留最近一次成功加载的内容
- 对 `failed` 任务明确提示“删除后重新创建”

## 测试策略

前端实现后至少验证以下内容：

1. 创建任务成功并自动选中
2. 生成分析师后正确进入确认态
3. `approve` 后能看到运行时进度变化
4. `regenerate` 后能刷新分析师卡片
5. 完成后能正确渲染最终报告与引用
6. 删除任务后列表和详情同步更新
7. 窄屏下布局不溢出、不出现横向滚动

## 非目标

当前版本不做以下内容：

- 不做复杂拖拽交互
- 不做任务批量操作
- 不做报告导出 PDF
- 不做引用质量评分
- 不做前端 SSE 流式接入

## 版本管理约束

- 所有前端实现都只在 `feature/deep-research` worktree 中进行
- `main` 保持干净，不承接本次前端实验状态
- 提交采用小步、单主题 commit

## 下一步

1. 基于本设计文档编写前端实现计划。
2. 建立 Deep Research 页面路由和侧边栏入口。
3. 按组件分层实现工作台。
4. 完成前后端联调与页面回归。
