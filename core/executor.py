#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
任务执行器抽象基类

定义了所有执行器必须实现的接口,使得 SuperAgent
可以支持多种类型的任务执行,而不仅限于代码执行。
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime


from common.models import TaskStatus


@dataclass
class Task:
    """
    任务数据模型

    通用的任务表示,可以用于代码生成、内容创作、设计等任何领域。

    Attributes:
        task_type: 任务类型 (如 "code", "writing", "design")
        description: 任务描述
        context: 任务上下文信息
        requirements: 任务要求列表
        metadata: 额外的元数据
    """

    task_type: str
    description: str
    context: Dict[str, Any] = field(default_factory=dict)
    requirements: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __repr__(self) -> str:
        return f"Task(type={self.task_type}, description={self.description[:50]}...)"


@dataclass
class ExecutionResult:
    """
    执行结果数据模型

    通用的执行结果表示。

    Attributes:
        success: 是否成功
        content: 生成的内容
        status: 任务状态
        error: 错误信息 (如果失败)
        metadata: 额外的元数据
        execution_time: 执行耗时 (秒)
    """

    success: bool
    content: Any
    status: TaskStatus
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)

    def __repr__(self) -> str:
        status_str = f"✅" if self.success else f"❌"
        return f"{status_str} ExecutionResult(success={self.success}, status={self.status.value})"


class Executor(ABC):
    """
    任务执行器抽象基类

    所有执行器必须继承此类并实现 execute() 方法。

    设计理念:
    - 依赖倒置: 高层模块依赖此抽象,而非具体实现
    - 开闭原则: 可以添加新的执行器而无需修改现有代码
    - 单一职责: 每个执行器只负责一种类型的任务
    """

    def __init__(self, name: Optional[str] = None):
        """
        初始化执行器

        Args:
            name: 执行器名称 (默认使用类名)
        """
        self.name = name or self.__class__.__name__

    @abstractmethod
    def execute(self, task: Task) -> ExecutionResult:
        """
        执行任务

        Args:
            task: 要执行的任务

        Returns:
            ExecutionResult: 执行结果

        Raises:
            NotImplementedError: 子类必须实现此方法
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement execute()")

    def can_handle(self, task_type: str) -> bool:
        """
        判断是否能处理指定类型的任务

        默认实现: 检查 task_type 是否在 get_supported_types() 返回的列表中

        Args:
            task_type: 任务类型

        Returns:
            bool: 是否能处理
        """
        return task_type in self.get_supported_types()

    def get_supported_types(self) -> List[str]:
        """
        获取支持的任务类型列表

        子类应该重写此方法以返回支持的任务类型。

        Returns:
            List[str]: 支持的任务类型列表
        """
        return []

    def validate_task(self, task: Task) -> bool:
        """
        验证任务是否有效

        默认实现: 检查任务类型是否支持

        Args:
            task: 要验证的任务

        Returns:
            bool: 任务是否有效
        """
        if not self.can_handle(task.task_type):
            return False

        if not task.description:
            return False

        return True

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name})"


class ExecutorError(Exception):
    """执行器异常基类"""

    def __init__(self, message: str, executor_name: str, task: Task):
        self.message = message
        self.executor_name = executor_name
        self.task = task
        super().__init__(f"[{executor_name}] {message}")


class TaskValidationError(ExecutorError):
    """任务验证失败异常"""

    pass


class TaskExecutionError(ExecutorError):
    """任务执行失败异常"""

    pass
