#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
版本升级脚本: v3.1 → v3.1

升级原因:
- 完成 P0 核心基础设施 (TaskListManager, GitAutoCommitManager, SingleTaskMode)
- 63个测试通过 (100%)
- 添加了核心功能,但保持向后兼容性
"""

import re
from pathlib import Path

def update_version_in_file(file_path: Path, old_version: str, new_version: str):
    """更新文件中的版本号"""
    try:
        content = file_path.read_text(encoding='utf-8')
        new_content = content.replace(old_version, new_version)

        if new_content != content:
            file_path.write_text(new_content, encoding='utf-8')
            return True
        return False
    except Exception as e:
        print(f"  [ERROR] {file_path}: {e}")
        return False

def main():
    """主函数"""
    project_root = Path(__file__).parent.parent
    old_version = "v3.1"
    new_version = "v3.1"

    # 需要更新的文件模式
    patterns = [
        "*.md",
        "*.py",
        "*.txt",
    ]

    print(f"版本升级: {old_version} → {new_version}")
    print("=" * 70)

    updated_files = []
    skipped_files = []

    # 遍历所有文件
    for pattern in patterns:
        for file_path in project_root.rglob(pattern):
            # 跳过特定目录
            if any(skip in str(file_path) for skip in ['.git', '__pycache__', '.pytest', 'node_modules', 'tmp']):
                continue

            # 只更新包含旧版本的文件
            if old_version in file_path.read_text(encoding='utf-8', errors='ignore'):
                if update_version_in_file(file_path, old_version, new_version):
                    updated_files.append(file_path)
                    print(f"  [OK] {file_path.relative_to(project_root)}")
                else:
                    skipped_files.append(file_path)

    print("\n" + "=" * 70)
    print(f"升级完成!")
    print(f"  更新文件数: {len(updated_files)}")
    print(f"  跳过文件数: {len(skipped_files)}")
    print("\n下一步:")
    print("  1. 检查变更: git diff")
    print("  2. 提交更新: git commit -am 'chore: bump version to v3.1'")
    print("  3. 创建标签: git tag v3.1.0")

if __name__ == "__main__":
    main()
