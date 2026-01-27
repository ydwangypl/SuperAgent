#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Agent 分派器

根据解析结果分派到对应的 Agent 执行。

功能:
- 将任务类型映射到 AgentType
- 异步/同步执行任务
- 返回分派结果
"""

import asyncio
from typing import Dict, Any, Optional
from pathlib import Path
import sys

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from adapters.unified_adapter import UnifiedAdapter
from common.models import AgentType


class DispatchResult:
    """分派结果"""

    def __init__(
        self,
        success: bool,
        message: str = "",
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ):
        self.success = success
        self.message = message
        self.result = result
        self.error = error

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "message": self.message,
            "result": self.result,
            "error": self.error
        }

    def __repr__(self):
        if self.success:
            return f"DispatchResult(success=True, message='{self.message}')"
        else:
            return f"DispatchResult(success=False, error='{self.error}')"


class AgentDispatcher:
    """Agent 分派器

    将任务分派到正确的 Agent 执行。

    任务类型到 AgentType 的映射:
    - coding      -> FULL_STACK_DEV
    - research    -> PRODUCT_MANAGEMENT
    - review      -> CODE_REVIEW
    - planning    -> API_DESIGN (使用 API_DESIGN 作为架构设计)
    - analysis    -> DATA_ARCHITECT (使用 DATA_ARCHITECT 进行数据分析)
    """

    # 任务类型到 AgentType 的映射
    TASK_TO_AGENT = {
        "coding": AgentType.FULL_STACK_DEV,
        "research": AgentType.PRODUCT_MANAGEMENT,
        "review": AgentType.CODE_REVIEW,
        "planning": AgentType.API_DESIGN,
        "analysis": AgentType.DATABASE_DESIGN,  # 使用 DATABASE_DESIGN 作为数据分析
    }

    # AgentType 到描述的映射
    AGENT_DESCRIPTIONS = {
        AgentType.FULL_STACK_DEV: "全栈开发",
        AgentType.BACKEND_DEV: "后端开发",
        AgentType.FRONTEND_DEV: "前端开发",
        AgentType.PRODUCT_MANAGEMENT: "产品管理",
        AgentType.CODE_REVIEW: "代码审查",
        AgentType.API_DESIGN: "API 设计与架构",
        AgentType.QA_ENGINEERING: "测试工程",
        AgentType.DEVOPS: "DevOps",
        AgentType.DATABASE_DESIGN: "数据库设计",
        AgentType.DOCUMENTATION: "文档编写",
        AgentType.TECHNICAL_WRITING: "技术文档",
        AgentType.SECURITY_AUDIT: "安全审计",
        AgentType.PERFORMANCE_OPTIMIZATION: "性能优化",
    }

    def __init__(self, project_root: Optional[Path] = None):
        """初始化 Agent 分派器

        Args:
            project_root: 项目根目录
        """
        self.project_root = project_root or Path(".")
        self.adapter = UnifiedAdapter(project_root=self.project_root)

    def dispatch(
        self,
        task_type: str,
        description: str,
        options: Optional[Dict[str, Any]] = None
    ) -> DispatchResult:
        """分派任务 (同步版本)

        Args:
            task_type: 任务类型
            description: 任务描述
            options: 附加选项

        Returns:
            DispatchResult: 分派结果
        """
        try:
            # 1. 确定 Agent 类型
            agent_type = self.TASK_TO_AGENT.get(
                task_type,
                AgentType.FULL_STACK_DEV
            )

            # 2. 构建任务数据
            task_data = {
                "description": description,
                "agent_type": agent_type.value,
                **(options or {})
            }

            # 3. 同步执行任务 (在新的事件循环中)
            result = asyncio.run(
                self.adapter.execute_task(
                    task_type=task_type,
                    task_data=task_data
                )
            )

            agent_name = self.AGENT_DESCRIPTIONS.get(agent_type, agent_type.value)

            return DispatchResult(
                success=result.success,
                message=f"任务已分派给 {agent_name}",
                result=result.to_dict()
            )

        except Exception as e:
            return DispatchResult(
                success=False,
                error=str(e)
            )

    async def dispatch_async(
        self,
        task_type: str,
        description: str,
        options: Optional[Dict[str, Any]] = None
    ) -> DispatchResult:
        """分派任务 (异步版本)

        Args:
            task_type: 任务类型
            description: 任务描述
            options: 附加选项

        Returns:
            DispatchResult: 分派结果
        """
        try:
            # 1. 确定 Agent 类型
            agent_type = self.TASK_TO_AGENT.get(
                task_type,
                AgentType.FULL_STACK_DEV
            )

            # 2. 构建任务数据
            task_data = {
                "description": description,
                "agent_type": agent_type.value,
                **(options or {})
            }

            # 3. 异步执行任务
            result = await self.adapter.execute_task(
                task_type=task_type,
                task_data=task_data
            )

            agent_name = self.AGENT_DESCRIPTIONS.get(agent_type, agent_type.value)

            return DispatchResult(
                success=result.success,
                message=f"任务已分派给 {agent_name}",
                result=result.to_dict()
            )

        except Exception as e:
            return DispatchResult(
                success=False,
                error=str(e)
            )

    def dispatch_from_parsed(
        self,
        parsed_result,
        options: Optional[Dict[str, Any]] = None
    ) -> DispatchResult:
        """从解析结果分派任务

        Args:
            parsed_result: NaturalLanguageParser 的解析结果
            options: 附加选项

        Returns:
            DispatchResult: 分派结果
        """
        return self.dispatch(
            task_type=parsed_result.task_type.value,
            description=parsed_result.description,
            options=options
        )

    async def dispatch_from_parsed_async(
        self,
        parsed_result,
        options: Optional[Dict[str, Any]] = None
    ) -> DispatchResult:
        """从解析结果分派任务 (异步)

        Args:
            parsed_result: NaturalLanguageParser 的解析结果
            options: 附加选项

        Returns:
            DispatchResult: 分派结果
        """
        return await self.dispatch_async(
            task_type=parsed_result.task_type.value,
            description=parsed_result.description,
            options=options
        )

    def get_agent_for_task_type(self, task_type: str) -> AgentType:
        """获取任务类型对应的 AgentType

        Args:
            task_type: 任务类型

        Returns:
            AgentType: 对应的 Agent 类型
        """
        return self.TASK_TO_AGENT.get(
            task_type,
            AgentType.FULL_STACK_DEV
        )

    def get_agent_description(self, agent_type: AgentType) -> str:
        """获取 Agent 类型的描述

        Args:
            agent_type: Agent 类型

        Returns:
            str: 描述文本
        """
        return self.AGENT_DESCRIPTIONS.get(
            agent_type,
            agent_type.value
        )


# ============ 测试代码 ============

if __name__ == "__main__":
    dispatcher = AgentDispatcher()

    test_cases = [
        ("coding", "创建一个用户登录模块"),
        ("research", "分析竞争对手的产品功能"),
        ("review", "审查代码质量"),
        ("planning", "设计系统架构"),
    ]

    for task_type, description in test_cases:
        result = dispatcher.dispatch(task_type, description)
        print(f"\n任务类型: {task_type}")
        print(f"描述: {description}")
        print(f"结果: {result}")
