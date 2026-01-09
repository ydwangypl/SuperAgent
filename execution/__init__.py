#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
执行层(Execution Layer)

负责具体的代码生成、测试、文档等任务执行
"""

from .models import (
    AgentCapability,
    AgentResult,
    AgentContext,
    AgentConfig
)
from .base_agent import BaseAgent
from .coding_agent import CodingAgent
from .testing_agent import TestingAgent
from .documentation_agent import DocumentationAgent
from .refactoring_agent import RefactoringAgent

__all__ = [
    # Models
    "AgentCapability",
    "AgentResult",
    "AgentContext",
    "AgentConfig",
    # Base Classes
    "BaseAgent",
    # Concrete Agents
    "CodingAgent",
    "TestingAgent",
    "DocumentationAgent",
    "RefactoringAgent",
]
