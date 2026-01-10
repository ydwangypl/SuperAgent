#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SuperAgent 交互式功能演示脚本
展示：单选、多选、手动输入兼容、跨平台按键处理
"""

import sys
import os
import time

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from utils.interactive import interactive_select

def run_demo():
    print("\033[1;36m" + "="*50)
    print("      SuperAgent 交互式功能演示 (CLI Demo)")
    print("="*50 + "\033[0m")
    
    try:
        # 1. 演示单选 (技术栈选择)
        print("\n\033[1;33m[场景 1: 单选测试]\033[0m")
        backend = interactive_select(
            "您希望使用哪种后端框架?",
            ["Python + FastAPI", "Node.js + Express", "Java + Spring Boot", "Go + Gin"],
            multiple=False
        )
        print(f"\n\033[1;32m✓ 已确认后端: {backend}\033[0m")
        time.sleep(0.5)

        # 2. 演示多选 (功能需求选择)
        print("\n\033[1;33m[场景 2: 多选测试]\033[0m")
        features = interactive_select(
            "请选择需要集成的功能 (多选):",
            ["用户注册/登录", "文章发布/管理", "评论系统", "Markdown 编辑器", "全文搜索", "RSS 订阅"],
            multiple=True
        )
        print(f"\n\033[1;32m✓ 已确认功能列表: {', '.join(features) if isinstance(features, list) else features}\033[0m")
        time.sleep(0.5)

        # 3. 演示手动输入兼容
        print("\n\033[1;33m[场景 3: 手动输入测试]\033[0m")
        database = interactive_select(
            "您有偏好的数据库吗?",
            ["SQLite (开发推荐)", "PostgreSQL (生产推荐)", "MongoDB"],
            multiple=False,
            allow_manual=True
        )
        print(f"\n\033[1;32m✓ 已确认数据库: {database}\033[0m")

        print("\n\033[1;36m" + "="*50)
        print("            演示结束，交互功能正常！")
        print("="*50 + "\033[0m")

    except KeyboardInterrupt:
        print("\n\n\033[1;31m⚠️  用户中断演示\033[0m")
    except Exception as e:
        print(f"\n\n\033[1;31m❌ 演示出错: {e}\033[0m")

if __name__ == "__main__":
    # 确保终端支持 ANSI 转义序列 (Windows 需要)
    if sys.platform == "win32":
        os.system('color')
    
    run_demo()
