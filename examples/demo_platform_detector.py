# -*- coding: utf-8 -*-
"""
P2 功能演示 - 平台检测器

演示 PlatformDetector 的自动平台检测功能
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from platform_adapters.platform_detector import PlatformDetector, Platform


def demo_platform_detector():
    """演示平台检测器功能"""

    print("=" * 80)
    print("[P2 功能演示] 平台检测器")
    print("=" * 80)
    print()

    # 创建平台检测器
    detector = PlatformDetector()

    # 1. 检测当前平台
    print("[功能 1] 检测当前平台")
    print("-" * 80)
    detected_platform = detector.detect_platform()

    if detected_platform:
        print(f"[OK] 检测到平台: {detected_platform.value}")
        platform_info = detector.get_platform_info(detected_platform)
        print(f"  平台名称: {platform_info.get('name', 'Unknown')}")
        print(f"  公司: {platform_info.get('company', 'Unknown')}")
        print(f"  描述: {platform_info.get('description', 'No description')}")
        print(f"  特性:")
        for feature in platform_info.get('features', []):
            print(f"    - {feature}")
    else:
        print("[未检测] 无法自动检测平台")
    print()

    # 2. 列出所有支持的平台
    print("[功能 2] 所有支持的平台")
    print("-" * 80)
    for platform in Platform:
        info = detector.get_platform_info(platform)
        print(f"  平台: {platform.value}")
        print(f"    名称: {info.get('name', 'Unknown')}")
        print(f"    公司: {info.get('company', 'Unknown')}")
    print()

    # 3. 检查平台兼容性
    print("[功能 3] 平台兼容性检查")
    print("-" * 80)
    for platform in Platform:
        is_compatible = detector.is_compatible(platform)
        status_str = "兼容" if is_compatible else "不兼容"
        print(f"  {platform.value:20} -> [{status_str}]")
    print()

    # 4. 列出兼容的平台
    print("[功能 4] 当前兼容的平台列表")
    print("-" * 80)
    compatible_platforms = detector.list_compatible_platforms()
    print(f"[OK] 兼容平台数: {len(compatible_platforms)}")
    for platform in compatible_platforms:
        info = detector.get_platform_info(platform)
        print(f"  - {info.get('name', platform.value)}")
    print()

    # 5. 平台检测详情
    print("[功能 5] 平台检测详情")
    print("-" * 80)
    print("  检测方法:")
    print("    1. Claude Code:   ANTHROPIC_API_KEY, VS Code 集成")
    print("    2. OpenAI Codex:  OPENAI_API_KEY, openai 模块")
    print("    3. OpenCode:      .git 目录, LICENSE 文件")
    print()

    # 6. 环境检查
    print("[功能 6] 当前环境检查")
    print("-" * 80)
    env_checks = {
        "ANTHROPIC_API_KEY": "Claude Code",
        "OPENAI_API_KEY": "OpenAI Codex",
        "VSCODE_PID": "VS Code 环境",
        "CODE_PID": "VS Code 环境"
    }

    print("  环境变量检查:")
    for env_var, platform_name in env_checks.items():
        exists = env_var in os.environ
        status_str = "[+]" if exists else "[ ]"
        print(f"    {status_str} {env_var:20} ({platform_name})")
    print()

    # 7. 文件系统检查
    print("[功能 7] 文件系统检查")
    print("-" * 80)
    file_checks = {
        ".git": "Git 仓库",
        ".git/config": "Git 配置",
        "LICENSE": "许可证文件",
        "README.md": "README 文件"
    }

    print("  文件系统检查:")
    for file_path, description in file_checks.items():
        exists = os.path.exists(file_path)
        status_str = "[+]" if exists else "[ ]"
        print(f"    {status_str} {file_path:20} ({description})")
    print()

    print("=" * 80)
    print("[完成] 平台检测器演示完成!")
    print("=" * 80)
    print()

    return detected_platform


if __name__ == "__main__":
    demo_platform_detector()
