#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Ralph Wiggum 修复验证脚本
验证 enable_ralph_wiggum 默认值是否已修改为 True
"""

import sys
from pathlib import Path

# 添加 SuperAgent 到路径
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 70)
print("Ralph Wiggum Fix Verification")
print("=" * 70)

# 测试 1: config/settings.py
print("\n[Test 1] config/settings.py - CodeReviewConfig")
try:
    from config.settings import CodeReviewConfig
    config = CodeReviewConfig()
    if config.enable_ralph_wiggum:
        print("[OK] enable_ralph_wiggum = True")
    else:
        print("[FAIL] enable_ralph_wiggum = False (should be True)")
        sys.exit(1)
except Exception as e:
    print(f"[ERROR] {e}")
    sys.exit(1)

# 测试 2: orchestration/models.py
print("\n[Test 2] orchestration/models.py - OrchestrationConfig")
try:
    from orchestration.models import OrchestrationConfig
    config = OrchestrationConfig()
    if config.enable_ralph_wiggum:
        print("[OK] enable_ralph_wiggum = True")
    else:
        print("[FAIL] enable_ralph_wiggum = False (should be True)")
        sys.exit(1)
except Exception as e:
    print(f"[ERROR] {e}")
    sys.exit(1)

# 测试 3: 检查默认迭代次数
print("\n[Test 3] Default max iterations")
try:
    from config.settings import CodeReviewConfig
    config = CodeReviewConfig()
    max_iter = config.ralph_wiggum_max_iterations
    print(f"[INFO] ralph_wiggum_max_iterations = {max_iter}")
    if 1 <= max_iter <= 10:
        print("[OK] Iterations in valid range (1-10)")
    else:
        print(f"[WARNING] Iterations {max_iter} outside recommended range (1-10)")
except Exception as e:
    print(f"[ERROR] {e}")
    sys.exit(1)

print("\n" + "=" * 70)
print("All tests passed!")
print("=" * 70)
print("\nSummary:")
print("  - config/settings.py: enable_ralph_wiggum = True [OK]")
print("  - orchestration/models.py: enable_ralph_wiggum = True [OK]")
print("  - Ralph Wiggum feature is now enabled by default [OK]")
print("\nFix completed successfully!")
