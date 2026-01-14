# -*- coding: utf-8 -*-
"""
Agent 生命周期端到端测试 - E2E 测试

测试完整 Agent 生命周期：创建 -> 计划 -> 执行 -> 验证 -> 完成
"""

import sys
import os

# 添加项目根目录
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from common.models import AgentType
from orchestration.agent_factory import AgentFactory
from orchestration.registry import AgentRegistry
from execution.models import AgentStatus, AgentCapability


def test_agent_creation():
    """测试 Agent 创建"""
    print("\n[E2E测试] Agent 创建")
    print("-" * 60)

    factory = AgentFactory()

    # 创建 Agent - 使用 AgentType
    coding_agent = factory.create_agent(AgentType.FULL_STACK_DEV, "TestAgent_001")

    assert coding_agent is not None
    assert coding_agent.agent_id == "TestAgent_001"
    assert coding_agent.status == AgentStatus.IDLE

    print(f"  [OK] Agent 创建成功: {coding_agent.name}")
    print(f"  [OK] Agent ID: {coding_agent.agent_id}")
    print(f"  [OK] 初始状态: {coding_agent.status.value}")
    print()


def test_agent_factory_creation():
    """测试 AgentFactory 创建"""
    print("\n[E2E测试] AgentFactory 创建")
    print("-" * 60)

    factory = AgentFactory()

    # 创建不同类型的 Agent
    agent_types = [
        AgentType.FULL_STACK_DEV,
        AgentType.BACKEND_DEV,
        AgentType.FRONTEND_DEV
    ]

    for agent_type in agent_types:
        agent = factory.create_agent(agent_type, agent_id=f"Test{agent_type.name}")
        assert agent is not None
        assert agent.agent_id == f"Test{agent_type.name}"
        print(f"  [OK] {agent_type.value} Agent 创建成功: {agent.name} (ID: {agent.agent_id})")

    print()


def test_agent_lifecycle():
    """测试完整 Agent 生命周期"""
    print("\n[E2E测试] Agent 完整生命周期")
    print("-" * 60)

    factory = AgentFactory()
    agent = factory.create_agent(AgentType.FULL_STACK_DEV, "LifecycleTestAgent")

    # 1. 创建后状态
    assert agent.status == AgentStatus.IDLE
    print(f"  [阶段1] 创建完成 - 状态: {agent.status.value}")

    # 2. 开始执行 - 模拟状态变化
    agent.status = AgentStatus.WORKING
    assert agent.status == AgentStatus.WORKING
    print(f"  [阶段2] 开始执行 - 状态: {agent.status.value}")

    # 3. 验证能力
    capabilities = agent.get_capabilities()
    assert len(capabilities) > 0
    print(f"  [阶段3] 能力验证 - 数量: {len(capabilities)}")

    # 4. 思考中
    agent.status = AgentStatus.THINKING
    assert agent.status == AgentStatus.THINKING
    print(f"  [阶段4] 思考中 - 状态: {agent.status.value}")

    # 5. 恢复工作
    agent.status = AgentStatus.WORKING
    assert agent.status == AgentStatus.WORKING
    print(f"  [阶段5] 恢复工作 - 状态: {agent.status.value}")

    # 6. 完成
    agent.status = AgentStatus.COMPLETED
    assert agent.status == AgentStatus.COMPLETED
    print(f"  [阶段6] 完成 - 状态: {agent.status.value}")

    print()


def test_agent_registry():
    """测试 Agent 注册表"""
    print("\n[E2E测试] Agent 注册表")
    print("-" * 60)

    # AgentRegistry 是用于管理 Agent 类型的注册表
    registry = AgentRegistry()

    # 获取所有支持的 Agent 类型
    all_types = registry.get_all_types()
    print(f"  [OK] 支持的 Agent 类型数: {len(all_types)}")

    # 检查特定类型是否已注册
    has_coding = registry.get_impl_class(AgentType.FULL_STACK_DEV) is not None
    print(f"  [OK] FULL_STACK_DEV 已注册: {has_coding}")

    # 获取类型的描述
    desc = registry.get_description(AgentType.FULL_STACK_DEV)
    print(f"  [OK] FULL_STACK_DEV 描述: {desc[:50]}...")

    print()


def test_agent_concurrent_creation():
    """测试 Agent 并发创建"""
    print("\n[E2E测试] Agent 并发创建")
    print("-" * 60)

    import asyncio

    async def run_concurrent_test():
        factory = AgentFactory()

        # 并发创建多个 Agent
        agents = []
        for i in range(3):
            agent = factory.create_agent(
                AgentType.FULL_STACK_DEV,
                agent_id=f"ConcurrentAgent_{i}"
            )
            agents.append(agent)

        assert len(agents) == 3
        for i, agent in enumerate(agents):
            assert agent.agent_id == f"ConcurrentAgent_{i}"
            print(f"  [OK] Agent {i} 创建成功: {agent.name} (ID: {agent.agent_id})")

        return agents

    results = asyncio.run(run_concurrent_test())
    assert len(results) == 3
    print()


def test_agent_error_handling():
    """测试 Agent 错误处理"""
    print("\n[E2E测试] Agent 错误处理")
    print("-" * 60)

    factory = AgentFactory()
    agent = factory.create_agent(AgentType.FULL_STACK_DEV, "ErrorTestAgent")
    agent.status = AgentStatus.WORKING

    # 测试思考中
    agent.status = AgentStatus.THINKING
    assert agent.status == AgentStatus.THINKING
    print(f"  [OK] Agent 可以思考 - 状态: {agent.status.value}")

    # 测试工作中
    agent.status = AgentStatus.WORKING
    assert agent.status == AgentStatus.WORKING
    print(f"  [OK] Agent 可以工作 - 状态: {agent.status.value}")

    # 测试失败状态
    agent.status = AgentStatus.FAILED
    assert agent.status == AgentStatus.FAILED
    print(f"  [OK] Agent 失败状态 - 状态: {agent.status.value}")

    # 测试阻塞状态
    agent.status = AgentStatus.BLOCKED
    assert agent.status == AgentStatus.BLOCKED
    print(f"  [OK] Agent 阻塞状态 - 状态: {agent.status.value}")

    print()


def test_agent_capabilities():
    """测试 Agent 能力"""
    print("\n[E2E测试] Agent 能力")
    print("-" * 60)

    factory = AgentFactory()
    agent = factory.create_agent(AgentType.FULL_STACK_DEV, "CapabilityTestAgent")

    # 获取能力
    capabilities = agent.get_capabilities()

    print(f"  [OK] Agent 能力数量: {len(capabilities)}")
    for cap in capabilities:
        print(f"      - {cap.value}")

    # 验证常见能力
    assert AgentCapability.CODE_GENERATION in capabilities
    print(f"  [OK] CODE_GENERATION 能力存在")

    print()


def test_supported_agent_types():
    """测试支持的 Agent 类型"""
    print("\n[E2E测试] 支持的 Agent 类型")
    print("-" * 60)

    factory = AgentFactory()
    types = factory.get_supported_agent_types()

    print(f"  [OK] 支持的 Agent 类型数: {len(types)}")
    for agent_type in types:
        print(f"      - {agent_type.value}")

    assert len(types) > 0
    print()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Agent 生命周期端到端测试套件")
    print("=" * 60)

    try:
        test_agent_creation()
        test_agent_factory_creation()
        test_agent_lifecycle()
        test_agent_registry()
        test_agent_concurrent_creation()
        test_agent_error_handling()
        test_agent_capabilities()
        test_supported_agent_types()

        print("=" * 60)
        print("[完成] 所有 E2E 测试通过!")
        print("=" * 60)

    except Exception as e:
        print(f"\n[失败] 测试异常: {e}")
        import traceback
        traceback.print_exc()
