#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
系统集成测试 - 完整端到端测试

测试从用户输入到Agent执行的完整流程
"""

import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from conversation.manager import ConversationManager
from planning.planner import ProjectPlanner
from orchestration.orchestrator import Orchestrator, OrchestrationConfig


async def test_full_stack_blog_system():
    """测试完整的博客系统开发流程"""
    print("="*70)
    print("  SuperAgent v3.0 系统集成测试")
    print("="*70)

    # 用户输入
    user_input = "开发一个带数据库的博客系统,需要用户管理和文章管理功能"

    print(f"\n用户需求: {user_input}")

    # ========== 步骤1: 对话管理 ==========
    print("\n" + "="*70)
    print("步骤1: 对话管理 - 意图识别")
    print("="*70)

    conv_mgr = ConversationManager()
    conv_result = await conv_mgr.process_input(user_input)

    print(f"意图类型: {conv_result.data['intent'].type.value}")
    print(f"需求状态: {conv_result.type}")

    if conv_result.type != "requirements_ready":
        print("[FAIL] 需求未准备好")
        return False

    # ========== 步骤2: 项目规划 ==========
    print("\n" + "="*70)
    print("步骤2: 项目规划 - 生成执行计划")
    print("="*70)

    planner = ProjectPlanner()
    plan = await planner.create_plan(user_input, conv_result.data['context'])

    print(f"生成步骤数: {len(plan.steps)}")
    print(f"项目类型: {plan.analysis.project_type}")

    for i, step in enumerate(plan.steps, 1):
        deps = f" (依赖: {', '.join(step.dependencies)})" if step.dependencies else ""
        print(f"  {i}. {step.name}{deps}")
        print(f"     Agent: {step.agent_type.value}")

    # ========== 步骤3: 任务编排(集成真实Agent) ==========
    print("\n" + "="*70)
    print("步骤3: 任务编排 - 执行计划(使用真实Agent)")
    print("="*70)

    # 创建配置(启用代码审查)
    config = OrchestrationConfig(
        max_parallel_tasks=2,
        enable_parallel_execution=True,
        enable_code_review=True,
        enable_style_check=True,
        enable_security_check=True
    )

    # 创建编排器
    orchestrator = Orchestrator(Path(__file__).parent, config)

    print(f"编排器ID: {orchestrator.state.project_id}")
    print(f"代码审查: {'启用' if orchestrator.code_reviewer else '未启用'}")

    # 执行计划
    print("\n开始执行任务...")
    result = await orchestrator.execute_plan(plan)

    # ========== 步骤4: 结果分析 ==========
    print("\n" + "="*70)
    print("步骤4: 执行结果")
    print("="*70)

    print(f"\n执行状态: {'[OK] 成功' if result.success else '[FAIL] 失败'}")
    print(f"完成任务: {result.completed_tasks}/{result.total_tasks}")
    print(f"失败任务: {result.failed_tasks}")
    print(f"执行时长: {result.duration_seconds}秒")
    print(f"成功率: {result.success_rate * 100:.1f}%")

    # 显示任务详情
    print(f"\n任务执行详情:")
    for task in result.task_executions:
        status_symbol = {
            "completed": "[OK]",
            "failed": "[FAIL]",
            "skipped": "[SKIP]",
            "pending": "[WAIT]"
        }.get(task.status.value, "[?]")

        print(f"  {status_symbol} {task.task_id}: {task.status.value.upper()}")

        if task.assignment:
            print(f"      Agent: {task.assignment.agent_type}")

        if task.result:
            artifacts_count = len(task.result.get('artifacts', []))
            files_count = len(task.result.get('files', []))
            print(f"      生成工件: {artifacts_count}个, 文件: {files_count}个")

        if task.error:
            print(f"      错误: {task.error}")

    # ========== 步骤5: 代码审查结果 ==========
    if result.code_review_summary:
        print("\n" + "="*70)
        print("步骤5: 代码审查结果")
        print("="*70)

        review = result.code_review_summary

        if review['status'] == 'completed':
            print(f"\n综合评分: {review['overall_score']:.1f}/100")
            print(f"审查文件: {review['file_count']}个")
            print(f"发现问题: {review['total_issues']}个")
            print(f"  - 严重: {review['critical_count']}个")
            print(f"  - 主要: {review['major_count']}个")
            print(f"  - 轻微: {review['minor_count']}个")
            print(f"质量达标: {'✅ 是' if review['meets_threshold'] else '❌ 否'}")

    # ========== 验证 ==========
    print("\n" + "="*70)
    print("验证结果")
    print("="*70)

    checks = [
        ("对话管理", conv_result.type == "requirements_ready"),
        ("项目规划", len(plan.steps) > 0),
        ("任务执行", result.success),
        ("Agent集成", result.completed_tasks > 0),
    ]

    all_passed = True
    for check_name, passed in checks:
        status = "[OK] 通过" if passed else "[FAIL] 失败"
        print(f"{status} - {check_name}")
        if not passed:
            all_passed = False

    if all_passed:
        print("\n" + "="*70)
        print("[SUCCESS] 系统集成测试完全通过!")
        print("="*70)
        print("\nSuperAgent v3.0 已实现完整的AI驱动开发流程:")
        print("  ✅ 自然语言交互")
        print("  ✅ 智能项目规划")
        print("  ✅ Agent自动执行")
        print("  ✅ 代码质量审查")
        print("\n系统可以端到端运行!")
        return True
    else:
        print("\n[FAIL] 部分测试失败")
        return False


async def test_multi_agent_collaboration():
    """测试多Agent协作场景"""
    print("\n" + "="*70)
    print("  多Agent协作测试")
    print("="*70)

    # 创建复杂项目计划
    user_input = "开发一个完整的电商网站,包括前后端、数据库、测试和文档"

    print(f"\n用户需求: {user_input}")

    # 生成计划
    planner = ProjectPlanner()
    plan = await planner.create_plan(user_input, {})

    print(f"\n生成的步骤数: {len(plan.steps)}")

    # 统计Agent类型
    agent_types = {}
    for step in plan.steps:
        agent_type = step.agent_type.value
        agent_types[agent_type] = agent_types.get(agent_type, 0) + 1

    print(f"\n使用的Agent类型:")
    for agent_type, count in agent_types.items():
        print(f"  - {agent_type}: {count}个任务")

    # 执行计划
    config = OrchestrationConfig(
        max_parallel_tasks=3,
        enable_parallel_execution=True,
        enable_code_review=False  # 加快测试速度
    )

    orchestrator = Orchestrator(Path(__file__).parent, config)
    result = await orchestrator.execute_plan(plan)

    # 分析结果
    print(f"\n执行结果:")
    print(f"  成功: {result.success}")
    print(f"  完成任务: {result.completed_tasks}/{result.total_tasks}")

    # 统计不同Agent的任务执行情况
    agent_results = {}
    for task in result.task_executions:
        if task.assignment:
            agent_type = task.assignment.agent_type
            if agent_type not in agent_results:
                agent_results[agent_type] = {"total": 0, "success": 0, "failed": 0}

            agent_results[agent_type]["total"] += 1
            if task.status.value == "completed":
                agent_results[agent_type]["success"] += 1
            elif task.status.value == "failed":
                agent_results[agent_type]["failed"] += 1

    print(f"\n各Agent执行情况:")
    for agent_type, stats in agent_results.items():
        print(f"  {agent_type}:")
        print(f"    总任务: {stats['total']}")
        print(f"    成功: {stats['success']}")
        print(f"    失败: {stats['failed']}")

    # 验证多Agent协作
    if result.completed_tasks >= 3:
        print("\n✅ 多Agent协作测试通过!")
        return True
    else:
        print("\n❌ 多Agent协作测试失败")
        return False


async def main():
    """运行所有系统集成测试"""
    print("\n" + "="*70)
    print("  SuperAgent v3.0 系统集成测试套件")
    print("="*70)

    tests = [
        ("完整E2E测试 - 博客系统", test_full_stack_blog_system),
        ("多Agent协作测试", test_multi_agent_collaboration),
    ]

    results = []
    for name, test_func in tests:
        try:
            success = await test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n[FAIL] {name}: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # 总结
    print("\n" + "="*70)
    print("测试总结")
    print("="*70)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{status} - {name}")

    print(f"\n总计: {passed}/{total} 测试通过")

    if passed == total:
        print("\n🎉 所有系统集成测试通过!")
        print("\nSuperAgent v3.0 已成功实现:")
        print("  ✅ 完整的端到端开发流程")
        print("  ✅ 多Agent协作能力")
        print("  ✅ 自动化代码生成和审查")
        print("  ✅ 智能任务编排")
        return 0
    else:
        print(f"\n⚠️ {total - passed} 个测试失败")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
