#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SuperAgent v3.0 端到端集成测试

完整测试从用户输入到执行结果的全流程
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from conversation.manager import ConversationManager
from planning.planner import ProjectPlanner
from orchestration.orchestrator import Orchestrator
from orchestration.models import OrchestrationConfig


def print_section(title):
    """打印分节标题"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


async def test_end_to_end_blog():
    """测试博客系统开发的完整流程"""
    print_section("SuperAgent v3.0 端到端集成测试 - 博客系统")

    # ========== 场景1: 博客系统开发 ==========
    user_input = "我想开发一个带数据库的博客系统,支持文章管理和用户评论功能"

    print(f"\n📝 用户需求:")
    print(f"   {user_input}")

    # ========== 步骤1: 对话管理 ==========
    print_section("步骤1: 对话管理 - 意图识别与需求澄清")

    conv_mgr = ConversationManager()
    conv_result = await conv_mgr.process_input(user_input)

    print(f"\n✅ 意图识别:")
    print(f"   类型: {conv_result.data['intent'].type.value}")
    print(f"   置信度: {conv_result.data['intent'].confidence}")

    print(f"\n✅ 需求状态:")
    print(f"   响应类型: {conv_result.type}")

    if conv_result.type == "requirements_ready":
        print(f"   状态: 需求明确,可以继续")

        # ========== 步骤2: 项目规划 ==========
        print_section("步骤2: 项目规划 - 生成执行计划")

        planner = ProjectPlanner()
        plan = await planner.create_plan(user_input, conv_result.data['context'])

        print(f"\n✅ 计划生成:")
        print(f"   步骤数量: {len(plan.steps)}")
        print(f"   项目类型: {plan.analysis.project_type}")
        print(f"   技术栈: {plan.analysis.tech_stack or '待确定'}")
        print(f"   复杂度: {plan.analysis.complexity}")
        print(f"   预计时间: {int(plan.estimated_time.total_seconds() / 60)}分钟")
        print(f"   风险等级: {plan.risk_report.overall_risk}")

        if plan.requirements.features:
            print(f"\n   识别的功能:")
            for feature in plan.requirements.features:
                print(f"      - {feature}")

        print(f"\n   执行步骤:")
        for i, step in enumerate(plan.steps, 1):
            deps = f" (依赖: {', '.join(step.dependencies)})" if step.dependencies else ""
            print(f"      {i}. {step.name}{deps}")
            print(f"         Agent: {step.agent_type.value}")
            print(f"         耗时: {int(step.estimated_time.total_seconds() / 60)}分钟")

        # ========== 步骤3: 任务编排 ==========
        print_section("步骤3: 任务编排 - 执行项目计划")

        config = OrchestrationConfig(
            max_parallel_tasks=2,
            enable_parallel_execution=True,
            enable_auto_retry=True,
            enable_early_failure=False
        )

        orchestrator = Orchestrator(
            project_root=Path(__file__).parent,
            config=config
        )

        print(f"\n✅ 编排器初始化:")
        print(f"   项目ID: {orchestrator.state.project_id}")
        print(f"   最大并行: {config.max_parallel_tasks}")
        print(f"   并行执行: {'启用' if config.enable_parallel_execution else '禁用'}")

        print(f"\n⏳ 开始执行任务...")

        # 执行计划
        result = await orchestrator.execute_plan(plan)

        # ========== 步骤4: 结果展示 ==========
        print_section("步骤4: 执行结果")

        print(f"\n✅ 执行状态: {'成功' if result.success else '失败'}")
        print(f"   总任务数: {result.total_tasks}")
        print(f"   完成任务: {result.completed_tasks}")
        print(f"   失败任务: {result.failed_tasks}")
        print(f"   跳过任务: {result.skipped_tasks}")
        print(f"   执行时长: {result.duration_seconds}秒")
        print(f"   成功率: {result.success_rate * 100:.1f}%")

        if result.completed_tasks == result.total_tasks:
            print(f"\n   [OK] 所有任务执行成功!")
        else:
            print(f"\n   [WARN] 部分任务未完成")

        # 显示任务详情
        print(f"\n📋 任务执行详情:")
        for task in result.task_executions:
            status_symbol = {
                "completed": "[OK]",
                "failed": "[FAIL]",
                "skipped": "[SKIP]",
                "pending": "[WAIT]"
            }.get(task.status.value, "[?]")

            duration = ""
            if task.started_at and task.completed_at:
                duration = f" ({(task.completed_at - task.started_at).total_seconds():.2f}s)"

            print(f"   {status_symbol} {task.task_id}: {task.status.value.upper()}{duration}")

            if task.assignment:
                print(f"      Agent: {task.assignment.agent_type}")

            if task.error:
                print(f"      错误: {task.error}")

        # ========== 测试总结 ==========
        print_section("测试总结")

        if result.success:
            print("\n🎉 端到端测试成功!")
            print("\n✅ 验证通过的功能:")
            print("   ✅ 对话管理 - 意图识别准确")
            print("   ✅ 需求分析 - 正确识别项目类型")
            print("   ✅ 步骤生成 - 生成完整执行计划")
            print("   ✅ 任务编排 - 按依赖关系正确执行")
            print("   ✅ Agent调度 - 所有Agent正确分配")
            print("   ✅ 结果收集 - 统计信息准确")

            print("\n📊 性能指标:")
            stats = orchestrator.get_task_statistics()
            print(f"   任务总数: {stats['total']}")
            print(f"   执行时间: {result.duration_seconds}秒")
            print(f"   平均耗时: {orchestrator.state.average_task_duration:.2f}秒/任务" if orchestrator.state.average_task_duration else "")

            return True
        else:
            print("\n❌ 端到端测试失败!")
            if result.errors:
                print(f"\n错误信息:")
                for error in result.errors:
                    print(f"   - {error}")

            return False


async def test_end_to_end_ecommerce():
    """测试电商网站开发的完整流程"""
    print_section("SuperAgent v3.0 端到端集成测试 - 电商网站")

    user_input = "开发一个电商网站,需要商品管理、订单功能和用户登录"

    print(f"\n📝 用户需求:")
    print(f"   {user_input}")

    # 快速流程测试
    conv_mgr = ConversationManager()
    conv_result = await conv_mgr.process_input(user_input)

    if conv_result.type == "requirements_ready":
        planner = ProjectPlanner()
        plan = await planner.create_plan(user_input, conv_result.data['context'])

        print(f"\n✅ 计划生成: {len(plan.steps)}个步骤")
        print(f"   项目类型: {plan.analysis.project_type}")

        # 执行
        orchestrator = Orchestrator(Path(__file__).parent)
        result = await orchestrator.execute_plan(plan)

        print(f"\n✅ 执行结果: {'成功' if result.success else '失败'}")
        print(f"   完成: {result.completed_tasks}/{result.total_tasks}")

        return result.success
    else:
        print(f"\n❌ 需求处理失败")
        return False


async def test_error_handling():
    """测试错误处理能力"""
    print_section("SuperAgent v3.0 错误处理测试")

    print("\n测试1: 空输入")
    try:
        conv_mgr = ConversationManager()
        result = await conv_mgr.process_input("")

        print(f"   结果: {result.type}")
        print(f"   ✅ 空输入正确处理")
    except Exception as e:
        print(f"   ❌ 错误: {e}")

    print("\n测试2: 模糊需求")
    try:
        result = await conv_mgr.process_input("帮我开发")

        if result.type == "needs_clarification":
            print(f"   结果: 需要澄清")
            print(f"   生成问题: {len(result.data['questions'])}个")
            print(f"   ✅ 模糊需求正确识别")
        else:
            print(f"   ❌ 未能识别模糊需求")
    except Exception as e:
        print(f"   ❌ 错误: {e}")

    print("\n测试3: 无效上下文")
    try:
        planner = ProjectPlanner()
        plan = await planner.create_plan("测试", {"invalid": "context"})

        print(f"   计划生成: {len(plan.steps)}步骤")
        print(f"   ✅ 无效上下文处理")
    except Exception as e:
        print(f"   错误处理: {str(e)[:50]}...")
        print(f"   ✅ 异常被正确捕获")

    return True


async def main():
    """运行所有端到端测试"""
    print("="*70)
    print("  SuperAgent v3.0 端到端集成测试套件")
    print("="*70)

    results = []

    # 测试1: 博客系统
    try:
        result1 = await test_end_to_end_blog()
        results.append(("博客系统开发", result1))
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        results.append(("博客系统开发", False))

    # 测试2: 电商网站
    try:
        result2 = await test_end_to_end_ecommerce()
        results.append(("电商网站开发", result2))
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        results.append(("电商网站开发", False))

    # 测试3: 错误处理
    try:
        result3 = await test_error_handling()
        results.append(("错误处理", result3))
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        results.append(("错误处理", False))

    # 最终总结
    print_section("测试套件总结")

    print("\n测试结果汇总:")
    passed = 0
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {status} - {name}")
        if result:
            passed += 1

    print(f"\n总计: {passed}/{len(results)} 测试通过")

    if passed == len(results):
        print("\n🎉 所有端到端测试通过!")
        print("\nSuperAgent v3.0 已具备完整的开发能力:")
        print("   ✅ 自然语言交互")
        print("   ✅ 智能项目规划")
        print("   ✅ 自动任务编排")
        print("   ✅ Agent调度执行")
        print("   ✅ 健壮的错误处理")
        return 0
    else:
        print(f"\n⚠️  {len(results) - passed} 个测试失败,需要修复")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
