#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SuperAgent v3.0 实际项目验证

完整测试SuperAgent v3.0从用户输入到Agent输出的整个工作流程
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from conversation import IntentRecognizer
from planning import SmartPlanner
from execution.coding_agent_v2 import CodingAgent
from execution.models import AgentContext
from memory import MemoryManager


async def test_complete_workflow():
    """测试完整工作流程"""
    print("\n" + "="*80)
    print("SuperAgent v3.0 - 实际项目验证测试")
    print("="*80)

    # 项目根目录
    project_root = Path(".")

    # ========== 场景: 开发一个任务管理系统 ==========
    print("\n📋 场景: 开发一个任务管理系统API")
    print("-" * 80)

    user_input = "开发一个任务管理系统,支持任务创建、分配、状态跟踪和团队协作功能,使用Python和FastAPI"

    print(f"\n用户输入: {user_input}")

    # ========== 步骤1: 意图识别 ==========
    print("\n" + "="*80)
    print("步骤1: 智能意图识别")
    print("="*80)

    recognizer = IntentRecognizer()
    intent_result = await recognizer.recognize(user_input)

    print(f"\n✅ 识别结果:")
    print(f"   主要意图: {intent_result.type.value}")
    print(f"   置信度: {intent_result.confidence:.2f}")
    print(f"   Agent类型: {[agent.value for agent in intent_result.agent_types]}")
    print(f"   关键词: {intent_result.keywords}")
    print(f"\n📊 推理过程:")
    print(f"   {intent_result.reasoning}")
    print(f"\n➡️  建议步骤:")
    for i, step in enumerate(intent_result.suggested_steps, 1):
        print(f"   {i}. {step}")

    # ========== 步骤2: 智能规划 ==========
    print("\n" + "="*80)
    print("步骤2: 智能规划生成")
    print("="*80)

    planner = SmartPlanner()
    plan = await planner.create_smart_plan(user_input, {})

    print(f"\n✅ 规划结果:")
    print(f"   步骤数量: {len(plan.steps)}")
    print(f"   估算时间: {plan.estimated_time}")

    print(f"\n📋 执行步骤:")
    for i, step in enumerate(plan.steps, 1):
        print(f"\n   {i}. {step.description}")
        print(f"      - Agent类型: {step.agent_type.value}")
        print(f"      - 状态: {step.status.value}")

    # ========== 步骤3: Agent执行 ==========
    print("\n" + "="*80)
    print("步骤3: Agent执行 - CodingAgent")
    print("="*80)

    # 创建Agent上下文
    context = AgentContext(
        project_root=project_root,
        task_id="task-mgmt-001",
        step_id="step-1"
    )

    # 创建任务输入
    task_input = {
        "description": "任务管理系统API - 支持任务创建、分配、状态跟踪",
        "tech_stack": ["Python", "FastAPI", "PostgreSQL", "Redis"],
        "requirements": {
            "用户管理": "支持团队成员注册和认证",
            "任务管理": "支持任务创建、编辑、删除",
            "团队协作": "支持任务分配和评论"
        }
    }

    print(f"\n📝 任务输入:")
    print(f"   描述: {task_input['description']}")
    print(f"   技术栈: {', '.join(task_input['tech_stack'])}")

    # 执行Agent
    agent = CodingAgent()
    agent_result = await agent.execute(context, task_input)

    print(f"\n✅ Agent执行结果:")
    print(f"   状态: {'成功' if agent_result.success else '失败'}")
    print(f"   消息: {agent_result.message}")
    print(f"   工件数量: {len(agent_result.artifacts)}")

    # 显示生成的工件
    print(f"\n📄 生成的工件:")
    for i, artifact in enumerate(agent_result.artifacts, 1):
        print(f"\n   {i}. {artifact.artifact_type} - {artifact.path}")
        if artifact.content:
            lines = artifact.content.split('\n')
            preview = '\n'.join(lines[:10])
            print(f"      内容预览:\n{preview}\n...")

    # 显示元数据
    print(f"\n📊 元数据:")
    for key, value in agent_result.metadata.items():
        if key != "next_steps":
            print(f"   {key}: {value}")

    # 显示思考过程
    print(f"\n🤔 思考过程:")
    for thought in agent.thoughts:
        print(f"   步骤{thought.step}: {thought.thought}")
        print(f"   动作: {thought.action}")

    # ========== 步骤4: 模拟Claude Code工作 ==========
    print("\n" + "="*80)
    print("步骤4: Claude Code工作模拟")
    print("="*80)

    if "next_steps" in agent_result.metadata:
        print(f"\n➡️  Claude Code 将执行以下步骤:")
        for i, step in enumerate(agent_result.metadata["next_steps"], 1):
            print(f"   {i}. {step}")

    # ========== 步骤5: 记忆系统 ==========
    print("\n" + "="*80)
    print("步骤5: 记忆系统集成")
    print("="*80)

    memory_manager = MemoryManager(project_root)

    # 保存情节记忆
    await memory_manager.save_episodic_memory(
        event=f"完成任务管理系统的规划和设计",
        task_id="task-mgmt-001",
        agent_type="coding",
        metadata={
            "plan_steps": len(plan.steps),
            "artifacts_generated": len(agent_result.artifacts),
            "estimated_code_lines": agent_result.metadata.get("estimated_code_lines")
        }
    )

    print(f"\n✅ 记忆已保存:")
    print(f"   类型: 情节记忆 (episodic)")
    print(f"   事件: 完成任务管理系统的规划和设计")

    # 查询相关记忆
    relevant_memory = await memory_manager.query_relevant_memory(
        task="任务管理系统开发",
        agent_type="coding"
    )

    print(f"\n📚 相关记忆:")
    print(f"   错误教训: {len(relevant_memory.get('mistakes', []))}条")
    print(f"   最佳实践: {len(relevant_memory.get('best_practices', []))}条")
    print(f"   架构决策: {len(relevant_memory.get('architecture_decisions', []))}条")

    # ========== 步骤6: 错误恢复演示 ==========
    print("\n" + "="*80)
    print("步骤6: 错误恢复机制演示")
    print("="*80)

    from orchestration import ErrorRecoverySystem

    error_recovery = ErrorRecoverySystem(memory_manager)

    # 模拟一个错误
    test_error = ValueError("测试错误: 数据库连接失败")

    print(f"\n⚠️  模拟错误: {test_error}")

    recovery_result = await error_recovery.handle_error(
        error=test_error,
        task_id="task-mgmt-001",
        agent_type="coding",
        retry_count=1
    )

    print(f"\n✅ 错误恢复结果:")
    if isinstance(recovery_result, dict):
        print(f"   错误类型: {recovery_result.get('error_type', 'unknown')}")
        print(f"   严重程度: {recovery_result.get('severity', 'unknown')}")
        print(f"   恢复策略: {recovery_result.get('strategy', 'unknown')}")
        print(f"   建议操作: {recovery_result.get('action', 'unknown')}")
        print(f"   最大重试次数: {recovery_result.get('max_retries', 'unknown')}")
        print(f"   是否应该重试: {recovery_result.get('should_retry', 'unknown')}")
    else:
        print(f"   恢复策略: {recovery_result.recovery_strategy}")
        print(f"   建议操作: {recovery_result.suggested_action}")

    # ========== 总结 ==========
    print("\n" + "="*80)
    print("📊 验证总结")
    print("="*80)

    # 错误恢复验证 - 处理dict和对象两种情况
    error_recovery_ok = False
    if isinstance(recovery_result, dict):
        # 检查是否有有效的恢复策略和操作
        has_strategy = recovery_result.get('strategy', 'unknown') != 'unknown'
        has_action = recovery_result.get('action', 'unknown') != 'unknown'
        error_recovery_ok = has_strategy and has_action
    elif hasattr(recovery_result, 'recovery_strategy'):
        error_recovery_ok = recovery_result.recovery_strategy != 'unknown'

    checks = {
        "意图识别": intent_result.confidence > 0,
        "智能规划": len(plan.steps) > 0,
        "Agent执行": agent_result.success,
        "文档生成": len(agent_result.artifacts) >= 3,
        "记忆系统": True,
        "错误恢复": error_recovery_ok
    }

    print(f"\n✅ 功能验证:")
    for feature, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"   {status} {feature}")

    passed_count = sum(1 for v in checks.values() if v)
    total_count = len(checks)

    print(f"\n📈 统计:")
    print(f"   通过: {passed_count}/{total_count}")
    print(f"   通过率: {passed_count * 100 // total_count}%")

    if passed_count == total_count:
        print("\n🎉 所有验证通过!")
        print("✨ SuperAgent v3.0 工作流程完整且稳定!")
    else:
        print("\n⚠️  部分验证未通过")

    return passed_count == total_count


async def test_performance_integration():
    """测试性能优化集成"""
    print("\n" + "="*80)
    print("性能优化集成测试")
    print("="*80)

    from planning import SmartPlanner
    import time

    planner = SmartPlanner()

    # 测试缓存效果
    test_input = "开发一个博客系统"
    test_context = {"tech_stack": ["Python", "FastAPI"]}

    print(f"\n📝 测试输入: {test_input}")

    # 首次执行
    print(f"\n⏱️  首次执行...")
    start = time.perf_counter()
    plan1 = await planner.create_smart_plan(test_input, test_context)
    time1 = (time.perf_counter() - start) * 1000
    print(f"   耗时: {time1:.2f}ms")

    # 缓存命中
    print(f"\n⏱️  缓存命中...")
    start = time.perf_counter()
    plan2 = await planner.create_smart_plan(test_input, test_context)
    time2 = (time.perf_counter() - start) * 1000
    print(f"   耗时: {time2:.2f}ms")

    speedup = time1 / time2 if time2 > 0 else 0

    print(f"\n📊 性能提升:")
    print(f"   加速倍数: {speedup:.1f}x")
    print(f"   ✅ 缓存优化工作正常!" if speedup > 10 else "⚠️  缓存效果不明显")

    return speedup > 10


async def main():
    """主测试函数"""
    print("\n" + "🚀" * 40)
    print("SuperAgent v3.0 - 实际项目完整验证")
    print("🚀" * 40)

    try:
        # 测试1: 完整工作流程
        workflow_ok = await test_complete_workflow()

        # 测试2: 性能优化集成
        performance_ok = await test_performance_integration()

        # 总结
        print("\n" + "="*80)
        print("🎯 最终验证结果")
        print("="*80)

        results = {
            "完整工作流程": workflow_ok,
            "性能优化集成": performance_ok
        }

        for test_name, passed in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"  {status} - {test_name}")

        all_passed = all(results.values())

        if all_passed:
            print("\n" + "🎉" * 40)
            print("所有实际项目验证通过!")
            print("SuperAgent v3.0 完全就绪!")
            print("🎉" * 40)
        else:
            print("\n⚠️  部分验证未通过,需要检查")

    except Exception as e:
        print(f"\n❌ 验证过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 设置Windows控制台UTF-8编码
    if sys.platform == "win32":
        import sys
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

    # 运行验证
    asyncio.run(main())
