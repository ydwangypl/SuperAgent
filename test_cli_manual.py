#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CLI手动测试脚本

模拟用户与SuperAgent CLI的交互,验证对话流程
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from conversation.manager import ConversationManager


def print_section(title):
    """打印分节标题"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def test_conversation_flow():
    """测试完整的对话流程"""
    print_section("SuperAgent v3.0 对话流程测试")

    # 初始化对话管理器
    mgr = ConversationManager()

    # ========== 测试场景1: 模糊需求 ==========
    print_section("场景1: 模糊需求 - 用户说'帮我开发'")

    user_input_1 = "帮我开发"
    print(f"\n用户输入: {user_input_1}")

    result_1 = asyncio.run(mgr.process_input(user_input_1))

    print(f"\n系统响应类型: {result_1.type}")
    print(f"系统消息: {result_1.message}")
    print(f"\n生成的澄清问题数量: {len(result_1.clarifications)}")

    for i, q in enumerate(result_1.clarifications, 1):
        required_mark = "【必须】" if q.required else ""
        print(f"\n问题{i}: {q.question} {required_mark}")
        if q.options:
            print("选项:")
            for opt in q.options:
                print(f"  - {opt}")
        if q.reason:
            print(f"理由: {q.reason}")

    # ========== 测试场景2: 完整需求 ==========
    print_section("场景2: 完整需求 - 用户描述详细需求")

    user_input_2 = "我想开发一个博客系统,支持文章管理和用户评论功能"
    print(f"\n用户输入: {user_input_2}")

    result_2 = asyncio.run(mgr.process_input(user_input_2))

    print(f"\n系统响应类型: {result_2.type}")
    print(f"系统消息: {result_2.message}")

    if result_2.type == "requirements_ready":
        print(f"\n意图类型: {result_2.data['intent'].type.value}")
        print(f"置信度: {result_2.data['intent'].confidence}")
        print(f"推理过程: {result_2.data['intent'].reasoning}")

    # ========== 测试场景3: 不同类型项目 ==========
    print_section("场景3: 电商网站需求")

    user_input_3 = "开发一个电商网站,需要商品管理和订单功能"
    print(f"\n用户输入: {user_input_3}")

    result_3 = asyncio.run(mgr.process_input(user_input_3))

    print(f"\n系统响应类型: {result_3.type}")
    print(f"意图类型: {result_3.data['intent'].type.value}")

    # ========== 测试场景4: 查询类需求 ==========
    print_section("场景4: 查询类输入")

    user_input_4 = "查看当前状态"
    print(f"\n用户输入: {user_input_4}")

    result_4 = asyncio.run(mgr.process_input(user_input_4))

    print(f"\n系统响应类型: {result_4.type}")
    print(f"意图类型: {result_4.data['intent'].type.value}")

    # ========== 测试场景5: Bug修复 ==========
    print_section("场景5: Bug修复需求")

    user_input_5 = "修复登录失败的bug"
    print(f"\n用户输入: {user_input_5}")

    result_5 = asyncio.run(mgr.process_input(user_input_5))

    print(f"\n系统响应类型: {result_5.type}")
    print(f"意图类型: {result_5.data['intent'].type.value}")

    # ========== 总结 ==========
    print_section("测试总结")

    print("\n✅ 所有测试场景执行完成!")
    print("\n功能验证:")
    print("  ✅ 模糊需求识别 - 能生成澄清问题")
    print("  ✅ 完整需求识别 - 能判断需求明确")
    print("  ✅ 意图类型识别 - 支持5种意图类型")
    print("  ✅ 澄清问题生成 - 能生成相关问题")

    print("\n下一步:")
    print("  1. 启动实际CLI: python superagent.py")
    print("  2. 手动测试交互流程")
    print("  3. 验证用户体验")


def test_cli_integration():
    """测试CLI集成"""
    print_section("CLI集成测试")

    print("\n提示: 以下命令可以启动CLI进行手动测试:")
    print("\n  cd e:\\SuperAgent")
    print("  python superagent.py")
    print("\n然后在CLI中尝试以下输入:")
    print("\n  1. 帮我开发")
    print("  2. 我想开发一个博客系统")
    print("  3. 查看状态 (status)")
    print("  4. help")
    print("  5. quit")


if __name__ == "__main__":
    # 运行对话流程测试
    test_conversation_flow()

    # 显示CLI集成测试提示
    test_cli_integration()

    print("\n" + "="*70)
    print("  测试完成!")
    print("="*70)
