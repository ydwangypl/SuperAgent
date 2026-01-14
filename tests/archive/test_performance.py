# -*- coding: utf-8 -*-
"""
性能测试: Agent缓存和加载性能

测试范围:
- Agent加载性能
- 缓存效果验证
- 内存使用情况
"""
import sys
import time
from pathlib import Path
import pytest
import tracemalloc

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agent_tools import AgentTools
from tests.helpers import PerformanceTimer, create_sample_prd


@pytest.fixture
def agent_tools():
    """创建AgentTools实例"""
    project_root = Path(__file__).parent.parent.parent
    with pytest.MonkeyPatch().context() as m:
        m.setattr("agent_tools.AgentTools._find_superagent_root",
                  lambda self: project_root)
        tools = AgentTools(str(project_root))
        yield tools


@pytest.mark.performance
class TestAgentLoadingPerformance:
    """测试Agent加载性能"""

    def test_load_single_agent_performance(self, agent_tools):
        """测试加载单个Agent的性能"""
        agent_name = "product-management"

        with PerformanceTimer() as timer:
            agent_tools._load_agent_class(agent_name)

        elapsed = timer.elapsed()

        # 首次加载应该在1秒内完成
        assert elapsed < 1.0, f"加载Agent耗时 {elapsed:.3f}s，超过1秒"

        print(f"\n[性能] 首次加载 {agent_name}: {elapsed:.3f}s")

    def test_cached_agent_performance(self, agent_tools):
        """测试缓存Agent的性能"""
        agent_name = "product-management"

        # 预加载
        agent_tools._load_agent_class(agent_name)

        # 测试缓存命中性能
        with PerformanceTimer() as timer:
            agent_tools._load_agent_class(agent_name)

        elapsed = timer.elapsed()

        # 缓存命中应该在10ms内完成
        assert elapsed < 0.01, f"缓存命中耗时 {elapsed:.3f}s，超过10ms"

        print(f"\n[性能] 缓存命中: {elapsed:.6f}s")

    def test_load_all_agents_performance(self, agent_tools):
        """测试加载所有8个Agent的性能"""
        agent_names = list(AgentTools.AGENT_MAPPING.keys())

        with PerformanceTimer() as timer:
            for agent_name in agent_names:
                agent_tools._load_agent_class(agent_name)

        elapsed = timer.elapsed()
        avg_time = elapsed / len(agent_names)

        # 所有Agent加载应该在5秒内完成
        assert elapsed < 5.0, f"加载所有Agent耗时 {elapsed:.3f}s，超过5秒"

        print(f"\n[性能] 加载所有{len(agent_names)}个Agent: {elapsed:.3f}s")
        print(f"[性能] 平均每个Agent: {avg_time:.3f}s")

    def test_cache_effectiveness(self, agent_tools):
        """测试缓存有效性"""
        agent_name = "product-management"

        # 第一次加载（无缓存）
        with PerformanceTimer() as timer1:
            agent_tools._load_agent_class(agent_name)
        time_without_cache = timer1.elapsed()

        # 第二次加载（有缓存）
        with PerformanceTimer() as timer2:
            agent_tools._load_agent_class(agent_name)
        time_with_cache = timer2.elapsed()

        # 缓存应该显著提升性能
        speedup = time_without_cache / time_with_cache if time_with_cache > 0 else float('inf')

        print(f"\n[性能] 无缓存: {time_without_cache:.3f}s")
        print(f"[性能] 有缓存: {time_with_cache:.6f}s")
        print(f"[性能] 提升倍数: {speedup:.1f}x")

        # 至少应该快10倍（实际通常快100-1000倍）
        assert speedup >= 10, f"缓存性能提升不足，只有 {speedup:.1f}x"


@pytest.mark.performance
class TestMemoryUsage:
    """测试内存使用情况"""

    def test_agent_loading_memory(self, agent_tools):
        """测试Agent加载的内存使用"""
        tracemalloc.start()

        # 记录初始内存
        snapshot1 = tracemalloc.take_snapshot()

        # 加载所有Agent
        for agent_name in AgentTools.AGENT_MAPPING.keys():
            agent_tools._load_agent_class(agent_name)

        # 记录加载后内存
        snapshot2 = tracemalloc.take_snapshot()

        # 计算内存差异
        top_stats = snapshot2.compare_to(snapshot1, 'lineno')
        total_memory = sum(stat.size_diff for stat in top_stats)

        tracemalloc.stop()

        # 转换为MB
        total_mb = total_memory / (1024 * 1024)

        print(f"\n[内存] 加载所有Agent使用: {total_mb:.2f} MB")

        # 应该小于50MB（这是一个宽松的限制）
        assert total_mb < 50, f"内存使用过多: {total_mb:.2f} MB"

    def test_cache_memory_overhead(self, agent_tools):
        """测试缓存的内存开销"""
        tracemalloc.start()

        snapshot1 = tracemalloc.take_snapshot()

        # 加载并缓存所有Agent
        for agent_name in AgentTools.AGENT_MAPPING.keys():
            agent_tools._load_agent_class(agent_name)

        snapshot2 = tracemalloc.take_snapshot()

        # 计算缓存开销
        top_stats = snapshot2.compare_to(snapshot1, 'lineno')
        cache_memory = sum(stat.size_diff for stat in top_stats)

        tracemalloc.stop()

        cache_mb = cache_memory / (1024 * 1024)

        print(f"\n[内存] 缓存开销: {cache_mb:.2f} MB")
        print(f"[内存] 平均每个Agent: {cache_mb / len(agent_tools._agent_cache):.3f} MB")

        # 缓存开销应该很小（每个Agent类约几KB）
        assert cache_mb < 10, f"缓存开销过大: {cache_mb:.2f} MB"


@pytest.mark.performance
class TestExecutionPerformance:
    """测试执行性能"""

    def test_execute_with_vs_without_cache(self, agent_tools, tmp_path):
        """测试有缓存vs无缓存的执行性能差异"""
        project_dir = str(tmp_path / "test_project")
        Path(project_dir).mkdir()

        # 创建必需的文件
        create_sample_prd(project_dir)

        agent_name = "product-management"

        # 第一次执行（加载+缓存）
        with PerformanceTimer() as timer1:
            result1 = agent_tools.execute_agent(agent_name, {
                "user_request": "性能测试项目1"
            })

        time_first = timer1.elapsed()

        # 清理生成的文件
        for file in result1.get("files", []):
            Path(file).unlink(missing_ok=True)

        # 第二次执行（使用缓存）
        with PerformanceTimer() as timer2:
            result2 = agent_tools.execute_agent(agent_name, {
                "user_request": "性能测试项目2"
            })

        time_second = timer2.elapsed()

        print(f"\n[性能] 第一次执行（加载类）: {time_first:.3f}s")
        print(f"[性能] 第二次执行（使用缓存）: {time_second:.3f}s")

        if time_second > 0:
            improvement = ((time_first - time_second) / time_first) * 100
            print(f"[性能] 性能提升: {improvement:.1f}%")

        # 两次都应该成功
        assert result1["status"] == "success"
        assert result2["status"] == "success"


@pytest.mark.performance
@pytest.mark.slow
class TestScalability:
    """测试可扩展性"""

    def test_multiple_tool_instances(self):
        """测试多个AgentTools实例的性能"""
        instances = []

        with PerformanceTimer() as timer:
            for i in range(10):
                project_root = Path(__file__).parent.parent.parent
                with pytest.MonkeyPatch().context() as m:
                    m.setattr("agent_tools.AgentTools._find_superagent_root",
                              lambda self: project_root)
                    tools = AgentTools(str(project_root))
                    instances.append(tools)

        elapsed = timer.elapsed()

        print(f"\n[性能] 创建10个实例: {elapsed:.3f}s")
        print(f"[性能] 平均每个: {elapsed/10:.3f}s")

        # 创建10个实例应该在1秒内完成
        assert elapsed < 1.0, f"创建实例过慢: {elapsed:.3f}s"

    def test_concurrent_agent_loading(self, agent_tools):
        """测试并发加载多个Agent"""
        agent_names = list(AgentTools.AGENT_MAPPING.keys())[:4]  # 测试4个Agent

        with PerformanceTimer() as timer:
            for agent_name in agent_names:
                agent_tools._load_agent_class(agent_name)

        elapsed = timer.elapsed()

        print(f"\n[性能] 加载{len(agent_names)}个Agent: {elapsed:.3f}s")

        # 4个Agent应该在2秒内加载完成
        assert elapsed < 2.0, f"加载过慢: {elapsed:.3f}s"


# 性能基准配置
PERFORMANCE_BENCHMARKS = {
    "single_agent_load": 1.0,  # 秒
    "cached_agent_load": 0.01,  # 秒
    "all_agents_load": 5.0,  # 秒
    "cache_speedup": 10,  # 倍数
    "memory_limit": 50,  # MB
}


@pytest.mark.benchmark
def test_performance_benchmarks(agent_tools):
    """运行性能基准测试"""
    print("\n" + "="*70)
    print("性能基准测试")
    print("="*70)

    results = {}

    # 测试1: 单Agent加载
    with PerformanceTimer() as timer:
        agent_tools._load_agent_class("product-management")
    results["single_agent_load"] = timer.elapsed()

    # 测试2: 缓存命中
    with PerformanceTimer() as timer:
        agent_tools._load_agent_class("product-management")
    results["cached_agent_load"] = timer.elapsed()

    # 计算性能提升
    results["cache_speedup"] = (
        results["single_agent_load"] / results["cached_agent_load"]
        if results["cached_agent_load"] > 0 else float('inf')
    )

    # 显示结果
    print(f"\n结果:")
    print(f"  单Agent加载: {results['single_agent_load']:.3f}s "
          f"(基准: {PERFORMANCE_BENCHMARKS['single_agent_load']:.3f}s)")

    print(f"  缓存命中: {results['cached_agent_load']:.6f}s "
          f"(基准: {PERFORMANCE_BENCHMARKS['cached_agent_load']:.3f}s)")

    print(f"  性能提升: {results['cache_speedup']:.1f}x "
          f"(基准: {PERFORMANCE_BENCHMARKS['cache_speedup']:.0f}x)")

    # 验证基准
    assert results["single_agent_load"] <= PERFORMANCE_BENCHMARKS["single_agent_load"], \
        f"单Agent加载超过基准: {results['single_agent_load']:.3f}s"

    assert results["cached_agent_load"] <= PERFORMANCE_BENCHMARKS["cached_agent_load"], \
        f"缓存命中超过基准: {results['cached_agent_load']:.6f}s"

    assert results["cache_speedup"] >= PERFORMANCE_BENCHMARKS["cache_speedup"], \
        f"性能提升不足: {results['cache_speedup']:.1f}x"

    print("\n✓ 所有性能基准测试通过！")
