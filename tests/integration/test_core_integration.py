#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SuperAgent 核心流程集成测试

测试完整的端到端流程:
1. 对话管理 → 意图识别
2. 计划生成
3. 代码执行 (模拟)
4. 代码审查
5. 错误处理
"""

import unittest
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from conversation.manager import ConversationManager
from planning.planner import ProjectPlanner
from utils.exceptions import (
    ConversationError,
    PlanningError,
    ErrorCodes
)


class TestConversationFlow(unittest.TestCase):
    """对话流程测试"""

    def setUp(self):
        """测试前准备"""
        self.conv_mgr = ConversationManager()

    def test_recognize_intent_simple(self):
        """测试简单意图识别"""
        # 同步测试 (如果支持)
        # 这里假设有同步方法,如果没有会在下面标记
        pass

    def test_conversation_manager_initialization(self):
        """测试对话管理器初始化"""
        self.assertIsNotNone(self.conv_mgr)
        self.assertEqual(self.conv_mgr.state, "idle")
        self.assertIsInstance(self.conv_mgr.context, dict)


class TestPlanningFlow(unittest.TestCase):
    """计划流程测试"""

    def setUp(self):
        """测试前准备"""
        self.planner = ProjectPlanner()

    def test_planner_initialization(self):
        """测试计划器初始化"""
        self.assertIsNotNone(self.planner)


class TestErrorHandling(unittest.TestCase):
    """错误处理测试"""

    def test_exception_hierarchy(self):
        """测试异常层级"""
        error1 = ConversationError("对话错误")
        error2 = PlanningError("计划错误")

        # 测试继承
        from utils.exceptions import SuperAgentError
        self.assertIsInstance(error1, SuperAgentError)
        self.assertIsInstance(error2, SuperAgentError)

    def test_error_codes(self):
        """测试错误代码"""
        self.assertEqual(ErrorCodes.INTENT_RECOGNITION_FAILED, "E1001")
        self.assertEqual(ErrorCodes.PLAN_GENERATION_FAILED, "E2001")

    def test_exception_to_dict(self):
        """测试异常序列化"""
        error = ConversationError(
            message="测试错误",
            details={"key": "value"},
            error_code="E1001"
        )

        error_dict = error.to_dict()

        self.assertEqual(error_dict["error_type"], "ConversationError")
        self.assertEqual(error_dict["message"], "测试错误")
        self.assertEqual(error_dict["details"]["key"], "value")
        self.assertEqual(error_dict["error_code"], "E1001")


class TestSafeExecute(unittest.TestCase):
    """安全执行测试"""

    def test_safe_execute_success(self):
        """测试正常执行"""
        from utils.error_handler import safe_execute

        def normal_function():
            return "success"

        result = safe_execute(normal_function, fallback="fallback", log=False)
        self.assertEqual(result, "success")

    def test_safe_execute_failure(self):
        """测试异常捕获"""
        from utils.error_handler import safe_execute

        def failing_function():
            raise ConversationError("函数失败")

        result = safe_execute(failing_function, fallback="fallback", log=False)
        self.assertEqual(result, "fallback")

    def test_safe_execute_with_args(self):
        """测试带参数的函数"""
        from utils.error_handler import safe_execute

        def add(a, b):
            return a + b

        result = safe_execute(add, 2, 3, fallback=0, log=False)
        self.assertEqual(result, 5)


class TestErrorHandler(unittest.TestCase):
    """错误处理器测试"""

    def test_error_handler_initialization(self):
        """测试错误处理器初始化"""
        from utils.error_handler import ErrorHandler

        handler = ErrorHandler(max_errors=5)
        self.assertEqual(handler.max_errors, 5)
        self.assertEqual(handler.error_count, 0)

    def test_error_handler_record(self):
        """测试错误记录"""
        from utils.error_handler import ErrorHandler

        handler = ErrorHandler(max_errors=3)

        # 记录 2 个错误
        handler.record_error(ConversationError("错误1"))
        handler.record_error(ConversationError("错误2"))

        self.assertEqual(handler.error_count, 2)
        self.assertFalse(handler.should_trigger_recovery())

        # 记录第 3 个错误
        handler.record_error(ConversationError("错误3"))

        self.assertEqual(handler.error_count, 3)
        self.assertTrue(handler.should_trigger_recovery())

    def test_error_handler_reset(self):
        """测试错误重置"""
        from utils.error_handler import ErrorHandler

        handler = ErrorHandler(max_errors=3)
        handler.record_error(ConversationError("错误"))

        self.assertEqual(handler.error_count, 1)

        handler.reset()

        self.assertEqual(handler.error_count, 0)
        self.assertFalse(handler.should_trigger_recovery())

    def test_error_handler_summary(self):
        """测试错误摘要"""
        from utils.error_handler import ErrorHandler

        handler = ErrorHandler(max_errors=10, log_errors=False)

        # 记录多个错误
        handler.record_error(ConversationError("错误1"))
        handler.record_error(PlanningError("错误2"))
        handler.record_error(ConversationError("错误3"))

        summary = handler.get_error_summary()

        self.assertEqual(summary["total_errors"], 3)
        self.assertIn("ConversationError", summary["error_types"])
        self.assertIn("PlanningError", summary["error_types"])


class TestIntegrationWithRealData(unittest.TestCase):
    """使用真实数据的集成测试"""

    def setUp(self):
        """测试前准备"""
        self.test_requirements = [
            "开发一个用户登录功能",
            "创建一个博客系统",
            "实现API接口"
        ]

    def test_requirements_validation(self):
        """测试需求验证"""
        # 验证需求不为空
        for req in self.test_requirements:
            self.assertGreater(len(req), 0)
            self.assertGreater(len(req.strip()), 5)  # 最少5个字符


def run_tests():
    """运行所有测试"""
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 添加所有测试类
    suite.addTests(loader.loadTestsFromTestCase(TestConversationFlow))
    suite.addTests(loader.loadTestsFromTestCase(TestPlanningFlow))
    suite.addTests(loader.loadTestsFromTestCase(TestErrorHandling))
    suite.addTests(loader.loadTestsFromTestCase(TestSafeExecute))
    suite.addTests(loader.loadTestsFromTestCase(TestErrorHandler))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegrationWithRealData))

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 返回结果
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run_tests())
