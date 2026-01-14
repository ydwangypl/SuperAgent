#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
交互式选择组件
支持光标移动、回车选择、多选以及手动输入
"""

import sys
import os

# 获取按键的逻辑
if sys.platform == "win32":
    import msvcrt
    def getch():
        return msvcrt.getch()
else:
    import tty
    import termios
    def getch():
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch.encode()

def interactive_select(question, options, multiple=False, allow_manual=True):
    """
    交互式选择器
    
    Args:
        question: 问题描述
        options: 选项列表
        multiple: 是否允许多选
        allow_manual: 是否允许手动输入
        
    Returns:
        选择的结果 (字符串或列表)
    """
    selected_indices = set()
    cursor_index = 0
    
    # 增加一个"手动输入"选项
    display_options = list(options)
    if allow_manual:
        display_options.append("[ 手动输入... ]")
    
    def render():
        # 清除之前的输出 (简单起见，这里假设选项不多，直接打印)
        # 实际开发中可以使用 ANSI 逃逸序列来移动光标，这里为了兼容性使用重绘
        sys.stdout.write("\033[K") # 清除当前行
        print(f"\n\033[1;34m❓ {question}\033[0m")
        if multiple:
            print("\033[2m(使用方向键移动, 空格选择/取消, 回车确认)\033[0m")
        else:
            print("\033[2m(使用方向键移动, 回车选择)\033[0m")
            
        for i, opt in enumerate(display_options):
            prefix = " > " if i == cursor_index else "   "
            
            if multiple:
                if i < len(options): # 只有原选项有复选框
                    mark = "[x]" if i in selected_indices else "[ ]"
                    line = f"{prefix}{mark} {opt}"
                else: # 手动输入选项
                    line = f"{prefix}    {opt}"
            else:
                line = f"{prefix} {opt}"
                
            if i == cursor_index:
                print(f"\033[1;32m{line}\033[0m")
            else:
                print(line)
        
        # 移动光标回到底部，准备清除
        sys.stdout.write(f"\033[{len(display_options) + 3}A")
        sys.stdout.flush()

    while True:
        render()
        
        # 获取按键
        key = getch()
        
        # Windows 箭头键
        if key == b'\x00' or key == b'\xe0':
            key = getch()
            if key == b'H': # Up
                cursor_index = (cursor_index - 1) % len(display_options)
            elif key == b'P': # Down
                cursor_index = (cursor_index + 1) % len(display_options)
        # Unix 箭头键
        elif key == b'\x1b':
            key = getch()
            if key == b'[':
                key = getch()
                if key == b'A': # Up
                    cursor_index = (cursor_index - 1) % len(display_options)
                elif key == b'B': # Down
                    cursor_index = (cursor_index + 1) % len(display_options)
        
        # 空格键 (多选)
        elif key == b' ' and multiple:
            if cursor_index < len(options):
                if cursor_index in selected_indices:
                    selected_indices.remove(cursor_index)
                else:
                    selected_indices.add(cursor_index)
            else:
                # 选择了手动输入
                break
                
        # 回车键
        elif key == b'\r' or key == b'\n':
            # 如果是多选，且光标不在"手动输入"上，则返回已选项
            if multiple:
                if cursor_index == len(display_options) - 1 and allow_manual:
                    # 选择了手动输入
                    break
                if selected_indices:
                    # 清除重绘的行，移动光标到末尾
                    sys.stdout.write(f"\033[{len(display_options) + 3}B")
                    print("\n")
                    return [options[i] for i in sorted(list(selected_indices))]
                elif cursor_index < len(options):
                    # 如果没有勾选任何项，但按了回车，则选择当前项并返回
                    sys.stdout.write(f"\033[{len(display_options) + 3}B")
                    print("\n")
                    return [options[cursor_index]]
            else:
                # 单选模式
                if cursor_index == len(display_options) - 1 and allow_manual:
                    # 选择了手动输入
                    break
                else:
                    sys.stdout.write(f"\033[{len(display_options) + 3}B")
                    print("\n")
                    return options[cursor_index]
        
        # Ctrl+C
        elif key == b'\x03':
            sys.stdout.write(f"\033[{len(display_options) + 3}B")
            print("\n已取消")
            raise KeyboardInterrupt

    # 处理手动输入
    sys.stdout.write(f"\033[{len(display_options) + 3}B")
    print("\n")
    manual_val = input("\033[1;34m请输入您的回答: \033[0m")
    return manual_val

if __name__ == "__main__":
    # 测试代码
    try:
        res = interactive_select("选择技术栈", ["Python", "Node.js", "Java", "Go"], multiple=True)
        print(f"最终选择: {res}")
    except KeyboardInterrupt:
        pass
