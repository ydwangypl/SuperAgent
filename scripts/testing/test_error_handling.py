#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
错误处理机制测试脚本

测试统一异常类和错误处理器的功能。
"""

import sys
import asyncio
from pathlib import Path

# 添加 SuperAgent 到路径
sys.path.insert(0, str(Path(__file__).parent))

from utils.exceptions import (
    ExecutionError,
    ReviewError,
    ConfigurationError,
    LLMError,
    MemoryError,
    ValidationError,
    TaskError,
    OrchestratorError,
    SuperAgentError,
    ConversationError,
    PlanningError,
    ErrorCodes
)
from utils.error_handler import (
    handle_errors,
    safe_execute,
    ErrorHandler
)


def test_exception_hierarchy():
    """测试异常类层级"""
    print("\n" + "=" * 70)
    print("测试 1: 异常类层级")
    print("=" * 70)

    # 测试基类
    error = SuperAgentError(
        message="基础错误",
        details={"key": "value"},
        error_code="E0001"
    )

    assert error.message == "基础错误"
    assert error.details == {"key": "value"}
    assert error.error_code == "E0001"

    print("[OK] SuperAgentError 基类")

    # 测试子类
    conv_error = ConversationError(
        message="对话错误",
        error_code=ErrorCodes.INTENT_RECOGNITION_FAILED
    )

    assert isinstance(conv_error, SuperAgentError)
    assert conv_error.message == "对话错误"

    print("[OK] ConversationError 子类")

    # 测试 to_dict()
    error_dict = conv_error.to_dict()
    assert error_dict["error_type"] == "ConversationError"
    assert error_dict["message"] == "对话错误"

    print("[OK] to_dict() 方法")


def test_error_codes():
    """测试错误代码"""
    print("\n" + "=" * 70)
    print("测试 2: 错误代码常量")
    print("=" * 70)

    assert ErrorCodes.INTENT_RECOGNITION_FAILED == "E1001"
    assert ErrorCodes.PLAN_GENERATION_FAILED == "E2001"
    assert ErrorCodes.TASK_EXECUTION_FAILED == "E3001"
    assert ErrorCodes.REVIEW_FAILED == "E4001"
    assert ErrorCodes.INVALID_CONFIG == "E5001"

    print("[OK] 所有错误代码常量定义正确")


def test_error_handler_decorator():
    """测试错误处理装饰器"""
    print("\n" + "=" * 70)
    print("测试 3: 错误处理装饰器")
    print("=" * 70)

    @handle_errors(
        error_type=ConversationError,
        fallback="fallback_value",
        log=False
    )
    async def test_function(should_fail: bool = False):
        """测试函数"""
        if should_fail:
            raise ConversationError("测试错误")
        return "success"

    # 测试正常情况
    async def test_normal():
        result = await test_function(should_fail=False)
        assert result == "success"
        print("[OK] 正常执行")

    asyncio.run(test_normal())

    # 测试异常情况
    async def test_exception():
        result = await test_function(should_fail=True)
        assert result == "fallback_value"
        print("[OK] 异常捕获并返回 fallback")

    asyncio.run(test_exception())


def test_safe_execute():
    """测试 safe_execute 函数"""
    print("\n" + "=" * 70)
    print("测试 4: safe_execute 函数")
    print("=" * 70)

    def risky_function(should_fail: bool = False):
        """可能失败的函数"""
        if should_fail:
            raise ConversationError("函数执行失败")
        return "success"

    # 测试正常情况
    result = safe_execute(
        risky_function,
        False,
        fallback="fallback",
        log=False
    )
    assert result == "success"
    print("[OK] 正常执行")

    # 测试异常情况
    result = safe_execute(
        risky_function,
        True,
        fallback="fallback",
        log=False
    )
    assert result == "fallback"
    print("[OK] 异常捕获并返回 fallback")


def test_error_handler_class():
    """测试 ErrorHandler 类"""
    print("\n" + "=" * 70)
    print("测试 5: ErrorHandler 类")
    print("=" * 70)

    handler = ErrorHandler(max_errors=3)

    # 记录错误
    for i in range(3):
        error = ConversationError(f"错误 {i+1}")
        should_recover = handler.record_error(error)

    # 检查错误计数
    summary = handler.get_error_summary()
    assert summary["total_errors"] == 3
    print("[OK] 错误计数正确")

    # 检查是否应该触发恢复
    should_recover = handler.should_trigger_recovery()
    assert should_recover == True
    print("[OK] 触发恢复机制")

    # 重置
    handler.reset()
    summary = handler.get_error_summary()
    assert summary["total_errors"] == 0
    print("[OK] 重置功能正常")


def test_exception_str_representation():
    """测试异常的字符串表示"""
    print("\n" + "=" * 70)
    print("测试 6: 异常字符串表示")
    print("=" * 70)

    # 测试基本错误
    error1 = SuperAgentError("基本错误")
    str1 = str(error1)
    assert "基本错误" in str1
    print(f"[OK] 基本错误: {str1}")

    # 测试带错误代码的错误
    error2 = SuperAgentError("带代码的错误", error_code="E0001")
    str2 = str(error2)
    assert "E0001" in str2
    print(f"[OK] 带代码错误: {str2}")

    # 测试带详情的错误
    error3 = SuperAgentError(
        "带详情的错误",
        details={"key": "value", "num": 123}
    )
    str3 = str(error3)
    assert "key=value" in str3
    print(f"[OK] 带详情错误: {str3}")


def test_error_inheritance():
    """测试异常继承关系"""
    print("\n" + "=" * 70)
    print("测试 7: 异常继承关系")
    print("=" * 70)

    # 测试所有自定义异常都继承自 SuperAgentError
    exceptions = [
        ConversationError,
        PlanningError,
        ExecutionError,
        ReviewError,
        ConfigurationError,
        LLMError,
        MemoryError,
        ValidationError,
        TaskError,
        OrchestratorError
    ]

    for exc_class in exceptions:
        # 创建实例
        error = exc_class("测试")
        # 检查继承
        assert isinstance(error, SuperAgentError)
        print(f"[OK] {exc_class.__name__} 继承自 SuperAgentError")


def main():
    """主测试函数"""
    print("=" * 70)
    print("SuperAgent 错误处理机制测试")
    print("=" * 70)

    try:
        test_exception_hierarchy()
        test_error_codes()
        test_error_handler_decorator()
        test_safe_execute()
        test_error_handler_class()
        test_exception_str_representation()
        test_error_inheritance()

        print("\n" + "=" * 70)
        print("所有测试通过!")
        print("=" * 70)

        print("\n总结:")
        print("  [OK] 异常类层级结构")
        print("  [OK] 错误代码常量")
        print("  [OK] 错误处理装饰器")
        print("  [OK] safe_execute 函数")
        print("  [OK] ErrorHandler 类")
        print("  [OK] 异常字符串表示")
        print("  [OK] 异常继承关系")

        print("\n错误处理机制已正确实现!")

        return 0

    except AssertionError as e:
        print(f"\n[FAIL] 测试失败: {e}")
        return 1
    except Exception as e:
        print(f"\n[ERROR] 测试出错: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
