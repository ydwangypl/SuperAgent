#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
对话管理器 - 错误处理增强版示例

展示如何在现有模块中应用统一的错误处理机制。

注意: 这是一个示例文件,展示如何修改 conversation/manager.py
"""

import logging
from typing import Dict, Any, Optional

# 导入统一异常类和错误处理器
from utils.exceptions import ConversationError, ErrorCodes
from utils.error_handler import handle_errors, ErrorHandler


logger = logging.getLogger(__name__)


class ConversationManagerWithErrorHandling:
    """
    对话管理器 - 错误处理增强版

    在原有 ConversationManager 基础上添加了统一的错误处理。
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化对话管理器"""
        self.config = config or {}

        # 初始化错误处理器
        self.error_handler = ErrorHandler(
            max_errors=10,
            reset_interval=300,
            log_errors=True
        )

        # 对话上下文
        self.context: Dict[str, Any] = {}
        self.state = "idle"

    @handle_errors(
        error_type=ConversationError,
        fallback=None,
        log=True
    )
    async def recognize_intent(self, user_input: str) -> Optional[Dict[str, Any]]:
        """
        识别用户意图 (带错误处理)

        Args:
            user_input: 用户输入

        Returns:
            意图识别结果

        Raises:
            ConversationError: 意图识别失败时抛出
        """
        # 验证输入
        if not user_input or not user_input.strip():
            raise ConversationError(
                message="用户输入不能为空",
                error_code=ErrorCodes.INPUT_VALIDATION_FAILED,
                details={"user_input": user_input}
            )

        # 检查状态
        if self.state != "idle":
            raise ConversationError(
                message=f"对话状态不正确,当前状态: {self.state}",
                error_code=ErrorCodes.TASK_INVALID_STATE,
                details={"current_state": self.state, "expected_state": "idle"}
            )

        try:
            # 原有的意图识别逻辑
            # ... (这里调用原有的意图识别代码)

            # 模拟结果
            result = {
                "intent": "feature_development",
                "confidence": 0.95
            }

            return result

        except Exception as e:
            # 记录错误
            self.error_handler.record_error(e, context={"user_input": user_input})

            # 转换为 ConversationError
            raise ConversationError(
                message=f"意图识别失败: {str(e)}",
                error_code=ErrorCodes.INTENT_RECOGNITION_FAILED,
                details={"user_input": user_input, "original_error": str(e)}
            ) from e

    @handle_errors(
        error_type=ConversationError,
        fallback=False,
        log=True
    )
    async def ask_clarifying_question(
        self,
        question: str,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        提出澄清问题 (带错误处理)

        Args:
            question: 澄清问题
            context: 上下文信息

        Returns:
            是否成功提出问题
        """
        if not question:
            raise ConversationError(
                message="澄清问题不能为空",
                error_code=ErrorCodes.PARAMETER_INVALID,
                details={"question": question}
            )

        try:
            # 原有的提问逻辑
            # ... (这里调用原有的提问代码)

            logger.info(f"提出澄清问题: {question}")
            return True

        except Exception as e:
            self.error_handler.record_error(e, context={"question": question})

            raise ConversationError(
                message=f"提出澄清问题失败: {str(e)}",
                error_code=ErrorCodes.CONVERSATION_TIMEOUT,
                details={"question": question, "context": context}
            ) from e

    def get_error_summary(self) -> Dict[str, Any]:
        """
        获取错误摘要

        Returns:
            错误统计信息
        """
        return self.error_handler.get_error_summary()

    def reset_errors(self):
        """重置错误计数"""
        self.error_handler.reset()


# 使用示例
async def example_usage():
    """使用示例"""

    # 创建带错误处理的对话管理器
    manager = ConversationManagerWithErrorHandling()

    # 示例 1: 正常调用
    try:
        result = await manager.recognize_intent("开发用户登录功能")
        print(f"识别结果: {result}")
    except ConversationError as e:
        print(f"错误: {e}")
        print(f"错误详情: {e.to_dict()}")

    # 示例 2: 错误输入 (会被装饰器捕获并返回 fallback)
    result = await manager.recognize_intent("")  # 返回 None (fallback)
    print(f"空输入结果: {result}")

    # 示例 3: 查看错误摘要
    error_summary = manager.get_error_summary()
    print(f"错误摘要: {error_summary}")

    # 示例 4: 检查是否需要触发恢复
    if manager.error_handler.should_trigger_recovery():
        print("错误次数过多,触发恢复机制")
        manager.reset_errors()
