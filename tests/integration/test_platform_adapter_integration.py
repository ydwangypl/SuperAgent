# -*- coding: utf-8 -*-
"""
平台适配器集成测试 - P2 Task 3.1

演示平台适配器如何集成到实际应用中
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from platform_adapters import (
    PlatformDetector,
    AdapterFactory,
    ToolMapper,
    Platform
)


def test_platform_detection_integration():
    """测试平台检测集成"""
    print("=" * 80)
    print("[集成测试] 平台检测")
    print("=" * 80)
    print()

    # 1. 自动检测平台
    detector = PlatformDetector()
    platform = detector.detect_platform()

    print(f"[步骤 1] 自动检测平台")
    print(f"  检测结果: {platform.value if platform else 'None'}")
    print()

    # 2. 验证平台信息
    if platform:
        info = detector.get_platform_info(platform)
        print(f"[步骤 2] 平台信息")
        print(f"  名称: {info.get('name')}")
        print(f"  公司: {info.get('company')}")
        print(f"  描述: {info.get('description')}")
        print()

    # 3. 检查兼容性
    print(f"[步骤 3] 平台兼容性")
    for p in Platform:
        is_compatible = detector.is_compatible(p)
        status = "兼容" if is_compatible else "不兼容"
        print(f"  {p.value:20} -> {status}")
    print()

    return platform


def test_adapter_integration():
    """测试适配器集成"""
    print("=" * 80)
    print("[集成测试] 适配器使用")
    print("=" * 80)
    print()

    # 1. 自动创建适配器
    print(f"[步骤 1] 自动创建适配器")
    adapter = AdapterFactory.create_auto_adapter()

    if not adapter:
        print("  [失败] 无法创建适配器")
        return None

    print(f"  [成功] 创建适配器: {adapter.get_platform_name()}")
    print()

    # 2. 获取可用工具
    print(f"[步骤 2] 获取可用工具")
    tools = adapter.get_available_tools()
    print(f"  工具数量: {len(tools)}")

    for tool in tools[:5]:
        print(f"    - {tool.name:20} {tool.description}")
    print()

    # 3. 获取平台上下文
    print(f"[步骤 3] 获取平台上下文")
    context = adapter.get_context()
    print(f"  平台: {context.get('platform')}")
    print(f"  工作目录: {context.get('workspace')}")
    print(f"  能力: {list(context.get('capabilities', {}).keys())}")
    print()

    # 4. 检查可用性
    print(f"[步骤 4] 检查平台可用性")
    is_available = adapter.is_available()
    print(f"  可用: {'是' if is_available else '否'}")
    print()

    return adapter


def test_tool_mapper_integration():
    """测试工具映射器集成"""
    print("=" * 80)
    print("[集成测试] 工具映射")
    print("=" * 80)
    print()

    mapper = ToolMapper()

    # 1. 工具名称映射
    print(f"[步骤 1] 工具名称映射")
    tool_name = "read_file"
    source = "claude_code"
    target = "openai_codex"

    mapped_name = mapper.map_tool_name(tool_name, source, target)
    print(f"  {source}.{tool_name} -> {target}.{mapped_name}")
    print()

    # 2. 参数映射
    print(f"[步骤 2] 参数映射")
    params = {"file_path": "test.py", "content": "print('hello')"}
    mapped_params = mapper.map_parameters("write_file", params, source, target)
    print(f"  源参数: {params}")
    print(f"  目标参数: {mapped_params}")
    print()

    # 3. 双向映射
    print(f"[步骤 3] 双向映射测试")
    round_trip = mapper.map_tool_name(mapped_name, target, source)
    print(f"  {source}.{tool_name} -> {target}.{mapped_name} -> {source}.{round_trip}")
    print()

    # 4. 跨平台映射
    print(f"[步骤 4] 跨平台映射 (Claude Code -> OpenCode)")
    opencode_mapped = mapper.map_tool_name("read_file", "claude_code", "opencode")
    print(f"  claude_code.read_file -> opencode.{opencode_mapped}")
    print()


def test_end_to_end_workflow():
    """端到端工作流测试"""
    print("=" * 80)
    print("[集成测试] 端到端工作流")
    print("=" * 80)
    print()

    # 1. 检测平台
    print(f"[阶段 1] 检测运行平台")
    platform = PlatformDetector().detect_platform()
    print(f"  当前平台: {platform.value if platform else '未知'}")
    print()

    # 2. 创建适配器
    print(f"[阶段 2] 创建平台适配器")
    adapter = AdapterFactory.create_auto_adapter()
    if not adapter:
        print("  [失败] 无法创建适配器")
        return

    print(f"  适配器: {adapter.get_platform_name()}")
    print()

    # 3. 获取工具列表
    print(f"[阶段 3] 获取可用工具")
    tools = adapter.get_available_tools()
    print(f"  可用工具数: {len(tools)}")
    for tool in tools[:3]:
        print(f"    - {tool.name}")
    print()

    # 4. 模拟工具执行准备
    print(f"[阶段 4] 准备工具执行")
    tool_name = "read_file"
    params = {"file_path": "README.md"}

    print(f"  工具: {tool_name}")
    print(f"  参数: {params}")
    print()

    # 5. 跨平台转换 (如果需要)
    if platform != Platform.CLAUDE_CODE:
        print(f"[阶段 5] 跨平台工具转换")
        mapper = ToolMapper()

        # 转换工具名称
        mapped_tool = mapper.map_tool_name(
            tool_name,
            "claude_code",
            platform.value
        )
        print(f"  工具映射: {tool_name} -> {mapped_tool}")

        # 转换参数
        mapped_params = mapper.map_parameters(
            tool_name,
            params,
            "claude_code",
            platform.value
        )
        print(f"  参数映射: {params}")
        print(f"          -> {mapped_params}")
        print()

    print(f"[完成] 端到端工作流测试完成!")
    print()


def test_integration_statistics():
    """集成统计测试"""
    print("=" * 80)
    print("[集成测试] 统计信息")
    print("=" * 80)
    print()

    # 1. 支持的平台数量
    platforms = AdapterFactory.list_supported_platforms()
    print(f"[统计 1] 支持的平台数")
    print(f"  总数: {len(platforms)}")
    for p in platforms:
        print(f"    - {p.value}")
    print()

    # 2. 工具映射数量
    mapper = ToolMapper()
    mappings_cc_oi = mapper.list_mappings_for_platforms("claude_code", "openai_codex")
    mappings_cc_oc = mapper.list_mappings_for_platforms("claude_code", "opencode")

    print(f"[统计 2] 工具映射数量")
    print(f"  Claude Code -> OpenAI Codex: {len(mappings_cc_oi)} 个映射")
    print(f"  Claude Code -> OpenCode:      {len(mappings_cc_oc)} 个映射")
    print()

    # 3. 各平台工具数量
    print(f"[统计 3] 各平台工具数量")
    for platform in platforms:
        adapter = AdapterFactory.get_adapter(platform)
        if adapter:
            tools = adapter.get_available_tools()
            print(f"  {platform.value:20} {len(tools)} 个工具")
    print()

    # 4. 可用平台
    print(f"[统计 4] 平台可用性")
    detector = PlatformDetector()
    for platform in platforms:
        is_compatible = detector.is_compatible(platform)
        adapter = AdapterFactory.get_adapter(platform)
        is_available = adapter.is_available() if adapter else False

        status = "可用" if is_available else "不可用"
        compatible = "兼容" if is_compatible else "不兼容"
        print(f"  {platform.value:20} {status:10} ({compatible})")
    print()


if __name__ == "__main__":
    print()
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 20 + "平台适配器集成测试套件" + " " * 34 + "║")
    print("╚" + "═" * 78 + "╝")
    print()

    # 运行所有集成测试
    try:
        test_platform_detection_integration()
        test_adapter_integration()
        test_tool_mapper_integration()
        test_end_to_end_workflow()
        test_integration_statistics()

        print("=" * 80)
        print("[完成] 所有集成测试完成!")
        print("=" * 80)
        print()

    except Exception as e:
        print(f"[错误] 测试失败: {e}")
        import traceback
        traceback.print_exc()
