#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
性能优化测试脚本

测试意图识别、记忆查询、计划生成的缓存优化效果
"""

import asyncio
import time
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from conversation import IntentRecognizer
from planning import SmartPlanner
from memory import MemoryManager


async def test_intent_recognition_performance():
    """测试意图识别性能"""
    print("\n" + "="*60)
    print("测试1: 意图识别性能 (带LRU缓存)")
    print("="*60)

    recognizer = IntentRecognizer()

    # 测试用例
    test_inputs = [
        "开发一个博客系统",
        "设计数据库schema",
        "实现用户认证功能",
        "开发一个博客系统",  # 重复测试缓存
        "设计数据库schema",  # 重复测试缓存
    ]

    print("\n📊 性能指标:")
    print("-" * 60)

    first_run_times = []
    cached_run_times = []

    for i, user_input in enumerate(test_inputs):
        start = time.perf_counter()
        result = await recognizer.recognize(user_input)
        elapsed = (time.perf_counter() - start) * 1000  # 转换为毫秒

        if i < 2:  # 前两次是非缓存
            first_run_times.append(elapsed)
            cache_status = "首次执行"
        else:  # 后面是缓存命中
            cached_run_times.append(elapsed)
            cache_status = "缓存命中"

        print(f"  {i+1}. [{cache_status}] {user_input[:30]:30s} - {elapsed:6.2f}ms")
        print(f"     → 意图: {result.type.value}, 置信度: {result.confidence:.2f}")

    # 统计
    avg_first = sum(first_run_times) / len(first_run_times)
    avg_cached = sum(cached_run_times) / len(cached_run_times)
    speedup = avg_first / avg_cached if avg_cached > 0 else 0

    print("\n📈 统计结果:")
    print(f"  首次执行平均时间: {avg_first:.2f}ms")
    print(f"  缓存命中平均时间: {avg_cached:.2f}ms")
    print(f"  性能提升倍数: {speedup:.1f}x")
    print(f"  缓存命中率: {len(cached_run_times)}/{len(test_inputs)} = {len(cached_run_times)*100//len(test_inputs)}%")

    return speedup > 5  # 期望至少5倍提升


async def test_memory_query_performance():
    """测试记忆查询性能"""
    print("\n" + "="*60)
    print("测试2: 记忆查询性能 (带时间缓存)")
    print("="*60)

    # 创建测试记忆管理器
    project_root = Path(__file__).parent
    memory_manager = MemoryManager(project_root)

    # 保存一些测试记忆
    print("\n📝 准备测试数据...")
    for i in range(5):
        await memory_manager.save_episodic_memory(
            event=f"测试任务 {i+1}",
            task_id=f"test-{i+1}"
        )

    # 测试查询性能
    test_limits = [10, 10, 10, 5, 5, 10]  # 重复测试缓存

    print("\n📊 性能指标:")
    print("-" * 60)

    first_run_times = []
    cached_run_times = []

    for i, limit in enumerate(test_limits):
        start = time.perf_counter()
        memories = await memory_manager.get_episodic_memories(limit)
        elapsed = (time.perf_counter() - start) * 1000

        # 判断是否缓存命中(第2次及以后的相同limit)
        if i == 0 or (i == 3 and limit == 5):  # 第一次查询该limit
            first_run_times.append(elapsed)
            cache_status = "首次执行"
        else:  # 缓存命中
            cached_run_times.append(elapsed)
            cache_status = "缓存命中"

        print(f"  {i+1}. [{cache_status}] 查询limit={limit:2d} - {elapsed:6.2f}ms (返回{len(memories)}条记忆)")

    # 统计
    if first_run_times and cached_run_times:
        avg_first = sum(first_run_times) / len(first_run_times)
        avg_cached = sum(cached_run_times) / len(cached_run_times)
        speedup = avg_first / avg_cached if avg_cached > 0 else 0

        print("\n📈 统计结果:")
        print(f"  首次查询平均时间: {avg_first:.2f}ms")
        print(f"  缓存命中平均时间: {avg_cached:.2f}ms")
        print(f"  性能提升倍数: {speedup:.1f}x")
        print(f"  缓存命中率: {len(cached_run_times)}/{len(test_limits)} = {len(cached_run_times)*100//len(test_limits)}%")

        return speedup > 3  # 期望至少3倍提升

    return False


async def test_plan_generation_performance():
    """测试计划生成性能"""
    print("\n" + "="*60)
    print("测试3: 计划生成性能 (带哈希缓存)")
    print("="*60)

    planner = SmartPlanner()

    # 测试用例
    test_cases = [
        ("开发一个博客系统", {}),
        ("开发一个博客系统", {}),  # 重复测试缓存
        ("设计电商数据库", {}),
        ("设计电商数据库", {}),  # 重复测试缓存
    ]

    print("\n📊 性能指标:")
    print("-" * 60)

    first_run_times = []
    cached_run_times = []

    for i, (user_input, context) in enumerate(test_cases):
        start = time.perf_counter()
        plan = await planner.create_smart_plan(user_input, context)
        elapsed = (time.perf_counter() - start) * 1000

        if i % 2 == 0:  # 偶数索引是非缓存
            first_run_times.append(elapsed)
            cache_status = "首次执行"
        else:  # 奇数索引是缓存命中
            cached_run_times.append(elapsed)
            cache_status = "缓存命中"

        print(f"  {i+1}. [{cache_status}] {user_input[:30]:30s} - {elapsed:6.2f}ms")
        print(f"     → 生成{len(plan.steps)}个步骤, 估算时间: {plan.estimated_time}")

    # 统计
    if first_run_times and cached_run_times:
        avg_first = sum(first_run_times) / len(first_run_times)
        avg_cached = sum(cached_run_times) / len(cached_run_times)
        speedup = avg_first / avg_cached if avg_cached > 0 else 0

        print("\n📈 统计结果:")
        print(f"  首次生成平均时间: {avg_first:.2f}ms")
        print(f"  缓存命中平均时间: {avg_cached:.2f}ms")
        print(f"  性能提升倍数: {speedup:.1f}x")
        print(f"  缓存命中率: {len(cached_run_times)}/{len(test_cases)} = {len(cached_run_times)*100//len(test_cases)}%")

        return speedup > 10  # 期望至少10倍提升

    return False


async def test_cache_clearing():
    """测试缓存清除功能"""
    print("\n" + "="*60)
    print("测试4: 缓存清除功能")
    print("="*60)

    # 测试IntentRecognizer缓存清除
    print("\n✅ IntentRecognizer.clear_cache()")
    recognizer = IntentRecognizer()
    recognizer.clear_cache()
    print("  → 意图识别缓存已清除")

    # 测试MemoryManager缓存清除
    print("\n✅ MemoryManager.clear_cache()")
    project_root = Path(__file__).parent
    memory_manager = MemoryManager(project_root)
    memory_manager.clear_cache()
    print("  → 记忆查询缓存已清除")

    # 测试SmartPlanner缓存清除
    print("\n✅ SmartPlanner.clear_cache()")
    planner = SmartPlanner()
    planner.clear_cache()
    print("  → 计划生成缓存已清除")

    return True


async def main():
    """主测试函数"""
    print("\n" + "🚀" * 30)
    print("SuperAgent v3.0 性能优化测试")
    print("🚀" * 30)

    results = {}

    try:
        # 测试1: 意图识别性能
        results['intent_recognition'] = await test_intent_recognition_performance()

        # 测试2: 记忆查询性能
        results['memory_query'] = await test_memory_query_performance()

        # 测试3: 计划生成性能
        results['plan_generation'] = await test_plan_generation_performance()

        # 测试4: 缓存清除
        results['cache_clearing'] = await test_cache_clearing()

    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return

    # 总结
    print("\n" + "="*60)
    print("📊 测试总结")
    print("="*60)

    passed_count = sum(1 for v in results.values() if v)
    total = len(results)

    print(f"\n✅ 通过: {passed_count}/{total}")
    print(f"\n详细结果:")
    for test_name, is_passed in results.items():
        status = "✅ PASS" if is_passed else "❌ FAIL"
        print(f"  {status} - {test_name}")

    if passed_count == total:
        print("\n🎉 所有性能优化测试通过!")
        print("✨ 缓存优化成功实现,性能提升显著!")
    else:
        print(f"\n⚠️  {total - passed_count} 个测试未通过,需要检查优化实现")


if __name__ == "__main__":
    # 设置Windows控制台UTF-8编码
    if sys.platform == "win32":
        import locale
        import sys
        import io
        # 重新配置stdout为UTF-8
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

    # 运行测试
    asyncio.run(main())
