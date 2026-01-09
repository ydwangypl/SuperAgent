#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
智能规划器测试

测试增强的规划功能
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

from planning import SmartPlanner


async def test_smart_plan_generation():
    """测试智能计划生成"""
    print("\n" + "="*60)
    print("测试 1: 智能计划生成")
    print("="*60)

    planner = SmartPlanner()

    test_cases = [
        "开发一个博客系统",
        "设计电商网站数据库",
        "构建React前端应用"
    ]

    for i, user_input in enumerate(test_cases, 1):
        print(f"\n测试用例 {i}: {user_input}")

        try:
            plan = await planner.create_smart_plan(user_input, {})

            print(f"  ✓ 计划生成成功")
            print(f"  步骤数: {len(plan.steps)}")
            print(f"  估算时间: {plan.estimated_time}")

            # 显示前3个步骤
            print(f"  前3个步骤:")
            for j, step in enumerate(plan.steps[:3], 1):
                print(f"    {j}. {step.name} ({step.agent_type.value})")

        except Exception as e:
            print(f"  ✗ 失败: {e}")


async def test_plan_suggestions():
    """测试计划建议"""
    print("\n" + "="*60)
    print("测试 2: 计划建议")
    print("="*60)

    planner = SmartPlanner()

    user_input = "开发一个任务管理系统,需要用户认证和任务分配功能"

    print(f"\n用户输入: {user_input}")

    suggestions = await planner.get_plan_suggestions(user_input)

    print(f"\n主要意图: {suggestions['primary_intent']}")
    print(f"置信度: {suggestions['confidence']:.2f}")
    print(f"复杂度: {suggestions['estimated_complexity']}")
    print(f"关键词: {', '.join(suggestions['keywords'])}")

    print(f"\n推荐的Agent类型:")
    for agent in suggestions['recommended_agents']:
        print(f"  - {agent['agent_type']}: {agent['reasoning']}")

    print(f"\n建议步骤:")
    for step in suggestions['suggested_steps']:
        print(f"  {step}")


async def test_intent_based_planning():
    """测试基于意图的规划"""
    print("\n" + "="*60)
    print("测试 3: 基于意图的规划")
    print("="*60)

    planner = SmartPlanner()
    recognizer = planner.intent_recognizer

    user_input = "使用Python和React开发全栈博客系统"

    print(f"\n用户输入: {user_input}")

    # 1. 识别意图
    intent_result = await recognizer.recognize(user_input)

    print(f"\n识别结果:")
    print(f"  意图: {intent_result.type.value}")
    print(f"  Agent类型: {[agent.value for agent in intent_result.agent_types]}")

    # 2. 基于意图生成计划
    plan = await planner.generate_plan_from_intent(intent_result, user_input)

    print(f"\n生成的计划:")
    print(f"  步骤数: {len(plan.steps)}")

    print(f"\n执行步骤:")
    for i, step in enumerate(plan.steps, 1):
        print(f"  {i}. {step.name} ({step.agent_type.value})")
        if step.dependencies:
            print(f"     依赖: {[d for d in step.dependencies]}")


async def test_complexity_estimation():
    """测试复杂度估算"""
    print("\n" + "="*60)
    print("测试 4: 复杂度估算")
    print("="*60)

    planner = SmartPlanner()

    test_cases = [
        ("简单项目", "开发一个登录页面"),
        ("中等项目", "开发一个用户管理系统"),
        ("复杂项目", "开发一个完整的电商平台,包含用户、商品、订单、支付、物流、推荐系统")
    ]

    for complexity, user_input in test_cases:
        suggestions = await planner.get_plan_suggestions(user_input)
        estimated = suggestions['estimated_complexity']

        print(f"\n{complexity}: {estimated}")
        print(f"  输入: {user_input[:50]}...")
        print(f"  Agent数量: {len(suggestions['recommended_agents'])}")
        print(f"  关键词数量: {len(suggestions['keywords'])}")


async def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("智能规划器测试")
    print("="*60)

    tests = [
        test_smart_plan_generation,
        test_plan_suggestions,
        test_intent_based_planning,
        test_complexity_estimation
    ]

    for test_func in tests:
        try:
            await test_func()
        except Exception as e:
            print(f"\n❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "="*60)
    print("测试完成")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
