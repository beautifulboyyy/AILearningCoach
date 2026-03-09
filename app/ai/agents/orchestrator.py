"""
Agent编排器（Orchestrator）
"""
from typing import Dict, Any, Optional, List, AsyncGenerator
from app.ai.agents.base import BaseAgent
from app.ai.agents.qa_agent import qa_agent
from app.ai.agents.planner_agent import planner_agent
from app.ai.agents.coach_agent import coach_agent
from app.ai.agents.analyst_agent import analyst_agent
from app.ai.rag.llm import llm
from app.utils.logger import app_logger


class AgentOrchestrator:
    """
    Agent编排器
    
    负责识别用户意图，路由到合适的Agent，协调多Agent协作
    """
    
    def __init__(self):
        """初始化编排器"""
        self.agents: List[BaseAgent] = [
            qa_agent,
            planner_agent,
            coach_agent,
            analyst_agent
        ]
        
        self.llm = llm
        
        app_logger.info(f"Agent编排器初始化完成，注册了 {len(self.agents)} 个Agent")
    
    async def identify_intent(self, user_input: str) -> Dict[str, Any]:
        """
        识别用户意图
        
        Args:
            user_input: 用户输入
        
        Returns:
            意图识别结果
        """
        # 基于规则的快速意图识别
        intent = self._rule_based_intent(user_input)
        
        if intent["confidence"] >= 0.8:
            app_logger.info(f"意图识别（规则）: {intent['intent']}, 置信度: {intent['confidence']}")
            return intent
        
        # 如果规则识别置信度低，使用LLM识别
        try:
            intent_llm = await self._llm_based_intent(user_input)
            app_logger.info(f"意图识别（LLM）: {intent_llm['intent']}, 置信度: {intent_llm['confidence']}")
            return intent_llm
        except Exception as e:
            app_logger.warning(f"LLM意图识别失败，使用规则结果: {e}")
            return intent
    
    def _rule_based_intent(self, user_input: str) -> Dict[str, Any]:
        """
        基于规则的意图识别（快速）
        
        Args:
            user_input: 用户输入
        
        Returns:
            意图和置信度
        """
        user_lower = user_input.lower()
        
        # 进度分析意图
        if any(kw in user_lower for kw in ["进度", "报告", "总结", "统计", "学了多少"]):
            return {"intent": "progress_inquiry", "confidence": 0.9}
        
        # 学习规划意图
        if any(kw in user_lower for kw in ["规划", "计划", "路径", "怎么学", "推荐", "建议"]):
            return {"intent": "learning_planning", "confidence": 0.85}
        
        # 项目指导意图
        if any(kw in user_lower for kw in ["项目", "代码", "bug", "错误", "实现", "调试"]):
            return {"intent": "project_guidance", "confidence": 0.85}
        
        # 技术问题意图（默认）
        if any(kw in user_lower for kw in ["什么是", "如何", "怎么", "为什么", "原理", "区别"]):
            return {"intent": "technical_question", "confidence": 0.9}
        
        # 默认为技术问题
        return {"intent": "technical_question", "confidence": 0.6}
    
    async def _llm_based_intent(self, user_input: str) -> Dict[str, Any]:
        """
        基于LLM的意图识别（准确但慢）
        
        Args:
            user_input: 用户输入
        
        Returns:
            意图和置信度
        """
        intent_prompt = f"""请识别用户输入的意图，从以下类别中选择一个：

意图类别：
1. technical_question - 技术问题（如"什么是RAG"、"如何实现Prompt工程"）
2. learning_planning - 学习规划（如"帮我规划学习路径"、"我应该学什么"）
3. project_guidance - 项目指导（如"项目怎么做"、"代码有bug"、"如何优化"）
4. progress_inquiry - 进度查询（如"我的进度怎么样"、"帮我总结"、"生成报告"）

用户输入：
{user_input}

请只返回JSON格式：
{{
    "intent": "technical_question",
    "confidence": 0.9,
    "reason": "简短理由"
}}
"""
        
        try:
            response = await self.llm.generate(
                messages=[{"role": "user", "content": intent_prompt}],
                temperature=0.3,
                max_tokens=200
            )
            
            # 解析JSON
            import json
            import re
            
            json_match = re.search(r'\{.*?\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return {
                    "intent": result.get("intent", "technical_question"),
                    "confidence": result.get("confidence", 0.7),
                    "reason": result.get("reason", "")
                }
            else:
                raise ValueError("无法解析意图识别结果")
                
        except Exception as e:
            app_logger.error(f"LLM意图识别失败: {e}")
            return {"intent": "technical_question", "confidence": 0.5}
    
    def select_agent(self, intent: str, user_input: str) -> BaseAgent:
        """
        根据意图选择Agent
        
        Args:
            intent: 意图
            user_input: 用户输入
        
        Returns:
            选中的Agent
        """
        # 遍历所有Agent，找到能处理的
        for agent in self.agents:
            if agent.can_handle(user_input, intent):
                app_logger.info(f"选择Agent: {agent.name} 处理意图 {intent}")
                return agent
        
        # 默认使用QA Agent
        app_logger.info(f"使用默认Agent: QA Agent 处理意图 {intent}")
        return qa_agent
    
    async def process(
        self,
        user_input: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        处理用户输入（主入口）
        
        流程：
        1. 识别意图
        2. 选择Agent
        3. Agent处理
        4. 返回结果
        
        Args:
            user_input: 用户输入
            context: 上下文信息
        
        Returns:
            处理结果
        """
        try:
            app_logger.info(f"编排器开始处理: {user_input[:50]}...")
            
            # 1. 识别意图
            intent_result = await self.identify_intent(user_input)
            intent = intent_result["intent"]
            confidence = intent_result["confidence"]
            
            # 2. 选择Agent
            selected_agent = self.select_agent(intent, user_input)
            
            # 3. Agent处理
            result = await selected_agent.process(user_input, context)
            
            # 4. 添加编排信息
            result["orchestrator"] = {
                "intent": intent,
                "intent_confidence": confidence,
                "selected_agent": selected_agent.name
            }
            
            app_logger.info(
                f"编排器处理完成: 意图={intent}, "
                f"Agent={selected_agent.name}, "
                f"成功={result.get('success', False)}"
            )
            
            return result
            
        except Exception as e:
            app_logger.error(f"编排器处理失败: {e}")
            
            # 降级：直接使用QA Agent
            try:
                result = await qa_agent.process(user_input, context)
                result["orchestrator"] = {
                    "intent": "unknown",
                    "intent_confidence": 0.0,
                    "selected_agent": "QA Agent (fallback)",
                    "error": str(e)
                }
                return result
            except Exception as e2:
                app_logger.error(f"降级处理也失败: {e2}")
                return {
                    "agent": "Orchestrator",
                    "type": "error",
                    "answer": "抱歉，系统遇到了问题，请稍后重试。",
                    "sources": [],
                    "confidence": 0.0,
                    "success": False,
                    "error": str(e)
                }
    
    async def process_stream(
        self,
        user_input: str,
        context: Dict[str, Any]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式处理用户输入

        流程：
        1. 识别意图
        2. 选择Agent
        3. Agent流式处理
        4. 流式返回结果

        Args:
            user_input: 用户输入
            context: 上下文信息

        Yields:
            处理结果片段
        """
        import asyncio

        try:
            app_logger.info(f"编排器开始流式处理: {user_input[:50]}...")

            # 立即发送"思考中"状态，让用户知道系统在工作
            yield {
                "type": "status",
                "status": "thinking",
                "message": "正在分析您的问题..."
            }
            await asyncio.sleep(0.05)  # 50ms 延迟确保事件被刷新

            # 1. 识别意图
            intent_result = await self.identify_intent(user_input)
            intent = intent_result["intent"]
            confidence = intent_result["confidence"]

            # 2. 选择Agent
            selected_agent = self.select_agent(intent, user_input)

            # 3. 发送编排信息
            yield {
                "type": "orchestrator",
                "intent": intent,
                "intent_confidence": confidence,
                "selected_agent": selected_agent.name
            }
            await asyncio.sleep(0.05)  # 50ms 延迟确保事件被刷新

            # 4. Agent流式处理
            async for chunk in selected_agent.process_stream(user_input, context):
                yield chunk

            app_logger.info(
                f"编排器流式处理完成: 意图={intent}, Agent={selected_agent.name}"
            )

        except Exception as e:
            app_logger.error(f"编排器流式处理失败: {e}")

            # 发送错误信息
            yield {
                "type": "error",
                "error": str(e),
                "agent": "Orchestrator"
            }

            # 降级：使用QA Agent的非流式处理
            try:
                result = await qa_agent.process(user_input, context)
                answer = result.get("answer", "抱歉，系统遇到了问题。")

                yield {
                    "type": "metadata",
                    "agent": "QA Agent (fallback)",
                    "sources": result.get("sources", []),
                    "confidence": result.get("confidence", 0.0)
                }

                # 分块返回答案
                chunk_size = 10
                for i in range(0, len(answer), chunk_size):
                    yield {
                        "type": "answer",
                        "content": answer[i:i + chunk_size],
                        "done": False
                    }

                yield {
                    "type": "answer",
                    "content": "",
                    "done": True
                }

            except Exception as e2:
                app_logger.error(f"降级处理也失败: {e2}")
                yield {
                    "type": "answer",
                    "content": "抱歉，系统遇到了问题，请稍后重试。",
                    "done": True
                }

    def get_available_agents(self) -> List[Dict[str, str]]:
        """
        获取可用的Agent列表

        Returns:
            Agent信息列表
        """
        return [
            {
                "name": agent.name,
                "description": agent.description
            }
            for agent in self.agents
        ]


# 全局编排器实例
agent_orchestrator = AgentOrchestrator()
