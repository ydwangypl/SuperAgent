#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SuperAgent 集成测试运行器

运行所有集成测试并生成报告。
"""

import sys
import unittest
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))


def run_all_tests():
    """运行所有集成测试"""

    print("=" * 70)
    print("SuperAgent 集成测试套件")
    print("=" * 70)

    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 1. 核心集成测试
    print("\n[1/3] 加载核心集成测试...")
    try:
        from tests.test_core_integration import (
            TestConversationFlow,
            TestPlanningFlow,
            TestErrorHandling,
            TestSafeExecute,
            TestErrorHandler,
            TestIntegrationWithRealData
        )
        suite.addTests(loader.loadTestsFromTestCase(TestConversationFlow))
        suite.addTests(loader.loadTestsFromTestCase(TestPlanningFlow))
        suite.addTests(loader.loadTestsFromTestCase(TestErrorHandling))
        suite.addTests(loader.loadTestsFromTestCase(TestSafeExecute))
        suite.addTests(loader.loadTestsFromTestCase(TestErrorHandler))
        suite.addTests(loader.loadTestsFromTestCase(TestIntegrationWithRealData))
        print("  [OK] 核心集成测试加载成功")
    except Exception as e:
        print(f"  [ERROR] 核心集成测试加载失败: {e}")

    # 2. 异步集成测试
    print("\n[2/3] 加载异步集成测试...")
    try:
        from tests.test_async_integration import (
            TestAsyncErrorHandling,
            TestAsyncErrorRecovery,
            TestAsyncIntegrationScenarios
        )
        suite.addTests(loader.loadTestsFromTestCase(TestAsyncErrorHandling))
        suite.addTests(loader.loadTestsFromTestCase(TestAsyncErrorRecovery))
        suite.addTests(loader.loadTestsFromTestCase(TestAsyncIntegrationScenarios))
        print("  [OK] 异步集成测试加载成功")
    except Exception as e:
        print(f"  [ERROR] 异步集成测试加载失败: {e}")

    # 3. 其他集成测试
    print("\n[3/3] 加载其他集成测试...")
    try:
        from tests.test_integration import TestFullIntegration
        suite.addTests(loader.loadTestsFromTestCase(TestFullIntegration))
        print("  [OK] 其他集成测试加载成功")
    except Exception as e:
        print(f"  [WARNING] 其他集成测试加载失败: {e}")

    # 运行测试
    print("\n" + "=" * 70)
    print("开始运行测试...")
    print("=" * 70 + "\n")

    runner = unittest.TextTestRunner(
        verbosity=2,
        stream=sys.stdout,
        failfast=False  # 不在第一个失败时停止
    )

    result = runner.run(suite)

    # 生成报告
    print("\n" + "=" * 70)
    print("测试报告")
    print("=" * 70)

    print(f"\n运行测试数: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    print(f"跳过: {len(result.skipped)}")

    if result.wasSuccessful():
        print("\n[SUCCESS] 所有测试通过!")
        return 0
    else:
        print("\n[FAILURE] 部分测试失败")

        if result.failures:
            print("\n失败的测试:")
            for test, traceback in result.failures[:5]:  # 只显示前5个
                print(f"  - {test}")

        if result.errors:
            print("\n错误的测试:")
            for test, traceback in result.errors[:5]:  # 只显示前5个
                print(f"  - {test}")

        return 1


def run_specific_test(test_name: str):
    """运行特定的测试"""
    print(f"运行测试: {test_name}")

    loader = unittest.TestLoader()
    suite = loader.loadTestsFromName(test_name)

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return 0 if result.wasSuccessful() else 1


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="SuperAgent 集成测试运行器")
    parser.add_argument(
        "--test",
        type=str,
        help="运行特定的测试 (例如: tests.test_core_integration.TestErrorHandling)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="详细输出"
    )

    args = parser.parse_args()

    if args.test:
        return run_specific_test(args.test)
    else:
        return run_all_tests()


if __name__ == "__main__":
    sys.exit(main())
