"""
Task Granularity Validator 单元测试

测试任务粒度验证器的所有功能
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

    def test_init_non_strict(self):
        """测试非严格模式初始化"""
        validator = TaskGranularityValidator(strict_mode=False)
        assert validator.strict_mode is False

    def test_validate_single_action_task(self):
        """测试单一动作任务"""
        task = Step(
            id="task-1",
            name="Test Task",
            description="Write failing test for user login",
            agent_type=AgentType.QA_ENGINEERING
        )
        validator = TaskGranularityValidator()

        assert validator.validate_task(task) is True
        assert len(validator.violations) == 0

    def test_validate_multi_action_task_strict(self):
        """测试多动作任务 (严格模式)"""
        task = Step(
            id="task-1",
            name="Multi-action Task",
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
            name="Multi-action Task",
            description="Write test and implement code",
            agent_type=AgentType.BACKEND_DEV
        )
        validator = TaskGranularityValidator(strict_mode=False)

        assert validator.validate_task(task) is False
        assert len(validator.violations) > 0

    def test_validate_task_too_long(self):
        """测试任务时间过长"""
        task = Step(
            id="task-1",
            name="Long Task",
            description="Implement feature",
            agent_type=AgentType.BACKEND_DEV,
            estimated_time=timedelta(seconds=600)  # 10 分钟
        )
        validator = TaskGranularityValidator()

        with pytest.raises(TaskTooLargeError):
            validator.validate_task(task)

    def test_validate_task_acceptable_duration(self):
        """测试可接受的任务时长"""
        task = Step(
            id="task-1",
            name="Normal Task",
            description="Write test",
            agent_type=AgentType.QA_ENGINEERING,
            estimated_time=timedelta(seconds=120)  # 2 分钟
        )
        validator = TaskGranularityValidator()

        assert validator.validate_task(task) is True

    def test_validate_description_too_long(self):
        """测试描述过长"""
        long_description = "Implement feature " * 20  # > 200 字符
        task = Step(
            id="task-1",
            name="Long Description Task",
            description=long_description,
            agent_type=AgentType.BACKEND_DEV
        )
        validator = TaskGranularityValidator()

        with pytest.raises(TaskTooLargeError):
            validator.validate_task(task)

    def test_validate_task_list(self):
        """测试任务列表验证"""
        tasks = [
            Step(id="task-1", name="Task 1", description="Write test", agent_type=AgentType.QA_ENGINEERING),
            Step(
                id="task-2",
                name="Task 2",
                description="Write code and commit",
                agent_type=AgentType.BACKEND_DEV,
                estimated_time=timedelta(seconds=600)
            ),
            Step(id="task-3", name="Task 3", description="Refactor code", agent_type=AgentType.BACKEND_DEV)
        ]
        validator = TaskGranularityValidator(strict_mode=False)

        result = validator.validate_task_list(tasks)

        assert result["all_valid"] is False
        assert result["total_steps"] == 3
        assert result["valid_steps"] == 2
        assert len(result["violations"]) >= 1
        # 检查是否包含 task-2 的违规信息
        has_task2_violation = any("task-2" in v for v in result["violations"])
        assert has_task2_violation is True


class TestTaskSplitting:
    """任务拆分测试"""

    def test_auto_split_single_action(self):
        """测试拆分单一动作任务 (无需拆分)"""
        task = Step(
            id="task-1",
            name="Task 1",
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
            name="Task 1",
            description="编写测试并实现代码",
            agent_type=AgentType.BACKEND_DEV
        )
        validator = TaskGranularityValidator()

        result = validator.auto_split_task(task)

        assert result.success is True
        assert len(result.subtasks) == 2
        assert result.subtasks[0].id == "task-1-0"
        assert result.subtasks[1].id == "task-1-1"
        assert result.subtasks[1].dependencies == ["task-1-0"]

    def test_auto_split_multi_action_english(self):
        """测试拆分多动作任务 (英文)"""
        task = Step(
            id="task-1",
            name="Task 1",
            description="Write test, implement code, and commit",
            agent_type=AgentType.BACKEND_DEV
        )
        validator = TaskGranularityValidator()

        result = validator.auto_split_task(task)

        assert result.success is True
        assert len(result.subtasks) >= 2

    def test_auto_split_preserves_properties(self):
        """测试拆分保留任务属性"""
        task = Step(
            id="task-1",
            name="Task 1",
            description="Write test and implement code",
            agent_type=AgentType.BACKEND_DEV,
            inputs={"file": "test.py"},
            estimated_time=timedelta(seconds=300)
        )
        validator = TaskGranularityValidator()

        result = validator.auto_split_task(task)

        assert result.success is True
        for subtask in result.subtasks:
            assert subtask.agent_type == task.agent_type
            assert subtask.inputs == task.inputs
            assert subtask.estimated_time.total_seconds() <= 150  # 拆分后时间减半

    def test_auto_split_with_dependencies(self):
        """测试拆分保留依赖关系"""
        task = Step(
            id="task-1",
            name="Task 1",
            description="Design schema and create tables",
            agent_type=AgentType.DATABASE_DESIGN,
            dependencies=["task-0"]  # 原有依赖
        )
        validator = TaskGranularityValidator()

        result = validator.auto_split_task(task)

        assert result.success is True
        # 第一个子任务保留原有依赖
        assert result.subtasks[0].dependencies == ["task-0"]
        # 第二个子任务依赖第一个子任务
        assert result.subtasks[1].dependencies == ["task-1-0"]


class TestConvenienceFunctions:
    """便捷函数测试"""

    def test_validate_task_granularity(self):
        """测试 validate_task_granularity 函数"""
        task = Step(
            id="task-1",
            name="Task 1",
            description="Write test",
            agent_type=AgentType.QA_ENGINEERING
        )

        assert validate_task_granularity(task) is True
        assert validate_task_granularity(task, strict_mode=False) is True

    def test_auto_split_large_task(self):
        """测试 auto_split_large_task 函数"""
        task = Step(
            id="task-1",
            name="Task 1",
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
            name="Task 1",
            description="",
            agent_type=AgentType.QA_ENGINEERING
        )
        validator = TaskGranularityValidator()

        # 空描述也算单一动作
        assert validator.validate_task(task) is True

    def test_task_with_colon_separation(self):
        """测试冒号分隔的动作"""
        task = Step(
            id="task-1",
            name="Task 1",
            description="Write test: implement code: run tests",
            agent_type=AgentType.BACKEND_DEV
        )
        validator = TaskGranularityValidator()

        result = validator.auto_split_task(task)

        # 冒号应该能拆分
        assert result.success is True
        assert len(result.subtasks) >= 2

    def test_task_with_numbering(self):
        """测试带序号的任务"""
        task = Step(
            id="task-1",
            name="Task 1",
            description="1. Write test 2. Implement code 3. Run tests",
            agent_type=AgentType.BACKEND_DEV
        )
        validator = TaskGranularityValidator()

        result = validator.auto_split_task(task)

        assert result.success is True
        # 序号应该被移除
        assert not result.subtasks[0].description.startswith("1.")

    def test_get_violations(self):
        """测试获取违规列表"""
        task = Step(
            id="task-1",
            name="Task 1",
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
            name="Task 1",
            description="Write test",
            agent_type=AgentType.QA_ENGINEERING
        )
        validator = TaskGranularityValidator()

        validator.validate_task(task)

        assert validator.has_violations() is False

    def test_very_long_task(self):
        """测试非常长的任务"""
        task = Step(
            id="task-1",
            name="Task 1",
            description="Write test",
            agent_type=AgentType.QA_ENGINEERING,
            estimated_time=timedelta(seconds=3600)  # 1 小时
        )
        validator = TaskGranularityValidator()

        with pytest.raises(TaskTooLargeError):
            validator.validate_task(task)

        # 拆分后应该合理
        result = validator.auto_split_task(task)
        assert result.success is True
        # 即使无法拆分,至少会保留原任务
        assert len(result.subtasks) >= 1
