#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Agent工厂

负责创建和管理Agent实例
"""

import logging
import uuid
import asyncio
from typing import Dict, Optional, Set, List

from common.models import AgentType
from .registry import AgentRegistry
from execution import (
    BaseAgent,
    AgentConfig
)
from execution.models import AgentCapability


logger = logging.getLogger(__name__)


class AgentFactory:
    """Agent工厂类 (Phase 3 重构版：基于 Registry)"""

    @classmethod
    def create_agent(
        cls,
        agent_type: AgentType,
        agent_id: Optional[str] = None,
        config: Optional[AgentConfig] = None
    ) -> BaseAgent:
        """创建Agent实例"""
        # 从注册中心获取类
        agent_class = AgentRegistry.get_impl_class(agent_type)

        if not agent_class:
            raise ValueError(f"不支持的Agent类型: {agent_type}")

        # 生成更规范的 agent_id
        if not agent_id:
            short_id = uuid.uuid4().hex[:6]
            agent_id = f"{agent_type.value}-{short_id}"

        # 创建Agent实例
        agent = agent_class(agent_id=agent_id, config=config)
        logger.info(f"创建Agent: {agent_id} (类型: {agent_type.value}, 类: {agent_class.__name__})")
        return agent

    @classmethod
    def get_agent_capabilities(cls, agent_type: AgentType) -> Set[AgentCapability]:
        """获取Agent的能力"""
        agent_class = AgentRegistry.get_impl_class(agent_type)
        if not agent_class:
            return set()

        try:
            return agent_class.get_capabilities()
        except Exception as e:
            logger.error(f"获取 Agent 能力失败 ({agent_type.value}): {e}")
            return set()

    @classmethod
    def get_supported_agent_types(cls) -> List[AgentType]:
        """获取支持的Agent类型列表"""
        return AgentRegistry.get_all_types()

    @classmethod
    def is_agent_type_supported(cls, agent_type: AgentType) -> bool:
        """检查Agent类型是否支持"""
        return AgentRegistry.get_impl_class(agent_type) is not None

    @classmethod
    async def create_agent_pool(
        cls,
        agent_types: Dict[AgentType, int],
        config: Optional[AgentConfig] = None
    ) -> Dict[str, BaseAgent]:
        """异步并发创建Agent池

        Args:
            agent_types: Agent类型和数量的映射
            config: Agent配置(可选)

        Returns:
            Dict[str, BaseAgent]: Agent实例映射
        """
        tasks = []
        for agent_type, count in agent_types.items():
            for i in range(count):
                agent_id = f"{agent_type.value}-{i + 1:02d}"
                tasks.append(cls._async_create_agent(agent_type, agent_id, config))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        pool: Dict[str, BaseAgent] = {}
        for result in results:
            if isinstance(result, BaseAgent):
                pool[result.agent_id] = result
            elif isinstance(result, Exception):
                logger.error(f"并发创建 Agent 失败: {type(result).__name__}: {result}")

        logger.info(f"并发创建Agent池完成: {len(pool)} 个Agent")
        return pool

    @classmethod
    async def _async_create_agent(
        cls,
        agent_type: AgentType,
        agent_id: str,
        config: Optional[AgentConfig] = None
    ) -> BaseAgent:
        """内部异步创建辅助方法 (针对轻量实例化优化)"""
        # 由于当前 Agent 实例化是纯内存操作且速度极快，直接执行优于线程切换
        # 如果未来涉及重型 I/O (如加载模型)，再考虑恢复 to_thread
        return cls.create_agent(agent_type, agent_id, config)
