#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
UI 工具类 (DRY 优化)

统一管理控制台输出格式、装饰线和样式
"""

class UIUtils:
    """控制台 UI 工具类"""

    @staticmethod
    def print_separator(char: str = "=", length: int = 60, prefix: str = ""):
        """打印装饰线"""
        print(f"{prefix}{char * length}")

    @staticmethod
    def print_header(text: str, char: str = "=", length: int = 60):
        """打印带标题的装饰块"""
        UIUtils.print_separator(char, length, prefix="\n")
        print(f"  {text}")
        UIUtils.print_separator(char, length)

    @staticmethod
    def print_success(text: str):
        """打印成功消息"""
        print(f"✅ {text}")

    @staticmethod
    def print_error(text: str):
        """打印错误消息"""
        print(f"❌ {text}")

    @staticmethod
    def print_warning(text: str):
        """打印警告消息"""
        print(f"⚠️  {text}")

    @staticmethod
    def print_info(text: str):
        """打印提示消息"""
        print(f"💡 {text}")
