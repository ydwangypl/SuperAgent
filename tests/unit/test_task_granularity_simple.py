"""
Task Granularity Validator 单元测试 (简化版)

测试任务粒度验证器的核心功能
"""

import pytest
from datetime import timedelta
from planning.task_granularity_validator import (
    TaskGranularityValidator,
    TaskTooLargeError,
    TaskSplitResult,
    validate_task_granularity,
    auto_split_large_task
)
from planning.models import Step
from common.models import AgentType


class TestTaskGranularityValidator:
    """TaskGranularityValidator 测试套件"""

    def test_init_default(self):
        """测试默认初始化"""
        validator = TaskGranularityValidator()
        assert validator.strict_mode is True
        assert len(validator.violations) == 0

    def test_validate_single_action_task(self):
        """测试单一动作任务"""
        task = Step(
            id="task-1",
            name="Write failing test",
            description="Write failing test for user login",
            agent_type=AgentType.QA_ENGINEERING,
            estimated_time=timedelta(minutes=2)
        )
        validator = TaskGranularityValidator()

        result = validator.validate_task(task)
        assert result is True
        assert len(validator.violations) == 0

    def test_validate_multi_action_task_strict(self):
        """测试多动作任务 (严格模式)"""
        task = Step(
            id="task-1",
            name="Multi-action task",
            description="Write test and implement code and commit",
            agent_type=AgentType.BACKEND_DEV
        )
        validator = TaskGranularityValidator(strict_mode=True)

        with pytest.raises(TaskTooLargeError) as exc_info:
            validator.validate_task(task)

        assert exc_info.value.task_id == "task-1"
        assert "包含多个动作" in str(exc_info.value)

    def test_validate_multi_action_task_non_strict(self):
        """测试多动作任务 (非严格模式)"""
        task = Step(
            id="task-1",
            name="Multi-action task",
            description="Write test and implement code",
            agent_type=AgentType.BACKEND_DEV
        )
        validator = TaskGranularityValidator(strict_mode=False)

        result = validator.validate_task(task)
        assert result is False
        assert len(validator.violations) > 0

    def test_validate_task_too_long(self):
        """测试任务时间过长"""
        task = Step(
            id="task-1",
            name="Long task",
            description="Implement feature",
            agent_type=AgentType.BACKEND_DEV,
            estimated_time=timedelta(minutes=10)  # 10 分钟
        )
        validator = TaskGranularityValidator()

        # 检查时长 (估计时间 > 5 分钟应该失败)
        # timedelta(minutes=10) = 600 seconds
        # 这应该触发超时检查
        with pytest.raises(TaskTooLargeError):
            validator.validate_task(task)

    def test_validate_task_acceptable_duration(self):
        """测试可接受的任务时长"""
        task = Step(
            id="task-1",
            name="Short task",
            description="Write test",
            agent_type=AgentType.QA_ENGINEERING,
            estimated_time=timedelta(minutes=2)  # 2 分钟
        )
        validator = TaskGranularityValidator()

        assert validator.validate_task(task) is True


class TestTaskSplitting:
    """任务拆分测试"""

    def test_auto_split_single_action(self):
        """测试拆分单一动作任务 (无需拆分)"""
        task = Step(
            id="task-1",
            name="Simple task",
            description="Write failing test",
            agent_type=AgentType.QA_ENGINEERING
        )
        validator = TaskGranularityValidator()

        result = validator.auto_split_task(task)

        assert result.success is False
        assert len(result.subtasks) == 1
        assert "无需拆分" in result.reason

    def test_auto_split_multi_action_chinese(self):
        """测试拆分多动作任务 (中文)"""
        task = Step(
            id="task-1",
            name="Multi-action task",
            description="编写测试并实现代码",
            agent_type=AgentType.BACKEND_DEV
        )
        validator = TaskGranularityValidator()

        result = validator.auto_split_task(task)

        assert result.success is True
        assert len(result.subtasks) == 2
        assert result.subtasks[0].id == "task-1-0"
        assert result.subtasks[1].id == "task-1-1"

    def test_auto_split_preserves_properties(self):
        """测试拆分保留任务属性"""
        task = Step(
            id="task-1",
            name="Multi-action with inputs",
            description="Write test and implement code",
            agent_type=AgentType.BACKEND_DEV,
            inputs={"file": "test.py"},
            estimated_time=timedelta(minutes=5)
        )
        validator = TaskGranularityValidator()

        result = validator.auto_split_task(task)

        assert result.success is True
        for subtask in result.subtasks:
            assert subtask.agent_type == task.agent_type
            assert subtask.inputs == task.inputs


class TestConvenienceFunctions:
    """便捷函数测试"""

    def test_validate_task_granularity(self):
        """测试 validate_task_granularity 函数"""
        task = Step(
            id="task-1",
            name="Simple task",
            description="Write test",
            agent_type=AgentType.QA_ENGINEERING,
            estimated_time=timedelta(minutes=2)
        )

        assert validate_task_granularity(task) is True
        assert validate_task_granularity(task, strict_mode=False) is True

    def test_auto_split_large_task(self):
        """测试 auto_split_large_task 函数"""
        task = Step(
            id="task-1",
            name="Large task",
            description="Write test and implement code",
            agent_type=AgentType.BACKEND_DEV
        )

        result = auto_split_large_task(task)

        assert result.success is True
        assert isinstance(result, TaskSplitResult)


class TestEdgeCases:
    """边界情况测试"""

    def test_empty_description(self):
        """测试空描述"""
        task = Step(
            id="task-1",
            name="Empty task",
            description="",
            agent_type=AgentType.QA_ENGINEERING,
            estimated_time=timedelta(minutes=1)
        )
        validator = TaskGranularityValidator()

        # 空描述也算单一动作
        assert validator.validate_task(task) is True

    def test_task_with_colon_separation(self):
        """测试冒号分隔的动作"""
        task = Step(
            id="task-1",
            name="Colon separated task",
            description="Write test: implement code: run tests",
            agent_type=AgentType.BACKEND_DEV
        )
        validator = TaskGranularityValidator()

        result = validator.auto_split_task(task)

        # 冒号应该能拆分
        assert result.success is True
        assert len(result.subtasks) >= 2

    def test_get_violations(self):
        """测试获取违规列表"""
        task = Step(
            id="task-1",
            name="Large task",
            description="Write test and implement code",
            agent_type=AgentType.BACKEND_DEV
        )
        validator = TaskGranularityValidator(strict_mode=False)

        validator.validate_task(task)

        violations = validator.get_violations()
        assert len(violations) > 0
        assert isinstance(violations, list)

    def test_has_violations(self):
        """测试检查是否有违规"""
        task = Step(
            id="task-1",
            name="Good task",
            description="Write test",
            agent_type=AgentType.QA_ENGINEERING,
            estimated_time=timedelta(minutes=2)
        )
        validator = TaskGranularityValidator()

        validator.validate_task(task)

        assert validator.has_violations() is False
