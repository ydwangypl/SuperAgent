#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
错误恢复系统测试

测试智能错误处理、历史记忆查询、自动重试策略
"""

import asyncio
import sys
import io
from pathlib import Path

# Windows 控制台 UTF-8 支持
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加项目根目录到 Python 路径
SUPERAGENT_ROOT = Path(__file__).parent
sys.path.insert(0, str(SUPERAGENT_ROOT))

from orchestration import (
    ErrorType,
    ErrorSeverity,
    ErrorClassifier,
    RetryStrategy,
    ErrorRecoverySystem
)
from memory import MemoryManager


async def test_error_classification():
    """测试错误分类"""
    print("\n" + "="*60)
    print("测试 1: 错误分类")
    print("="*60)

    test_cases = [
        ("SyntaxError: invalid syntax", ErrorType.SYNTAX_ERROR),
        ("ImportError: No module named 'requests'", ErrorType.IMPORT_ERROR),
        ("AttributeError: 'NoneType' object has no attribute 'x'", ErrorType.ATTRIBUTE_ERROR),
        ("KeyError: 'test_key'", ErrorType.KEY_ERROR),
        ("ValueError: invalid literal for int()", ErrorType.VALUE_ERROR),
        ("ConnectionError: Max retries exceeded", ErrorType.NETWORK_ERROR),
        ("FileNotFoundError: file not found", ErrorType.FILE_ERROR),
    ]

    for error_msg, expected_type in test_cases:
        classified_type = ErrorClassifier.classify(error_msg)
        status = "✓" if classified_type == expected_type else "✗"
        print(f"  {status} {error_msg[:50]}")
        print(f"     期望: {expected_type.value}, 实际: {classified_type.value}")

    print("\n✓ 错误分类测试完成")


async def test_severity_estimation():
    """测试严重程度估算"""
    print("\n" + "="*60)
    print("测试 2: 严重程度估算")
    print("="*60)

    test_cases = [
        ("SyntaxError: invalid syntax", ErrorType.SYNTAX_ERROR, ErrorSeverity.CRITICAL),
        ("ImportError: No module named 'requests'", ErrorType.IMPORT_ERROR, ErrorSeverity.HIGH),
        ("KeyError: 'test_key'", ErrorType.KEY_ERROR, ErrorSeverity.LOW),
        ("AttributeError: object has no attribute", ErrorType.ATTRIBUTE_ERROR, ErrorSeverity.MEDIUM),
    ]

    for error_msg, error_type, expected_severity in test_cases:
        severity = ErrorClassifier.estimate_severity(error_type, error_msg)
        status = "✓" if severity == expected_severity else "✗"
        print(f"  {status} {error_type.value}")
        print(f"     期望: {expected_severity.value}, 实际: {severity.value}")

    print("\n✓ 严重程度估算测试完成")


async def test_retry_strategy():
    """测试重试策略"""
    print("\n" + "="*60)
    print("测试 3: 重试策略")
    print("="*60)

    test_cases = [
        (ErrorType.SYNTAX_ERROR, ErrorSeverity.CRITICAL, 0, "manual"),
        (ErrorType.IMPORT_ERROR, ErrorSeverity.HIGH, 0, "retry"),
        (ErrorType.NETWORK_ERROR, ErrorSeverity.MEDIUM, 2, "retry"),
        (ErrorType.KEY_ERROR, ErrorSeverity.LOW, 3, "fallback"),
    ]

    for error_type, severity, retry_count, expected_strategy in test_cases:
        strategy = RetryStrategy.get_strategy(error_type, severity, retry_count)
        status = "✓" if strategy.strategy_type == expected_strategy else "✗"
        print(f"  {status} {error_type.value} (重试 {retry_count})")
        print(f"     期望: {expected_strategy}, 实际: {strategy.strategy_type}")
        print(f"     最大重试: {strategy.max_retries}, 延迟: {strategy.retry_delay}s")

    print("\n✓ 重试策略测试完成")


async def test_error_recovery_system():
    """测试错误恢复系统"""
    print("\n" + "="*60)
    print("测试 4: 错误恢复系统")
    print("="*60)

    # 创建临时记忆管理器
    test_project_root = SUPERAGENT_ROOT / ".test_error_recovery"
    test_project_root.mkdir(exist_ok=True)

    memory_manager = MemoryManager(test_project_root)
    recovery_system = ErrorRecoverySystem(memory_manager)

    # 模拟错误处理
    test_errors = [
        ImportError("No module named 'test_module'"),
        KeyError("test_key"),
        AttributeError("'NoneType' object has no attribute 'test'"),
    ]

    for i, error in enumerate(test_errors, 1):
        print(f"\n处理错误 {i}: {type(error).__name__}")

        result = await recovery_system.handle_error(
            error=error,
            task_id=f"test_task_{i}",
            agent_type="backend-dev",
            retry_count=0
        )

        print(f"  错误类型: {result['error_type']}")
        print(f"  严重程度: {result['severity']}")
        print(f"  策略: {result['strategy']}")
        print(f"  是否重试: {result['should_retry']}")
        print(f"  重试延迟: {result['retry_delay']}s")

    # 显示统计
    stats = recovery_system.get_statistics()
    print(f"\n统计信息:")
    print(f"  总错误数: {stats['total_errors']}")
    print(f"  已重试: {stats['retried']}")
    print(f"  已降级: {stats['fallback']}")
    print(f"  需人工: {stats['manual']}")

    print("\n✓ 错误恢复系统测试完成")


async def test_memory_based_recovery():
    """测试基于记忆的恢复"""
    print("\n" + "="*60)
    print("测试 5: 基于记忆的恢复")
    print("="*60)

    # 创建临时记忆管理器
    test_project_root = SUPERAGENT_ROOT / ".test_error_recovery"
    test_project_root.mkdir(exist_ok=True)

    memory_manager = MemoryManager(test_project_root)
    recovery_system = ErrorRecoverySystem(memory_manager)

    # 先保存一个错误到记忆
    await memory_manager.save_mistake(
        error=KeyError("test_key"),
        context="测试任务",
        fix="检查字典键是否存在",
        learning="使用dict.get()方法避免KeyError"
    )

    print("已保存错误到记忆系统")

    # 现在处理相同类型的错误
    error = KeyError("test_key")
    result = await recovery_system.handle_error(
        error=error,
        task_id="test_task_memory",
        agent_type="backend-dev",
        retry_count=0
    )

    if result.get("memory_fix"):
        print(f"\n✓ 找到历史修复方案:")
        print(f"  修复: {result['memory_fix']['fix']}")
        print(f"  经验: {result['memory_fix'].get('learning', 'N/A')}")
        print(f"  置信度: {result['memory_fix'].get('confidence', 'N/A')}")
    else:
        print("\n✗ 未找到历史修复方案")

    print("\n✓ 基于记忆的恢复测试完成")


async def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("错误恢复系统测试")
    print("="*60)

    tests = [
        test_error_classification,
        test_severity_estimation,
        test_retry_strategy,
        test_error_recovery_system,
        test_memory_based_recovery
    ]

    for test_func in tests:
        try:
            await test_func()
        except Exception as e:
            print(f"\n❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "="*60)
    print("测试完成")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
