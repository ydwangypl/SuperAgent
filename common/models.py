#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
核心公共模型
"""

from enum import Enum


class StepStatus(Enum):
    """步骤状态"""
    PENDING = "pending"         # 待执行
    READY = "ready"             # 就绪(依赖已满足)
    IN_PROGRESS = "in_progress" # 执行中
    COMPLETED = "completed"     # 已完成
    FAILED = "failed"           # 失败
    SKIPPED = "skipped"         # 跳过


class AgentType(Enum):
    """Agent类型 (v3.1 扩展版)"""
    # 核心管理与设计
    PRODUCT_MANAGEMENT = "product-management"
    DATABASE_DESIGN = "database-design"
    API_DESIGN = "api-design"
    
    # 核心开发
    BACKEND_DEV = "backend-dev"
    FRONTEND_DEV = "frontend-dev"
    FULL_STACK_DEV = "full-stack-dev"
    MINI_PROGRAM_DEV = "mini-program-dev"
    
    # 质量与安全
    QA_ENGINEERING = "qa-engineering"
    SECURITY_AUDIT = "security-audit"
    CODE_REVIEW = "code-review"
    
    # 运维与优化
    DEVOPS_ENGINEERING = "devops-engineering"
    PERFORMANCE_OPTIMIZATION = "performance-optimization"
    INFRA_SETUP = "infra-setup"
    
    # 专项处理
    TECHNICAL_WRITING = "technical-writing"
    CODE_REFACTORING = "code-refactoring"
    DATA_MIGRATION = "data-migration"
    UI_DESIGN = "ui-design"
