#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
核心执行器抽象层单元测试
"""

import pytest
import sys
from pathlib import Path
from typing import List

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.executor import (
    Executor,
    Task,
    ExecutionResult,
    TaskStatus,
    ExecutorError,
    TaskValidationError,
    TaskExecutionError
)


class MockCodeExecutor(Executor):
    """模拟代码执行器 - 用于测试"""

    def get_supported_types(self) -> List[str]:
        return ["code", "coding"]

    def execute(self, task: Task) -> ExecutionResult:
        if not self.validate_task(task):
            return ExecutionResult(
                success=False,
                content=None,
                status=TaskStatus.FAILED,
                error="Invalid task"
            )

        # 模拟执行
        return ExecutionResult(
            success=True,
            content=f"Generated code for: {task.description}",
            status=TaskStatus.COMPLETED,
            metadata={"language": "python"}
        )


class MockWritingExecutor(Executor):
    """模拟写作执行器 - 用于测试"""

    def get_supported_types(self) -> List[str]:
        return ["writing", "content"]

    def execute(self, task: Task) -> ExecutionResult:
        if not self.validate_task(task):
            return ExecutionResult(
                success=False,
                content=None,
                status=TaskStatus.FAILED,
                error="Invalid task"
            )

        # 模拟执行
        return ExecutionResult(
            success=True,
            content=f"Written content for: {task.description}",
            status=TaskStatus.COMPLETED,
            metadata={"word_count": 500}
        )


class TestTask:
    """Task 数据模型测试"""

    def test_task_creation(self):
        """测试任务创建"""
        task = Task(
            task_type="code",
            description="Create a user login function",
            requirements=["Use JWT", "Handle errors"]
        )

        assert task.task_type == "code"
        assert task.description == "Create a user login function"
        assert len(task.requirements) == 2
        assert task.context == {}

    def test_task_repr(self):
        """测试任务字符串表示"""
        task = Task(
            task_type="writing",
            description="A" * 100  # 长描述
        )

        repr_str = repr(task)
        assert "writing" in repr_str
        assert "..." in repr_str  # 应该被截断


class TestExecutionResult:
    """ExecutionResult 数据模型测试"""

    def test_success_result(self):
        """测试成功结果"""
        result = ExecutionResult(
            success=True,
            content="Generated code",
            status=TaskStatus.COMPLETED
        )

        assert result.success is True
        assert result.content == "Generated code"
        assert result.status == TaskStatus.COMPLETED
        assert result.error is None

    def test_failed_result(self):
        """测试失败结果"""
        result = ExecutionResult(
            success=False,
            content=None,
            status=TaskStatus.FAILED,
            error="Execution failed"
        )

        assert result.success is False
        assert result.content is None
        assert result.status == TaskStatus.FAILED
        assert result.error == "Execution failed"

    def test_result_repr(self):
        """测试结果字符串表示"""
        success_result = ExecutionResult(
            success=True,
            content="",
            status=TaskStatus.COMPLETED
        )
        assert "✅" in repr(success_result)

        failed_result = ExecutionResult(
            success=False,
            content=None,
            status=TaskStatus.FAILED
        )
        assert "❌" in repr(failed_result)


class TestExecutor:
    """Executor 抽象类测试"""

    def test_cannot_instantiate_abstract_executor(self):
        """测试不能实例化抽象执行器"""
        with pytest.raises(TypeError):
            Executor()

    def test_executor_name(self):
        """测试执行器名称"""
        executor = MockCodeExecutor()
        assert executor.name == "MockCodeExecutor"

        custom_executor = MockCodeExecutor(name="CustomExecutor")
        assert custom_executor.name == "CustomExecutor"

    def test_can_handle(self):
        """测试 can_handle 方法"""
        executor = MockCodeExecutor()

        assert executor.can_handle("code") is True
        assert executor.can_handle("coding") is True
        assert executor.can_handle("writing") is False
        assert executor.can_handle("design") is False

    def test_get_supported_types(self):
        """测试获取支持的类型"""
        code_executor = MockCodeExecutor()
        writing_executor = MockWritingExecutor()

        assert "code" in code_executor.get_supported_types()
        assert "writing" in writing_executor.get_supported_types()

    def test_validate_task_valid(self):
        """测试验证有效任务"""
        executor = MockCodeExecutor()
        task = Task(
            task_type="code",
            description="Create a function"
        )

        assert executor.validate_task(task) is True

    def test_validate_task_invalid_type(self):
        """测试验证无效类型任务"""
        executor = MockCodeExecutor()
        task = Task(
            task_type="writing",  # 错误的类型
            description="Write an article"
        )

        assert executor.validate_task(task) is False

    def test_validate_task_empty_description(self):
        """测试验证空描述任务"""
        executor = MockCodeExecutor()
        task = Task(
            task_type="code",
            description=""  # 空描述
        )

        assert executor.validate_task(task) is False

    def test_execute_success(self):
        """测试成功执行"""
        executor = MockCodeExecutor()
        task = Task(
            task_type="code",
            description="Create a login function"
        )

        result = executor.execute(task)

        assert result.success is True
        assert result.status == TaskStatus.COMPLETED
        assert "Generated code" in result.content
        assert result.metadata["language"] == "python"

    def test_execute_invalid_task(self):
        """测试执行无效任务"""
        executor = MockCodeExecutor()
        task = Task(
            task_type="writing",  # 错误的类型
            description="Write an article"
        )

        result = executor.execute(task)

        assert result.success is False
        assert result.status == TaskStatus.FAILED
        assert result.error == "Invalid task"

    def test_executor_repr(self):
        """测试执行器字符串表示"""
        executor = MockCodeExecutor(name="TestExecutor")
        repr_str = repr(executor)

        assert "MockCodeExecutor" in repr_str
        assert "TestExecutor" in repr_str


class TestExecutorErrors:
    """执行器异常测试"""

    def test_executor_error_creation(self):
        """测试执行器异常创建"""
        task = Task(task_type="code", description="Test")

        error = ExecutorError(
            message="Test error",
            executor_name="TestExecutor",
            task=task
        )

        assert error.message == "Test error"
        assert error.executor_name == "TestExecutor"
        assert error.task == task
        assert "TestExecutor" in str(error)

    def test_task_validation_error(self):
        """测试任务验证异常"""
        task = Task(task_type="code", description="Test")

        error = TaskValidationError(
            message="Validation failed",
            executor_name="TestExecutor",
            task=task
        )

        assert isinstance(error, ExecutorError)

    def test_task_execution_error(self):
        """测试任务执行异常"""
        task = Task(task_type="code", description="Test")

        error = TaskExecutionError(
            message="Execution failed",
            executor_name="TestExecutor",
            task=task
        )

        assert isinstance(error, ExecutorError)


class TestMultipleExecutors:
    """多执行器测试"""

    def test_different_executors_different_types(self):
        """测试不同执行器支持不同类型"""
        code_executor = MockCodeExecutor()
        writing_executor = MockWritingExecutor()

        # 代码执行器应该处理代码任务
        code_task = Task(task_type="code", description="Create code")
        assert code_executor.can_handle(code_task.task_type)

        # 写作执行器应该处理写作任务
        writing_task = Task(task_type="writing", description="Write article")
        assert writing_executor.can_handle(writing_task.task_type)

        # 交叉测试 - 不应该处理
        assert not code_executor.can_handle(writing_task.task_type)
        assert not writing_executor.can_handle(code_task.task_type)

    def test_execute_with_different_executors(self):
        """测试使用不同执行器执行任务"""
        code_executor = MockCodeExecutor()
        writing_executor = MockWritingExecutor()

        code_task = Task(task_type="code", description="Create a function")
        writing_task = Task(task_type="writing", description="Write an article")

        code_result = code_executor.execute(code_task)
        writing_result = writing_executor.execute(writing_task)

        assert code_result.success is True
        assert "Generated code" in code_result.content

        assert writing_result.success is True
        assert "Written content" in writing_result.content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
