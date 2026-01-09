#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
对话管理层单元测试
"""

import unittest
import asyncio
from unittest.mock import MagicMock, patch

from conversation.manager import ConversationManager
from conversation.models import Intent, IntentType, ClarificationQuestion


class TestConversationManager(unittest.TestCase):
    """对话管理器测试套件"""

    def setUp(self):
        """测试前准备"""
        self.mgr = ConversationManager()

    def test_initialization(self):
        """测试初始化"""
        self.assertIsNotNone(self.mgr)
        self.assertEqual(self.mgr.state, "idle")
        self.assertEqual(len(self.mgr.decision_history), 0)
        self.assertEqual(len(self.mgr.conversation_history), 0)

    async def test_process_input_simple_requirement(self):
        """测试处理简单需求"""
        user_input = "我想开发一个博客系统"
        result = await self.mgr.process_input(user_input)

        self.assertEqual(result.type, "requirements_ready")
        self.assertIn("博客系统", result.data['user_input'])
        self.assertEqual(result.data['intent'].type, IntentType.NEW_PROJECT)
        self.assertGreater(result.data['intent'].confidence, 0.5)

    async def test_process_input_vague_requirement(self):
        """测试处理模糊需求"""
        user_input = "帮我开发"
        result = await self.mgr.process_input(user_input)

        self.assertEqual(result.type, "clarification")
        self.assertGreater(len(result.clarifications), 0)
        self.assertIn("需要更多信息", result.message)

    async def test_recognize_intent_new_project(self):
        """测试识别新建项目意图"""
        text = "我想开发一个博客系统"
        intent = self.mgr._recognize_intent(text)

        self.assertEqual(intent.type, IntentType.NEW_PROJECT)
        self.assertGreater(intent.confidence, 0.7)

    async def test_recognize_intent_query(self):
        """测试识别查询意图"""
        text = "查看当前状态"
        intent = self.mgr._recognize_intent(text)

        self.assertEqual(intent.type, IntentType.QUERY)
        self.assertGreater(intent.confidence, 0.7)

    async def test_recognize_intent_fix_bug(self):
        """测试识别Bug修复意图"""
        text = "修复登录失败的bug"
        intent = self.mgr._recognize_intent(text)

        self.assertEqual(intent.type, IntentType.FIX_BUG)
        self.assertGreater(intent.confidence, 0.7)

    def test_is_requirements_unclear_short_input(self):
        """测试短输入判断"""
        text = "开发"
        intent = Intent(type=IntentType.NEW_PROJECT, confidence=0.8)

        result = self.mgr._is_requirements_unclear(text, intent)
        self.assertTrue(result)

    def test_is_requirements_unclear_complete_input(self):
        """测试完整输入判断"""
        text = "我想开发一个博客系统,支持文章管理和评论功能"
        intent = Intent(type=IntentType.NEW_PROJECT, confidence=0.8)

        result = self.mgr._is_requirements_unclear(text, intent)
        self.assertFalse(result)

    def test_is_requirements_unclear_query_type(self):
        """测试查询类型不需要澄清"""
        text = "查看当前状态"
        intent = Intent(type=IntentType.QUERY, confidence=0.8)

        result = self.mgr._is_requirements_unclear(text, intent)
        self.assertFalse(result)

    def test_generate_questions_for_vague_input(self):
        """测试为模糊输入生成问题"""
        user_input = "帮我开发"
        intent = Intent(type=IntentType.NEW_PROJECT, confidence=0.5)

        questions = self.mgr._generate_questions(user_input, intent)

        self.assertGreater(len(questions), 0)
        self.assertIsInstance(questions[0], ClarificationQuestion)

        # 检查第一个问题是必须的
        self.assertTrue(questions[0].required)

        # 检查问题有选项
        self.assertIsNotNone(questions[0].options)
        self.assertGreater(len(questions[0].options), 0)

    def test_context_management(self):
        """测试上下文管理"""
        # 设置上下文
        self.mgr.set_context("test_key", "test_value")
        result = self.mgr.get_context("test_key")

        self.assertEqual(result, "test_value")

        # 测试默认值
        result = self.mgr.get_context("nonexistent", "default")
        self.assertEqual(result, "default")

    def test_decision_history(self):
        """测试决策历史记录"""
        from conversation.models import Decision

        decision = Decision(
            topic="测试决策",
            decision="选择方案A",
            reasoning="理由是...",
            timestamp=12345
        )

        self.mgr.record_decision(decision)

        history = self.mgr.get_decision_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].topic, "测试决策")

    def test_conversation_history(self):
        """测试对话历史记录"""
        # 添加历史
        self.mgr._add_to_history("user", "用户输入")
        self.mgr._add_to_history("assistant", "系统回复")

        self.assertEqual(len(self.mgr.conversation_history), 2)

    def test_clear_history(self):
        """测试清空历史"""
        # 添加一些历史
        self.mgr.set_context("test", "value")
        self.mgr._add_to_history("user", "test")

        # 清空
        self.mgr.clear_history()

        self.assertEqual(len(self.mgr.conversation_history), 0)
        self.assertEqual(len(self.mgr.context), 0)
        self.assertEqual(self.mgr.state, "idle")


if __name__ == '__main__':
    unittest.main()
