import time
import pytest
from pathlib import Path
from common.security import SecurityValidator
from memory.memory_manager import MemoryManager

def test_performance_benchmarks():
    base = Path("E:/SuperAgent").resolve()
    
    # 1. 路径验证性能基准 (1000次连续验证)
    start_time = time.time()
    for i in range(1000):
        SecurityValidator.validate_path(Path(f"file_{i}.txt"), base)
    end_time = time.time()
    avg_time = (end_time - start_time) / 1000
    print(f"\nSecurityValidator 平均验证时间: {avg_time:.6f}s")
    assert avg_time < 0.005 # 必须在 5ms 内完成
    
    # 2. 记忆管理器初始化性能
    start_time = time.time()
    for _ in range(10):
        mm = MemoryManager()
    end_time = time.time()
    avg_init_time = (end_time - start_time) / 10
    print(f"MemoryManager 平均初始化时间: {avg_init_time:.6f}s")
    assert avg_init_time < 0.1 # 初始化应在 100ms 内完成

def test_input_sanitization_perf():
    # 测试大规模文本清理性能
    large_text = "<script>alert(1)</script> " * 1000 + "normal text"
    start_time = time.time()
    for _ in range(100):
        SecurityValidator.sanitize_input(large_text)
    end_time = time.time()
    avg_sanitize_time = (end_time - start_time) / 100
    print(f"输入清理平均时间 (25KB文本): {avg_sanitize_time:.6f}s")
    assert avg_sanitize_time < 0.05
