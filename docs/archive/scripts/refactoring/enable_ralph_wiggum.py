#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自动启用 Ralph Wiggum 功能
"""

import sys
from pathlib import Path

def enable_ralph_wiggum():
    """启用 Ralph Wiggum 功能"""

    # SuperAgent 根目录
    if len(sys.argv) > 1:
        superagent_root = Path(sys.argv[1])
    else:
        superagent_root = Path(__file__).parent

    print("=" * 60)
    print("SuperAgent - Ralph Wiggum 启用工具")
    print("=" * 60)
    print(f"\nSuperAgent 目录: {superagent_root}")

    # 1. 修改 config/settings.py
    print("\n[1/2] 修改 config/settings.py...")
    settings_file = superagent_root / "config" / "settings.py"

    if not settings_file.exists():
        print(f"[ERROR] File not found: {settings_file}")
        return False

    try:
        content = settings_file.read_text(encoding='utf-8')

        # 检查是否已经修改
        if 'enable_ralph_wiggum: bool = True' in content:
            print("   [OK] Already enabled, skipped")
        else:
            # 替换配置
            content = content.replace(
                "enable_ralph_wiggum: bool = False",
                "enable_ralph_wiggum: bool = True"
            )

            settings_file.write_text(content, encoding='utf-8')
            print("   [OK] Modified: enable_ralph_wiggum: False -> True")

    except Exception as e:
        print(f"   ❌ 修改失败: {e}")
        return False

    # 2. 修改 orchestration/models.py
    print("\n[2/2] 修改 orchestration/models.py...")
    models_file = superagent_root / "orchestration" / "models.py"

    if not models_file.exists():
        print(f"❌ 文件不存在: {models_file}")
        return False

    try:
        content = models_file.read_text(encoding='utf-8')

        # 检查是否已经修改
        if 'enable_ralph_wiggum: bool = True  # 启用Ralph Wiggum迭代改进' in content:
            print("   [OK] Already enabled, skipped")
        else:
            # 替换配置
            content = content.replace(
                "enable_ralph_wiggum: bool = False  # 启用Ralph Wiggum迭代改进",
                "enable_ralph_wiggum: bool = True  # 启用Ralph Wiggum迭代改进"
            )

            models_file.write_text(content, encoding='utf-8')
            print("   [OK] Modified: enable_ralph_wiggum: False -> True")

    except Exception as e:
        print(f"   ❌ 修改失败: {e}")
        return False

    # 3. 总结
    print("\n" + "=" * 60)
    print("✅ Ralph Wiggum 已成功启用!")
    print("=" * 60)
    print("\n下次使用 SuperAgent 时会自动:")
    print("  1. 审查代码质量")
    print("  2. 如果不达标 (默认<70分) → 自动改进")
    print("  3. 重新审查")
    print("  4. 重复直到达标 (最多3次)")
    print("\n默认配置:")
    print("  - 最低质量要求: 70分")
    print("  - 最大迭代次数: 3次")
    print("  - 自动应用改进建议")
    print("\n如何自定义配置:")
    print("  查看: RALPH_WIGGUM_FIX.md")
    print("=" * 60)

    return True

if __name__ == "__main__":
    success = enable_ralph_wiggum()
    sys.exit(0 if success else 1)
