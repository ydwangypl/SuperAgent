#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
安全验证模块

提供输入验证、路径验证、SQL 注入防护等安全功能。

v3.3 新增: 统一安全验证层
"""

import re
import os
from pathlib import Path
from typing import Optional, List, Union
from urllib.parse import urlparse

from common.exceptions import SecurityError

# 安全的白名单字符集（用于不同场景）
SAFE_PATH_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_/\\. "
)
SAFE_FILENAME_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_."
)
SAFE_COMMAND_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_/\\. "
)
# 允许的特殊字符（但不允许单独使用）
SAFE_SPECIAL_CHARS = frozenset("@$%^*()[]{}|+=:,.~` ")


class InputValidator:
    """输入验证器 - 提供统一的输入验证功能"""

    # 危险命令黑名单
    DANGEROUS_COMMANDS = frozenset([
        "rm", "del", "format", "mkfs", "dd", "shred", "chmod", "chown",
        "wget", "curl", "nc", "netcat", "ssh", "telnet", "ftp",
        "python", "perl", "ruby", "php", "java", "node",
        "eval", "exec", "system", "popen", "execve",
        "cat", "tail", "head", "less", "more",
    ])

    # 危险模式正则表达式
    DANGEROUS_PATTERNS = [
        r"[;|&`$]",  # 命令注入字符
        r"\.\./",    # 路径遍历
        r"^\s*/etc/",  # 尝试访问系统配置
        r"^\s*/proc/",  # 尝试访问进程信息
        r"^\s*/dev/",  # 尝试访问设备
        r"\\0",  # 空字节注入
        r"%00",  # URL 编码空字节
        r"{{.*}}",  # 模板注入
        r"\$\{.*\}",  # Shell 变量注入
        r"\#[0-9]+",  # Shell 历史命令
    ]

    @classmethod
    def sanitize_input(cls, user_input: str, allow_whitespace: bool = True) -> str:
        """清理用户输入，去除危险字符

        Args:
            user_input: 原始输入
            allow_whitespace: 是否允许空白字符

        Returns:
            清理后的安全输入
        """
        if not user_input:
            return ""

        result = []
        allowed_chars = SAFE_PATH_CHARS if allow_whitespace else SAFE_PATH_CHARS - frozenset(" ")

        for char in user_input:
            if char in allowed_chars:
                result.append(char)
            elif char == '\0':
                # 移除空字节
                continue
            else:
                # 对于未知字符，替换为下划线
                result.append('_')

        return ''.join(result)

    @classmethod
    def validate_path(cls, path: Union[str, Path], workspace_root: Path) -> Path:
        """验证路径是否在允许的工作区内（防止路径遍历攻击）

        Args:
            path: 要验证的路径
            workspace_root: 工作区根目录

        Returns:
            解析后的绝对路径

        Raises:
            SecurityError: 如果路径越界
        """
        if path is None:
            raise SecurityError("路径不能为空")

        # 转换为 Path 对象并解析
        try:
            input_path = Path(path).resolve()
            root_path = workspace_root.resolve()
        except (OSError, ValueError) as e:
            raise SecurityError(f"路径解析失败: {e}")

        # 检查是否在工作区内
        try:
            input_path.relative_to(root_path)
        except ValueError:
            raise SecurityError(
                f"路径越界: {path} 不在允许的工作区内 ({workspace_root})"
            )

        # 检查是否是符号链接并且指向工作区外
        if input_path.is_symlink():
            real_path = input_path.resolve()
            try:
                real_path.relative_to(root_path)
            except ValueError:
                raise SecurityError(
                    f"符号链接指向工作区外: {path}"
                )

        return input_path

    @classmethod
    def validate_filename(cls, filename: str, allow_extensions: Optional[List[str]] = None) -> str:
        """验证文件名（防止路径遍历和危险文件名）

        Args:
            filename: 文件名
            allow_extensions: 允许的文件扩展名列表（不含点）

        Returns:
            验证通过的文件名

        Raises:
            SecurityError: 如果文件名不合法
        """
        if not filename:
            raise SecurityError("文件名不能为空")

        # 检查文件名长度
        if len(filename) > 255:
            raise SecurityError("文件名过长")

        # 检查是否包含路径分隔符（防止路径遍历）
        if "/" in filename or "\\" in filename:
            raise SecurityError("文件名不能包含路径分隔符")

        # 检查所有字符是否安全
        for char in filename:
            if char not in SAFE_FILENAME_CHARS:
                raise SecurityError(f"文件名包含非法字符: {char}")

        # 检查扩展名
        if allow_extensions:
            ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
            if ext and ext not in [e.lower() for e in allow_extensions]:
                raise SecurityError(f"不支持的文件扩展名: .{ext}")

        return filename

    @classmethod
    def validate_command_args(cls, args: List[str]) -> List[str]:
        """验证命令参数（防止命令注入）

        Args:
            args: 命令参数列表

        Returns:
            验证后的参数列表

        Raises:
            SecurityError: 如果包含危险参数
        """
        validated = []
        for arg in args:
            if not isinstance(arg, str):
                raise SecurityError(f"参数类型错误: {type(arg)}")

            # 检查是否为空
            if not arg or not arg.strip():
                continue

            # 检查危险模式
            for pattern in cls.DANGEROUS_PATTERNS:
                if re.search(pattern, arg):
                    raise SecurityError(f"参数包含危险模式: {pattern}")

            # 检查是否以危险命令开头
            arg_parts = arg.strip().split()
            if arg_parts and arg_parts[0].lower() in cls.DANGEROUS_COMMANDS:
                # 排除一些安全的内置命令
                safe_commands = {"echo", "printf", "pwd", "ls", "cat", "date", "whoami"}
                if arg_parts[0].lower() not in safe_commands:
                    raise SecurityError(f"禁止使用危险命令: {arg_parts[0]}")

            validated.append(arg)

        return validated

    @classmethod
    def validate_url(cls, url: str, allowed_schemes: Optional[List[str]] = None) -> str:
        """验证 URL（防止 URL 注入和 SSRF 攻击）

        Args:
            url: 要验证的 URL
            allowed_schemes: 允许的协议（默认只允许 http/https）

        Returns:
            验证后的 URL

        Raises:
            SecurityError: 如果 URL 不合法
        """
        if not url:
            raise SecurityError("URL 不能为空")

        allowed_schemes = allowed_schemes or ["http", "https"]

        try:
            parsed = urlparse(url)
        except Exception as e:
            raise SecurityError(f"URL 解析失败: {e}")

        if parsed.scheme.lower() not in allowed_schemes:
            raise SecurityError(f"不支持的 URL 协议: {parsed.scheme}")

        # 检查是否是私有 IP（防止 SSRF）
        if parsed.hostname:
            private_patterns = [
                r"^127\.\d+\.\d+\.\d+$",  # Loopback
                r"^10\.\d+\.\d+\.\d+$",   # Private Class A
                r"^172\.(1[6-9]|2\d|3[01])\.\d+\.\d+$",  # Private Class B
                r"^192\.168\.\d+\.\d+$",  # Private Class C
                r"^::1$",  # IPv6 Loopback
                r"^fe80:",  # IPv6 Link-local
            ]
            for pattern in private_patterns:
                if re.match(pattern, parsed.hostname):
                    raise SecurityError(f"禁止访问私有 IP: {parsed.hostname}")

        return url

    @classmethod
    def sanitize_json_field(cls, field_value: str) -> str:
        """清理 JSON 字段值（防止 XSS 和注入）

        Args:
            field_value: 字段值

        Returns:
            清理后的值
        """
        if not field_value:
            return ""

        # 移除 HTML/JS 标签
        sanitized = re.sub(r"<[^>]*>", "", field_value)

        # 移除 JavaScript 事件处理程序
        sanitized = re.sub(r"on\w+\s*=", "", sanitized)

        # 移除 javascript: 协议
        sanitized = re.sub(r"javascript\s*:", "", sanitized)

        # 移除 data: URL（可能包含 base64 恶意代码）
        sanitized = re.sub(r"data\s*:\s*[^,]+", "", sanitized)

        # 转义 HTML 实体
        replacements = {
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#x27;",
        }
        for old, new in replacements.items():
            sanitized = sanitized.replace(old, new)

        return sanitized


class PathSanitizer:
    """路径清理器 - 提供安全的路径操作"""

    @classmethod
    def safe_join(cls, base_path: Path, relative_path: str) -> Path:
        """安全地拼接路径

        Args:
            base_path: 基础路径
            relative_path: 相对路径

        Returns:
            拼接后的安全路径
        """
        # 清理相对路径中的危险字符
        sanitized = InputValidator.sanitize_input(relative_path)

        # 验证拼接后的路径
        joined = (base_path / sanitized).resolve()

        # 确保在基础路径内
        if not str(joined).startswith(str(base_path.resolve())):
            raise SecurityError("路径拼接后越界")

        return joined

    @classmethod
    def normalize_path(cls, path: Union[str, Path]) -> Path:
        """标准化路径（移除冗余部分）

        Args:
            path: 原始路径

        Returns:
            标准化后的路径
        """
        path = Path(path)

        # 解析符号链接
        resolved = path.resolve()

        # 规范化（移除 . 和 ..）
        parts = []
        for part in resolved.parts:
            if part == "..":
                if parts and parts[-1] != "/":
                    parts.pop()
            elif part != ".":
                parts.append(part)

        if not parts:
            return Path("/")

        return Path(*parts)

    @classmethod
    def get_safe_relative_path(cls, workspace_root: Path, target_path: Path) -> Path:
        """获取目标路径相对于工作区的安全相对路径

        Args:
            workspace_root: 工作区根目录
            target_path: 目标路径

        Returns:
            相对路径
        """
        root_resolved = workspace_root.resolve()
        target_resolved = target_path.resolve()

        # 验证目标路径在工作区内
        InputValidator.validate_path(target_path, workspace_root)

        # 获取相对路径
        try:
            return target_resolved.relative_to(root_resolved)
        except ValueError:
            # 如果无法获取相对路径，返回绝对路径（已在上面验证过）
            return target_resolved
