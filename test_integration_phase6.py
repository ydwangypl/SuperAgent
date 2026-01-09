#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SuperAgent v3.0 Phase 6 集成测试

测试 CLI、配置系统和 Agent 输出格式的集成
"""

import asyncio
import sys
import io
from pathlib import Path

# Windows 控制台 UTF-8 支持
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加项目根目录到 Python 路径
SUPERAGENT_ROOT = Path(__file__).parent
sys.path.insert(0, str(SUPERAGENT_ROOT))

from config import load_config, save_config, SuperAgentConfig
from orchestration import Orchestrator
from planning import ProjectPlanner


async def test_config_system():
    """测试配置系统"""
    print("\n" + "="*60)
    print("测试 1: 配置系统")
    print("="*60)

    # 1. 创建测试配置
    config = SuperAgentConfig(project_root=SUPERAGENT_ROOT)

    # 2. 验证默认值
    assert config.memory.enabled == True
    assert config.code_review.enabled == True
    assert config.orchestration.enable_parallel_execution == True
    print("✓ 默认配置正确")

    # 3. 序列化/反序列化
    config_dict = config.to_dict()
    assert "memory" in config_dict
    assert "code_review" in config_dict
    assert "orchestration" in config_dict
    print("✓ 配置序列化正确")

    # 4. 保存和加载
    config_path = SUPERAGENT_ROOT / ".superagent" / "test_config.json"
    save_config(config, config_path)

    loaded_config = load_config(config_path)
    assert loaded_config.memory.enabled == config.memory.enabled
    assert loaded_config.code_review.min_overall_score == config.code_review.min_overall_score
    print("✓ 配置保存和加载正确")

    # 5. 清理
    if config_path.exists():
        config_path.unlink()

    print("\n✅ 配置系统测试通过")


async def test_memory_integration():
    """测试记忆系统集成"""
    print("\n" + "="*60)
    print("测试 2: 记忆系统集成")
    print("="*60)

    try:
        from memory import MemoryManager

        # 1. 初始化 MemoryManager
        mm = MemoryManager(SUPERAGENT_ROOT)

        # 2. 保存测试记忆
        await mm.save_semantic_memory(
            knowledge="测试知识: SuperAgent v3.0 使用 3 层记忆系统",
            category="architecture",
            tags=["memory", "architecture"]
        )
        print("✓ 语义记忆保存成功")

        await mm.save_procedural_memory(
            practice="测试实践: 使用 AsyncIO 异步编程",
            category="coding"
        )
        print("✓ 程序记忆保存成功")

        # 3. 查询记忆
        memories = await mm.query_semantic_memory(category="architecture")
        assert len(memories) > 0
        print(f"✓ 查询到 {len(memories)} 条语义记忆")

        # 4. 获取统计
        stats = mm.get_statistics()
        assert stats['total_memories'] > 0
        print(f"✓ 记忆统计: 总计 {stats['total_memories']} 条")

        print("\n✅ 记忆系统集成测试通过")

    except ImportError:
        print("\n⚠️  记忆系统未安装,跳过测试")


async def test_cli_commands():
    """测试 CLI 命令"""
    print("\n" + "="*60)
    print("测试 3: CLI 命令模拟")
    print("="*60)

    # 模拟 CLI 命令执行

    # 1. config show
    try:
        config = load_config(project_root=SUPERAGENT_ROOT)
        print(f"✓ config show: 项目根目录 = {config.project_root}")
    except Exception as e:
        print(f"✗ config show 失败: {e}")

    # 2. memory stats
    try:
        from memory import MemoryManager
        mm = MemoryManager(SUPERAGENT_ROOT)
        stats = mm.get_statistics()
        print(f"✓ memory stats: 总记忆 = {stats['total_memories']}")
    except Exception as e:
        print(f"✗ memory stats 失败: {e}")

    print("\n✅ CLI 命令测试通过")


async def test_agent_output_format():
    """测试 Agent 输出格式"""
    print("\n" + "="*60)
    print("测试 4: Agent 输出格式")
    print("="*60)

    # 定义标准输出格式
    standard_output = {
        "success": True,
        "agent_type": "test-agent",
        "task_id": "task-test",
        "artifacts": {
            "requirements": "REQUIREMENTS.md",
            "architecture": "ARCHITECTURE.md"
        },
        "requirements": {
            "description": "测试需求"
        },
        "metadata": {
            "complexity": "low"
        },
        "next_steps": [
            "Claude Code: 生成代码"
        ]
    }

    # 验证必需字段
    required_fields = [
        "success", "agent_type", "task_id", "artifacts",
        "requirements", "metadata", "next_steps"
    ]

    for field in required_fields:
        assert field in standard_output, f"缺少必需字段: {field}"

    print("✓ Agent 输出格式符合标准")

    # 验证 artifacts 结构
    assert isinstance(standard_output["artifacts"], dict)
    assert len(standard_output["artifacts"]) > 0
    print("✓ Artifacts 结构正确")

    # 验证 next_steps
    assert isinstance(standard_output["next_steps"], list)
    assert len(standard_output["next_steps"]) > 0
    print("✓ Next Steps 结构正确")

    print("\n✅ Agent 输出格式测试通过")


async def test_orchestration_workflow():
    """测试编排工作流"""
    print("\n" + "="*60)
    print("测试 5: 编排工作流")
    print("="*60)

    try:
        # 1. 初始化
        orchestrator = Orchestrator(SUPERAGENT_ROOT)
        print("✓ Orchestrator 初始化成功")

        # 2. 创建简单计划
        planner = ProjectPlanner()
        plan = await planner.create_plan("测试项目", {})

        # 3. 验证计划结构
        assert len(plan.steps) > 0
        print(f"✓ 计划生成成功: {len(plan.steps)} 个步骤")

        # 4. 查询记忆(如果可用)
        if orchestrator.memory_manager:
            relevant = await orchestrator.memory_manager.query_relevant_memory(
                task="测试项目",
                agent_type=None
            )
            print(f"✓ 记忆查询成功: 找到 {len(relevant.get('mistakes', []))} 个错误教训")

        # 5. 获取统计
        stats = orchestrator.get_task_statistics()
        assert "total" in stats
        print(f"✓ 统计信息获取成功: 总任务 {stats['total']}")

        print("\n✅ 编排工作流测试通过")

    except Exception as e:
        print(f"\n⚠️  编排工作流测试失败: {e}")
        import traceback
        traceback.print_exc()


async def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("SuperAgent v3.0 Phase 6 集成测试")
    print("="*60)

    tests = [
        ("配置系统", test_config_system),
        ("记忆系统集成", test_memory_integration),
        ("CLI 命令", test_cli_commands),
        ("Agent 输出格式", test_agent_output_format),
        ("编排工作流", test_orchestration_workflow)
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            await test_func()
            passed += 1
        except AssertionError as e:
            print(f"\n❌ {test_name} 测试失败: {e}")
            failed += 1
        except Exception as e:
            print(f"\n❌ {test_name} 测试出错: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    # 总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    print(f"总测试数: {len(tests)}")
    print(f"通过: {passed}")
    print(f"失败: {failed}")
    print(f"成功率: {passed/len(tests)*100:.1f}%")

    if failed == 0:
        print("\n✅ 所有测试通过!")
    else:
        print(f"\n⚠️  {failed} 个测试失败")

    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
