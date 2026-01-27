"""技能安全验证器 (SkillValidator)

Gemini 建议 #2 - 防止敏感信息泄露，自动脱敏处理。
"""

import re
from typing import List, Tuple
import logging

logger = logging.getLogger(__name__)


class SkillValidator:
    """技能安全验证器

    职责：
    - 检测代码中的敏感信息（密码、API密钥等）
    - 自动脱敏处理（替换为占位符）
    - 验证代码安全性（防止危险操作）
    """

    # 敏感信息模式列表
    SENSITIVE_PATTERNS: List[Tuple[str, str]] = [
        # 密码类
        (r'password\s*[:=]\s*["\']?[\w]+["\']?', "password={{REDACTED}}"),
        (r'passwd\s*[:=]\s*["\']?[\w]+["\']?', "passwd={{REDACTED}}"),
        (r'pwd\s*[:=]\s*["\']?[\w]+["\']?', "pwd={{REDACTED}}"),

        # API 密钥
        (r'api[_-]?key\s*[:=]\s*["\']?[\w\-]+["\']?', "api_key={{REDACTED}}"),
        (r'secret[_-]?key\s*[:=]\s*["\']?[\w\-]+["\']?', "secret_key={{REDACTED}}"),
        (r'access[_-]?token\s*[:=]\s*["\']?[\w\-\.]+["\']?', "access_token={{REDACTED}}"),
        (r'auth[_-]?token\s*[:=]\s*["\']?[\w\-\.]+["\']?', "auth_token={{REDACTED}}"),

        # 数据库连接
        (r'mongodb://\w+:\w+@', "mongodb://user:password@"),
        (r'postgresql://\w+:\w+@', "postgresql://user:password@"),
        (r'mysql://\w+:\w+@', "mysql://user:password@"),

        # 绝对路径（跨平台）
        (r'[A-Z]:\\[\w\\\-\.]+', "{{PROJECT_ROOT}}"),  # Windows
        (r'/home/\w+/', "{{PROJECT_ROOT}}/"),           # Linux
        (r'/Users/\w+/', "{{PROJECT_ROOT}}/"),          # macOS
    ]

    # 危险操作检测
    DANGEROUS_PATTERNS = [
        r'os\.system\(',               # 直接执行系统命令
        r'subprocess\.call.*shell=True',  # shell=True 存在注入风险
        r'eval\(',                    # eval 执行任意代码
        r'exec\(',                    # exec 执行任意代码
        r'__import__\s*\(\s*["\']os["\']',  # 动态导入危险模块
    ]

    def __init__(self):
        """初始化验证器"""
        self.sensitive_regex = [(re.compile(pattern, re.IGNORECASE), repl)
                                for pattern, repl in self.SENSITIVE_PATTERNS]
        self.dangerous_regex = [re.compile(pattern, re.IGNORECASE)
                               for pattern in self.DANGEROUS_PATTERNS]

    def sanitize(self, code: str) -> str:
        """脱敏处理

        Args:
            code: 原始代码

        Returns:
            脱敏后的代码
        """
        sanitized = code

        # 应用所有脱敏规则
        for pattern, replacement in self.sensitive_regex:
            sanitized = pattern.sub(replacement, sanitized)

        if sanitized != code:
            logger.warning("SkillValidator: 敏感信息已脱敏")

        return sanitized

    def validate_safety(self, code: str) -> Tuple[bool, List[str]]:
        """验证代码安全性

        Args:
            code: 代码内容

        Returns:
            (是否安全, 警告列表)
        """
        warnings = []

        for pattern in self.dangerous_regex:
            matches = pattern.findall(code)
            if matches:
                warnings.append(f"检测到危险操作: {matches}")

        is_safe = len(warnings) == 0
        return is_safe, warnings

    def validate_skill(self, code_example: str) -> Tuple[str, bool, List[str]]:
        """验证技能卡代码

        Args:
            code_example: 代码示例

        Returns:
            (脱敏后代码, 是否安全, 警告列表)
        """
        # 1. 脱敏
        sanitized = self.sanitize(code_example)

        # 2. 安全检查
        is_safe, warnings = self.validate_safety(sanitized)

        return sanitized, is_safe, warnings
