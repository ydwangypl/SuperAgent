#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SuperAgent v3.0 测试运行器

运行所有单元测试和集成测试
"""

import sys
import unittest
from pathlib import Path

# 添加项目根目录到路径
SUPERAGENT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(SUPERAGENT_ROOT))

from tests.test_cli import TestSuperAgentCLI
from tests.test_conversation import TestConversationManager
from tests.test_planning import (
    TestProjectPlanner,
    TestStepGenerator,
    TestDependencyAnalyzer,
    TestDataModels
)
from tests.test_integration import (
    TestFullIntegration,
    TestErrorHandling,
    TestPerformance
)


def run_tests():
    """运行所有测试"""
    print("="*70)
    print("  SuperAgent v3.0 单元测试")
    print("="*70)

    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 添加所有测试类
    test_classes = [
        # CLI测试
        TestSuperAgentCLI,

        # 对话管理测试
        TestConversationManager,

        # 规划层测试
        TestProjectPlanner,
        TestStepGenerator,
        TestDependencyAnalyzer,
        TestDataModels,

        # 集成测试
        TestFullIntegration,
        TestErrorHandling,
        TestPerformance
    ]

    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 打印总结
    print("\n" + "="*70)
    print("  测试总结")
    print("="*70)

    print(f"\n总测试数: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")

    if result.wasSuccessful():
        print("\n状态: ✅ 所有测试通过!")
        return 0
    else:
        print("\n状态: ❌ 有测试失败")
        return 1


if __name__ == '__main__':
    sys.exit(run_tests())
