#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
意图识别器单元测试
"""

import unittest
from conversation.intent_recognizer import IntentRecognizer
from conversation.models import IntentType
from common.models import AgentType


class TestIntentRecognizer(unittest.IsolatedAsyncioTestCase):
    """意图识别器测试类"""

    async def asyncSetUp(self):
        self.recognizer = IntentRecognizer()

    async def test_recognize_backend_intent(self):
        """测试后端开发意图"""
        user_input = "使用Python和FastAPI开发一个用户管理系统的后端API"
        result = await self.recognizer.recognize(user_input)
        
        # 验证 Agent 类型
        self.assertIn(AgentType.BACKEND_DEV, result.agent_types)
        self.assertTrue(result.confidence > 0.4)
        # 验证关键词
        self.assertIn("python", result.keywords)
        self.assertIn("用户管理", result.keywords)

    async def test_recognize_database_intent(self):
        """测试数据库设计意图"""
        user_input = "设计一个电商系统的数据库(Database)表结构，包含订单和商品"
        result = await self.recognizer.recognize(user_input)
        
        self.assertIn(AgentType.DATABASE_DESIGN, result.agent_types)
        self.assertIn("database", result.keywords)

    async def test_recognize_frontend_intent(self):
        """测试前端开发意图"""
        user_input = "使用React和Tailwind CSS创建一个响应式的登录页面"
        result = await self.recognizer.recognize(user_input)
        
        self.assertIn(AgentType.FRONTEND_DEV, result.agent_types)
        # "登录" matches "用户管理" patterns
        self.assertIn("用户管理", result.keywords)

    async def test_recognize_mixed_intent(self):
        """测试混合意图"""
        user_input = "开发一个全栈应用，前端用Vue，后端用Node.js，部署到Docker"
        result = await self.recognizer.recognize(user_input)

        # 全栈意图应该被识别
        self.assertIn(AgentType.FULL_STACK_DEV, result.agent_types)
        # DevOps意图也应该被识别 (v3.3: 支持 DEVOPS 或 DEVOPS_ENGINEERING)
        self.assertTrue(
            AgentType.DEVOPS in result.agent_types or AgentType.DEVOPS_ENGINEERING in result.agent_types,
            f"期望 DevOps 意图, 实际: {result.agent_types}"
        )

    async def test_sanitize_input_integration(self):
        """测试输入清理集成"""
        # 包含潜在脚本标签的输入
        user_input = "创建一个用户管理系统 <script>alert('xss')</script>"
        result = await self.recognizer.recognize(user_input)
        
        # 关键词提取不应受脚本标签干扰
        self.assertIn("用户管理", result.keywords)

    async def test_empty_input(self):
        """测试空输入"""
        user_input = ""
        result = await self.recognizer.recognize(user_input)
        
        self.assertEqual(result.type, IntentType.UNKNOWN)
        self.assertEqual(result.confidence, 0.0)


if __name__ == '__main__':
    unittest.main()
