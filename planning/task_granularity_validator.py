"""
Task Granularity Validator - 任务粒度验证器

强制任务保持 2-5 分钟的粒度,确保任务足够小且专注

规则:
1. 每个任务应该是单一动作
2. 任务描述不应包含多个动作连接词
3. 任务估计时间不应超过 5 分钟
4. 超范围任务自动拆分

作者: SuperAgent Team
版本: v3.2.0
日期: 2026-01-13
"""

import re
from typing import List, Dict, Any
from dataclasses import dataclass
from datetime import timedelta
from planning.models import Step
import logging

logger = logging.getLogger(__name__)


class TaskTooLargeError(Exception):
    """任务过大异常"""

    def __init__(self, message: str, task_id: str = None):
        self.task_id = task_id
        super().__init__(message)


@dataclass
class TaskSplitResult:
    """任务拆分结果"""
    original_task: Step
    subtasks: List[Step]
    reason: str
    success: bool


class TaskGranularityValidator:
    """
    任务粒度验证器

    确保所有任务保持 2-5 分钟的合理粒度
    """

    # 最大任务时长 (秒)
    MAX_TASK_DURATION = 300  # 5 分钟

    # 多动作连接词 (中英文)
    ACTION_WORDS = [
        "并", "和", "然后", "之后", "以及", "同时",
        "and", "then", "after", "also", "plus"
    ]

    # 拆分关键词
    SPLIT_PATTERNS = [
        r'\s*\d+[\.\)]\s*',  # 序号如 1. 或 2)
        r'[,;:]\s*',  # 逗号、分号或冒号
        r'\s*和\s*',  # 中文"和"(空格可选)
        r'\s*并\s*',  # 中文"并"(空格可选)
        r'\s+and\s+',  # 英文"and"
        r'\s+然后\s*',  # 中文"然后"
        r'\s+then\s+',  # 英文"then"
    ]

    def __init__(self, strict_mode: bool = True):
        """
        初始化任务粒度验证器

        Args:
            strict_mode: 严格模式,如果为 True 则任何违规都会抛出异常
        """
        self.strict_mode = strict_mode
        self.violations: List[str] = []

    def validate_task(self, task: Step) -> bool:
        """
        验证任务粒度是否符合要求

        Args:
            task: 要验证的任务

        Returns:
            bool: 如果任务粒度符合要求返回 True

        Raises:
            TaskTooLargeError: 当任务过大时 (仅在严格模式)
        """
        self.violations = []

        # 1. 检查是否包含多个动作
        if self._is_multi_action_task(task):
            error_msg = (
                f"任务 {task.id} ('{task.description}') 包含多个动作, "
                f"必须拆分为单一动作的任务"
            )
            self._handle_violation(error_msg, "multi_action")
            if self.strict_mode:
                raise TaskTooLargeError(error_msg, task_id=task.id)
            return False

        # 2. 检查估计时间
        if hasattr(task, 'estimated_time') and task.estimated_time:
            estimated_seconds = int(task.estimated_time.total_seconds())
            if estimated_seconds > self.MAX_TASK_DURATION:
                error_msg = (
                    f"任务 {task.id} 预计 {estimated_seconds}s, "
                    f"超过限制 ({self.MAX_TASK_DURATION}s = 5分钟)"
                )
                self._handle_violation(error_msg, "too_long")
                if self.strict_mode:
                    raise TaskTooLargeError(error_msg, task_id=task.id)
                return False

        # 3. 检查描述长度 (简单启发式)
        if len(task.description) > 200:
            error_msg = (
                f"任务 {task.id} 描述过长 ({len(task.description)} 字符), "
                f"可能包含多个动作"
            )
            self._handle_violation(error_msg, "description_too_long")
            if self.strict_mode:
                raise TaskTooLargeError(error_msg, task_id=task.id)
            return False

        return True

    def validate_task_list(self, tasks: List[Step]) -> Dict[str, Any]:
        """批量验证任务列表"""
        valid_count = 0
        all_violations = []

        for task in tasks:
            if self.validate_task(task):
                valid_count += 1
            else:
                all_violations.extend(self.get_violations())

        return {
            "total_steps": len(tasks),
            "valid_steps": valid_count,
            "all_valid": valid_count == len(tasks),
            "violations": all_violations
        }

    def auto_split_task(self, task: Step) -> TaskSplitResult:
        """
        自动拆分超范围任务

        Args:
            task: 要拆分的任务

        Returns:
            TaskSplitResult: 拆分结果
        """
        try:
            # 1. 获取估计时间
            estimated_seconds = 0
            if hasattr(task, 'estimated_time') and task.estimated_time:
                estimated_seconds = int(task.estimated_time.total_seconds())

            # 2. 尝试按动作拆分
            actions = self._split_into_actions(task.description)

            if len(actions) <= 1:
                # 无法按动作拆分,检查是否因为时间超限需要拆分
                if estimated_seconds <= self.MAX_TASK_DURATION:
                    return TaskSplitResult(
                        original_task=task,
                        subtasks=[task],
                        reason="任务已经是单一动作且时长合理,无需拆分",
                        success=False
                    )

                # 时间超限,按时间强制拆分
                num_splits = (estimated_seconds + self.MAX_TASK_DURATION - 1) // \
                    self.MAX_TASK_DURATION
                actions = [
                    f"{task.description} (第 {i+1}/{num_splits} 阶段)"
                    for i in range(num_splits)
                ]
                reason = (
                    f"任务时长 ({estimated_seconds}s) 超过限制,"
                    f"按时间强制拆分为 {num_splits} 个阶段"
                )
            else:
                reason = f"任务已根据动作描述拆分为 {len(actions)} 个子任务"

            # 3. 创建子任务
            subtasks = []
            for i, action in enumerate(actions):
                action = action.strip()
                if not action:
                    continue

                # 确定依赖
                if i == 0:
                    dependencies = list(task.dependencies) if task.dependencies else []
                else:
                    dependencies = [f"{task.id}-{i-1}"]

                # 计算子任务的估计时间
                # 尽量均匀分配时间,但不超过限制
                subtask_seconds = min(
                    estimated_seconds // len(actions) if estimated_seconds > 0 else 180,
                    self.MAX_TASK_DURATION
                )

                subtask = Step(
                    id=f"{task.id}-{i}",
                    name=f"{task.name} (part {i+1})",
                    description=action,
                    agent_type=task.agent_type,
                    dependencies=dependencies,
                    inputs=task.inputs,
                    can_parallel=task.can_parallel,
                    estimated_time=timedelta(seconds=subtask_seconds)
                )
                subtasks.append(subtask)

            return TaskSplitResult(
                original_task=task,
                subtasks=subtasks,
                reason=reason,
                success=True
            )

        except Exception as e:
            logger.error(f"拆分任务 {task.id} 失败: {e}")
            return TaskSplitResult(
                original_task=task,
                subtasks=[task],
                reason=f"拆分失败: {str(e)}",
                success=False
            )

    def _is_multi_action_task(self, task: Step) -> bool:
        """
        检测任务是否包含多个动作

        Args:
            task: 要检查的任务

        Returns:
            bool: 如果包含多个动作返回 True
        """
        description = task.description.lower()

        # 检查是否包含多动作连接词
        for word in self.ACTION_WORDS:
            if word in description:
                # 确保是独立词,而不是其他词的一部分
                pattern = rf'\b{re.escape(word)}\b'
                if re.search(pattern, description):
                    return True

        return False

    def _split_into_actions(self, description: str) -> List[str]:
        """
        将任务描述拆分为多个动作

        Args:
            description: 任务描述

        Returns:
            List[str]: 动作列表
        """
        actions = [description]

        # 尝试各种拆分模式
        for pattern in self.SPLIT_PATTERNS:
            new_actions = []
            for action in actions:
                parts = re.split(pattern, action)
                new_actions.extend(parts)
            actions = new_actions

            # 如果成功拆分,停止
            if len(actions) > 1:
                break

        # 清理动作
        cleaned_actions = []
        for action in actions:
            action = action.strip()
            if action:
                # 移除序号
                action = re.sub(r'^\d+[\.\)]\s*', '', action)
                cleaned_actions.append(action)

        return cleaned_actions

    def _handle_violation(self, message: str, violation_type: str) -> None:
        """
        处理违规情况

        Args:
            message: 违规消息
            violation_type: 违规类型
        """
        self.violations.append(message)
        logger.warning(f"Task Granularity Violation: {message}")

    def get_violations(self) -> List[str]:
        """
        获取所有违规消息

        Returns:
            List[str]: 违规消息列表
        """
        return self.violations.copy()

    def has_violations(self) -> bool:
        """
        检查是否有违规

        Returns:
            bool: 如果有违规返回 True
        """
        return len(self.violations) > 0


# 便捷函数

def validate_task_granularity(task: Step, strict_mode: bool = True) -> bool:
    """
    验证任务粒度

    Args:
        task: 要验证的任务
        strict_mode: 严格模式

    Returns:
        bool: 如果任务粒度符合要求返回 True

    Example:
        >>> from planning.models import Step
        >>> task = Step(id="task-1", description="Write failing test")
        >>> if validate_task_granularity(task):
        ...     print("任务粒度符合要求")
    """
    validator = TaskGranularityValidator(strict_mode=strict_mode)
    return validator.validate_task(task)


def auto_split_large_task(task: Step) -> TaskSplitResult:
    """
    自动拆分大任务

    Args:
        task: 要拆分的任务

    Returns:
        TaskSplitResult: 拆分结果

    Example:
        >>> result = auto_split_large_task(large_task)
        >>> if result.success:
        ...     print(f"任务已拆分为 {len(result.subtasks)} 个子任务")
    """
    validator = TaskGranularityValidator(strict_mode=False)
    return validator.auto_split_task(task)
