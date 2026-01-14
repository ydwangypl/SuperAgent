#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
对话管理器

管理用户对话流程,需求澄清,意图识别
"""

import time
import re
from typing import List, Dict, Any, Optional
from pathlib import Path

from .models import (
    UserInput, Intent, IntentType, Response,
    ClarificationQuestion, Decision
)
from .intent_recognizer import IntentRecognizer
from context.smart_compressor import SmartContextCompressor
from config.settings import TokenOptimizationConfig


class ConversationManager:
    """对话管理器"""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """初始化对话管理器

        Args:
            config: 配置字典
        """
        self.config = config or {}

        # 对话上下文
        self.context: Dict[str, Any] = {}

        # 决策历史
        self.decision_history: List[Decision] = []

        # 对话历史(最近N轮)
        self.conversation_history: List[Dict[str, Any]] = []
        self.max_history = 10

        # 当前状态
        self.state = "idle"  # idle, clarifying, planning, executing

        # 初始化 Agent 注册中心 (确保意图识别器能获取到最新的关键词)
        from orchestration.registry import AgentRegistry
        AgentRegistry.initialize()

        # 初始化智能意图识别器
        self.intent_recognizer = IntentRecognizer()

        # 初始化上下文压缩器 (Phase 3)
        self.token_config = TokenOptimizationConfig()
        self.compressor = SmartContextCompressor()

        # 需求检查模式 (通用化升级: 不再局限于特定业务领域)
        self._key_info_patterns = [
            # 1. 项目/动作描述 (如: 创建、重构、修复、实现)
            re.compile(r"创建|开发|重构|修复|实现|编写|create|refactor|fix|implement|build", re.IGNORECASE),
            # 2. 技术对象 (如: 代码、功能、模块、类、函数、插件、工具)
            re.compile(r"代码|功能|模块|类|函数|插件|工具|code|feature|module|class|function|plugin|tool", re.IGNORECASE),
            # 3. 目标描述 (用户输入中包含具体名词)
            re.compile(r"\w{2,}", re.UNICODE) 
        ]

        self._project_type_pattern = re.compile(r"项目|工具|应用|系统|插件|库|framework|library|tool|app", re.IGNORECASE)
        self._tech_stack_pattern = re.compile(r"python|javascript|typescript|java|go|rust|cpp|php|ruby", re.IGNORECASE)

        self.initialized = True

    async def process_input(self, user_input: str) -> Response:
        """处理用户输入

        Args:
            user_input: 用户输入文本

        Returns:
            Response: 系统响应
        """
        # 记录输入
        input_obj = UserInput(
            raw_text=user_input,
            timestamp=time.time()
        )

        # 添加到历史
        self._add_to_history("user", user_input)

        # 1. 意图识别 (使用统一的识别器)
        intent = await self.intent_recognizer.recognize(user_input)

        # 2. 检查需求明确性
        if self._is_requirements_unclear(user_input, intent):
            return await self._ask_clarifying_questions(user_input, intent)

        # 3. 需求明确,返回成功响应
        self.state = "planning"
        return Response(
            type="requirements_ready",
            message="需求已明确,可以开始规划",
            data={
                "user_input": user_input,
                "intent": intent,
                "context": self.context
            }
        )

    def _is_requirements_unclear(
        self,
        text: str,
        intent: Intent
    ) -> bool:
        """检查需求是否不明确

        Args:
            text: 用户输入
            intent: 意图

        Returns:
            bool: True表示需要澄清
        """
        # 查询类意图不需要澄清(直接返回数据)
        if intent.type == IntentType.QUERY:
            return False

        # 规则1: 输入太短(<10个字符)
        if len(text.strip()) < 10:
            return True

        # 规则2: 缺少关键信息
        has_key_info = any(pattern.search(text) for pattern in self._key_info_patterns)
        if not has_key_info:
            return True

        # 规则3: 低置信度
        if intent.confidence < 0.6:
            return True

        return False

    async def _ask_clarifying_questions(
        self,
        user_input: str,
        intent: Intent
    ) -> Response:
        """生成澄清问题

        Args:
            user_input: 用户输入
            intent: 意图

        Returns:
            Response: 包含澄清问题的响应
        """
        questions = self._generate_questions(user_input, intent)

        self.state = "clarifying"

        return Response(
            type="clarification",
            message="需要更多信息来理解您的需求",
            data={
                "user_input": user_input,
                "intent": intent,
                "context": self.context
            },
            clarifications=questions
        )

    def _generate_questions(
        self,
        user_input: str,
        intent: Intent
    ) -> List[ClarificationQuestion]:
        """生成澄清问题 (通用化升级: 适应各种业务领域)"""
        questions = []
        user_input_lower = user_input.lower()

        # 根据意图类型生成不同的问题
        if intent.type == IntentType.NEW_PROJECT:
            # 新建项目的关键问题
            if not self._project_type_pattern.search(user_input_lower):
                questions.append(ClarificationQuestion(
                    question_id="project_type",
                    question="您想开发什么类型的项目?",
                    options=["Web 应用/API", "CLI 命令行工具", "插件/扩展", "库/框架", "其他"],
                    required=True,
                    reason="需要确定项目形态以规划目录结构"
                ))

            # 询问核心目标
            questions.append(ClarificationQuestion(
                question_id="main_purpose",
                question="这个项目的主要核心功能或目标是什么?",
                options=None, # 强制手动输入
                required=True,
                reason="需要了解核心业务逻辑"
            ))

            # 技术栈偏好
            if not self._tech_stack_pattern.search(user_input_lower):
                questions.append(ClarificationQuestion(
                    question_id="tech_stack",
                    question="有技术栈偏好吗?",
                    options=["Python", "JavaScript/TypeScript", "Go", "Rust", "不确定,请推荐"],
                    required=False,
                    reason="根据技术栈选择合适的 Agent"
                ))

        return questions

    def record_decision(self, decision: Decision) -> None:
        """记录决策

        Args:
            decision: 决策对象
        """
        self.decision_history.append(decision)

    def get_context(self, key: str, default: Any = None) -> Any:
        """获取上下文信息

        Args:
            key: 键
            default: 默认值

        Returns:
            Any: 上下文值
        """
        return self.context.get(key, default)

    def set_context(self, key: str, value: Any) -> None:
        """设置上下文信息

        Args:
            key: 键
            value: 值
        """
        self.context[key] = value

    def get_decision_history(self, limit: int = 10) -> List[Decision]:
        """获取决策历史

        Args:
            limit: 返回数量限制

        Returns:
            List[Decision]: 决策列表
        """
        return self.decision_history[-limit:]

    def _add_to_history(self, role: str, content: str) -> None:
        """添加到对话历史

        Args:
            role: 角色(user/assistant)
            content: 内容
        """
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": time.time()
        })

        # 保持历史记录在限制内
        if len(self.conversation_history) > self.max_history:
            self.conversation_history = self.conversation_history[-self.max_history:]

    def clear_history(self) -> None:
        """清空对话历史"""
        self.conversation_history = []
        self.context = {}
        self.state = "idle"

    def get_optimized_history(self) -> List[Dict[str, Any]]:
        """获取优化后的对话历史 (Phase 3: 启用上下文压缩)
        
        Returns:
            List[Dict]: 压缩或截断后的历史记录
        """
        if not self.token_config.enabled or not self.token_config.enable_message_compression:
            return self.conversation_history

        # 使用 SmartContextCompressor 进行智能压缩
        compressed_history, stats = self.compressor.compress_messages(
            self.conversation_history,
            max_tokens=self.token_config.max_message_tokens
        )
        
        return compressed_history

    # ========== 智能意图识别方法 ==========

    async def smart_recognize(self, user_input: str) -> Dict[str, Any]:
        """使用智能意图识别器

        Args:
            user_input: 用户输入

        Returns:
            Dict[str, Any]: 识别结果
        """
        try:
            result = await self.intent_recognizer.recognize(user_input)

            return {
                "type": result.type.value,
                "confidence": result.confidence,
                "agent_types": [agent.value for agent in result.agent_types],
                "reasoning": result.reasoning,
                "keywords": result.keywords,
                "suggested_steps": result.suggested_steps
            }
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"智能意图识别失败 ({type(e).__name__}): {e}", exc_info=True)
            return {
                "type": "unknown",
                "confidence": 0.0,
                "agent_types": [],
                "reasoning": f"识别异常 ({type(e).__name__}): {str(e)}",
                "keywords": [],
                "suggested_steps": []
            }

    async def get_agent_suggestions(self, user_input: str) -> List[Dict[str, Any]]:
        """获取Agent类型建议

        Args:
            user_input: 用户输入

        Returns:
            List[Dict[str, Any]]: Agent建议列表
        """
        return await self.intent_recognizer.get_agent_type_suggestions(user_input)

    async def get_suggested_steps(self, user_input: str) -> List[str]:
        """获取建议的执行步骤

        Args:
            user_input: 用户输入

        Returns:
            List[str]: 建议步骤列表
        """
        result = await self.intent_recognizer.recognize(user_input)
        return result.suggested_steps
