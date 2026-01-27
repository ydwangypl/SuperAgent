#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SuperAgent v3.2 配置管理模块

提供统一的配置管理接口

v3.3 新增: 环境变量配置支持
"""

import json
import logging
import os
from pathlib import Path
from typing import Optional, Dict, Any
from urllib.parse import urlparse
from pydantic import BaseModel, Field, field_validator

from common.exceptions import SecurityError

logger = logging.getLogger(__name__)


# v3.3: 环境变量配置键名映射
# v3.3 安全增强：敏感字段列表，用于日志脱敏
_SENSITIVE_ENV_KEYS = frozenset({"PASSWORD", "SECRET", "TOKEN", "KEY"})

ENV_CONFIG_MAPPING: Dict[str, tuple[str, Optional[str]]] = {
    "SUPERAGENT_LOG_LEVEL": ("logging", "level"),
    "SUPERAGENT_LOG_FILE": ("logging", "file_path"),
    "SUPERAGENT_REDIS_URL": ("distribution", "broker_url"),
    "SUPERAGENT_REDIS_PASSWORD": ("distribution", "redis_password"),
    "SUPERAGENT_REDIS_REQUIRE_AUTH": ("distribution", "require_auth"),
    "SUPERAGENT_WORKER_CONCURRENCY": ("distribution", "worker_concurrency"),
    "SUPERAGENT_MEMORY_ENABLED": ("memory", "enabled"),
    "SUPERAGENT_MEMORY_RETENTION_DAYS": ("memory", "retention_days"),
    "SUPERAGENT_ORCHESTRATION_PARALLEL": ("orchestration", "enable_parallel_execution"),
    "SUPERAGENT_ORCHESTRATION_MAX_TASKS": ("orchestration", "max_parallel_tasks"),
    "SUPERAGENT_TOKEN_OPT_ENABLED": ("token_optimization", "enabled"),
    "SUPERAGENT_EXPERIENCE_LEVEL": ("experience_level", None),
}


class MemoryConfig(BaseModel):
    """记忆系统配置"""

    # 是否启用记忆系统
    enabled: bool = True

    # 记忆保留天数 (0 = 永久保留)
    retention_days: int = Field(default=0, ge=0)

    # 最大记忆条目数
    max_episodic_memories: int = Field(default=1000, gt=0)
    max_semantic_memories: int = Field(default=500, gt=0)
    max_procedural_memories: int = Field(default=500, gt=0)

    # 是否自动保存 CONTINUITY.md
    auto_save_continuity: bool = True


class CodeReviewConfig(BaseModel):
    """代码审查配置"""

    # 是否启用代码审查
    enabled: bool = True

    # 最低质量评分要求
    min_overall_score: float = Field(default=70.0, ge=0.0, le=100.0)

    # 最多允许的严重问题数
    max_critical_issues: int = Field(default=0, ge=0)

    # 审查选项
    enable_style_check: bool = True
    enable_security_check: bool = True
    enable_performance_check: bool = True
    enable_best_practices: bool = True

    # Ralph Wiggum 循环配置
    enable_ralph_wiggum: bool = True  # ✅ 默认启用 Ralph Wiggum 迭代改进
    ralph_wiggum_max_iterations: int = Field(default=3, ge=1, le=10)


class OrchestrationConfig(BaseModel):
    """编排配置"""

    # 是否启用并行执行
    enable_parallel_execution: bool = True

    # 最大并行任务数
    max_parallel_tasks: int = Field(default=3, ge=1, le=10)

    # 每个 Agent 的最大并发数
    max_concurrent_per_agent: int = Field(default=1, ge=1, le=5)

    # 是否启用快速失败
    enable_early_failure: bool = False

    # Git Worktree 配置
    enable_worktree: bool = False
    worktree_auto_cleanup: bool = False
    worktree_path: Optional[str] = None

    # Agent 超时配置 (秒)
    agent_timeout_seconds: int = Field(default=300, ge=30, le=3600)
    agent_retry_delay_seconds: int = Field(default=5, ge=1, le=60)


class LoggingConfig(BaseModel):

    # 日志级别
    level: str = "INFO"

    # 日志格式
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # 日志文件路径
    file_path: Optional[str] = None

    @field_validator('level')
    @classmethod
    def validate_level(cls, v: str) -> str:
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed:
            raise ValueError(f"日志级别必须是 {allowed} 之一")
        return v.upper()

    # 是否输出到控制台
    console_output: bool = True

    # 是否输出到文件
    file_output: bool = True


class TokenOptimizationConfig(BaseModel):
    """Token优化配置"""

    # 是否启用Token优化
    enabled: bool = True

    # 压缩方法: "auto", "semantic", "structured"
    compression_method: str = "auto"

    # 目标压缩比例 (0.0-1.0)
    target_ratio: float = Field(default=0.5, ge=0.0, le=1.0)

    # 压缩阈值(超过此字符数才压缩)
    compression_threshold: int = Field(default=1000, ge=0)

    # 是否启用消息历史压缩
    enable_message_compression: bool = True

    # 最大消息历史Token数
    max_message_tokens: int = Field(default=8000, gt=0)

    # Agent定制压缩规则
    agent_rules: Dict[str, Dict] = Field(default_factory=lambda: {
        "coding": {"target_ratio": 0.5, "focus": ["tech", "requirements", "decisions"]},
        "backend-dev": {"target_ratio": 0.4, "focus": ["tech", "api", "requirements"]},
        "frontend-dev": {"target_ratio": 0.4, "focus": ["ui", "ux", "requirements"]},
        "database-design": {"target_ratio": 0.4, "focus": ["tech", "decisions"]},
        "product-management": {"target_ratio": 0.3, "focus": ["product", "requirements"]},
        "testing": {"target_ratio": 0.5, "focus": ["requirements", "decisions"]},
    })


class SnapshotConfig(BaseModel):
    """增量更新快照配置"""

    # 是否启用增量更新
    enabled: bool = True

    # 快照保留天数
    retention_days: int = Field(default=30, ge=0)

    # 增量阈值(差异比例低于此值时使用增量更新)
    incremental_threshold: float = Field(default=0.3, ge=0.0, le=1.0)

    # 每个文件最多保留的快照数
    max_snapshots_per_file: int = Field(default=10, ge=1)

    # 是否缓存文件内容用于diff
    cache_content: bool = True

    # 快照目录
    snapshot_dir: str = ".superagent/snapshots"


class TokenMonitorConfig(BaseModel):
    """Token监控配置"""

    # 是否启用监控
    enabled: bool = True

    # 监控日志文件
    log_file: str = ".superagent/token_usage.jsonl"

    # 保留天数
    retention_days: int = Field(default=30, ge=0)

    # 是否追踪压缩节省
    track_compression_savings: bool = True

    # 是否追踪增量节省
    track_incremental_savings: bool = True

    # 预算相关
    enable_budget: bool = False
    total_budget: int = Field(default=1000000, ge=0)
    warning_threshold: float = Field(default=0.8, ge=0.0, le=1.0)
    stop_on_exceed: bool = True


class DistributionConfig(BaseModel):
    """分布式任务队列配置"""

    # 是否启用分布式执行
    enabled: bool = False

    # Broker URL (e.g., redis://localhost:6379/0)
    # v3.3: 如果使用 Redis，建议在 URL 中包含密码: redis://:password@localhost:6379/0
    broker_url: str = "redis://localhost:6379/0"

    # Result Backend URL
    result_backend: str = "redis://localhost:6379/0"

    # v3.3: Redis 密码 (推荐通过 URL 设置，或使用此字段)
    redis_password: Optional[str] = None

    # v3.3: 是否强制要求 Redis 认证
    require_auth: bool = False

    # 任务超时 (秒)
    task_timeout: int = Field(default=3600, ge=60)

    # 并发数
    worker_concurrency: int = Field(default=4, ge=1, le=32)

    def validate_connection(self) -> bool:
        """验证分布式配置连通性"""
        if not self.enabled:
            return True

        # v3.3: 检查 Redis 认证
        if self.require_auth:
            if not self._has_redis_password():
                raise SecurityError("Redis 认证已启用，但未配置密码")

        try:
            import redis
            r = redis.from_url(self.broker_url, socket_timeout=2)
            r.ping()
            return True
        except (ImportError, ModuleNotFoundError):
            logger.warning("未安装 redis 库，无法验证分布式连接")
            return False
        except Exception as e:
            logger.debug(f"Redis 连接验证失败: {e}")
            return False

    def _has_redis_password(self) -> bool:
        """检查是否配置了 Redis 密码"""
        # 1. 检查显式配置的密码
        if self.redis_password:
            return True

        # 2. 检查 broker_url 中是否包含密码
        # 格式: redis://:password@host:port/db
        parsed = urlparse(self.broker_url)
        if parsed.password:
            return True

        return False


class SuperAgentConfig(BaseModel):
    """SuperAgent 完整配置"""

    # 项目根目录
    project_root: Path = Field(default_factory=lambda: Path.cwd())

    # 用户经验等级: novice (新手/小白), master (专家/大神)
    experience_level: str = Field(default="novice")

    # 记忆系统配置
    memory: MemoryConfig = Field(default_factory=MemoryConfig)

    # 代码审查配置
    code_review: CodeReviewConfig = Field(default_factory=CodeReviewConfig)

    # 编排配置
    orchestration: OrchestrationConfig = Field(default_factory=OrchestrationConfig)

    # 分布式配置
    distribution: DistributionConfig = Field(default_factory=DistributionConfig)

    # 日志配置
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    # Token优化配置
    token_optimization: TokenOptimizationConfig = Field(default_factory=TokenOptimizationConfig)

    # 快照配置
    snapshot: SnapshotConfig = Field(default_factory=SnapshotConfig)

    # Token监控配置
    token_monitor: TokenMonitorConfig = Field(default_factory=TokenMonitorConfig)

    class Config:
        arbitrary_types_allowed = True

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SuperAgentConfig":
        """从字典创建配置"""
        return cls.model_validate(data)


def get_default_config_path(project_root: Optional[Path] = None) -> Path:
    """获取默认配置文件路径"""
    if project_root is None:
        project_root = Path.cwd()

    return project_root / ".superagent" / "config.json"


def load_config(
    config_path: Optional[Path] = None,
    project_root: Optional[Path] = None
) -> SuperAgentConfig:
    """加载配置

    Args:
        config_path: 配置文件路径,如果为 None 则使用默认路径
        project_root: 项目根目录

    Returns:
        SuperAgentConfig: 配置对象
    """
    # 确定配置文件路径
    if config_path is None:
        config_path = get_default_config_path(project_root)

    # 如果配置文件不存在,返回默认配置
    if not config_path.exists():
        logger.info(f"配置文件不存在: {config_path}, 使用默认配置")
        return SuperAgentConfig(project_root=project_root or Path.cwd())

    # 读取配置文件
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        logger.info(f"已加载配置: {config_path}")
        return SuperAgentConfig.from_dict(data)

    except (json.JSONDecodeError, TypeError, ValueError) as e:
        logger.error(f"加载配置失败 (解析错误): {e}, 使用默认配置")
        return SuperAgentConfig(project_root=project_root or Path.cwd())
    except (OSError, IOError) as e:
        logger.error(f"加载配置失败 (IO错误): {e}, 使用默认配置")
        return SuperAgentConfig(project_root=project_root or Path.cwd())
    except Exception as e:
        logger.error(f"加载配置遇到非预期错误: {e}, 使用默认配置")
        return SuperAgentConfig(project_root=project_root or Path.cwd())


def save_config(
    config: SuperAgentConfig,
    config_path: Optional[Path] = None
) -> None:
    """保存配置

    Args:
        config: 配置对象
        config_path: 配置文件路径,如果为 None 则使用默认路径
    """
    # 确定配置文件路径
    if config_path is None:
        config_path = get_default_config_path(config.project_root)

    # 确保目录存在
    config_path.parent.mkdir(parents=True, exist_ok=True)

    # 保存配置文件
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config.to_dict(), f, ensure_ascii=False, indent=2)

        logger.info(f"配置已保存: {config_path}")

    except (TypeError, ValueError) as e:
        logger.error(f"保存配置失败 (序列化错误): {e}")
        raise
    except (OSError, IOError) as e:
        logger.error(f"保存配置失败 (IO错误): {e}")
        raise
    except Exception as e:
        logger.error(f"保存配置遇到非预期错误: {e}")
        raise


def setup_logging(config: LoggingConfig) -> None:
    """设置日志系统

    Args:
        config: 日志配置
    """
    import logging

    # 创建 logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, config.level.upper(), logging.INFO))

    # 清除现有 handlers
    logger.handlers.clear()

    # 日志格式
    formatter = logging.Formatter(config.format)

    # 控制台输出
    if config.console_output:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # 文件输出
    if config.file_output and config.file_path:
        file_handler = logging.FileHandler(config.file_path, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)


def load_config_from_env() -> Dict[str, Any]:
    """从环境变量加载配置覆盖值

    Returns:
        Dict[str, Any]: 配置覆盖字典 (仅包含设置的 env vars)
    """
    overrides: Dict[str, Any] = {}

    for env_key, (section, field) in ENV_CONFIG_MAPPING.items():
        value = os.environ.get(env_key)
        if value is None:
            continue

        # 处理布尔值
        if value.lower() in ("true", "false", "1", "0"):
            value = value.lower() in ("true", "1")

        # 处理整数值
        int_fields = {
            ("distribution", "worker_concurrency"),
            ("memory", "retention_days"),
            ("orchestration", "max_parallel_tasks"),
        }
        if (section, field) in int_fields:
            try:
                value = int(value)
            except ValueError:
                # v3.3 安全增强：转换失败时记录错误并使用默认值
                logger.error(f"环境变量 {env_key} 值 '{value}' 无效，无法转换为整数，跳过此配置")
                continue

        if section == "experience_level":
            overrides["experience_level"] = value
        else:
            if section not in overrides:
                overrides[section] = {}
            overrides[section][field] = value

    return overrides


def load_config(
    config_path: Optional[Path] = None,
    project_root: Optional[Path] = None,
    allow_env_overrides: bool = True
) -> SuperAgentConfig:
    """加载配置

    v3.3: 支持从环境变量覆盖配置

    Args:
        config_path: 配置文件路径,如果为 None 则使用默认路径
        project_root: 项目根目录
        allow_env_overrides: 是否允许环境变量覆盖配置文件

    Returns:
        SuperAgentConfig: 配置对象
    """
    # v3.3: 如果允许环境变量覆盖，合并到配置中
    env_overrides = {}
    if allow_env_overrides:
        env_overrides = load_config_from_env()
        if env_overrides:
            logger.info(f"从环境变量加载配置覆盖: {list(env_overrides.keys())}")

    # 确定配置文件路径
    if config_path is None:
        config_path = get_default_config_path(project_root)

    # 如果配置文件不存在,返回默认配置
    if not config_path.exists():
        config = SuperAgentConfig(project_root=project_root or Path.cwd())
        # 应用环境变量覆盖
        if env_overrides:
            _apply_overrides(config, env_overrides)
        logger.info(f"配置文件不存在: {config_path}, 使用默认配置(包含环境变量覆盖)")
        return config

    # 读取配置文件
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # v3.3: 合并环境变量覆盖
        if env_overrides:
            _apply_overrides_to_dict(data, env_overrides)

        logger.info(f"已加载配置: {config_path}")
        return SuperAgentConfig.from_dict(data)

    except (json.JSONDecodeError, TypeError, ValueError) as e:
        logger.error(f"加载配置失败 (解析错误): {e}, 使用默认配置")
        return SuperAgentConfig(project_root=project_root or Path.cwd())
    except (OSError, IOError) as e:
        logger.error(f"加载配置失败 (IO错误): {e}, 使用默认配置")
        return SuperAgentConfig(project_root=project_root or Path.cwd())
    except Exception as e:
        logger.error(f"加载配置遇到非预期错误: {e}, 使用默认配置")
        return SuperAgentConfig(project_root=project_root or Path.cwd())


def save_config(config: SuperAgentConfig, config_path: Optional[Path] = None) -> None:
    """保存配置到文件

    Args:
        config: 配置对象
        config_path: 配置文件路径,如果为 None 则使用默认路径
    """
    if config_path is None:
        config_path = get_default_config_path(config.project_root)

    # 确保目录存在
    config_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config.model_dump(), f, ensure_ascii=False, indent=2)
        logger.info(f"配置已保存到: {config_path}")
    except Exception as e:
        logger.error(f"保存配置失败: {e}")
        raise


def _apply_overrides(config: SuperAgentConfig, overrides: Dict[str, Any]) -> None:
    """应用环境变量覆盖到配置对象 (v3.3 安全增强)

    使用深拷贝避免修改原始配置，只更新允许的字段。
    """
    import copy
    for section, fields in overrides.items():
        if section == "experience_level":
            config.experience_level = fields
            continue

        if not hasattr(config, section):
            continue

        section_obj = getattr(config, section)
        if hasattr(section_obj, "model_dump"):
            # v3.3 安全增强：使用深拷贝避免修改原始配置
            section_dict = copy.deepcopy(section_obj.model_dump())
            # v3.3 安全增强：只更新允许的字段（交集）
            allowed_fields = set(section_dict.keys()) & set(fields.keys())
            for field_name in allowed_fields:
                section_dict[field_name] = fields[field_name]
            new_section = type(section_obj)(**section_dict)
            setattr(config, section, new_section)


def _apply_overrides_to_dict(data: Dict[str, Any], overrides: Dict[str, Any]) -> None:
    """应用环境变量覆盖到配置字典"""
    for section, fields in overrides.items():
        if section == "experience_level":
            data["experience_level"] = fields
            continue

        if section not in data:
            data[section] = {}
        data[section].update(fields)


def get_env_config_summary() -> str:
    """获取当前环境变量配置摘要

    v3.3 安全增强：使用常量判断敏感字段

    Returns:
        str: 配置摘要
    """
    active_vars = []
    for env_key, _ in ENV_CONFIG_MAPPING.items():
        value = os.environ.get(env_key)
        if value is not None:
            # v3.3 安全增强：使用常量判断敏感字段
            if any(sensitive in env_key for sensitive in _SENSITIVE_ENV_KEYS):
                value = "***"
            active_vars.append(f"{env_key}={value}")

    if not active_vars:
        return "无活动的环境变量配置"

    return "活动的环境变量配置:\n  " + "\n  ".join(active_vars)
