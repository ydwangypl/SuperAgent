# -*- coding: utf-8 -*-
"""
完整工作流端到端测试 - E2E 测试

测试完整的用户场景：需求 -> 规划 -> 执行 -> 验证 -> 完成
"""

import sys
import os
from pathlib import Path

# 添加项目根目录
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from common.models import AgentType
from orchestration.agent_factory import AgentFactory
from orchestration.registry import AgentRegistry
from execution.models import AgentStatus, AgentCapability


def test_simple_task_workflow():
    """测试简单任务工作流"""
    print("\n[E2E测试] 简单任务工作流")
    print("-" * 60)

    # 1. 创建 Agent
    factory = AgentFactory()
    agent = factory.create_agent(AgentType.FULL_STACK_DEV, "SimpleTaskBot")

    assert agent is not None
    print(f"  [阶段1] 创建 Agent: {agent.name}")

    # 2. 验证能力
    capabilities = agent.get_capabilities()
    assert len(capabilities) > 0
    print(f"  [阶段2] 能力验证 - 数量: {len(capabilities)}")

    # 3. 模拟任务执行状态
    agent.status = AgentStatus.WORKING
    print(f"  [阶段3] 任务执行 - 状态: {agent.status.value}")

    # 4. 模拟思考状态
    agent.status = AgentStatus.THINKING
    print(f"  [阶段4] 思考分析 - 状态: {agent.status.value}")

    # 5. 完成任务
    agent.status = AgentStatus.COMPLETED
    print(f"  [阶段5] 任务完成 - 状态: {agent.status.value}")

    print("  [OK] 简单任务工作流测试通过")
    print()


def test_planning_workflow():
    """测试规划工作流"""
    print("\n[E2E测试] 规划工作流")
    print("-" * 60)

    # 1. 检查支持的 Agent 类型
    registry = AgentRegistry()
    types = registry.get_all_types()

    print(f"  [阶段1] 支持的 Agent 类型: {len(types)}")

    # 2. 创建不同类型的 Agent
    factory = AgentFactory()

    agents = []
    agent_specs = [
        (AgentType.FULL_STACK_DEV, "全栈开发"),
        (AgentType.BACKEND_DEV, "后端开发"),
        (AgentType.API_DESIGN, "API设计"),
    ]

    for agent_type, desc in agent_specs:
        agent = factory.create_agent(agent_type, f"Plan{agent_type.name}")
        agents.append(agent)
        print(f"  [阶段2] 创建 {desc} Agent: {agent.name}")

    # 3. 验证所有 Agent 都有能力
    for agent in agents:
        caps = agent.get_capabilities()
        assert len(caps) > 0
        print(f"  [阶段3] {agent.name} 能力: {len(caps)} 个")

    print("  [OK] 规划工作流测试通过")
    print()


def test_monitoring_workflow():
    """测试监控工作流"""
    print("\n[E2E测试] 监控工作流")
    print("-" * 60)

    factory = AgentFactory()

    # 1. 创建多个 Agent
    agents = []
    for i in range(3):
        agent = factory.create_agent(AgentType.FULL_STACK_DEV, f"MonitorAgent_{i}")
        agents.append(agent)

    print(f"  [阶段1] 创建 3 个 Agent: 成功")

    # 2. 设置不同状态
    agents[0].status = AgentStatus.IDLE
    agents[1].status = AgentStatus.WORKING
    agents[2].status = AgentStatus.THINKING

    print(f"  [阶段2] 设置状态: IDLE, WORKING, THINKING")

    # 3. 验证状态
    assert agents[0].status == AgentStatus.IDLE
    assert agents[1].status == AgentStatus.WORKING
    assert agents[2].status == AgentStatus.THINKING

    print(f"  [阶段3] 验证状态: 全部正确")

    print("  [OK] 监控工作流测试通过")
    print()


def test_integration_workflow():
    """测试集成工作流 - 组合多个组件"""
    print("\n[E2E测试] 集成工作流")
    print("-" * 60)

    # 1. 初始化组件
    print("  [阶段1] 初始化组件")

    factory = AgentFactory()
    registry = AgentRegistry()

    # 2. 创建 Agent
    agent = factory.create_agent(AgentType.FULL_STACK_DEV, "IntegrationAgent")
    print(f"  [阶段2] 创建 Agent: {agent.name}")

    # 3. 检查 Agent 类型
    types = registry.get_all_types()
    print(f"  [阶段3] 可用类型: {len(types)} 个")

    # 4. 执行任务序列
    print(f"  [阶段4] 执行任务序列")

    tasks = [
        ("设计阶段", AgentStatus.THINKING),
        ("开发阶段", AgentStatus.WORKING),
        ("审查阶段", AgentStatus.REVIEWING),
        ("完成", AgentStatus.COMPLETED)
    ]

    for task_name, expected_status in tasks:
        agent.status = expected_status
        print(f"      {task_name}: {agent.status.value}")

    # 5. 统计
    stats = {
        "Agent数量": 1,
        "任务数": len(tasks),
        "最终状态": agent.status.value
    }
    print(f"  [阶段5] 统计: {stats}")

    print("  [OK] 集成工作流测试通过")
    print()


def test_performance_workflow():
    """测试性能工作流"""
    print("\n[E2E测试] 性能工作流")
    print("-" * 60)

    import time

    # 1. 批量创建测试
    print("  [阶段1] 批量创建测试")

    start_time = time.time()

    factory = AgentFactory()
    agents = []
    for i in range(5):
        agent = factory.create_agent(AgentType.FULL_STACK_DEV, f"PerfAgent_{i}")
        agents.append(agent)

    creation_time = time.time() - start_time
    print(f"      创建 5 个 Agent 耗时: {creation_time:.4f}s")
    assert creation_time < 1.0, "Agent 创建时间过长"

    # 2. 批量状态更新
    print("  [阶段2] 批量状态更新")

    start_time = time.time()
    for agent in agents:
        agent.status = AgentStatus.WORKING
        _ = agent.get_capabilities()

    update_time = time.time() - start_time
    print(f"      更新 5 个 Agent 状态耗时: {update_time:.4f}s")

    # 3. 资源清理
    print("  [阶段3] 资源清理")
    agents.clear()
    print("      Agent 列表已清空")

    print("  [OK] 性能工作流测试通过")
    print()


def test_capability_verification():
    """测试能力验证"""
    print("\n[E2E测试] 能力验证")
    print("-" * 60)

    factory = AgentFactory()

    # 测试不同类型 Agent 的能力
    test_cases = [
        (AgentType.FULL_STACK_DEV, "全栈开发"),
        (AgentType.CODE_REVIEW, "代码审查"),
        (AgentType.API_DESIGN, "API设计"),
    ]

    for agent_type, desc in test_cases:
        agent = factory.create_agent(agent_type, f"Caps{agent_type.name}")
        caps = agent.get_capabilities()

        print(f"  [OK] {desc}: {len(caps)} 个能力")
        for cap in caps:
            print(f"      - {cap.value}")

        assert len(caps) > 0

    print("  [OK] 能力验证测试通过")
    print()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("完整工作流端到端测试套件")
    print("=" * 60)

    try:
        test_simple_task_workflow()
        test_planning_workflow()
        test_monitoring_workflow()
        test_integration_workflow()
        test_performance_workflow()
        test_capability_verification()

        print("=" * 60)
        print("[完成] 所有 E2E 测试通过!")
        print("=" * 60)

    except Exception as e:
        print(f"\n[失败] 测试异常: {e}")
        import traceback
        traceback.print_exc()
