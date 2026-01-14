#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SuperAgent 系统全自动验证脚本 (v3.2)
用于快速验证系统功能、代码质量和性能。
"""

import os
import sys
import argparse
import subprocess
import time
from pathlib import Path

# 颜色定义
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_step(msg):
    print(f"\n{Colors.HEADER}{Colors.BOLD}>>> {msg}{Colors.ENDC}")

def run_command(cmd, cwd=None):
    """运行 shell 命令并返回成功与否"""
    print(f"{Colors.OKCYAN}运行: {' '.join(cmd)}{Colors.ENDC}")
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=False,
            text=True
        )
        return result.returncode == 0
    except Exception as e:
        print(f"{Colors.FAIL}执行错误: {e}{Colors.ENDC}")
        return False

def verify_fast():
    """Fast 模式: 核心冒烟测试 + 代码风格检查"""
    print_step("执行 Fast 模式: 核心冒烟测试 + 代码风格检查")
    
    steps = [
        ("冒烟测试", ["python", "-m", "pytest", "tests/unit/test_single_task_mode.py", "tests/unit/test_task_list_manager.py", "-v"]),
        ("代码风格检查 (Flake8)", ["python", "-m", "flake8", "orchestration", "memory", "planning", "--max-line-length=100"]),
    ]
    
    return run_steps(steps)

def verify_full():
    """Full 模式: 所有单元测试 + 集成测试 + 覆盖率检查 + 静态分析"""
    print_step("执行 Full 模式: 全量验证")
    
    steps = [
        ("单元测试", ["python", "-m", "pytest", "tests/unit/", "-v", "--cov=.", "--cov-report=term"]),
        ("集成测试", ["python", "-m", "pytest", "tests/integration/", "-v"]),
        ("代码风格检查 (Flake8)", ["python", "-m", "flake8", "orchestration", "memory", "planning", "--max-line-length=100"]),
    ]
    
    return run_steps(steps)

def run_steps(steps):
    all_success = True
    for name, cmd in steps:
        print(f"\n正在进行: {name}")
        if not run_command(cmd):
            print(f"{Colors.FAIL}❌ {name} 失败{Colors.ENDC}")
            all_success = False
        else:
            print(f"{Colors.OKGREEN}✅ {name} 通过{Colors.ENDC}")
    return all_success

def main():
    parser = argparse.ArgumentParser(description="SuperAgent 系统验证工具 (v3.2)")
    parser.add_argument(
        "--mode", 
        choices=["fast", "full"], 
        default="fast",
        help="验证模式: fast-冒烟+lint, full-全量"
    )
    # 兼容旧的 --level 参数
    parser.add_argument("--level", type=int, choices=[1, 2, 3], help="兼容旧版级别 (1/2 -> fast, 3 -> full)")
    
    args = parser.parse_args()
    
    mode = args.mode
    if args.level:
        mode = "fast" if args.level <= 2 else "full"
    
    start_time = time.time()
    
    print(f"{Colors.BOLD}{Colors.OKBLUE}========================================")
    print(f"   SuperAgent v3.2 系统验证工具")
    print(f"   模式: {mode.upper()}")
    print(f"========================================{Colors.ENDC}")
    
    if mode == "fast":
        success = verify_fast()
    else:
        success = verify_full()
        
    duration = time.time() - start_time
    
    print(f"\n{Colors.BOLD}========================================")
    if success:
        print(f"{Colors.OKGREEN}🎉 验证通过! 耗时: {duration:.2f}s{Colors.ENDC}")
    else:
        print(f"{Colors.FAIL}❌ 验证失败! 耗时: {duration:.2f}s{Colors.ENDC}")
    print(f"{Colors.BOLD}========================================{Colors.ENDC}")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
