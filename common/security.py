#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
安全工具类

提供输入清理、路径验证和敏感数据检查等功能
"""

import re
from pathlib import Path
from typing import List, Optional, Union


from .exceptions import SecurityError


def sanitize_input(text: str) -> str:
    """
    清理用户输入，防止基本的注入攻击。
    
    Args:
        text: 原始文本
        
    Returns:
        str: 清理后的文本
    """
    return SecurityValidator.sanitize_input(text)


class SecureLogger:
    """
    安全的日志记录器,提供脱敏和安全异常记录功能
    """
    
    # 敏感信息模式
    SENSITIVE_PATTERNS = [
        # Email
        re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
        # API Keys / Tokens (常见的 32-64 位 16 进制或 Base64 字符串)
        re.compile(r'\b(api[_-]?key|apikey|secret|token|password|auth)\b\s*[:=]\s*[\'"]?[A-Za-z0-9_\-]{16,}[\'"]?', re.IGNORECASE),
        # 可能是路径敏感信息 (Windows 用户名)
        re.compile(r'([Cc]:\\Users\\)([a-zA-Z0-9_\-]+)', re.IGNORECASE),
    ]

    @classmethod
    def sanitize(cls, message: str) -> str:
        """清理日志消息中的敏感信息"""
        if not isinstance(message, str):
            message = str(message)
            
        for pattern in cls.SENSITIVE_PATTERNS:
            # 对于 API Key 等，保留前缀，替换值为 [REDACTED]
            if "api" in pattern.pattern.lower() or "secret" in pattern.pattern.lower():
                message = pattern.sub(r'\1: [REDACTED]', message)
            elif "Users" in pattern.pattern:
                message = pattern.sub(r'\1[USER]', message)
            else:
                message = pattern.sub('[REDACTED]', message)
                
        return message

    @classmethod
    def error(cls, logger, message: str, *args, **kwargs):
        """安全地记录错误日志"""
        safe_msg = cls.sanitize(message)
        logger.error(safe_msg, *args, **kwargs)

    @classmethod
    def warning(cls, logger, message: str, *args, **kwargs):
        """安全地记录警告日志"""
        safe_msg = cls.sanitize(message)
        logger.warning(safe_msg, *args, **kwargs)

    @classmethod
    def info(cls, logger, message: str, *args, **kwargs):
        """安全地记录信息日志"""
        safe_msg = cls.sanitize(message)
        logger.info(safe_msg, *args, **kwargs)


def validate_git_ref(ref: str) -> str:
    """
    验证Git引用名称(分支、标签等)是否符合规范,防止注入
    
    Args:
        ref: Git引用名称
        
    Returns:
        str: 验证后的引用名称
        
    Raises:
        SecurityError: 如果名称包含非法字符
    """
    return SecurityValidator.validate_git_ref(ref)


def validate_path(path: Union[str, Path], base_dir: Union[str, Path]) -> Path:
    """
    增强的路径验证,防止所有类型的路径穿越攻击 (包括符号链接绕过)

    Args:
        path: 要验证的路径
        base_dir: 允许的基础目录

    Returns:
        Path: 解析后的安全路径

    Raises:
        SecurityError: 如果检测到目录穿越、路径无效或恶意符号链接
    """
    return SecurityValidator.validate_path(path, base_dir)


class SecurityValidator:
    """
    安全验证器 - 提供完整的安全验证功能

    Usage Examples:
        >>> from pathlib import Path
        >>> from common.security import SecurityValidator
        >>> base = Path("E:/SuperAgent")
        >>> # 验证路径
        >>> safe_path = SecurityValidator.validate_path(Path("common/security.py"), base)
        >>> # 清理输入
        >>> clean_text = SecurityValidator.sanitize_input("<script>alert(1)</script>hello")
        >>> print(clean_text)  # 输出: hello
        >>> # 验证 Git 引用
        >>> branch = SecurityValidator.validate_git_ref("feature/security-fix")
    """

    @staticmethod
    def validate_path(path: Union[str, Path], base_dir: Union[str, Path]) -> Path:
        """
        增强的路径验证,防止所有类型的路径穿越攻击 (包括符号链接绕过)

        Args:
            path: 要验证的路径
            base_dir: 允许的基础目录

        Returns:
            Path: 解析后的安全路径

        Raises:
            SecurityError: 如果检测到目录穿越、路径无效或恶意符号链接

        Example:
            >>> base = Path("/app/data")
            >>> SecurityValidator.validate_path(Path("user/profile.json"), base)
            Path("/app/data/user/profile.json")
            >>> SecurityValidator.validate_path(Path("../../etc/passwd"), base)
            SecurityError: 路径穿越检测...
        """
        import os
        
        # 确保是 Path 对象
        path = Path(path)
        base_dir = Path(base_dir)

        try:
            # 检查非法字符 (例如零字节)
            if '\0' in str(path):
                raise SecurityError(f"路径包含非法字符: {path}")

            # 1. 基础目录必须存在且是目录
            if not base_dir.exists() or not base_dir.is_dir():
                raise SecurityError(f"基础目录无效: {base_dir}")

            # 2. 解析基础目录 (处理符号链接)
            resolved_base = base_dir.resolve(strict=True)

            # 3. 构造完整路径并初步解析
            if path.is_absolute():
                resolved_path = path.resolve()
            else:
                # 使用 / 运算符连接，然后 resolve。strict=False 因为文件可能还不存在
                resolved_path = (resolved_base / path).resolve(strict=False)

            # 4. 使用 commonpath 检查路径是否在基础目录内 (处理 Windows 驱动器差异)
            try:
                # os.path.commonpath 需要字符串
                common = os.path.commonpath([str(resolved_base), str(resolved_path)])
                if common != str(resolved_base):
                    raise SecurityError(
                        f"路径穿越检测: {path} -> {resolved_path} 超出基础目录 {resolved_base}"
                    )
            except ValueError:
                # 不同驱动器上的路径 (Windows)
                raise SecurityError(f"路径跨越驱动器: {path}")

            # 5. 检查路径中的每一级是否存在指向外部的符号链接
            current = resolved_path
            # 向上追溯直到到达 base_dir 或根目录
            while current != resolved_base and current != current.parent:
                if current.exists() and current.is_symlink():
                    # 读取链接指向的实际位置
                    link_target = Path(os.readlink(current))
                    # 如果链接是相对的，则相对于当前目录解析它
                    if not link_target.is_absolute():
                        link_target = (current.parent / link_target).resolve()
                    else:
                        link_target = link_target.resolve()
                    
                    # 检查链接目标是否仍在 base_dir 内
                    try:
                        if not link_target.is_relative_to(resolved_base):
                            raise SecurityError(f"检测到恶意符号链接: {current} 指向 {link_target}")
                    except AttributeError:
                        if resolved_base not in link_target.parents and link_target != resolved_base:
                            raise SecurityError(f"检测到恶意符号链接: {current} 指向 {link_target}")
                
                current = current.parent

            # 6. 最终 is_relative_to 验证 (双重保障)
            try:
                if not resolved_path.is_relative_to(resolved_base):
                    raise SecurityError(f"路径不在允许范围内: {resolved_path}")
            except AttributeError:
                # 兼容旧版本 Python
                if resolved_base not in resolved_path.parents and resolved_path != resolved_base:
                    raise SecurityError(f"路径不在允许范围内: {resolved_path}")

            return resolved_path

        except (ValueError, RuntimeError, OSError) as e:
            if isinstance(e, SecurityError):
                raise
            raise SecurityError(f"路径验证系统错误: {e}")

    @staticmethod
    def sanitize_input(text: str) -> str:
        """
        清理用户输入，防止基本的注入攻击。
        """
        if not isinstance(text, str):
            return str(text)

        # 移除空字节
        text = text.replace('\0', '')

        # 移除潜在的脚本标签 (虽然我们不渲染HTML，但这是良好的防御性编程)
        text = re.sub(r'<script.*?>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)

        return text.strip()

    @staticmethod
    def validate_git_ref(ref: str) -> str:
        """
        验证Git引用名称(分支、标签等)是否符合规范,防止注入
        """
        if not ref:
            raise SecurityError("Git引用名称不能为空")

        # Git分支名称规范: 
        # 1. 不能包含 ..
        # 2. 不能包含空格, ~ ^ : ? * [
        # 3. 不能以 / 结尾
        # 4. 不能以 . 结尾
        # 5. 不能包含 @{
        # 6. 不能包含 \
        # 这里使用更严格的白名单
        if not re.match(r'^[a-zA-Z0-9_\-\./]+$', ref):
            raise SecurityError(f"Git引用名称包含非法字符: {ref}")

        if len(ref) > 255:
            raise SecurityError(f"Git引用名称过长 (最大 255 字符): {len(ref)}")

        if '..' in ref or ref.startswith('/') or ref.endswith('/') or ref.endswith('.'):
            raise SecurityError(f"Git引用名称格式不正确: {ref}")

        return ref


def check_sensitive_data(text: str) -> List[str]:
    """
    检查文本中是否包含潜在的敏感数据（API密钥、密码等）。
    
    Args:
        text: 要检查的文本
        
    Returns:
        List[str]: 发现的敏感数据类型列表
    """
    findings = []
    patterns = {
        "API Key/Secret": r'(?:api_key|apikey|secret|token|password|passwd|pwd|auth_key|access_key|secret_key)\s*[:=]\s*["\'][a-zA-Z0-9\-_]{8,}["\']',
        "Private Key": r'-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----',
        "OpenAI Key": r'sk-[a-zA-Z0-9]{32,}|sk-proj-[a-zA-Z0-9\-]{32,}',
        "AWS Access Key": r'(?:AKIA|ASIA)[0-9A-Z]{16}',
        "AWS Secret Key": r'secret_key\s*[:=]\s*["\'][a-zA-Z0-9/+=]{40}["\']',
        "GitHub Token": r'gh[pous]_[a-zA-Z0-9]{36,}',
        "Generic Bearer Token": r'Bearer\s+[a-zA-Z0-9\-\._~+/]+=*',
        "Environment Variable Export": r'export\s+(?:API_KEY|SECRET|TOKEN|PASSWORD)=[^\s]+'
    }
    
    for label, pattern in patterns.items():
        if re.search(pattern, text, re.IGNORECASE):
            findings.append(label)
            
    return findings
