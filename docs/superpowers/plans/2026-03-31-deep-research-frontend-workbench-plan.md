# Deep Research 前端工作台实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 基于现有 Deep Research 后端接口实现一套高信息密度的单页研究工作台，支持任务管理、分析师确认、运行进度查看和最终报告阅读。

**架构：** 前端新增一套 deep research 专用类型、API 和 Pinia store，并通过单页 `DeepResearchWorkbench` 组合左侧任务轨道和右侧工作区。工作区根据任务状态切换分析师确认、运行进度和报告阅读面板，轮询逻辑集中放在 store 中统一管理。

**技术栈：** Vue 3、TypeScript、Pinia、Vue Router、Element Plus、SCSS、Axios

---

## 文件结构

### 创建

- `frontend/src/types/deepResearch.d.ts`
  - Deep Research 任务、分析师、进度、请求体类型
- `frontend/src/api/deepResearch.ts`
  - 对接 `/api/v1/deep-research` 正式接口
- `frontend/src/stores/deepResearch.ts`
  - 任务列表、当前任务、进度、轮询和任务动作
- `frontend/src/views/deep-research/DeepResearchWorkbench.vue`
  - 页面主容器和双栏布局
- `frontend/src/components/deep-research/ResearchComposer.vue`
  - 新建任务表单
- `frontend/src/components/deep-research/TaskRail.vue`
  - 任务列表、筛选和删除入口
- `frontend/src/components/deep-research/TaskHeader.vue`
  - 当前任务摘要
- `frontend/src/components/deep-research/AnalystReviewPanel.vue`
  - 分析师确认与重生
- `frontend/src/components/deep-research/ResearchProgressPanel.vue`
  - 运行进度和阶段时间线
- `frontend/src/components/deep-research/ReportViewer.vue`
  - 最终报告和引用阅读

### 修改

- `frontend/src/api/index.ts`
  - 导出 Deep Research API
- `frontend/src/router/index.ts`
  - 注册 `deep-research` 路由
- `frontend/src/components/common/AppSidebar.vue`
  - 增加侧边栏入口

### 清理

- 删除历史 Deep Research 前端草稿文件（若存在且与新实现重复）

## 任务 1：建立数据类型与 API 封装

**文件：**
- 创建：`frontend/src/types/deepResearch.d.ts`
- 创建：`frontend/src/api/deepResearch.ts`
- 修改：`frontend/src/api/index.ts`
- 验证：`npm run build:check`

- [ ] 定义任务、分析师、进度和反馈请求类型
- [ ] 封装列表、详情、创建、删除、生成分析师、提交反馈、查询进度接口
- [ ] 在统一 API 出口中导出 `deepResearchApi`
- [ ] 运行 `npm run build:check`
- [ ] Commit：`feat(deep_research): 新增前端数据类型与接口封装`

## 任务 2：建立 Pinia store 和轮询机制

**文件：**
- 创建：`frontend/src/stores/deepResearch.ts`
- 测试：`npm run build:check`

- [ ] 维护 `tasks`、`selectedTaskId`、`currentTask`、`progress`、加载态
- [ ] 实现创建、加载列表、加载详情、删除、生成分析师、提交反馈
- [ ] 实现运行中轮询与停止轮询逻辑
- [ ] 处理 `pending / awaiting_feedback / running / completed / failed`
- [ ] 运行 `npm run build:check`
- [ ] Commit：`feat(deep_research): 新增前端任务状态管理`

## 任务 3：实现工作台左栏

**文件：**
- 创建：`frontend/src/components/deep-research/ResearchComposer.vue`
- 创建：`frontend/src/components/deep-research/TaskRail.vue`
- 测试：`npm run build:check`

- [ ] 实现新建任务表单和校验
- [ ] 实现任务列表、状态标签、选中态和空状态
- [ ] 提供删除入口和任务切换事件
- [ ] 保证窄屏下可折叠或不破版
- [ ] 运行 `npm run build:check`
- [ ] Commit：`feat(deep_research): 实现工作台任务轨道`

## 任务 4：实现工作台右栏核心面板

**文件：**
- 创建：`frontend/src/components/deep-research/TaskHeader.vue`
- 创建：`frontend/src/components/deep-research/AnalystReviewPanel.vue`
- 创建：`frontend/src/components/deep-research/ResearchProgressPanel.vue`
- 创建：`frontend/src/components/deep-research/ReportViewer.vue`
- 测试：`npm run build:check`

- [ ] 实现任务头部摘要
- [ ] 实现分析师卡片、反馈输入、approve/regenerate 操作
- [ ] 实现阶段时间线和当前进度消息
- [ ] 实现 Markdown 风格报告阅读与引用区
- [ ] 运行 `npm run build:check`
- [ ] Commit：`feat(deep_research): 实现工作台核心面板`

## 任务 5：组装页面并接入路由导航

**文件：**
- 创建：`frontend/src/views/deep-research/DeepResearchWorkbench.vue`
- 修改：`frontend/src/router/index.ts`
- 修改：`frontend/src/components/common/AppSidebar.vue`
- 清理：历史 Deep Research 草稿文件（若存在）
- 验证：`npm run build:check`

- [ ] 组装双栏页面与状态驱动视图切换
- [ ] 注册 `/deep-research` 路由
- [ ] 在侧边栏增加入口
- [ ] 清理无用的旧 Deep Research 前端草稿
- [ ] 运行 `npm run build:check`
- [ ] Commit：`feat(deep_research): 接入研究工作台页面`

## 任务 6：联调收口与视觉回归

**文件：**
- 修改：上述前端文件按需调整
- 验证：`npm run build:check`

- [ ] 对照真实接口检查创建、生成分析师、反馈、进度和报告展示链路
- [ ] 修复空状态、错误态和轮询边界
- [ ] 检查桌面端和窄屏布局是否出现横向滚动
- [ ] 运行 `npm run build:check`
- [ ] Commit：`fix(deep_research): 收口联调与交互细节`
