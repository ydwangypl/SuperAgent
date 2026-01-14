# -*- coding: utf-8 -*-
"""
P1 功能演示 - 并行执行优化

演示 ParallelExecutor 的智能并行任务调度和资源管理
"""

import sys
import os
import time

# 添加项目路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from orchestration.parallel_executor import (
    ParallelExecutor,
    Step,
    ExecutionStatus
)


def demo_parallel_executor():
    """演示并行执行功能"""

    print("=" * 80)
    print("[P1 功能演示 #4] 并行执行优化")
    print("=" * 80)
    print()

    # 创建并行执行器
    executor = ParallelExecutor(max_workers=3)

    # 定义任务列表 (钻石形依赖)
    # 1 -> 2, 3, 4 (并行)
    # 2 -> 5
    # 3 -> 5
    # 4 -> 6
    # 5, 6 -> 7
    steps = [
        Step(
            step_id="1",
            description="初始化环境",
            dependencies=[],
            estimated_duration=1
        ),
        Step(
            step_id="2",
            description="编译模块 A",
            dependencies=["1"],
            estimated_duration=2
        ),
        Step(
            step_id="3",
            description="编译模块 B",
            dependencies=["1"],
            estimated_duration=2
        ),
        Step(
            step_id="4",
            description="编译模块 C",
            dependencies=["1"],
            estimated_duration=2
        ),
        Step(
            step_id="5",
            description="集成模块 A+B",
            dependencies=["2", "3"],
            estimated_duration=1
        ),
        Step(
            step_id="6",
            description="测试模块 C",
            dependencies=["4"],
            estimated_duration=1
        ),
        Step(
            step_id="7",
            description="最终打包",
            dependencies=["5", "6"],
            estimated_duration=1
        ),
    ]

    print("[任务列表]")
    print(f"  总任务数: {len(steps)}")
    print(f"  最大并发: {executor.max_workers}")
    print(f"  预计总耗时: 10 秒 (串行)")
    print()

    # 模拟执行函数
    def mock_executor(step: Step):
        time.sleep(0.05)  # 模拟耗时操作
        return f"完成: {step.description}"

    # 执行任务
    print("[开始执行]")
    print("-" * 80)
    start_time = time.time()
    results = executor.execute_steps_parallel(steps, mock_executor)
    end_time = time.time()
    duration = end_time - start_time

    # 统计结果
    successful = sum(1 for r in results if r.success)
    failed = sum(1 for r in results if not r.success)
    total_duration = sum(r.duration for r in results)

    print(f"[OK] 执行完成")
    print(f"  总结果数: {len(results)}")
    print(f"  成功: {successful}")
    print(f"  失败: {failed}")
    print(f"  实际耗时: {duration:.2f} 秒")
    print(f"  任务总耗时: {total_duration:.2f} 秒")
    print()

    # 执行统计
    print("[执行统计]")
    print("-" * 80)
    stats = executor.get_execution_statistics()
    print(f"[OK] 统计信息:")
    print(f"  总执行数: {stats['total_executions']}")
    print(f"  成功: {stats['successful']}")
    print(f"  失败: {stats['failed']}")
    print(f"  成功率: {stats['success_rate']:.1%}")
    print(f"  平均耗时: {stats['average_duration']:.3f} 秒")
    print()

    # 资源锁统计
    print("[资源管理]")
    print("-" * 80)
    lock_stats = stats['lock_statistics']
    print(f"[OK] 锁统计:")
    print(f"  文件锁: {lock_stats['total_files']}")
    print(f"  资源锁: {lock_stats['total_resources']}")
    print(f"  总锁数: {lock_stats['total_locks']}")
    print()

    # 详细执行顺序
    print("[执行顺序分析]")
    print("-" * 80)
    print("  根据依赖关系识别的并行组:")
    print("    组 1: [1] - 初始化环境")
    print("    组 2: [2, 3, 4] - 并行编译模块 A, B, C")
    print("    组 3: [5, 6] - 并行集成和测试")
    print("    组 4: [7] - 最终打包")
    print()

    # 资源竞争示例
    print("[资源竞争演示]")
    print("-" * 80)

    # 创建有资源冲突的任务
    resource_steps = [
        Step(
            step_id="r1",
            description="读取文件 A",
            required_resources=["config.json"]
        ),
        Step(
            step_id="r2",
            description="读取文件 A",
            required_resources=["config.json"]
        ),
        Step(
            step_id="r3",
            description="写入文件 B",
            required_resources=["output.txt"]
        ),
    ]

    executor2 = ParallelExecutor(max_workers=2)
    results2 = executor2.execute_steps_parallel(resource_steps, mock_executor)

    print(f"[OK] 资源冲突任务执行完成")
    print(f"  任务数: {len(results2)}")
    print(f"  全部成功: {all(r.success for r in results2)}")

    lock_stats2 = executor2.get_execution_statistics()['lock_statistics']
    print(f"  文件锁: {lock_stats2['total_files']}")
    print()

    # 循环依赖检测示例
    print("[循环依赖检测演示]")
    print("-" * 80)

    cyclic_steps = [
        Step(step_id="a", description="Task A", dependencies=["b"]),
        Step(step_id="b", description="Task B", dependencies=["c"]),
        Step(step_id="c", description="Task C", dependencies=["a"]),  # 形成环
    ]

    try:
        executor3 = ParallelExecutor()
        executor3.execute_steps_parallel(cyclic_steps, mock_executor)
        print("[错误] 应该检测到循环依赖!")
    except ValueError as e:
        print(f"[OK] 成功检测到循环依赖:")
        print(f"  错误信息: {str(e)[:60]}...")
    print()

    print("=" * 80)
    print("[完成] 并行执行优化演示完成!")
    print("=" * 80)
    print()

    return stats


if __name__ == "__main__":
    demo_parallel_executor()
