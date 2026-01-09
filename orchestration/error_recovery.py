#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
错误恢复系统

智能错误处理、历史记忆查询、自动重试策略
"""

import asyncio
import logging
import re
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
from dataclasses import dataclass


logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """错误类型枚举"""
    # 语法错误
    SYNTAX_ERROR = "syntax_error"
    # 导入错误
    IMPORT_ERROR = "import_error"
    # 类型错误
    TYPE_ERROR = "type_error"
    # 属性错误
    ATTRIBUTE_ERROR = "attribute_error"
    # 键错误
    KEY_ERROR = "key_error"
    # 值错误
    VALUE_ERROR = "value_error"
    # 网络错误
    NETWORK_ERROR = "network_error"
    # 文件错误
    FILE_ERROR = "file_error"
    # 权限错误
    PERMISSION_ERROR = "permission_error"
    # 依赖错误
    DEPENDENCY_ERROR = "dependency_error"
    # 配置错误
    CONFIG_ERROR = "config_error"
    # 未知错误
    UNKNOWN_ERROR = "unknown_error"


class ErrorSeverity(Enum):
    """错误严重程度"""
    LOW = "low"           # 低: 可以忽略
    MEDIUM = "medium"     # 中: 需要处理但不致命
    HIGH = "high"         # 高: 必须处理
    CRITICAL = "critical" # 严重: 阻塞执行


@dataclass
class ErrorContext:
    """错误上下文"""
    error_type: ErrorType
    severity: ErrorSeverity
    error_message: str
    traceback: str
    task_id: str
    agent_type: str
    timestamp: datetime
    additional_context: Dict[str, Any]


@dataclass
class RecoveryStrategy:
    """恢复策略"""
    strategy_type: str  # retry, fallback, skip, manual
    max_retries: int
    retry_delay: float
    backoff_multiplier: float
    action: str
    fallback_options: List[str]


class ErrorClassifier:
    """错误分类器"""

    # 错误类型模式映射
    ERROR_PATTERNS = {
        ErrorType.SYNTAX_ERROR: [
            r"SyntaxError",
            r"IndentationError",
            r"TabError"
        ],
        ErrorType.IMPORT_ERROR: [
            r"ImportError",
            r"ModuleNotFoundError"
        ],
        ErrorType.TYPE_ERROR: [
            r"TypeError"
        ],
        ErrorType.ATTRIBUTE_ERROR: [
            r"AttributeError"
        ],
        ErrorType.KEY_ERROR: [
            r"KeyError"
        ],
        ErrorType.VALUE_ERROR: [
            r"ValueError"
        ],
        ErrorType.NETWORK_ERROR: [
            r"ConnectionError",
            r"TimeoutError",
            r"HTTPError",
            r"RequestException"
        ],
        ErrorType.FILE_ERROR: [
            r"FileNotFoundError",
            r"FileExistsError",
            r"IsADirectoryError",
            r"NotADirectoryError"
        ],
        ErrorType.PERMISSION_ERROR: [
            r"PermissionError",
            r"AccessDenied"
        ],
        ErrorType.DEPENDENCY_ERROR: [
            r"DependencyError",
            r"PackageNotFoundError"
        ],
        ErrorType.CONFIG_ERROR: [
            r"ConfigurationError",
            r"ConfigError"
        ]
    }

    # 关键词映射到错误类型
    KEYWORD_PATTERNS = {
        ErrorType.IMPORT_ERROR: [r"import", r"module", r"package"],
        ErrorType.FILE_ERROR: [r"file", r"directory", r"path"],
        ErrorType.NETWORK_ERROR: [r"network", r"connection", r"timeout"],
        ErrorType.PERMISSION_ERROR: [r"permission", r"access", r"denied"],
        ErrorType.DEPENDENCY_ERROR: [r"dependency", r"requirement"],
        ErrorType.CONFIG_ERROR: [r"config", r"setting", r"configuration"]
    }

    @classmethod
    def classify(cls, error_message: str) -> ErrorType:
        """分类错误类型

        Args:
            error_message: 错误信息

        Returns:
            ErrorType: 错误类型
        """
        # 首先尝试直接匹配异常类型
        for error_type, patterns in cls.ERROR_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, error_message, re.IGNORECASE):
                    return error_type

        # 尝试关键词匹配
        for error_type, keywords in cls.KEYWORD_PATTERNS.items():
            for keyword in keywords:
                if re.search(keyword, error_message, re.IGNORECASE):
                    return error_type

        # 默认未知错误
        return ErrorType.UNKNOWN_ERROR

    @classmethod
    def estimate_severity(
        cls,
        error_type: ErrorType,
        error_message: str
    ) -> ErrorSeverity:
        """估算错误严重程度

        Args:
            error_type: 错误类型
            error_message: 错误信息

        Returns:
            ErrorSeverity: 错误严重程度
        """
        # 关键错误类型
        if error_type in [ErrorType.SYNTAX_ERROR, ErrorType.CONFIG_ERROR]:
            return ErrorSeverity.CRITICAL

        # 高严重程度
        if error_type in [ErrorType.IMPORT_ERROR, ErrorType.DEPENDENCY_ERROR]:
            return ErrorSeverity.HIGH

        # 中等严重程度
        if error_type in [
            ErrorType.TYPE_ERROR,
            ErrorType.ATTRIBUTE_ERROR,
            ErrorType.PERMISSION_ERROR
        ]:
            return ErrorSeverity.MEDIUM

        # 低严重程度
        if error_type in [ErrorType.KEY_ERROR, ErrorType.VALUE_ERROR]:
            # 检查是否是关键错误
            if any(keyword in error_message.lower() for keyword in ["critical", "fatal", "abort"]):
                return ErrorSeverity.HIGH
            return ErrorSeverity.LOW

        # 网络/文件错误 - 根据上下文判断
        if error_type in [ErrorType.NETWORK_ERROR, ErrorType.FILE_ERROR]:
            return ErrorSeverity.MEDIUM

        # 未知错误默认为高
        return ErrorSeverity.HIGH


class MemoryBasedRecovery:
    """基于记忆的恢复策略"""

    def __init__(self, memory_manager):
        """初始化记忆恢复

        Args:
            memory_manager: 记忆管理器
        """
        self.memory_manager = memory_manager

    async def find_similar_errors(
        self,
        error_message: str,
        agent_type: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """查找相似的历史错误

        Args:
            error_message: 错误信息
            agent_type: Agent类型
            limit: 返回数量限制

        Returns:
            List[Dict[str, Any]]: 相似错误列表
        """
        try:
            # 从情节记忆中查找
            episodic_memories = await self.memory_manager.get_episodic_memories(
                limit=limit * 2  # 获取更多,然后过滤
            )

            # 合并结果
            similar_errors = []

            for memory in episodic_memories:
                content = memory.get("content", "")
                # 检查是否包含错误信息
                if "错误信息" in content or "错误:" in content:
                    similar_errors.append({
                        "memory_type": "episodic",
                        "content": content,
                        "timestamp": memory.get("timestamp", ""),
                        "metadata": memory.get("metadata", {})
                    })

            # 按相关性排序(这里简单按时间倒序)
            similar_errors.sort(
                key=lambda x: x.get("timestamp", ""),
                reverse=True
            )

            return similar_errors[:limit]

        except (AttributeError, RuntimeError) as e:
            logger.warning(f"查找相似错误失败 - 记忆系统配置错误或运行时异常: {e}")
            return []
        except Exception as e:
            logger.warning(f"查找相似错误失败 - 非预期错误 ({type(e).__name__}): {e}")
            return []

    async def suggest_fix(
        self,
        error_context: ErrorContext
    ) -> Optional[Dict[str, Any]]:
        """基于历史记忆建议修复方案

        Args:
            error_context: 错误上下文

        Returns:
            Optional[Dict[str, Any]]: 修复方案
        """
        # 查找相似错误
        similar_errors = await self.find_similar_errors(
            error_context.error_message,
            error_context.agent_type
        )

        if not similar_errors:
            return None

        # 返回最相关的修复方案
        best_match = similar_errors[0]

        # 从content中提取修复方案
        content = best_match.get("content", "")
        if "修复方案" in content:
            # 简单提取:找到修复方案行
            lines = content.split("\n")
            fix = None
            for line in lines:
                if "修复方案" in line or "**修复方案**" in line:
                    # 获取下一行或当前行内容
                    idx = lines.index(line)
                    if idx + 1 < len(lines):
                        fix = lines[idx + 1].strip()
                    break

            if fix:
                return {
                    "strategy": "memory_based",
                    "fix": fix,
                    "learning": "从历史错误中学习",
                    "confidence": "high" if len(similar_errors) > 2 else "medium",
                    "similar_errors_count": len(similar_errors)
                }

        return None


class RetryStrategy:
    """重试策略管理器"""

    # 默认重试配置
    DEFAULT_RETRY_CONFIG = {
        ErrorType.SYNTAX_ERROR: {"max_retries": 0, "retry_delay": 0},  # 语法错误不重试
        ErrorType.IMPORT_ERROR: {"max_retries": 1, "retry_delay": 2.0},
        ErrorType.TYPE_ERROR: {"max_retries": 3, "retry_delay": 1.0},
        ErrorType.ATTRIBUTE_ERROR: {"max_retries": 3, "retry_delay": 1.0},
        ErrorType.KEY_ERROR: {"max_retries": 2, "retry_delay": 0.5},
        ErrorType.VALUE_ERROR: {"max_retries": 2, "retry_delay": 0.5},
        ErrorType.NETWORK_ERROR: {"max_retries": 5, "retry_delay": 2.0},
        ErrorType.FILE_ERROR: {"max_retries": 2, "retry_delay": 1.0},
        ErrorType.PERMISSION_ERROR: {"max_retries": 0, "retry_delay": 0},  # 权限错误不重试
        ErrorType.DEPENDENCY_ERROR: {"max_retries": 1, "retry_delay": 3.0},
        ErrorType.CONFIG_ERROR: {"max_retries": 0, "retry_delay": 0},  # 配置错误不重试
        ErrorType.UNKNOWN_ERROR: {"max_retries": 3, "retry_delay": 1.0}
    }

    @classmethod
    def get_strategy(
        cls,
        error_type: ErrorType,
        severity: ErrorSeverity,
        retry_count: int = 0
    ) -> RecoveryStrategy:
        """获取重试策略

        Args:
            error_type: 错误类型
            severity: 错误严重程度
            retry_count: 当前重试次数

        Returns:
            RecoveryStrategy: 恢复策略
        """
        # 获取默认配置
        config = cls.DEFAULT_RETRY_CONFIG.get(
            error_type,
            cls.DEFAULT_RETRY_CONFIG[ErrorType.UNKNOWN_ERROR]
        )

        max_retries = config["max_retries"]
        base_delay = config["retry_delay"]

        # 根据严重程度调整
        if severity == ErrorSeverity.CRITICAL:
            max_retries = 0  # 严重错误不重试
        elif severity == ErrorSeverity.HIGH:
            max_retries = min(max_retries, 2)

        # 指数退避
        delay = base_delay * (2 ** retry_count)

        # 确定策略类型
        if max_retries == 0:
            strategy_type = "manual"
        elif retry_count >= max_retries:
            strategy_type = "fallback"
        else:
            strategy_type = "retry"

        # 构建策略
        strategy = RecoveryStrategy(
            strategy_type=strategy_type,
            max_retries=max_retries,
            retry_delay=delay,
            backoff_multiplier=2.0,
            action=cls._get_action_description(error_type, strategy_type),
            fallback_options=cls._get_fallback_options(error_type)
        )

        return strategy

    @classmethod
    def _get_action_description(
        cls,
        error_type: ErrorType,
        strategy_type: str
    ) -> str:
        """获取操作描述

        Args:
            error_type: 错误类型
            strategy_type: 策略类型

        Returns:
            str: 操作描述
        """
        descriptions = {
            "retry": f"重试执行任务(错误类型: {error_type.value})",
            "fallback": f"使用降级方案(错误类型: {error_type.value})",
            "skip": f"跳过当前步骤(错误类型: {error_type.value})",
            "manual": f"需要人工干预(错误类型: {error_type.value})"
        }

        return descriptions.get(strategy_type, "未知操作")

    @classmethod
    def _get_fallback_options(cls, error_type: ErrorType) -> List[str]:
        """获取降级选项

        Args:
            error_type: 错误类型

        Returns:
            List[str]: 降级选项列表
        """
        fallback_map = {
            ErrorType.IMPORT_ERROR: [
                "尝试安装缺失的依赖",
                "使用替代库",
                "跳过相关功能"
            ],
            ErrorType.NETWORK_ERROR: [
                "使用本地缓存",
                "稍后重试",
                "跳过网络请求"
            ],
            ErrorType.FILE_ERROR: [
                "创建默认文件",
                "使用替代路径",
                "跳过文件操作"
            ],
            ErrorType.DEPENDENCY_ERROR: [
                "使用兼容版本",
                "跳过依赖功能",
                "回退到基础实现"
            ]
        }

        return fallback_map.get(error_type, ["记录错误并继续"])


class ErrorRecoverySystem:
    """
    错误恢复系统 (Error Recovery System)
    
    核心功能:
        1. 错误分类: 识别语法、导入、网络等不同类型的错误。
        2. 严重程度评估: 根据错误类型和上下文评估对系统的影响。
        3. 智能恢复策略: 提供重试、降级、跳过或人工干预建议。
        4. 记忆集成: 自动查询历史相似错误的修复方案。
        5. 统计与学习: 记录错误历史并将其转化为长期记忆。

    Usage:
        >>> recovery = ErrorRecoverySystem(memory_manager)
        >>> result = await recovery.handle_error(exc, "task-123", "coding")
        >>> if result["should_retry"]:
        >>>    await asyncio.sleep(result["retry_delay"])
        >>>    # 执行重试逻辑
    """

    def __init__(self, memory_manager=None, error_history: Optional[Dict] = None):
        """初始化错误恢复系统

        Args:
            memory_manager: 记忆管理器(可选)
            error_history: 历史错误记录(可选)
        """
        self.memory_manager = memory_manager
        self.error_history = error_history or {}
        self.classifier = ErrorClassifier()
        self.retry_strategy = RetryStrategy()

        # 如果有记忆管理器,初始化记忆恢复
        self.memory_recovery = None
        if memory_manager:
            self.memory_recovery = MemoryBasedRecovery(memory_manager)

        # 统计信息
        self.recovery_stats = {
            "total_errors": 0,
            "recovered": 0,
            "retried": 0,
            "fallback": 0,
            "manual": 0
        }

    async def handle_error(
        self,
        error: Exception,
        task_id: str,
        agent_type: str,
        retry_count: int = 0,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """处理错误

        Args:
            error: 异常对象
            task_id: 任务ID
            agent_type: Agent类型
            retry_count: 当前重试次数
            additional_context: 额外上下文

        Returns:
            Dict[str, Any]: 处理结果
        """
        # 更新统计
        self.recovery_stats["total_errors"] += 1

        # 1. 构建错误上下文
        error_context = self._build_error_context(
            error,
            task_id,
            agent_type,
            additional_context
        )

        logger.info(
            f"处理错误: {error_context.error_type.value} "
            f"(严重程度: {error_context.severity.value})"
        )

        # 2. 分类错误
        error_type = error_context.error_type
        severity = error_context.severity

        # 3. 获取恢复策略
        strategy = self.retry_strategy.get_strategy(
            error_type,
            severity,
            retry_count
        )

        logger.info(f"恢复策略: {strategy.strategy_type}")

        # 4. 查询历史修复方案(如果有记忆管理器)
        memory_fix = None
        if self.memory_recovery:
            memory_fix = await self.memory_recovery.suggest_fix(error_context)
            if memory_fix:
                logger.info(f"找到历史修复方案: {memory_fix['fix']}")

        # 5. 构建恢复建议
        recovery_result = {
            "error_type": error_type.value,
            "severity": severity.value,
            "strategy": strategy.strategy_type,
            "action": strategy.action,
            "max_retries": strategy.max_retries,
            "current_retry": retry_count,
            "should_retry": retry_count < strategy.max_retries,
            "retry_delay": strategy.retry_delay,
            "memory_fix": memory_fix,
            "fallback_options": strategy.fallback_options
        }

        # 更新错误历史记录
        if task_id not in self.error_history:
            self.error_history[task_id] = []
        
        self.error_history[task_id].append({
            "timestamp": datetime.now().isoformat(),
            "error_type": error_type.value,
            "error_message": str(error),
            "retry_count": retry_count,
            "strategy": strategy.strategy_type
        })

        # 6. 更新统计
        if strategy.strategy_type == "retry":
            self.recovery_stats["retried"] += 1
        elif strategy.strategy_type == "fallback":
            self.recovery_stats["fallback"] += 1
        elif strategy.strategy_type == "manual":
            self.recovery_stats["manual"] += 1

        # 7. 保存错误教训(如果有记忆管理器)
        if self.memory_manager:
            await self._save_error_to_memory(
                error_context,
                strategy,
                memory_fix
            )

        return recovery_result

    def _build_error_context(
        self,
        error: Exception,
        task_id: str,
        agent_type: str,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> ErrorContext:
        """构建错误上下文

        Args:
            error: 异常对象
            task_id: 任务ID
            agent_type: Agent类型
            additional_context: 额外上下文

        Returns:
            ErrorContext: 错误上下文
        """
        error_message = str(error)
        error_type = self.classifier.classify(error_message)
        severity = self.classifier.estimate_severity(error_type, error_message)

        # 获取traceback
        import traceback
        traceback_str = "".join(traceback.format_exception(
            type(error),
            error,
            error.__traceback__
        ))

        return ErrorContext(
            error_type=error_type,
            severity=severity,
            error_message=error_message,
            traceback=traceback_str,
            task_id=task_id,
            agent_type=agent_type,
            timestamp=datetime.now(),
            additional_context=additional_context or {}
        )

    async def _save_error_to_memory(
        self,
        error_context: ErrorContext,
        strategy: RecoveryStrategy,
        memory_fix: Optional[Dict[str, Any]]
    ):
        """保存错误到记忆系统

        Args:
            error_context: 错误上下文
            strategy: 恢复策略
            memory_fix: 记忆中的修复方案
        """
        try:
            # 构建学习内容
            learning = f"""错误类型: {error_context.error_type.value}
严重程度: {error_context.severity.value}
错误信息: {error_context.error_message}
任务ID: {error_context.task_id}
Agent类型: {error_context.agent_type}

恢复策略: {strategy.strategy_type}
操作: {strategy.action}
"""

            if memory_fix:
                learning += f"\n历史修复方案: {memory_fix['fix']}"
                if memory_fix.get('learning'):
                    learning += f"\n历史经验: {memory_fix['learning']}"

            # 保存错误教训
            await self.memory_manager.save_mistake(
                error=Exception(error_context.error_message),
                context=f"任务 {error_context.task_id} 执行错误",
                fix=strategy.action,
                learning=learning
            )

            logger.info("错误已保存到记忆系统")

        except (AttributeError, RuntimeError) as e:
            logger.warning(f"保存错误到记忆失败 - 记忆系统不可用或配置错误 ({type(e).__name__}): {e}")
        except Exception as e:
            logger.warning(f"保存错误到记忆失败 - 非预期错误 ({type(e).__name__}): {e}")

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息

        Returns:
            Dict[str, Any]: 统计信息
        """
        return self.recovery_stats.copy()

    def reset_statistics(self):
        """重置统计信息"""
        self.recovery_stats = {
            "total_errors": 0,
            "recovered": 0,
            "retried": 0,
            "fallback": 0,
            "manual": 0
        }
