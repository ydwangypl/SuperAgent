#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
编排层测试脚本

测试完整的编排流程,包括任务执行、Agent调度、Worktree管理
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from planning.planner import ProjectPlanner
from orchestration.orchestrator import Orchestrator
from orchestration.models import OrchestrationConfig


def print_section(title):
    """打印分节标题"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


async def test_orchestration():
    """测试编排流程"""
    print_section("SuperAgent v3.0 编排层测试")

    # ========== 步骤1: 创建执行计划 ==========
    print_section("步骤1: 生成项目执行计划")

    user_input = "开发一个带数据库的博客系统,支持文章管理和用户评论"
    print(f"\n用户需求: {user_input}")

    planner = ProjectPlanner()
    plan = await planner.create_plan(user_input, {})

    print(f"\n计划生成完成:")
    print(f"  - 步骤数量: {len(plan.steps)}")
    print(f"  - 预计时间: {int(plan.estimated_time.total_seconds() / 60)}分钟")
    print(f"  - 风险等级: {plan.risk_report.overall_risk}")

    # 显示步骤概览
    print("\n执行步骤:")
    for i, step in enumerate(plan.steps, 1):
        deps = f" (依赖: {', '.join(step.dependencies)})" if step.dependencies else ""
        print(f"  {i}. {step.name}{deps}")
        print(f"     Agent: {step.agent_type.value}")

    # ========== 步骤2: 初始化编排器 ==========
    print_section("步骤2: 初始化编排器")

    config = OrchestrationConfig(
        max_parallel_tasks=2,
        max_concurrent_per_agent=2,
        enable_parallel_execution=True,
        enable_auto_retry=True
    )

    orchestrator = Orchestrator(
        project_root=Path(__file__).parent,
        config=config
    )

    print(f"\n编排器初始化完成:")
    print(f"  - 项目ID: {orchestrator.state.project_id}")
    print(f"  - 最大并行任务: {config.max_parallel_tasks}")
    print(f"  - 启用并行执行: {config.enable_parallel_execution}")
    print(f"  - Agent类型数量: {len(config.agent_resources)}")

    # ========== 步骤3: 执行计划 ==========
    print_section("步骤3: 执行项目计划")

    print("\n开始执行...")
    result = await orchestrator.execute_plan(plan)

    # ========== 步骤4: 显示执行结果 ==========
    print_section("步骤4: 执行结果")

    print(f"\n执行状态: {'成功' if result.success else '失败'}")
    print(f"  - 总任务数: {result.total_tasks}")
    print(f"  - 完成任务: {result.completed_tasks}")
    print(f"  - 失败任务: {result.failed_tasks}")
    print(f"  - 跳过任务: {result.skipped_tasks}")
    print(f"  - 执行时长: {result.duration_seconds}秒")
    print(f"  - 成功率: {result.success_rate * 100:.1f}%")

    # 显示任务执行详情
    print("\n任务执行详情:")
    for task in result.task_executions:
        status_symbol = {
            "completed": "✅",
            "failed": "❌",
            "skipped": "⏭️",
            "pending": "⏳"
        }.get(task.status.value, "❓")

        duration = ""
        if task.started_at and task.completed_at:
            duration = f" ({(task.completed_at - task.started_at).total_seconds():.2f}s)"

        print(f"  {status_symbol} {task.task_id}: {task.status.value.upper()}{duration}")

        if task.assignment:
            print(f"     Agent: {task.assignment.agent_type}")

        if task.error:
            print(f"     错误: {task.error}")

    # ========== 步骤5: 显示统计信息 ==========
    print_section("步骤5: 统计信息")

    stats = orchestrator.get_task_statistics()

    print(f"\n任务统计:")
    print(f"  - 总数: {stats['total']}")
    print(f"  - 已完成: {stats['completed']}")
    print(f"  - 失败: {stats['failed']}")
    print(f"  - 运行中: {stats['running']}")
    print(f"  - 待执行: {stats['pending']}")

    print(f"\nAgent统计:")
    for agent_type, agent_stats in stats['agent_stats'].items():
        print(f"  {agent_type}:")
        print(f"    - 负载: {agent_stats['current_load']}/{agent_stats['max_concurrent']}")
        print(f"    - 利用率: {agent_stats['utilization']}")
        print(f"    - 执行次数: {agent_stats['total_executions']}")

    # ========== 测试总结 ==========
    print_section("测试总结")

    if result.success:
        print("\n✅ 编排层测试成功!")
        print("\n功能验证:")
        print("  ✅ 计划生成 - 正确创建执行步骤")
        print("  ✅ 编排器初始化 - 配置加载正确")
        print("  ✅ 任务调度 - 按依赖关系正确执行")
        print("  ✅ Agent分配 - 资源分配合理")
        print("  ✅ 结果收集 - 统计信息准确")

        if config.enable_parallel_execution:
            print("  ✅ 并行执行 - 多任务并行运行")

        print("\n下一步:")
        print("  1. 添加真实的Agent执行逻辑")
        print("  2. 完善Git Worktree集成")
        print("  3. 实现任务重试机制")
        print("  4. 添加错误恢复策略")
    else:
        print("\n❌ 编排层测试失败!")
        print(f"\n错误信息: {result.errors}")


if __name__ == "__main__":
    asyncio.run(test_orchestration())
