#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Agent 注册中心 (Phase 3 重构核心)

作为 Agent 元数据的单一事实来源，解耦规划、实例化和分发逻辑。
"""

import logging
from typing import Dict, Type, List, Optional, Union
from dataclasses import dataclass, field
from common.models import AgentType
from execution.base_agent import BaseAgent

logger = logging.getLogger(__name__)


@dataclass
class AgentMetadata:
    """Agent 元数据定义"""
    agent_type: AgentType
    impl_class: Union[Type[BaseAgent], str]  # 支持直接引用或导入路径(用于延迟加载)
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
                AgentType.PRODUCT_MANAGEMENT, "execution.coding_agent.CodingAgent",
                "负责产品需求分析、功能规划和 PRD 编写 (支持 RICE/MoSCoW 框架)", 1, 3,
                keywords=[r"需求|规划|prd|分析|产品|management|design"]
            ),
            AgentMetadata(
                AgentType.DATABASE_DESIGN, "execution.coding_agent.CodingAgent",
                "负责数据库 Schema 设计、索引优化 and 数据建模", 2, 5,
                keywords=[
                    r"数据库|database|schema|table|索引|migration",
                    r"sql|mysql|postgresql|mongodb|redis",
                    r"数据模型|数据结构|存储"
                ]
            ),
            AgentMetadata(
                AgentType.API_DESIGN, "execution.coding_agent.CodingAgent",
                "负责 RESTful/GraphQL API 接口定义 and Swagger 文档生成", 2, 5,
                keywords=[r"api|接口|restful|graphql|swagger|endpoint|路由"]
            ),

            # 核心开发 (映射到 CodingAgent)
            AgentMetadata(
                AgentType.BACKEND_DEV, "execution.coding_agent.CodingAgent",
                "负责服务端业务逻辑、数据处理 and 系统集成", 3, 10,
                keywords=[
                    r"后端|backend|服务端|server|后台",
                    r"业务逻辑|数据处理|微服务|功能|管理",
                    r"fastapi|flask|django|express"
                ]
            ),
            AgentMetadata(
                AgentType.FRONTEND_DEV, "execution.coding_agent.CodingAgent",
                "负责 UI 组件开发、交互逻辑 and 前端架构", 3, 10,
                keywords=[
                    r"前端|frontend|界面|ui|页面",
                    r"react|vue|angular|组件",
                    r"用户体验|交互|响应式"
                ]
            ),
            AgentMetadata(
                AgentType.FULL_STACK_DEV, "execution.coding_agent.CodingAgent",
                "负责端到端的完整功能实现", 3, 8,
                keywords=[
                    r"全栈|fullstack|前后端",
                    r"全栈开发|完整应用"
                ]
            ),
            AgentMetadata(
                AgentType.MINI_PROGRAM_DEV, "execution.coding_agent.CodingAgent",
                "负责小程序/移动端专用逻辑开发", 4, 5,
                keywords=[r"小程序|微信小程序|uniapp|移动端|mobile"]
            ),

            # 质量保证与运维
            AgentMetadata(
                AgentType.TESTING, "execution.testing_agent.TestingAgent",
                "负责单元测试、集成测试、自动化测试脚本编写 and 漏洞扫描", 2, 5,
                keywords=[r"测试|test|junit|pytest|jest|cypress|selenium|coverage|单元测试|自动化测试"]
            ),
            AgentMetadata(
                AgentType.CODE_REVIEW, "execution.coding_agent.CodingAgent",
                "负责代码质量审查、安全漏洞检查 and 性能优化建议", 2, 5,
                keywords=[r"review|审查|审计|代码评审|质量|优化|代码规范"]
            ),
            AgentMetadata(
                AgentType.DEVOPS, "execution.coding_agent.CodingAgent",
                "负责 CI/CD 流水线配置、Docker 容器化 and 云原生部署 (K8s)", 4, 3,
                keywords=[r"devops|docker|k8s|kubernetes|jenkins|cicd|部署|pipeline|容器"]
            ),

            # 辅助类
            AgentMetadata(
                AgentType.DOCUMENTATION, "execution.documentation_agent.DocumentationAgent",
                "负责项目文档维护、API 文档生成 and 用户手册编写", 5, 2,
                keywords=[r"文档|doc|readme|manual|用户手册|注释|wiki"]
            ),
            AgentMetadata(
                AgentType.REFACTORING, "execution.refactoring_agent.RefactoringAgent",
                "负责遗留代码重构、架构升级 and 技术债清理", 3, 3,
                keywords=[r"重构|refactor|清理|解耦|架构升级|技术债"]
            ),

            # 自动化
            AgentMetadata(
                AgentType.N8N_AUTOMATION, "extensions.executors.n8n_executor.N8nExecutor",
                "负责 n8n 工作流自动化任务，包括工作流生成、模板应用和节点查询", 5, 3,
                keywords=[r"n8n|workflow|automation|自动化|工作流|webhook"]
            ),
            AgentMetadata(
                AgentType.PROMPT_ARCHITECT, "extensions.executors.prompt_executor.PromptExecutor",
                "负责提示词优化和结构化，将模糊需求转化为高质量提示词", 5, 3,
                keywords=[r"提示词|prompt|优化|结构化|写作|文案"]
            )
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
        """获取 Agent 实现类 (支持按需动态导入)"""
        meta = cls.get_metadata(agent_type)
        if not meta:
            return None

        if isinstance(meta.impl_class, str):
            # 动态导入类
            try:
                import importlib
                module_path, class_name = meta.impl_class.rsplit(".", 1)
                module = importlib.import_module(module_path)
                cls_obj = getattr(module, class_name)
                # 缓存回 metadata 以避免重复导入
                meta.impl_class = cls_obj
                return cls_obj
            except (ImportError, AttributeError) as e:
                logger.error(f"无法动态加载 Agent 类 {meta.impl_class}: {e}")
                return None

        return meta.impl_class

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
