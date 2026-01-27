#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SuperAgent 常量配置

集中管理超时、缓存、重试等配置值。
"""

from pathlib import Path
from enum import Enum


class Timeouts(Enum):
    """超时配置（秒）"""
    REVIEW = 600       # 10 minutes - 代码审查超时
    TEST = 300         # 5 minutes - 测试执行超时
    TASK = 1800        # 30 minutes - 任务执行超时
    INDEX_WAIT = 30    # 30 seconds - 索引等待超时
    LLM_RESPONSE = 120 # 2 minutes - LLM 响应超时


class Defaults(Enum):
    """默认值配置"""
    MAX_RETRIES = 3                # 最大重试次数
    BATCH_SIZE = 10                # 批处理大小
    CACHE_TTL = 300                # 5 minutes - 缓存 TTL
    MAX_CACHE_SIZE = 1000          # 最大缓存条目数
    LOG_LEVEL = "INFO"             # 默认日志级别


class Paths(Enum):
    """路径配置"""
    MEMORY_DIR = ".superagent/memory"
    EPISODIC_DIR = "episodic"
    SEMANTIC_DIR = "semantic"
    PROCEDURAL_DIR = "procedural"
    CONTINUITY_FILE = "CONTINUITY.md"
    INDEX_FILE = "memory_index.json"


class MemoryConfig(Enum):
    """记忆系统配置"""
    CACHE_TTL = 300        # 5分钟缓存 TTL
    MAX_CACHE_SIZE = 1000  # 每个类型的最大缓存条目数
    BATCH_SIZE = 50        # 批量处理大小


class ReviewConfig(Enum):
    """代码审查配置"""
    DEFAULT_TIMEOUT = 600  # 10分钟
    PASSING_SCORE = 80     # 通过分数
    WARNING_SCORE = 60     # 警告分数


class AgentConfig(Enum):
    """Agent 配置"""
    DEFAULT_TIMEOUT = 1800     # 30分钟
    MAX_STEPS = 50             # 最大步骤数
    RETRY_COUNT = 3            # 重试次数
