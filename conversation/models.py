#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
对话管理数据模型

定义对话相关的数据结构
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum


class IntentType(Enum):
    """意图类型"""
    NEW_PROJECT = "new_project"          # 新建项目
    ADD_FEATURE = "add_feature"          # 添加功能
    FIX_BUG = "fix_bug"                  # 修复Bug
    CLARIFY = "clarify"                  # 需要澄清
    QUERY = "query"                      # 查询
    UNKNOWN = "unknown"                  # 未知


@dataclass
class UserInput:
    """用户输入"""
    raw_text: str                        # 原始输入文本
    timestamp: float                     # 时间戳
    context: Dict[str, Any] = field(default_factory=dict)  # 上下文信息


@dataclass
class Intent:
    """意图识别结果"""
    type: IntentType                     # 意图类型
    confidence: float                    # 置信度 (0-1)
    agent_types: List[Any] = field(default_factory=list)  # 推荐的Agent类型
    entities: Dict[str, Any] = field(default_factory=dict)  # 提取的实体
    reasoning: str = ""                  # 推理过程
    keywords: List[str] = field(default_factory=list)     # 提取的关键词
    suggested_steps: List[str] = field(default_factory=list) # 建议的步骤


@dataclass
class ClarificationQuestion:
    """澄清问题"""
    question_id: str                     # 问题ID
    question: str                        # 问题文本
    options: Optional[List[str]] = None  # 可选项(如果有)
    required: bool = True                # 是否必须回答
    reason: str = ""                     # 为什么问这个问题


@dataclass
class Response:
    """系统响应"""
    type: str                            # 响应类型
    message: str                         # 响应消息
    data: Dict[str, Any] = field(default_factory=dict)  # 附加数据
    clarifications: List[ClarificationQuestion] = field(default_factory=list)  # 澄清问题


@dataclass
class Decision:
    """决策记录"""
    topic: str                           # 决策主题
    decision: str                        # 决策内容
    reasoning: str                       # 决策理由
    timestamp: float                     # 时间戳
    alternatives: List[str] = field(default_factory=list)  # 备选方案
