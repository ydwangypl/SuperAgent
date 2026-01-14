#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Agent 注册中心 (Phase 3 重构核心)

作为 Agent 元数据的单一事实来源，解耦规划、实例化和分发逻辑。
"""

import logging
from typing import Dict, Type, List, Optional
from dataclasses import dataclass, field
from common.models import AgentType
from execution.base_agent import BaseAgent
from execution.coding_agent import CodingAgent
from execution.testing_agent import TestingAgent
from execution.documentation_agent import DocumentationAgent
from execution.refactoring_agent import RefactoringAgent

logger = logging.getLogger(__name__)


@dataclass
class AgentMetadata:
    """Agent 元数据定义"""
    agent_type: AgentType
    impl_class: Type[BaseAgent]
    description: str
    priority: int = 99
    max_concurrent: int = 5
    capabilities: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)  # 用于意图识别的关键词/正则


class AgentRegistry:
    """Agent 注册中心 - 管理所有 Agent 的元数据与映射"""

    _metadata: Dict[AgentType, AgentMetadata] = {}
    _initialized = False

    @classmethod
    def initialize(cls):
        """初始化注册表 (建立所有 Agent 的统一映射)"""
        if cls._initialized:
            return

        # 定义所有 Agent 的元数据
        agents = [
            # 核心管理与设计
            AgentMetadata(
                AgentType.PRODUCT_MANAGEMENT, CodingAgent,
                "负责产品需求分析、功能规划和 PRD 编写 (支持 RICE/MoSCoW 框架)", 1, 3,
                keywords=[r"需求|规划|prd|分析|产品|management|design"]
            ),
            AgentMetadata(
                AgentType.DATABASE_DESIGN, CodingAgent,
                "负责数据库 Schema 设计、索引优化 and 数据建模", 2, 5,
                keywords=[
                    r"数据库|database|schema|table|索引|migration",
                    r"sql|mysql|postgresql|mongodb|redis",
                    r"数据模型|数据结构|存储"
                ]
            ),
            AgentMetadata(
                AgentType.API_DESIGN, CodingAgent,
                "负责 RESTful/GraphQL API 接口定义 and Swagger 文档生成", 2, 5,
                keywords=[r"api|接口|restful|graphql|swagger|endpoint|路由"]
            ),

            # 核心开发 (映射到 CodingAgent)
            AgentMetadata(
                AgentType.BACKEND_DEV, CodingAgent,
                "负责服务端业务逻辑、数据处理 and 系统集成", 3, 10,
                keywords=[
                    r"后端|backend|服务端|server|后台",
                    r"业务逻辑|数据处理|微服务|功能|管理",
                    r"fastapi|flask|django|express"
                ]
            ),
            AgentMetadata(
                AgentType.FRONTEND_DEV, CodingAgent,
                "负责 UI 组件开发、交互逻辑 and 前端架构", 3, 10,
                keywords=[
                    r"前端|frontend|界面|ui|页面",
                    r"react|vue|angular|组件",
                    r"用户体验|交互|响应式"
                ]
            ),
            AgentMetadata(
                AgentType.FULL_STACK_DEV, CodingAgent,
                "负责端到端的完整功能实现", 3, 8,
                keywords=[
                    r"全栈|fullstack|前后端",
                    r"全栈开发|完整应用"
                ]
            ),
            AgentMetadata(
                AgentType.MINI_PROGRAM_DEV, CodingAgent,
                "负责小程序/移动端专用逻辑开发", 4, 5,
                keywords=[r"小程序|微信小程序|uniapp|移动端|mobile"]
            ),

            # 质量与安全
            AgentMetadata(
                AgentType.QA_ENGINEERING, TestingAgent,
                "负责单元测试、集成测试生成 and 自动化测试流程", 5, 10,
                keywords=[
                    r"测试|test|单元测试|集成测试",
                    r"pytest|jest|测试用例|覆盖率",
                    r"质量保证|qa"
                ]
            ),
            AgentMetadata(
                AgentType.SECURITY_AUDIT, CodingAgent,
                "负责代码安全扫描、漏洞识别 and 安全加固建议", 6, 3,
                keywords=[r"安全|扫描|漏洞|audit|security|加固|注入|xss"]
            ),
            AgentMetadata(
                AgentType.CODE_REVIEW, CodingAgent,
                "负责自动化代码质量检查 and 风格一致性评审", 6, 5,
                keywords=[r"审查|评审|review|规范|质量|风格|lint"]
            ),

            # 运维与优化
            AgentMetadata(
                AgentType.DEVOPS_ENGINEERING, CodingAgent,
                "负责 CI/CD 流水线配置、容器化 and 部署脚本生成", 7, 5,
                keywords=[
                    r"部署|deploy|ci|cd|docker|k8s",
                    r"运维|监控|日志|管道",
                    r"自动化|构建|发布"
                ]
            ),
            AgentMetadata(
                AgentType.PERFORMANCE_OPTIMIZATION, CodingAgent,
                "负责系统瓶颈分析 and 代码/SQL 性能调优建议", 7, 3,
                keywords=[r"性能|优化|调优|瓶颈|performance|吞吐量|并发"]
            ),
            AgentMetadata(
                AgentType.INFRA_SETUP, CodingAgent,
                "负责基础设施即代码 (IaC) and 云资源初始化配置", 7, 3,
                keywords=[r"基础设施|iac|terraform|cloud|云资源|初始化"]
            ),

            # 专项处理
            AgentMetadata(
                AgentType.TECHNICAL_WRITING, DocumentationAgent,
                "负责用户手册、技术文档、API 参考 and 架构说明的编写", 8, 5,
                keywords=[
                    r"文档|documentation|readme|指南",
                    r"api文档|使用手册|说明"
                ]
            ),
            AgentMetadata(
                AgentType.CODE_REFACTORING, RefactoringAgent,
                "负责既有代码的结构优化、模式改进 and 技术债清理", 8, 3,
                keywords=[r"重构|refactor|解耦|清晰|清理"]
            ),
            AgentMetadata(
                AgentType.DATA_MIGRATION, CodingAgent,
                "负责数据迁移脚本编写 and ETL 逻辑实现", 8, 3,
                keywords=[r"迁移|migration|etl|导入|导出|同步"]
            ),
            AgentMetadata(
                AgentType.UI_DESIGN, CodingAgent,
                "负责界面视觉设计、切图说明 and 样式表生成", 9, 3,
                keywords=[r"设计|视觉|切图|样式|css|less|sass|figma"]
            ),
        ]

        for meta in agents:
            cls._metadata[meta.agent_type] = meta

        cls._initialized = True
        logger.info(f"AgentRegistry 初始化完成，共注册 {len(cls._metadata)} 种 Agent 类型")

    @classmethod
    def get_metadata(cls, agent_type: AgentType) -> Optional[AgentMetadata]:
        """获取 Agent 元数据"""
        cls.initialize()
        return cls._metadata.get(agent_type)

    @classmethod
    def get_impl_class(cls, agent_type: AgentType) -> Optional[Type[BaseAgent]]:
        """获取 Agent 实现类"""
        meta = cls.get_metadata(agent_type)
        return meta.impl_class if meta else None

    @classmethod
    def get_description(cls, agent_type: AgentType) -> str:
        """获取 Agent 描述 (用于规划理由)"""
        meta = cls.get_metadata(agent_type)
        return meta.description if meta else "通用智能 Agent"

    @classmethod
    def get_priority(cls, agent_type: AgentType) -> int:
        """获取 Agent 优先级"""
        meta = cls.get_metadata(agent_type)
        return meta.priority if meta else 99

    @classmethod
    def get_max_concurrent(cls, agent_type: AgentType) -> int:
        """获取 Agent 最大并发数"""
        meta = cls.get_metadata(agent_type)
        return meta.max_concurrent if meta else 5

    @classmethod
    def get_all_types(cls) -> List[AgentType]:
        """获取所有已注册的 Agent 类型"""
        cls.initialize()
        return list(cls._metadata.keys())

    @classmethod
    def from_string(cls, type_str: str) -> Optional[AgentType]:
        """从字符串安全转换回 AgentType"""
        try:
            return AgentType(type_str)
        except ValueError:
            # 兼容性处理：尝试模糊匹配
            type_str = type_str.lower().replace("_", "-")
            for atype in AgentType:
                if atype.value == type_str:
                    return atype
            return None

    @classmethod
    def get_keywords(cls, agent_type: AgentType) -> List[str]:
        """获取 Agent 识别关键词"""
        meta = cls.get_metadata(agent_type)
        return meta.keywords if meta else []

    @classmethod
    def get_all_keywords(cls) -> Dict[AgentType, List[str]]:
        """获取所有 Agent 的关键词映射"""
        cls.initialize()
        return {atype: meta.keywords for atype, meta in cls._metadata.items()}
