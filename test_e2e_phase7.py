#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Phase 7 端到端集成测试

测试完整的智能化工作流:
1. 智能意图识别 (Phase 7.1)
2. 智能规划 (Phase 7.2)
3. 错误恢复 (Phase 7.3)
"""

import asyncio
import sys
import io
from pathlib import Path

# Windows 控制台 UTF-8 支持
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加项目根目录到 Python 路径
SUPERAGENT_ROOT = Path(__file__).parent
sys.path.insert(0, str(SUPERAGENT_ROOT))

from conversation import ConversationManager, IntentRecognizer
from planning import SmartPlanner, ProjectPlanner
from orchestration import (
    Orchestrator,
    ErrorRecoverySystem,
    ErrorClassifier,
    ErrorType,
    ErrorSeverity
)
from memory import MemoryManager


async def test_e2e_workflow_simple():
    """测试端到端工作流 - 简单项目"""
    print("\n" + "="*60)
    print("测试 1: 端到端工作流 - 简单项目")
    print("="*60)

    # 创建测试项目目录
    test_project_root = SUPERAGENT_ROOT / ".test_e2e_simple"
    test_project_root.mkdir(exist_ok=True)

    # 1. 智能意图识别 (Phase 7.1)
    print("\n步骤 1: 智能意图识别")
    recognizer = IntentRecognizer()

    user_input = "开发一个简单的登录页面"
    intent_result = await recognizer.recognize(user_input)

    print(f"  用户输入: {user_input}")
    print(f"  主要意图: {intent_result.type.value}")
    print(f"  置信度: {intent_result.confidence:.2f}")
    print(f"  识别的Agent类型: {[agent.value for agent in intent_result.agent_types]}")
    print(f"  关键词: {intent_result.keywords}")

    # 2. 智能规划 (Phase 7.2)
    print("\n步骤 2: 智能规划")
    planner = SmartPlanner()

    plan = await planner.create_smart_plan(user_input, {})

    print(f"  生成的步骤数: {len(plan.steps)}")
    print(f"  估算时间: {plan.estimated_time}")
    print(f"  执行步骤:")
    for i, step in enumerate(plan.steps[:3], 1):
        print(f"    {i}. {step.name} ({step.agent_type.value})")

    # 3. 获取计划建议
    print("\n步骤 3: 计划建议")
    suggestions = await planner.get_plan_suggestions(user_input)

    print(f"  复杂度: {suggestions['estimated_complexity']}")
    print(f"  推荐Agent:")
    for agent in suggestions['recommended_agents'][:3]:
        print(f"    - {agent['agent_type']}: {agent['reasoning']}")

    print("\n✓ 端到端工作流测试完成 (简单项目)")


async def test_e2e_workflow_complex():
    """测试端到端工作流 - 复杂项目"""
    print("\n" + "="*60)
    print("测试 2: 端到端工作流 - 复杂项目")
    print("="*60)

    # 1. 智能意图识别 (Phase 7.1)
    print("\n步骤 1: 智能意图识别")
    recognizer = IntentRecognizer()

    user_input = "开发一个完整的电商系统,包含用户管理、商品管理、订单处理、支付功能"
    intent_result = await recognizer.recognize(user_input)

    print(f"  用户输入: {user_input}")
    print(f"  主要意图: {intent_result.type.value}")
    print(f"  置信度: {intent_result.confidence:.2f}")
    print(f"  识别的Agent类型: {[agent.value for agent in intent_result.agent_types]}")
    print(f"  关键词: {intent_result.extracted_keywords}")

    # 2. 智能规划 (Phase 7.2)
    print("\n步骤 2: 智能规划")
    planner = SmartPlanner()

    plan = await planner.create_smart_plan(user_input, {})

    print(f"  生成的步骤数: {len(plan.steps)}")
    print(f"  估算时间: {plan.estimated_time}")
    print(f"  执行步骤:")
    for i, step in enumerate(plan.steps[:5], 1):
        print(f"    {i}. {step.name} ({step.agent_type.value})")
        if step.dependencies:
            print(f"       依赖: {step.dependencies}")

    # 3. 获取计划建议
    print("\n步骤 3: 计划建议")
    suggestions = planner.get_plan_suggestions(user_input)

    print(f"  复杂度: {suggestions['estimated_complexity']}")
    print(f"  推荐Agent:")
    for agent in suggestions['recommended_agents']:
        print(f"    - {agent['agent_type']}: {agent['reasoning']}")

    print("\n✓ 端到端工作流测试完成 (复杂项目)")


async def test_e2e_with_error_recovery():
    """测试端到端工作流 - 带错误恢复"""
    print("\n" + "="*60)
    print("测试 3: 端到端工作流 - 带错误恢复")
    print("="*60)

    # 创建测试项目目录
    test_project_root = SUPERAGENT_ROOT / ".test_e2e_error_recovery"
    test_project_root.mkdir(exist_ok=True)

    # 1. 初始化记忆管理器
    print("\n步骤 1: 初始化记忆管理器")
    memory_manager = MemoryManager(test_project_root)
    print("  ✓ 记忆管理器已初始化")

    # 2. 先保存一个错误到记忆
    print("\n步骤 2: 保存历史错误到记忆")
    await memory_manager.save_mistake(
        error=ImportError("No module named 'test_module'"),
        context="测试任务执行",
        fix="使用pip install安装缺失的依赖",
        learning="在执行任务前检查所有依赖是否已安装"
    )
    print("  ✓ 历史错误已保存")

    # 3. 创建错误恢复系统
    print("\n步骤 3: 初始化错误恢复系统")
    recovery_system = ErrorRecoverySystem(memory_manager)
    print("  ✓ 错误恢复系统已初始化")

    # 4. 模拟错误发生
    print("\n步骤 4: 模拟错误发生")
    test_error = ImportError("No module named 'test_module'")

    recovery_result = await recovery_system.handle_error(
        error=test_error,
        task_id="test_task_001",
        agent_type="backend-dev",
        retry_count=0
    )

    print(f"  错误类型: {recovery_result['error_type']}")
    print(f"  严重程度: {recovery_result['severity']}")
    print(f"  恢复策略: {recovery_result['strategy']}")
    print(f"  是否重试: {recovery_result['should_retry']}")
    print(f"  重试延迟: {recovery_result['retry_delay']}s")

    if recovery_result.get("memory_fix"):
        print(f"  找到历史修复方案:")
        print(f"    修复: {recovery_result['memory_fix']['fix']}")
        print(f"    置信度: {recovery_result['memory_fix']['confidence']}")

    # 5. 显示统计
    print("\n步骤 5: 错误恢复统计")
    stats = recovery_system.get_statistics()
    print(f"  总错误数: {stats['total_errors']}")
    print(f"  已重试: {stats['retried']}")
    print(f"  已降级: {stats['fallback']}")
    print(f"  需人工: {stats['manual']}")

    print("\n✓ 端到端工作流测试完成 (带错误恢复)")


async def test_conversation_manager_integration():
    """测试对话管理器集成"""
    print("\n" + "="*60)
    print("测试 4: 对话管理器集成")
    print("="*60)

    # 创建对话管理器
    manager = ConversationManager()

    # 测试智能识别
    test_inputs = [
        "开发一个博客系统",
        "设计数据库结构",
        "编写API文档"
    ]

    print("\n测试智能识别:")
    for user_input in test_inputs:
        result = manager.smart_recognize(user_input)

        print(f"\n  输入: {user_input}")
        print(f"  意图: {result['primary_intent']}")
        print(f"  Agent类型: {result['agent_types']}")
        print(f"  关键词: {result['keywords']}")

    # 测试获取Agent建议
    print("\n\n测试Agent建议:")
    user_input = "开发一个任务管理系统,需要用户认证和任务分配功能"
    suggestions = manager.get_agent_suggestions(user_input)

    for suggestion in suggestions[:3]:
        print(f"  - {suggestion['agent_type']}: {suggestion['reason']}")

    # 测试获取建议步骤
    print("\n\n测试建议步骤:")
    user_input = "开发一个全栈博客系统"
    suggested_steps = manager.get_suggested_steps(user_input)

    for step in suggested_steps[:5]:
        print(f"  {step}")

    print("\n✓ 对话管理器集成测试完成")


async def test_error_classification_comprehensive():
    """测试错误分类 - 全面测试"""
    print("\n" + "="*60)
    print("测试 5: 错误分类 - 全面测试")
    print("="*60)

    # 测试用例
    test_cases = [
        ("SyntaxError: invalid syntax", ErrorType.SYNTAX_ERROR, ErrorSeverity.CRITICAL),
        ("IndentationError: unexpected indent", ErrorType.SYNTAX_ERROR, ErrorSeverity.CRITICAL),
        ("ImportError: No module named 'requests'", ErrorType.IMPORT_ERROR, ErrorSeverity.HIGH),
        ("ModuleNotFoundError: No module named 'numpy'", ErrorType.IMPORT_ERROR, ErrorSeverity.HIGH),
        ("AttributeError: 'NoneType' object has no attribute 'x'", ErrorType.ATTRIBUTE_ERROR, ErrorSeverity.MEDIUM),
        ("TypeError: 'int' object is not subscriptable", ErrorType.TYPE_ERROR, ErrorSeverity.MEDIUM),
        ("KeyError: 'test_key'", ErrorType.KEY_ERROR, ErrorSeverity.LOW),
        ("ValueError: invalid literal for int()", ErrorType.VALUE_ERROR, ErrorSeverity.LOW),
        ("ConnectionError: Max retries exceeded", ErrorType.NETWORK_ERROR, ErrorSeverity.MEDIUM),
        ("TimeoutError: Request timed out", ErrorType.NETWORK_ERROR, ErrorSeverity.MEDIUM),
        ("FileNotFoundError: file not found", ErrorType.FILE_ERROR, ErrorSeverity.MEDIUM),
        ("PermissionError: [Errno 13] Permission denied", ErrorType.PERMISSION_ERROR, ErrorSeverity.MEDIUM),
    ]

    print(f"\n测试 {len(test_cases)} 种错误类型:")

    correct = 0
    for error_msg, expected_type, expected_severity in test_cases:
        # 分类
        error_type = ErrorClassifier.classify(error_msg)
        severity = ErrorClassifier.estimate_severity(error_type, error_msg)

        type_match = error_type == expected_type
        severity_match = severity == expected_severity

        if type_match and severity_match:
            correct += 1
            status = "✓"
        else:
            status = "✗"

        print(f"  {status} {error_msg[:50]}")
        if not type_match:
            print(f"     类型错误: 期望 {expected_type.value}, 实际 {error_type.value}")
        if not severity_match:
            print(f"     严重程度错误: 期望 {expected_severity.value}, 实际 {severity.value}")

    accuracy = (correct / len(test_cases)) * 100
    print(f"\n准确率: {accuracy:.1f}% ({correct}/{len(test_cases)})")

    print("\n✓ 错误分类测试完成")


async def test_smart_planner_optimizations():
    """测试智能规划器优化"""
    print("\n" + "="*60)
    print("测试 6: 智能规划器优化")
    print("="*60)

    planner = SmartPlanner()

    # 测试用例
    test_cases = [
        ("开发博客系统", "low"),
        ("开发任务管理系统", "low"),
        ("开发完整的电商平台", "high"),
    ]

    print("\n测试复杂度估算和优化:")
    for user_input, expected_complexity in test_cases:
        suggestions = planner.get_plan_suggestions(user_input)
        estimated_complexity = suggestions['estimated_complexity']

        complexity_match = estimated_complexity == expected_complexity
        status = "✓" if complexity_match else "✗"

        print(f"\n  {status} {user_input}")
        print(f"     估算复杂度: {estimated_complexity} (期望: {expected_complexity})")
        print(f"     Agent数量: {len(suggestions['recommended_agents'])}")
        print(f"     关键词数量: {len(suggestions['keywords'])}")

    # 测试基于意图的规划
    print("\n\n测试基于意图的规划:")
    recognizer = planner.intent_recognizer

    user_input = "使用Python和React开发全栈博客系统"
    intent_result = recognizer.recognize(user_input)

    print(f"  用户输入: {user_input}")
    print(f"  识别的Agent: {[agent.value for agent in intent_result.agent_types]}")

    plan = await planner.generate_plan_from_intent(intent_result, user_input)

    print(f"  生成计划步骤数: {len(plan.steps)}")
    print(f"  执行步骤:")
    for i, step in enumerate(plan.steps[:3], 1):
        print(f"    {i}. {step.name} ({step.agent_type.value})")

    print("\n✓ 智能规划器优化测试完成")


async def main():
    """运行所有端到端测试"""
    print("\n" + "="*60)
    print("SuperAgent v3.0 Phase 7 端到端集成测试")
    print("="*60)

    tests = [
        test_e2e_workflow_simple,
        test_e2e_workflow_complex,
        test_e2e_with_error_recovery,
        test_conversation_manager_integration,
        test_error_classification_comprehensive,
        test_smart_planner_optimizations
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            await test_func()
            passed += 1
        except Exception as e:
            failed += 1
            print(f"\n❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()

    # 总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    print(f"总测试数: {len(tests)}")
    print(f"通过: {passed}")
    print(f"失败: {failed}")
    print(f"成功率: {(passed/len(tests)*100):.1f}%")

    if failed == 0:
        print("\n🎉 所有测试通过!")
    else:
        print(f"\n⚠️  有 {failed} 个测试失败")

    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
