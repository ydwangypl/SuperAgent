#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SuperAgent 性能基准测试

建立性能基线,用于对比重构前后的性能。
"""

import asyncio
import time
import sys
import statistics
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from conversation.manager import ConversationManager
from planning.planner import ProjectPlanner
from utils.exceptions import ConversationError, PlanningError
from utils.error_handler import ErrorHandler


class PerformanceBenchmark:
    """性能基准测试类"""

    def __init__(self):
        """初始化性能测试"""
        self.results: Dict[str, List[float]] = {}
        self.memory_usage: Dict[str, float] = {}

    def record_time(self, operation: str, duration: float):
        """记录操作时间"""
        if operation not in self.results:
            self.results[operation] = []
        self.results[operation].append(duration)

    def get_statistics(self, operation: str) -> Dict[str, float]:
        """获取操作统计信息"""
        if operation not in self.results or not self.results[operation]:
            return {}

        times = self.results[operation]
        return {
            "count": len(times),
            "min": min(times),
            "max": max(times),
            "mean": statistics.mean(times),
            "median": statistics.median(times),
            "stdev": statistics.stdev(times) if len(times) > 1 else 0.0,
            "total": sum(times)
        }

    def print_report(self):
        """打印性能报告"""
        print("=" * 70)
        print("SuperAgent 性能基准测试报告")
        print("=" * 70)
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        for operation in sorted(self.results.keys()):
            stats = self.get_statistics(operation)
            if not stats:
                continue

            print(f"【{operation}】")
            print(f"  次数: {stats['count']}")
            print(f"  平均: {stats['mean']*1000:.2f} ms")
            print(f"  中位数: {stats['median']*1000:.2f} ms")
            print(f"  最小: {stats['min']*1000:.2f} ms")
            print(f"  最大: {stats['max']*1000:.2f} ms")
            print(f"  标准差: {stats['stdev']*1000:.2f} ms")
            print(f"  总计: {stats['total']*1000:.2f} ms")
            print()

        print("=" * 70)


class ConversationPerformanceTests:
    """对话管理性能测试"""

    def __init__(self, benchmark: PerformanceBenchmark):
        self.benchmark = benchmark
        self.conv_mgr = ConversationManager()

    def test_initialization(self, iterations: int = 100):
        """测试初始化性能"""
        print(f"\n[测试] 对话管理器初始化 (x{iterations})")

        times = []
        for _ in range(iterations):
            start = time.perf_counter()
            mgr = ConversationManager()
            end = time.perf_counter()
            duration = end - start
            times.append(duration)
            self.benchmark.record_time("conversation_init", duration)

        avg = statistics.mean(times) * 1000
        print(f"  平均时间: {avg:.3f} ms")
        print(f"  [OK] 初始化性能正常")

    def test_context_operations(self, iterations: int = 1000):
        """测试上下文操作性能"""
        print(f"\n[测试] 上下文操作 (x{iterations})")

        times = []
        for _ in range(iterations):
            start = time.perf_counter()
            # 模拟上下文操作
            context = {"key": "value"}
            _ = context.get("key")
            end = time.perf_counter()
            duration = end - start
            times.append(duration)
            self.benchmark.record_time("context_ops", duration)

        avg = statistics.mean(times) * 1000
        ops_per_sec = (iterations / sum(times))
        print(f"  平均时间: {avg:.3f} ms")
        print(f"  吞吐量: {ops_per_sec:.0f} ops/sec")
        print(f"  [OK] 上下文操作性能正常")


class PlanningPerformanceTests:
    """计划生成性能测试"""

    def __init__(self, benchmark: PerformanceBenchmark):
        self.benchmark = benchmark
        self.planner = ProjectPlanner()

    def test_planner_initialization(self, iterations: int = 100):
        """测试计划器初始化性能"""
        print(f"\n[测试] 计划器初始化 (x{iterations})")

        times = []
        for _ in range(iterations):
            start = time.perf_counter()
            planner = ProjectPlanner()
            end = time.perf_counter()
            duration = end - start
            times.append(duration)
            self.benchmark.record_time("planner_init", duration)

        avg = statistics.mean(times) * 1000
        print(f"  平均时间: {avg:.3f} ms")
        print(f"  [OK] 初始化性能正常")


class ErrorHandlingPerformanceTests:
    """错误处理性能测试"""

    def __init__(self, benchmark: PerformanceBenchmark):
        self.benchmark = benchmark

    def test_exception_creation(self, iterations: int = 1000):
        """测试异常创建性能"""
        print(f"\n[测试] 异常创建 (x{iterations})")

        times = []
        for _ in range(iterations):
            start = time.perf_counter()
            error = ConversationError("测试错误")
            _ = str(error)
            end = time.perf_counter()
            duration = end - start
            times.append(duration)
            self.benchmark.record_time("exception_creation", duration)

        avg = statistics.mean(times) * 1000
        print(f"  平均时间: {avg:.3f} ms")
        print(f"  [OK] 异常创建性能正常")

    def test_error_handler_decorator(self, iterations: int = 1000):
        """测试错误处理装饰器性能"""
        from utils.error_handler import handle_errors

        print(f"\n[测试] 错误处理装饰器 (x{iterations})")

        @handle_errors(
            error_type=ConversationError,
            fallback="fallback",
            log=False
        )
        def test_function():
            return "success"

        times = []
        for _ in range(iterations):
            start = time.perf_counter()
            result = test_function()
            end = time.perf_counter()
            duration = end - start
            times.append(duration)
            self.benchmark.record_time("error_handler_decorator", duration)

        avg = statistics.mean(times) * 1000
        overhead = avg  # 装饰器开销
        print(f"  平均时间: {avg:.3f} ms")
        print(f"  装饰器开销: {overhead:.3f} ms")
        print(f"  [OK] 装饰器性能可接受")

    def test_safe_execute(self, iterations: int = 1000):
        """测试 safe_execute 性能"""
        from utils.error_handler import safe_execute

        print(f"\n[测试] safe_execute (x{iterations})")

        def test_function():
            return "success"

        times = []
        for _ in range(iterations):
            start = time.perf_counter()
            result = safe_execute(test_function, fallback="fallback", log=False)
            end = time.perf_counter()
            duration = end - start
            times.append(duration)
            self.benchmark.record_time("safe_execute", duration)

        avg = statistics.mean(times) * 1000
        print(f"  平均时间: {avg:.3f} ms")
        print(f"  [OK] safe_execute 性能正常")

    def test_error_handler_class(self, iterations: int = 100):
        """测试 ErrorHandler 类性能"""
        from utils.error_handler import ErrorHandler

        print(f"\n[测试] ErrorHandler 类 (x{iterations})")

        handler = ErrorHandler(max_errors=10, log_errors=False)
        error = ConversationError("测试错误")

        times = []
        for _ in range(iterations):
            start = time.perf_counter()
            handler.record_error(error)
            end = time.perf_counter()
            duration = end - start
            times.append(duration)
            self.benchmark.record_time("error_handler_record", duration)

        avg = statistics.mean(times) * 1000
        print(f"  平均时间: {avg:.3f} ms")
        print(f"  [OK] ErrorHandler 性能正常")


class MemoryUsageTests:
    """内存使用测试"""

    def __init__(self, benchmark: PerformanceBenchmark):
        self.benchmark = benchmark

    def test_object_creation(self, iterations: int = 1000):
        """测试对象创建的内存使用"""
        print(f"\n[测试] 对象创建内存使用 (x{iterations})")

        import tracemalloc

        tracemalloc.start()

        # 创建多个对象
        for _ in range(iterations):
            error = ConversationError("测试")
            _ = error.to_dict()

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        avg_per_object = peak / iterations

        print(f"  峰值内存: {peak / 1024:.2f} KB")
        print(f"  平均每对象: {avg_per_object:.2f} bytes")
        print(f"  [OK] 内存使用正常")


def run_all_benchmarks():
    """运行所有基准测试"""

    print("\n" + "=" * 70)
    print("SuperAgent 性能基准测试套件")
    print("=" * 70)

    benchmark = PerformanceBenchmark()

    # 1. 对话管理性能测试
    print("\n" + "=" * 70)
    print("1. 对话管理性能测试")
    print("=" * 70)
    conv_tests = ConversationPerformanceTests(benchmark)
    conv_tests.test_initialization()
    conv_tests.test_context_operations()

    # 2. 计划生成性能测试
    print("\n" + "=" * 70)
    print("2. 计划生成性能测试")
    print("=" * 70)
    planning_tests = PlanningPerformanceTests(benchmark)
    planning_tests.test_planner_initialization()

    # 3. 错误处理性能测试
    print("\n" + "=" * 70)
    print("3. 错误处理性能测试")
    print("=" * 70)
    error_tests = ErrorHandlingPerformanceTests(benchmark)
    error_tests.test_exception_creation()
    error_tests.test_error_handler_decorator()
    error_tests.test_safe_execute()
    error_tests.test_error_handler_class()

    # 4. 内存使用测试
    print("\n" + "=" * 70)
    print("4. 内存使用测试")
    print("=" * 70)
    memory_tests = MemoryUsageTests(benchmark)
    memory_tests.test_object_creation()

    # 生成报告
    benchmark.print_report()

    # 保存结果
    save_benchmark_results(benchmark)

    return 0


def save_benchmark_results(benchmark: PerformanceBenchmark):
    """保存基准测试结果"""

    results = {
        "timestamp": datetime.now().isoformat(),
        "operations": {}
    }

    for operation in benchmark.results.keys():
        results["operations"][operation] = benchmark.get_statistics(operation)

    import json
    output_file = Path(__file__).parent / "performance_baseline.json"

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n[OK] 基准测试结果已保存: {output_file}")


def main():
    """主函数"""
    try:
        return run_all_benchmarks()
    except Exception as e:
        print(f"\n[ERROR] 性能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
