#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CLI编排功能测试
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from cli.main import SuperAgentCLI


def test_cli_workflow():
    """测试CLI工作流程"""
    print("="*70)
    print("  SuperAgent v3.0 CLI 编排功能测试")
    print("="*70)

    # 创建CLI实例
    cli = SuperAgentCLI()

    # 测试1: 生成计划
    print("\n[测试1] 生成项目计划")
    print("-"*70)

    user_input = "开发一个带数据库的博客系统"
    print(f"用户输入: {user_input}")

    # 模拟用户输入
    cli.default(user_input)

    if cli.current_plan:
        print(f"\n✅ 计划生成成功: {len(cli.current_plan.steps)}个步骤")

        # 测试2: 执行计划
        print("\n[测试2] 执行计划")
        print("-"*70)

        cli.do_execute("")

        if cli.last_result:
            print(f"\n✅ 执行完成: {cli.last_result.completed_tasks}/{cli.last_result.total_tasks}")

            # 测试3: 查看结果
            print("\n[测试3] 查看结果")
            print("-"*70)

            cli.do_result("tasks")

            print("\n[OK] 所有测试通过!")
            return True
        else:
            print("\n[FAIL] 执行失败")
            return False
    else:
        print("\n[FAIL] 计划生成失败")
        return False


if __name__ == "__main__":
    success = test_cli_workflow()
    sys.exit(0 if success else 1)
