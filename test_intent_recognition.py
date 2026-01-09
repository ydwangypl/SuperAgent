#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
智能意图识别器测试

测试增强的意图识别功能
"""

import sys
import io
import asyncio
from pathlib import Path

# Windows 控制台 UTF-8 支持
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加项目根目录到 Python 路径
SUPERAGENT_ROOT = Path(__file__).parent
sys.path.insert(0, str(SUPERAGENT_ROOT))

from conversation import IntentRecognizer


async def test_basic_recognition():
    """测试基本意图识别"""
    print("\n" + "="*60)
    print("测试 1: 基本意图识别")
    print("="*60)

    recognizer = IntentRecognizer()

    test_cases = [
        {
            "input": "开发一个用户管理系统,需要注册和登录功能",
            "expected_agents": ["backend-dev", "database-dev"]
        },
        {
            "input": "设计博客系统的数据库结构",
            "expected_agents": ["database-dev"]
        },
        {
            "input": "使用React构建前端页面",
            "expected_agents": ["frontend-dev"]
        },
        {
            "input": "编写API文档",
            "expected_agents": ["documentation"]
        }
    ]

    for i, test in enumerate(test_cases, 1):
        print(f"\n测试用例 {i}:")
        print(f"  输入: {test['input']}")

        result = await recognizer.recognize(test['input'])

        print(f"  主要意图: {result.type.value}")
        print(f"  置信度: {result.confidence:.2f}")
        print(f"  匹配的Agent: {[agent.value for agent in result.agent_types]}")
        print(f"  关键词: {result.keywords}")

        # 验证
        if result.agent_types:
            print(f"  ✓ 成功识别到Agent类型")
        else:
            print(f"  ⚠️  未识别到Agent类型")


async def test_agent_suggestions():
    """测试Agent建议"""
    print("\n" + "="*60)
    print("测试 2: Agent类型建议")
    print("="*60)

    recognizer = IntentRecognizer()

    user_input = "开发一个电商网站,需要用户注册、商品管理、订单系统和支付功能"

    print(f"\n用户输入: {user_input}")

    # 注意：IntentRecognizer 目前没有 get_agent_type_suggestions 方法，
    # 它的逻辑已经整合到 recognize 中了。
    result = await recognizer.recognize(user_input)

    print(f"\n推荐的Agent类型 ({len(result.agent_types)}个):")
    for i, agent_type in enumerate(result.agent_types, 1):
        print(f"\n{i}. {agent_type.value}")


async def main():
    """主函数"""
    await test_basic_recognition()
    await test_agent_suggestions()
    print("\n意图识别测试完成!")


if __name__ == "__main__":
    asyncio.run(main())
