# -*- coding: utf-8 -*-
"""
P1 功能演示 - 系统化调试流程

演示 SystematicDebugger 的 4 阶段科学调试方法
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from execution.systematic_debugger import SystematicDebugger


def demo_systematic_debugger():
    """演示系统化调试流程"""

    print("=" * 80)
    print("[P1 功能演示 #3] 系统化调试流程")
    print("=" * 80)
    print()

    # 创建调试器
    debugger = SystematicDebugger()

    # 定义模拟错误场景
    error_info = {
        "error_type": "AttributeError",
        "error_message": "'NoneType' object has no attribute 'split'",
        "stack_trace": [
            'File "test.py", line 15, in process_user_input',
            '    parts = name.split(" ")',
            "AttributeError: 'NoneType' object has no attribute 'split'"
        ],
        "code_context": {
            "function": "process_user_input",
            "line": 15,
            "code": 'parts = name.split(" ")'
        }
    }

    print("[错误场景]")
    print(f"  错误类型: {error_info['error_type']}")
    print(f"  错误信息: {error_info['error_message']}")
    print(f"  函数名: {error_info['code_context']['function']}")
    print()

    # 阶段 1: 错误观察
    print("[阶段 1] 错误观察")
    print("-" * 80)
    observation = debugger.start_debugging(error_info)
    print(f"[OK] 完成错误观察")
    print(f"  错误类型: {observation.error_type}")
    print(f"  错误消息: {observation.error_message}")
    print(f"  堆栈层数: {len(observation.stack_trace)}")
    print(f"  相关文件: {len(observation.related_files)} 个")
    print(f"  复现步骤: {len(observation.reproduction_steps)} 步")
    print()

    # 阶段 2: 假设生成
    print("[阶段 2] 假设生成")
    print("-" * 80)
    hypotheses = debugger.generate_hypotheses(observation)
    print(f"[OK] 生成了 {len(hypotheses)} 个假设:")
    for i, hyp in enumerate(hypotheses, 1):
        print(f"\n  假设 {i}: {hyp.hypothesis_id}")
        print(f"    标题: {hyp.title}")
        print(f"    可能性: {hyp.likelihood}")
        print(f"    建议测试: {hyp.suggested_tests[0][:60]}...")
    print()

    # 阶段 3: 假设验证
    print("[阶段 3] 假设验证")
    print("-" * 80)
    # 验证第一个假设
    first_hypothesis = hypotheses[0]
    print(f"  验证假设: {first_hypothesis.hypothesis_id}")

    # 模拟测试结果
    test_results = [
        "在 user_data 字典中没有 'name' 键",
        "user_data.get('name') 返回 None",
        "None 对象没有 split() 方法"
    ]

    verification = debugger.verify_hypothesis(first_hypothesis, test_results)
    print(f"[OK] 验证完成")
    print(f"  假设成立: {verification.is_valid}")
    print(f"  置信度: {verification.confidence:.2f}")
    print(f"  测试结果数: {len(verification.test_results)}")
    print()

    # 阶段 4: 根因确认
    print("[阶段 4] 根因确认")
    print("-" * 80)
    root_cause = debugger.confirm_root_cause(first_hypothesis.hypothesis_id)
    print(f"[OK] 根因确认完成")
    print(f"  根因 ID: {root_cause.root_cause_id}")
    print(f"  描述: {root_cause.description[:80]}...")
    print(f"  修复建议数: {len(root_cause.fix_suggestions)}")
    print(f"  防止策略数: {len(root_cause.prevention_strategies)}")
    print()

    # 显示修复建议
    print("[修复建议]")
    for i, suggestion in enumerate(root_cause.fix_suggestions[:3], 1):
        print(f"  {i}. {suggestion[:70]}...")
    print()

    # 显示防止策略
    print("[防止策略]")
    for i, strategy in enumerate(root_cause.prevention_strategies[:3], 1):
        print(f"  {i}. {strategy[:70]}...")
    print()

    # 获取完整报告
    print("[完整调试报告]")
    print("-" * 80)
    report = debugger.get_debugging_report()
    print(f"[OK] 报告生成完成")
    print(f"  当前阶段: {report.phase.value}")
    print(f"  假设数量: {len(report.hypotheses)}")
    print(f"  验证数量: {len(report.verifications)}")
    print(f"  根因确认: {'是' if report.root_cause else '否'}")
    print()

    # 获取调试历史
    print("[调试历史]")
    print("-" * 80)
    history = debugger.get_debugging_history()
    print(f"[OK] 历史记录数: {len(history)}")
    for i, record in enumerate(history, 1):
        phase = record['phase']
        print(f"  {i}. {phase}")
    print()

    print("=" * 80)
    print("[完成] 系统化调试流程演示完成!")
    print("=" * 80)
    print()

    return report


if __name__ == "__main__":
    demo_systematic_debugger()
