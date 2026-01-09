import pytest
import asyncio
from pathlib import Path
from common.security import SecurityValidator, SecurityError
from memory.memory_manager import MemoryManager

def test_security_validator_boundaries():
    base = Path("E:/SuperAgent").resolve()
    
    # 1. 测试绝对路径越权 (Windows 环境下)
    # 假设 C:\Windows 存在且不在 base 内
    win_dir = Path("C:/Windows")
    if win_dir.exists():
        with pytest.raises(SecurityError):
            SecurityValidator.validate_path(win_dir, base)
    
    # 2. 测试非法的路径穿越尝试
    with pytest.raises(SecurityError):
        SecurityValidator.validate_path(Path("../" * 20 + "windows/system32/config/SAM"), base)

    # 3. 测试空路径或点号路径 (应被视为 base 本身或抛出异常，取决于具体实现需求)
    # 我们的 validate_path 应该返回 base 路径
    assert SecurityValidator.validate_path(Path(""), base) == base
    assert SecurityValidator.validate_path(Path("."), base) == base

    # 4. 测试不安全的字节/特殊字符路径
    with pytest.raises(SecurityError):
        # 模拟包含零字节的路径
        SecurityValidator.validate_path(Path("illegal\0byte.txt"), base)

@pytest.mark.asyncio
async def test_memory_manager_boundaries(tmp_path):
    # 1. 测试不存在但可创建的根目录
    invalid_root = tmp_path / "new_project"
    
    # 因为 MemoryManager 是单例，我们需要重置它以便测试不同的根目录
    MemoryManager._instance = None
    
    # 因为 MemoryManager.__init__ 内部启动了异步任务，我们需要在 loop 中运行
    mm = MemoryManager(project_root=invalid_root)
    assert mm.project_root == invalid_root
    assert mm.initialized is True
    
    # 给异步任务一点时间执行或清理
    await asyncio.sleep(0.1)

def test_git_ref_boundaries():
    # 1. 测试超长分支名
    long_ref = "feature/" + "a" * 250
    with pytest.raises(SecurityError):
        SecurityValidator.validate_git_ref(long_ref) # 我们的正则限制了长度或字符

    # 2. 测试包含控制字符的分支名
    with pytest.raises(SecurityError):
        SecurityValidator.validate_git_ref("branch\nname")
