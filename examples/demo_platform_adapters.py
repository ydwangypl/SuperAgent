# -*- coding: utf-8 -*-
"""
P2 功能演示 - 平台适配器系统

演示平台适配器的完整功能:
- 自动平台检测
- 适配器创建和注册
- 工具执行
- 工具映射
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from platform_adapters import (
    PlatformDetector,
    AdapterFactory,
    ToolMapper,
    ClaudeCodeAdapter,
    OpenAICodexAdapter,
    OpenCodeAdapter,
    Platform
)


def demo_platform_detectors():
    """演示平台检测功能"""
    print("=" * 80)
    print("[P2 功能演示] 平台适配器系统")
    print("=" * 80)
    print()

    # 1. 自动平台检测
    print("[功能 1] 自动平台检测")
    print("-" * 80)
    detector = PlatformDetector()
    detected = detector.detect_platform()

    if detected:
        print(f"[OK] 检测到平台: {detected.value}")
        info = detector.get_platform_info(detected)
        print(f"  名称: {info.get('name')}")
        print(f"  公司: {info.get('company')}")
    else:
        print("[未检测] 无法检测平台")
    print()

    # 2. 适配器工厂
    print("[功能 2] 适配器工厂")
    print("-" * 80)
    supported = AdapterFactory.list_supported_platforms()
    print(f"[OK] 支持的平台数: {len(supported)}")
    for platform in supported:
        print(f"  - {platform.value}")
    print()

    # 3. 自动创建适配器
    print("[功能 3] 自动创建适配器")
    print("-" * 80)
    adapter = AdapterFactory.create_auto_adapter()

    if adapter:
        print(f"[OK] 成功创建适配器: {adapter.get_platform_name()}")
        print(f"  可用工具数: {len(adapter.get_available_tools())}")
        print(f"  平台可用: {adapter.is_available()}")
    else:
        print("[失败] 无法创建适配器")
    print()

    # 4. 手动创建适配器
    print("[功能 4] 手动创建适配器")
    print("-" * 80)

    # Claude Code 适配器
    claude_adapter = AdapterFactory.get_adapter(Platform.CLAUDE_CODE)
    if claude_adapter:
        print(f"[OK] Claude Code 适配器")
        print(f"  平台: {claude_adapter.get_platform_name()}")
        print(f"  工具数: {len(claude_adapter.get_available_tools())}")
        tools = claude_adapter.get_available_tools()
        for tool in tools[:3]:
            print(f"    - {tool.name}: {tool.description}")
    print()

    # OpenAI Codex 适配器
    openai_adapter = AdapterFactory.get_adapter(Platform.OPENAI_CODEX)
    if openai_adapter:
        print(f"[OK] OpenAI Codex 适配器")
        print(f"  平台: {openai_adapter.get_platform_name()}")
        print(f"  工具数: {len(openai_adapter.get_available_tools())}")
        tools = openai_adapter.get_available_tools()
        for tool in tools[:3]:
            print(f"    - {tool.name}: {tool.description}")
    print()

    # OpenCode 适配器
    opencode_adapter = AdapterFactory.get_adapter(Platform.OPENCODE)
    if opencode_adapter:
        print(f"[OK] OpenCode 适配器")
        print(f"  平台: {opencode_adapter.get_platform_name()}")
        print(f"  工具数: {len(opencode_adapter.get_available_tools())}")
        tools = opencode_adapter.get_available_tools()
        for tool in tools[:3]:
            print(f"    - {tool.name}: {tool.description}")
    print()

    # 5. 工具映射
    print("[功能 5] 工具映射")
    print("-" * 80)
    mapper = ToolMapper()

    # 映射示例
    tool_name = "read_file"
    source = "claude_code"
    target = "openai_codex"

    mapped_name = mapper.map_tool_name(tool_name, source, target)
    print(f"  工具名称映射:")
    print(f"    {source}.{tool_name} -> {target}.{mapped_name}")

    # 参数映射
    params = {"file_path": "test.py"}
    mapped_params = mapper.map_parameters(tool_name, params, source, target)
    print(f"  参数映射:")
    print(f"    源参数: {params}")
    print(f"    目标参数: {mapped_params}")
    print()

    # 6. 平台对比
    print("[功能 6] 平台对比")
    print("-" * 80)
    platforms = [
        (Platform.CLAUDE_CODE, claude_adapter),
        (Platform.OPENAI_CODEX, openai_adapter),
        (Platform.OPENCODE, opencode_adapter)
    ]

    print(f"{'平台':<15} {'可用性':<10} {'工具数':<10}")
    print("-" * 80)
    for platform, adapter in platforms:
        if adapter:
            available = "是" if adapter.is_available() else "否"
            tool_count = len(adapter.get_available_tools())
            print(f"{platform.value:<15} {available:<10} {tool_count:<10}")
    print()

    # 7. 工具名称对比
    print("[功能 7] 工具名称对比")
    print("-" * 80)
    print("  文件读取工具在不同平台的名称:")
    print(f"    Claude Code:    read_file")
    print(f"    OpenAI Codex:   read")
    print(f"    OpenCode:       read")
    print()
    print("  文件写入工具在不同平台的名称:")
    print(f"    Claude Code:    write_file")
    print(f"    OpenAI Codex:   write")
    print(f"    OpenCode:       write")
    print()

    # 8. 参数名称对比
    print("[功能 8] 参数名称对比")
    print("-" * 80)
    print("  read 工具的参数名称:")
    print(f"    Claude Code:    file_path")
    print(f"    OpenAI Codex:   file")
    print(f"    OpenCode:       path")
    print()

    print("  write 工具的参数名称:")
    print(f"    Claude Code:    file_path, content")
    print(f"    OpenAI Codex:   file, contents")
    print(f"    OpenCode:       path, data")
    print()

    # 9. 适配器特性
    print("[功能 9] 适配器特性")
    print("-" * 80)
    print("  Claude Code 特性:")
    print("    - VS Code 集成")
    print("    - Anthropic API 支持")
    print("    - 完整的文件操作")
    print("    - Bash 命令执行")
    print()

    print("  OpenAI Codex 特性:")
    print("    - OpenAI API 支持")
    print("    - 标准化工具接口")
    print("    - 代码补全优化")
    print()

    print("  OpenCode 特性:")
    print("    - 社区驱动")
    print("    - Git 集成")
    print("    - 开源项目友好")
    print("    - 默认平台")
    print()

    print("=" * 80)
    print("[完成] 平台适配器系统演示完成!")
    print("=" * 80)
    print()

    print("总结:")
    print("  [OK] 支持 3 个平台")
    print("  [OK] 自动平台检测")
    print("  [OK] 工具映射系统")
    print("  [OK] 统一接口")
    print("  [OK] 可扩展架构")
    print()


if __name__ == "__main__":
    demo_platform_detectors()
