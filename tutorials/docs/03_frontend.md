# 前端深度学习

## 前端技术栈
- Vue3 + TypeScript + Vite + Pinia + Element Plus。
- 重点目录：`frontend/src/views`, `frontend/src/stores`, `frontend/src/api`。

## 聊天页面关键链路
1. 页面触发发送： [frontend/src/views/chat/ChatView.vue](/D:/Code/python/AILearningCoach/frontend/src/views/chat/ChatView.vue)
2. 状态管理：`chat store` 维护消息列表、会话、发送状态。
3. API 调用： [frontend/src/api/chat.ts](/D:/Code/python/AILearningCoach/frontend/src/api/chat.ts)
4. SSE 处理：逐行解析 `data: {json}`，持续渲染 assistant 消息。

## 你要能解释的点
1. 为什么 `sendMessageStream` 用 `fetch` 而不是 axios：SSE 流读取更直接。
2. 为什么要把会话和消息放 Pinia：跨组件共享和状态可追踪。
3. 为什么 UI 要支持“流式逐字更新”：提升交互感知速度。

## 建议你做的 3 个前端练习
1. 在聊天页增加“当前 Agent 标签”动画提示。
2. 增加“重试发送上一次问题”按钮。
3. 对 SSE 断流增加兜底提示（比如“网络中断，可重试”）。

## 前端面试表达模板
- 我负责的是 AI 聊天核心交互链路。
- 把一次性响应改成 SSE 流式渲染，提升用户感知速度。
- 处理了鉴权、错误提示、会话历史切换和自动滚动等细节。
