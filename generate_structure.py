#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""生成项目结构树"""

from pathlib import Path
from typing import Set

# 排除的目录和文件
EXCLUDE_DIRS = {
    '__pycache__', '.git', '.superagent', 'backup', 'venv',
    'env', '.venv', 'dist', 'build', '*.egg-info', 'node_modules'
}

EXCLUDE_FILES = {
    '*.pyc', '*.pyo', '*.pyd', '*.so', '*.dylib', '*.dll',
    '*.log', '*.tmp', '.DS_Store', 'Thumbs.db'
}

def should_exclude(name: str, is_dir: bool) -> bool:
    """判断是否应该排除"""
    if is_dir:
        return name in EXCLUDE_DIRS or name.startswith('.')
    else:
        # 检查文件扩展名
        for pattern in EXCLUDE_FILES:
            if pattern.startswith('*'):
                if name.endswith(pattern[1:]):
                    return True
        return False

def generate_tree(path: Path, prefix: str = "", is_last: bool = True, max_depth: int = 10) -> str:
    """生成目录树"""
    if max_depth == 0:
        return ""

    result = []

    try:
        names = sorted([n for n in path.iterdir() if not should_exclude(n.name, n.is_dir())],
                      key=lambda x: (not x.is_dir(), x.name.lower()))
    except PermissionError:
        return ""

    # 统计目录和文件数量
    dirs = [n for n in names if n.is_dir()]
    files = [n for n in names if not n.is_dir()]

    for i, item in enumerate(names):
        is_last_item = i == len(names) - 1
        current_prefix = "└── " if is_last_item else "├── "
        item_prefix = "    " if is_last_item else "│   "

        # 添加文件/目录行
        line = prefix + current_prefix + item.name
        if item.is_dir():
            line += "/"
        result.append(line)

        # 如果是目录,递归处理
        if item.is_dir():
            result.append(generate_tree(
                item,
                prefix + item_prefix,
                is_last_item,
                max_depth - 1
            ))

    return "\n".join(result)

def get_stats(path: Path) -> dict:
    """获取项目统计信息"""
    stats = {
        'total_files': 0,
        'total_dirs': 0,
        'py_files': 0,
        'test_files': 0,
        'md_files': 0,
        'total_lines': 0
    }

    for item in path.rglob('*'):
        if should_exclude(item.name, item.is_dir()):
            continue

        if item.is_file():
            stats['total_files'] += 1

            if item.suffix == '.py':
                stats['py_files'] += 1
                if item.name.startswith('test_') or item.name.endswith('_test.py'):
                    stats['test_files'] += 1

                # 统计代码行数
                try:
                    with open(item, 'r', encoding='utf-8', errors='ignore') as f:
                        stats['total_lines'] += len(f.readlines())
                except:
                    pass

            elif item.suffix in ['.md', '.MD']:
                stats['md_files'] += 1

        elif item.is_dir():
            stats['total_dirs'] += 1

    return stats

def main():
    """主函数"""
    root = Path.cwd()

    # 标题
    print("=" * 80)
    print("SuperAgent v3.0 Project Structure Tree")
    print("=" * 80)
    print()

    # 项目根目录
    print(f"{root.name}/")
    print()

    # 生成目录树
    tree = generate_tree(root, max_depth=10)
    print(tree)
    print()

    # 统计信息
    print("=" * 80)
    print("Project Statistics")
    print("=" * 80)

    stats = get_stats(root)

    print(f"Total Directories: {stats['total_dirs']:,}")
    print(f"Total Files: {stats['total_files']:,}")
    print(f"Python Files: {stats['py_files']:,}")
    print(f"Test Files: {stats['test_files']:,}")
    print(f"Documentation Files: {stats['md_files']:,}")
    print(f"Total Lines of Code: {stats['total_lines']:,}")
    print()
    print("=" * 80)

if __name__ == "__main__":
    main()
