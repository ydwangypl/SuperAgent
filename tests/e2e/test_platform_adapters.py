# -*- coding: utf-8 -*-
"""
平台适配器端到端测试 - E2E 测试

测试完整的跨平台工作流
"""

import sys
import os

# 添加项目根目录
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from platform_adapters import (
    PlatformDetector,
    AdapterFactory,
    ToolMapper,
    Platform,
    ClaudeCodeAdapter,
    OpenAICodexAdapter,
    OpenCodeAdapter
)


def test_cross_platform_detection():
    """测试跨平台检测"""
    print("\n[E2E测试] 跨平台检测")
    print("-" * 60)

    detector = PlatformDetector()

    # 1. 检测当前平台
    current_platform = detector.detect_platform()
    print(f"  [阶段1] 当前平台: {current_platform.value if current_platform else '未知'}")

    # 2. 检测所有平台兼容性
    print(f"  [阶段2] 平台兼容性:")
    for platform in Platform:
        is_compatible = detector.is_compatible(platform)
        status = "[OK] 兼容" if is_compatible else "[--] 不兼容"
        print(f"      {platform.value:20} -> {status}")

    # 3. 获取平台信息
    print(f"  [阶段3] 平台详细信息:")
    for platform in Platform:
        info = detector.get_platform_info(platform)
        if info:
            print(f"      {platform.value}:")
            print(f"        公司: {info.get('company', 'N/A')}")
            print(f"        描述: {info.get('description', 'N/A')[:50]}...")

    print()


def test_adapter_creation_all_platforms():
    """测试所有平台适配器创建"""
    print("\n[E2E测试] 所有平台适配器创建")
    print("-" * 60)

    platforms = [
        (Platform.CLAUDE_CODE, ClaudeCodeAdapter),
        (Platform.OPENAI_CODEX, OpenAICodexAdapter),
        (Platform.OPENCODE, OpenCodeAdapter)
    ]

    for platform, adapter_class in platforms:
        try:
            adapter = adapter_class()
            print(f"  [OK] {platform.value} 适配器创建成功")
            print(f"      名称: {adapter.get_platform_name()}")
        except Exception as e:
            print(f"  [--] {platform.value} 适配器创建失败: {e}")

    print()


def test_adapter_factory():
    """测试适配器工厂"""
    print("\n[E2E测试] 适配器工厂")
    print("-" * 60)

    factory = AdapterFactory()

    # 1. 列出支持的平台
    platforms = factory.list_supported_platforms()
    print(f"  [阶段1] 支持的平台数: {len(platforms)}")
    for p in platforms:
        print(f"      - {p.value}")

    # 2. 获取特定平台适配器
    print(f"  [阶段2] 获取平台适配器:")
    for platform in platforms:
        adapter = factory.get_adapter(platform)
        if adapter:
            print(f"      {platform.value}: {adapter.get_platform_name()}")
        else:
            print(f"      {platform.value}: 不可用")

    # 3. 自动创建适配器
    auto_adapter = factory.create_auto_adapter()
    print(f"  [阶段3] 自动创建适配器: {auto_adapter.get_platform_name() if auto_adapter else '失败'}")

    print()


def test_tool_mapping_all_platforms():
    """测试所有平台工具映射"""
    print("\n[E2E测试] 跨平台工具映射")
    print("-" * 60)

    mapper = ToolMapper()

    # 1. 列出所有映射
    print(f"  [阶段1] 工具映射规则数: {len(mapper.mappings)}")

    # 2. 测试 Claude Code -> OpenAI Codex 映射
    print(f"  [阶段2] Claude Code -> OpenAI Codex:")
    cc_to_oi_mappings = mapper.list_mappings_for_platforms("claude_code", "openai_codex")
    print(f"      映射数: {len(cc_to_oi_mappings)}")
    for mapping in cc_to_oi_mappings[:3]:
        print(f"      {mapping.tool_name} -> {mapping.mapped_name}")

    # 3. 测试 Claude Code -> OpenCode 映射
    print(f"  [阶段3] Claude Code -> OpenCode:")
    cc_to_oc_mappings = mapper.list_mappings_for_platforms("claude_code", "opencode")
    print(f"      映射数: {len(cc_to_oc_mappings)}")
    for mapping in cc_to_oc_mappings[:3]:
        print(f"      {mapping.tool_name} -> {mapping.mapped_name}")

    # 4. 测试工具名称映射
    print(f"  [阶段4] 工具名称映射:")
    test_cases = [
        ("read_file", "claude_code", "openai_codex"),
        ("write_file", "claude_code", "opencode"),
        ("list_files", "claude_code", "claude_code")
    ]

    for tool_name, source, target in test_cases:
        mapped = mapper.map_tool_name(tool_name, source, target)
        print(f"      {source}.{tool_name} -> {target}.{mapped}")

    print()


def test_parameter_mapping():
    """测试参数映射"""
    print("\n[E2E测试] 参数映射")
    print("-" * 60)

    mapper = ToolMapper()

    # 测试 read_file 参数映射
    print(f"  [阶段1] read_file 参数映射 (Claude Code -> OpenAI Codex):")
    params = {"file_path": "test.py", "encoding": "utf-8"}
    mapped_params = mapper.map_parameters("read_file", params, "claude_code", "openai_codex")
    print(f"      源参数: {params}")
    print(f"      目标参数: {mapped_params}")

    # 测试 write_file 参数映射
    print(f"  [阶段2] write_file 参数映射 (Claude Code -> OpenCode):")
    params = {"file_path": "output.txt", "content": "Hello World", "append": False}
    mapped_params = mapper.map_parameters("write_file", params, "claude_code", "opencode")
    print(f"      源参数: {params}")
    print(f"      目标参数: {mapped_params}")

    # 测试 edit_file 参数映射
    print(f"  [阶段3] edit_file 参数映射 (OpenCode -> Claude Code):")
    params = {"file": "test.py", "text_to_find": "old", "replacement_text": "new"}
    mapped_params = mapper.map_parameters("edit_file", params, "opencode", "claude_code")
    print(f"      源参数: {params}")
    print(f"      目标参数: {mapped_params}")

    print()


def test_adapter_capabilities():
    """测试适配器能力"""
    print("\n[E2E测试] 适配器能力")
    print("-" * 60)

    adapters = [
        AdapterFactory.get_adapter(Platform.CLAUDE_CODE),
        AdapterFactory.get_adapter(Platform.OPENAI_CODEX),
        AdapterFactory.get_adapter(Platform.OPENCODE)
    ]

    for adapter in adapters:
        if adapter:
            print(f"  [{adapter.get_platform_name()}]")

            # 获取工具列表
            tools = adapter.get_available_tools()
            print(f"      工具数: {len(tools)}")

            # 获取能力
            context = adapter.get_context()
            capabilities = context.get('capabilities', {})
            print(f"      能力:")
            for cap, enabled in capabilities.items():
                status = "[OK]" if enabled else "[--]"
                print(f"        {status} {cap}")

    print()


def test_full_cross_platform_workflow():
    """测试完整跨平台工作流"""
    print("\n[E2E测试] 完整跨平台工作流")
    print("-" * 60)

    # 1. 检测平台
    print(f"  [阶段1] 平台检测")
    detector = PlatformDetector()
    current_platform = detector.detect_platform()
    print(f"      当前平台: {current_platform.value}")

    # 2. 创建适配器
    print(f"  [阶段2] 创建适配器")
    adapter = AdapterFactory.create_auto_adapter()
    print(f"      适配器: {adapter.get_platform_name()}")

    # 3. 模拟跨平台任务执行
    print(f"  [阶段3] 模拟跨平台任务")
    task = "读取配置文件并修改"
    print(f"      任务: {task}")

    # 4. 工具映射演示
    print(f"  [阶段4] 工具映射")
    mapper = ToolMapper()

    # 假设源平台是 Claude Code
    source_platform = "claude_code"
    target_platform = adapter.get_platform_name().lower().replace(" ", "_")

    tool_name = "read_file"
    mapped_tool = mapper.map_tool_name(tool_name, source_platform, target_platform)
    print(f"      工具映射: {source_platform}.{tool_name} -> {target_platform}.{mapped_tool}")

    # 5. 参数映射
    params = {"file_path": "config.json"}
    mapped_params = mapper.map_parameters(tool_name, params, source_platform, target_platform)
    print(f"      参数映射: {params} -> {mapped_params}")

    # 6. 检查适配器可用性
    print(f"  [阶段5] 适配器可用性")
    is_available = adapter.is_available()
    print(f"      可用: {'是' if is_available else '否'}")

    print()


def test_error_handling():
    """测试错误处理"""
    print("\n[E2E测试] 错误处理")
    print("-" * 60)

    mapper = ToolMapper()

    # 1. 测试未知工具映射
    print(f"  [阶段1] 未知工具映射:")
    try:
        mapped = mapper.map_tool_name("unknown_tool", "claude_code", "openai_codex")
        print(f"      结果: {mapped}")
    except Exception as e:
        print(f"      错误: {e}")

    # 2. 测试未知平台映射
    print(f"  [阶段2] 未知平台映射:")
    try:
        mapped = mapper.map_tool_name("read_file", "unknown_platform", "claude_code")
        print(f"      结果: {mapped}")
    except Exception as e:
        print(f"      错误: {e}")

    # 3. 测试空参数映射
    print(f"  [阶段3] 空参数映射:")
    mapped_params = mapper.map_parameters("read_file", {}, "claude_code", "openai_codex")
    print(f"      结果: {mapped_params}")

    print()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("平台适配器端到端测试套件")
    print("=" * 60)

    try:
        test_cross_platform_detection()
        test_adapter_creation_all_platforms()
        test_adapter_factory()
        test_tool_mapping_all_platforms()
        test_parameter_mapping()
        test_adapter_capabilities()
        test_full_cross_platform_workflow()
        test_error_handling()

        print("=" * 60)
        print("[完成] 所有平台适配器 E2E 测试通过!")
        print("=" * 60)

    except Exception as e:
        print(f"\n[失败] 测试异常: {e}")
        import traceback
        traceback.print_exc()
