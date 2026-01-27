#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
抽象基类模块

定义 SuperAgent 的核心抽象基类，确保接口一致性。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol, TypeVar
from pathlib import Path


# 类型变量
T = TypeVar('T')
AgentType = TypeVar('AgentType')


class Agent(ABC):
    """Agent 抽象基类

    所有 Agent 实现都应继承此类。
    """

    @abstractmethod
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """执行任务

        Args:
            task: 任务数据

        Returns:
            执行结果
        """
        pass

    @abstractmethod
    async def validate(self, task: Dict[str, Any]) -> bool:
        """验证任务数据

        Args:
            task: 任务数据

        Returns:
            是否有效
        """
        pass

    @abstractmethod
    async def get_status(self) -> Dict[str, Any]:
        """获取 Agent 状态

        Returns:
            状态信息
        """
        pass


class Adapter(ABC):
    """适配器抽象基类

    所有适配器实现都应继承此类。
    """

    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """执行适配操作

        Args:
            **kwargs: 参数

        Returns:
            执行结果
        """
        pass

    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """验证配置

        Args:
            config: 配置

        Returns:
            是否有效
        """
        pass


class Reviewer(ABC):
    """代码审查抽象基类

    所有审查器实现都应继承此类。
    """

    @abstractmethod
    async def review(self, artifact: Any) -> 'ReviewResult':
        """审查产物

        Args:
            artifact: 要审查的产物

        Returns:
            审查结果
        """
        pass

    @abstractmethod
    def get_supported_types(self) -> List[str]:
        """获取支持的产物类型

        Returns:
            支持的类型列表
        """
        pass


class ReviewResult:
    """审查结果（协议，非 ABC）"""

    @property
    @abstractmethod
    def status(self) -> str:
        pass

    @property
    @abstractmethod
    def overall_score(self) -> float:
        pass

    @property
    @abstractmethod
    def feedback(self) -> str:
        pass

    @property
    @abstractmethod
    def approved(self) -> bool:
        pass


class MemoryStore(ABC):
    """记忆存储抽象基类

    所有记忆存储实现都应继承此类。
    """

    @abstractmethod
    async def save(self, key: str, value: Any) -> bool:
        """保存记忆"""
        pass

    @abstractmethod
    async def load(self, key: str) -> Optional[Any]:
        """加载记忆"""
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """删除记忆"""
        pass

    @abstractmethod
    async def search(self, query: str) -> List[Any]:
        """搜索记忆"""
        pass


class TaskPlanner(ABC):
    """任务规划器抽象基类"""

    @abstractmethod
    async def create_plan(self, requirements: Dict[str, Any]) -> 'ExecutionPlan':
        """创建执行计划

        Args:
            requirements: 需求

        Returns:
            执行计划
        """
        pass

    @abstractmethod
    async def update_plan(self, plan_id: str, updates: Dict[str, Any]) -> bool:
        """更新计划

        Args:
            plan_id: 计划 ID
            updates: 更新内容

        Returns:
            是否成功
        """
        pass


class ExecutionPlan:
    """执行计划（协议，非 ABC）"""

    @property
    @abstractmethod
    def plan_id(self) -> str:
        pass

    @property
    @abstractmethod
    def tasks(self) -> List[Dict[str, Any]]:
        pass

    @property
    @abstractmethod
    def status(self) -> str:
        pass


class Hook(ABC):
    """Hook 抽象基类"""

    @abstractmethod
    async def before_execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行前钩子

        Args:
            context: 执行上下文

        Returns:
            处理的上下文
        """
        pass

    @abstractmethod
    async def after_execute(
        self,
        context: Dict[str, Any],
        result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行后钩子

        Args:
            context: 执行上下文
            result: 执行结果

        Returns:
            处理的上下文
        """
        pass


class Observer(ABC):
    """观察者抽象基类（用于事件监听）"""

    @abstractmethod
    async def update(self, event: str, data: Dict[str, Any]) -> None:
        """更新

        Args:
            event: 事件类型
            data: 事件数据
        """
        pass


class Subject(ABC):
    """被观察者抽象基类"""

    @abstractmethod
    def attach(self, observer: Observer) -> None:
        """添加观察者"""
        pass

    @abstractmethod
    def detach(self, observer: Observer) -> None:
        """移除观察者"""
        pass

    @abstractmethod
    def notify(self, event: str, data: Dict[str, Any]) -> None:
        """通知观察者"""
        pass
