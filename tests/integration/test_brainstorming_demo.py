"""
P1 功能演示 - 脑暴设计流程

演示 BrainstormingManager 的 4 阶段设计探索流程
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from planning.brainstorming_manager import BrainstormingManager


def demo_brainstorming():
    """演示脑暴设计流程"""

    print("=" * 80)
    print("🧠 P1 功能演示 #1: 脑暴设计流程")
    print("=" * 80)
    print()

    # 创建脑暴管理器
    manager = BrainstormingManager()

    # 定义用户请求
    user_request = "实现一个用户管理 API 服务器"

    print("📋 用户请求:")
    print(f"   {user_request}")
    print()

    # 阶段 1: 需求收集
    print("🔍 阶段 1: 需求收集")
    print("-" * 80)
    result = manager.start_brainstorming(user_request)
    print(f"✅ 当前阶段: {result['phase']}")
    print(f"   消息: {result['message']}")
    print(f"   生成了 {len(result['questions'])} 个澄清问题:")
    for i, question in enumerate(result['questions'][:5], 1):
        print(f"   {i}. {question}")
    print()

    # 阶段 2: 方案探索
    print("💡 阶段 2: 方案探索")
    print("-" * 80)
    requirements = {
        "功能需求": "用户 CRUD、认证、权限管理",
        "性能需求": "支持 1000 并发用户",
        "技术栈": "Python 框架",
        "部署": "Docker 容器化"
    }
    design_options = manager.explore_solutions(requirements)
    print(f"✅ 生成了 {len(design_options)} 个设计方案:")
    for i, option in enumerate(design_options, 1):
        print(f"\n   方案 {i}: {option.title}")
        print(f"   描述: {option.description}")
        print(f"   优势: {', '.join(option.pros[:2])}")
        print(f"   劣势: {', '.join(option.cons[:2])}")
        print(f"   复杂度: {option.implementation_complexity}")
    print()

    # 阶段 3: 方案对比
    print("📊 阶段 3: 方案对比")
    print("-" * 80)
    comparison = manager.compare_alternatives(design_options)
    print("✅ 多维度对比完成:")
    print(f"   推荐方案: {comparison['recommended_option']}")
    print(f"   推荐理由: {comparison['rationale'][:100]}...")
    print()

    # 阶段 4: 决策确认
    print("✅ 阶段 4: 决策确认")
    print("-" * 80)
    # 假设选择第一个方案
    selected_option = design_options[0]
    design_spec = manager.finalize_design(selected_option, design_options, comparison['rationale'])
    print("✅ 生成设计规格:")
    print(f"   需求数量: {len(design_spec.requirements)}")
    print(f"   选中方案: {design_spec.selected_option.title}")
    print(f"   备选方案数: {len(design_spec.considered_alternatives)}")
    print(f"   决策理由: {design_spec.rationale[:80]}...")
    print(f"   架构说明: {design_spec.architecture_notes[:80]}...")
    print(f"   验收标准数: {len(design_spec.acceptance_criteria)}")
    print()

    print("=" * 80)
    print("🎉 脑暴设计流程演示完成!")
    print("=" * 80)
    print()

    return design_spec


if __name__ == "__main__":
    demo_brainstorming()
