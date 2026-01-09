#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
配置管理命令行工具

用于管理 SuperAgent 配置
"""

import json
import sys
from pathlib import Path
from typing import Optional

# 添加项目根目录到 Python 路径
SUPERAGENT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(SUPERAGENT_ROOT))

from config.settings import (
    SuperAgentConfig,
    load_config,
    save_config,
    get_default_config_path
)


def cmd_config_show(args):
    """显示当前配置"""
    config_path = args.config if hasattr(args, 'config') and args.config else None
    config = load_config(config_path)

    print("\n" + "="*60)
    print("  SuperAgent v3.0 配置")
    print("="*60)

    print(f"\n项目根目录: {config.project_root}")
    print(f"配置文件: {config.project_root / '.superagent' / 'config.json'}")

    print("\n" + "-"*60)
    print("  记忆系统配置")
    print("-"*60)
    print(f"启用: {config.memory.enabled}")
    print(f"保留天数: {config.memory.retention_days if config.memory.retention_days > 0 else '永久'}")
    print(f"最大情节记忆: {config.memory.max_episodic_memories}")
    print(f"最大语义记忆: {config.memory.max_semantic_memories}")
    print(f"最大程序记忆: {config.memory.max_procedural_memories}")

    print("\n" + "-"*60)
    print("  代码审查配置")
    print("-"*60)
    print(f"启用: {config.code_review.enabled}")
    print(f"最低评分: {config.code_review.min_overall_score}")
    print(f"最多严重问题: {config.code_review.max_critical_issues}")
    print(f"风格检查: {config.code_review.enable_style_check}")
    print(f"安全检查: {config.code_review.enable_security_check}")
    print(f"性能检查: {config.code_review.enable_performance_check}")
    print(f"最佳实践: {config.code_review.enable_best_practices}")
    print(f"Ralph Wiggum: {config.code_review.enable_ralph_wiggum}")

    print("\n" + "-"*60)
    print("  编排配置")
    print("-"*60)
    print(f"并行执行: {config.orchestration.enable_parallel_execution}")
    print(f"最大并行任务: {config.orchestration.max_parallel_tasks}")
    print(f"Agent最大并发: {config.orchestration.max_concurrent_per_agent}")
    print(f"快速失败: {config.orchestration.enable_early_failure}")
    print(f"Git Worktree: {config.orchestration.enable_worktree}")
    print(f"Agent超时: {config.orchestration.agent_timeout_seconds}秒")
    print(f"Agent重试: {config.orchestration.agent_retry_count}次")

    print("\n" + "-"*60)
    print("  日志配置")
    print("-"*60)
    print(f"级别: {config.logging.level}")
    print(f"控制台输出: {config.logging.console_output}")
    print(f"文件输出: {config.logging.file_output}")
    if config.logging.file_output:
        print(f"日志文件: {config.logging.file_path or '.superagent/superagent.log'}")


def cmd_config_init(args):
    """初始化配置文件"""
    config_path = args.config if hasattr(args, 'config') and args.config else get_default_config_path()

    if config_path.exists():
        print(f"\n⚠️  配置文件已存在: {config_path}")
        confirm = input("是否覆盖? (yes/no): ")
        if confirm.lower() != 'yes':
            print("已取消")
            return

    # 创建默认配置
    config = SuperAgentConfig(project_root=Path.cwd())

    # 保存配置
    save_config(config, config_path)

    print(f"\n✓ 配置文件已创建: {config_path}")
    print("\n提示:")
    print("  - 使用 'config show' 查看配置")
    print("  - 使用 'config edit' 编辑配置")


def cmd_config_edit(args):
    """编辑配置"""
    config_path = args.config if hasattr(args, 'config') and args.config else get_default_config_path()

    if not config_path.exists():
        print(f"\n❌ 配置文件不存在: {config_path}")
        print("   使用 'config init' 创建配置文件")
        return

    # 加载配置
    config = load_config(config_path)

    print(f"\n正在编辑配置: {config_path}")
    print("\n可编辑的选项:")
    print("  1. memory.enabled")
    print("  2. memory.retention_days")
    print("  3. code_review.min_overall_score")
    print("  4. orchestration.max_parallel_tasks")
    print("  5. orchestration.enable_parallel_execution")
    print("  6. logging.level")

    try:
        key = input("\n输入选项键 (例如 memory.enabled): ").strip()
        value = input("输入新值: ").strip()

        # 解析键路径
        keys = key.split('.')
        if len(keys) != 2:
            print("❌ 无效的键格式")
            return

        section, attr = keys

        # 获取对应的配置对象
        config_map = {
            "memory": config.memory,
            "code_review": config.code_review,
            "orchestration": config.orchestration,
            "logging": config.logging
        }

        if section not in config_map:
            print(f"❌ 未知的配置节: {section}")
            return

        config_obj = config_map[section]

        if not hasattr(config_obj, attr):
            print(f"❌ 未知的配置项: {attr}")
            return

        # 类型转换
        current_value = getattr(config_obj, attr)
        if isinstance(current_value, bool):
            value = value.lower() in ('true', 'yes', '1', 'on')
        elif isinstance(current_value, int):
            value = int(value)
        elif isinstance(current_value, float):
            value = float(value)

        # 设置新值
        setattr(config_obj, attr, value)

        # 保存配置
        save_config(config, config_path)

        print(f"\n✓ 配置已更新: {key} = {value}")

    except KeyboardInterrupt:
        print("\n\n已取消")
    except Exception as e:
        print(f"\n❌ 编辑失败: {e}")


def cmd_config_export(args):
    """导出配置"""
    config_path = args.config if hasattr(args, 'config') and args.config else None
    config = load_config(config_path)

    output_path = args.output if hasattr(args, 'output') and args.output else "config_export.json"

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(config.to_dict(), f, ensure_ascii=False, indent=2)

    print(f"\n✓ 配置已导出到: {output_path}")


def main():
    """主入口"""
    import argparse

    parser = argparse.ArgumentParser(
        description="SuperAgent v3.0 配置管理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--config',
        type=str,
        help='配置文件路径'
    )

    subparsers = parser.add_subparsers(dest='command', help='子命令')

    # show 命令
    show_parser = subparsers.add_parser('show', help='显示当前配置')
    show_parser.set_defaults(func=cmd_config_show)

    # init 命令
    init_parser = subparsers.add_parser('init', help='初始化配置文件')
    init_parser.set_defaults(func=cmd_config_init)

    # edit 命令
    edit_parser = subparsers.add_parser('edit', help='编辑配置')
    edit_parser.set_defaults(func=cmd_config_edit)

    # export 命令
    export_parser = subparsers.add_parser('export', help='导出配置')
    export_parser.add_argument('--output', '-o', type=str, help='输出文件路径')
    export_parser.set_defaults(func=cmd_config_export)

    # 解析参数
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # 执行命令
    try:
        args.func(args)
    except Exception as e:
        print(f"\n❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
