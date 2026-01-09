#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
代码生成Agent (v3.0 - 完善版)

负责根据需求生成代码框架和需求文档,而非完整代码
"""

import asyncio
import logging
import re
from typing import List, Dict, Any, Set, Optional
from pathlib import Path

from .base_agent import BaseAgent
from .models import (
    AgentCapability,
    AgentResult,
    AgentContext,
    AgentConfig,
    AgentStatus,
    Artifact
)
from .agent_output_builder import AgentOutputBuilder


logger = logging.getLogger(__name__)


class CodingAgent(BaseAgent):
    """代码生成Agent - 返回需求框架而非完整代码"""

    def __init__(
        self,
        agent_id: str = "coding-agent",
        config: Optional[AgentConfig] = None
    ):
        """初始化代码生成Agent

        Args:
            agent_id: Agent ID
            config: Agent配置
        """
        super().__init__(agent_id, config)

    @property
    def name(self) -> str:
        """返回Agent名称"""
        return "代码生成Agent"

    @classmethod
    def get_capabilities(cls) -> Set[AgentCapability]:
        """返回Agent能力"""
        return {
            AgentCapability.CODE_GENERATION,
            AgentCapability.ARCHITECTURE
        }

    async def plan(
        self,
        context: AgentContext,
        task_input: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """规划执行步骤"""
        self.add_step("analyze_requirements", "分析功能需求", "功能需求列表")
        self.add_step("design_architecture", "设计系统架构", "架构设计文档")
        self.add_step("generate_documents", "生成需求文档", "REQUIREMENTS.md, ARCHITECTURE.md等")
        return self.steps

    async def execute_impl(
        self,
        context: AgentContext,
        task_input: Dict[str, Any]
    ) -> List[Artifact]:
        """实现代码生成任务的具体逻辑 (Phase 3 优化)"""
        self.thoughts = []  # 清空之前的思考过程

        # 步骤1: 分析需求
        description = task_input.get("description", "")
        tech_stack = task_input.get("tech_stack", ["Python", "FastAPI"])

        self.add_thought(
            step=1,
            thought=f"分析需求: {description}",
            action=f"技术栈: {', '.join(tech_stack)}"
        )

        # 提取功能需求
        functional_reqs = self._extract_functional_requirements(description)
        self.add_log(f"提取了{len(functional_reqs)}个功能需求")

        # 提取非功能需求
        non_functional_reqs = self._extract_non_functional_requirements(description, tech_stack)
        self.add_log(f"提取了{len(non_functional_reqs)}个非功能需求")

        # 步骤2: 设计架构
        architecture = self._design_architecture(description, tech_stack)

        self.add_thought(
            step=2,
            thought="设计系统架构",
            action=f"架构模式: {architecture['pattern']}, 层数: {len(architecture['layers'])}"
        )

        # 步骤3: 生成工件列表
        artifacts = []

        # 生成需求文档
        req_artifact = AgentOutputBuilder.create_requirements_artifact(
            feature_name=self._sanitize_filename(description),
            functional_requirements=functional_reqs,
            non_functional_requirements=non_functional_reqs,
            technical_constraints=tech_stack,
            base_dir=context.project_root,
            worktree_path=context.worktree_path
        )
        artifacts.append(req_artifact)
        self.add_log(f"生成需求文档: {req_artifact.path}")

        # 生成架构文档
        arch_artifact = AgentOutputBuilder.create_architecture_artifact(
            feature_name=self._sanitize_filename(description),
            pattern=architecture["pattern"],
            layers=architecture["layers"],
            dependencies=tech_stack,
            directory_structure=architecture["structure"],
            base_dir=context.project_root,
            worktree_path=context.worktree_path
        )
        artifacts.append(arch_artifact)
        self.add_log(f"生成架构文档: {arch_artifact.path}")

        # 生成API规范(如果需要)
        if self._needs_api(description):
            api_endpoints = self._design_api_endpoints(functional_reqs)
            api_artifact = AgentOutputBuilder.create_api_spec_artifact(
                feature_name=self._sanitize_filename(description),
                endpoints=api_endpoints,
                base_dir=context.project_root,
                worktree_path=context.worktree_path
            )
            artifacts.append(api_artifact)
            self.add_log(f"生成API规范: {api_artifact.path}")

        # 生成文件列表
        file_list = self._generate_file_list(architecture)
        file_list_artifact = AgentOutputBuilder.create_file_list_artifact(
            files=file_list,
            description=f"{self._sanitize_filename(description)} - 文件列表",
            base_dir=context.project_root,
            worktree_path=context.worktree_path
        )
        artifacts.append(file_list_artifact)
        self.add_log(f"生成文件列表: {file_list_artifact.path}")

        self.add_thought(
            step=3,
            thought="生成工件和后续计划",
            action=f"生成了{len(artifacts)}个文档工件"
        )

        # 设置指标
        self.set_metric("functional_requirements_count", len(functional_reqs))
        self.set_metric("non_functional_requirements_count", len(non_functional_reqs))
        self.set_metric("artifacts_count", len(artifacts))

        return artifacts

    def _extract_functional_requirements(self, description: str) -> List[str]:
        """从描述中提取功能需求 (跨领域通用化)"""
        requirements = []

        # 定义通用功能维度
        patterns = {
            # 1. 数据持久化
            r"数据库|存储|持久化|save|db": "数据持久化 - 实现数据的可靠存储与检索",
            # 2. 通信/接口
            r"API|接口|REST|RPC|通信|network": "通信接口 - 实现模块间或系统间的交互协议",
            # 3. 用户交互
            r"用户|界面|UI|交互|frontend": "用户交互 - 实现直观、友好的操作界面与反馈机制",
            # 4. 安全/权限
            r"安全|权限|认证|加密|auth": "安全机制 - 确保数据访问受控与传输加密",
            # 5. 核心逻辑/算法
            r"计算|算法|处理|logic|core": "核心逻辑 - 实现业务所需的计算、转换或处理算法",
            # 6. 文件/资源管理
            r"文件|上传|下载|资源|file": "资源管理 - 实现对文件、内存或外部资源的有效管理",
            # 7. 并发/性能
            r"并发|多线程|性能|optimize": "并发处理 - 确保系统在高负载下的稳定性与响应速度",
            # 8. 监控/日志
            r"日志|监控|审计|log": "可观测性 - 实现日志记录与运行状态监控"
        }

        # 匹配模式
        for pattern, requirement in patterns.items():
            if re.search(pattern, description, re.IGNORECASE):
                requirements.append(requirement)

        # 如果没有匹配到,生成通用需求
        if not requirements:
            requirements = [
                "基本功能实现 - 根据需求描述实现核心功能",
                "数据验证 - 输入参数验证和错误处理",
                "异常处理 - 完善的异常捕获和错误返回"
            ]

        logger.debug(f"提取功能需求: {requirements}")
        return requirements

    def _extract_non_functional_requirements(
        self,
        description: str,
        tech_stack: List[str]
    ) -> List[str]:
        """提取非功能需求

        Args:
            description: 功能描述
            tech_stack: 技术栈

        Returns:
            List[str]: 非功能需求列表
        """
        requirements = [
            "性能: API响应时间 < 200ms (P95)",
            "安全: 密码使用bcrypt或Argon2加密存储",
            "可用性: 99.9% uptime,支持优雅降级",
            "可扩展性: 支持水平扩展,无状态设计"
        ]

        # 根据技术栈添加特定需求
        if any("PostgreSQL" in tech or "MySQL" in tech for tech in tech_stack):
            requirements.append("数据持久化: 使用关系型数据库,支持事务ACID")

        if any("Redis" in tech for tech in tech_stack):
            requirements.append("缓存策略: 热点数据缓存,缓存过期时间合理设置")

        if "FastAPI" in tech_stack:
            requirements.append("API规范: 遵循OpenAPI 3.0规范,自动生成API文档")

        logger.debug(f"非功能需求: {requirements}")
        return requirements

    def _design_architecture(
        self,
        description: str,
        tech_stack: List[str]
    ) -> Dict[str, Any]:
        """设计架构 (支持多技术栈与模式)"""
        
        # 1. 识别项目类型
        is_web = any(kw in description.lower() or kw in str(tech_stack).lower() 
                    for kw in ["web", "api", "http", "fastapi", "flask", "django", "spring"])
        is_cli = any(kw in description.lower() for kw in ["cli", "command", "工具", "命令行"])
        is_system = any(kw in str(tech_stack).lower() for kw in ["rust", "cpp", "c++", "golang", "embedded"])

        if is_web:
            pattern = "分层架构 (Layered Architecture)"
            layers = ["接口层 (API/Controller)", "业务逻辑层 (Service)", "数据持久化层 (Repository/DAO)"]
            structure = """src/
├── api/          # 接口定义
├── services/     # 业务逻辑
├── models/       # 数据模型
└── core/         # 核心配置"""
        elif is_system or is_cli:
            pattern = "模块化架构 (Modular Architecture)"
            layers = ["核心引擎 (Core Engine)", "适配器/驱动 (Adapters)", "工具集 (Utils)"]
            structure = """src/
├── core/         # 核心逻辑
├── modules/      # 功能模块
├── utils/        # 通用工具
└── main.py       # 入口文件"""
        else:
            pattern = "通用分层架构"
            layers = ["呈现层", "逻辑层", "数据层"]
            structure = """src/
├── domain/       # 领域模型
├── app/          # 应用逻辑
└── infra/         # 基础设施"""

        return {
            "pattern": pattern,
            "layers": layers,
            "structure": structure
        }

    def _needs_api(self, description: str) -> bool:
        """判断是否需要API

        Args:
            description: 功能描述

        Returns:
            bool: 是否需要API
        """
        api_keywords = ["API", "接口", "web", "服务", "server", "http"]
        return any(keyword in description.lower() for keyword in api_keywords)

    def _design_api_endpoints(self, functional_reqs: List[str]) -> List[Dict[str, Any]]:
        """设计API端点

        Args:
            functional_reqs: 功能需求列表

        Returns:
            List[Dict]: API端点列表
        """
        endpoints = []

        # 用户注册
        if any("注册" in req or "用户" in req for req in functional_reqs):
            endpoints.append({
                "method": "POST",
                "path": "/api/v1/users/register",
                "description": "注册新用户",
                "request": {
                    "email": "user@example.com",
                    "password": "secure_password",
                    "username": "johndoe"
                },
                "response": {
                    "user_id": "123",
                    "email": "user@example.com",
                    "username": "johndoe",
                    "created_at": "2026-01-09T00:00:00Z"
                }
            })

        # 用户登录
        if any("登录" in req or "认证" in req for req in functional_reqs):
            endpoints.append({
                "method": "POST",
                "path": "/api/v1/users/login",
                "description": "用户登录",
                "request": {
                    "email": "user@example.com",
                    "password": "secure_password"
                },
                "response": {
                    "token": "jwt_token_here",
                    "token_type": "Bearer",
                    "expires_in": 3600
                }
            })

        # 通用CRUD端点
        endpoints.append({
            "method": "GET",
            "path": "/api/v1/resources/{id}",
            "description": "获取单个资源",
            "response": {
                "id": "123",
                "name": "Resource Name",
                "created_at": "2026-01-09T00:00:00Z"
            }
        })

        endpoints.append({
            "method": "GET",
            "path": "/api/v1/resources",
            "description": "获取资源列表",
            "response": {
                "items": [],
                "total": 0,
                "page": 1,
                "page_size": 20
            }
        })

        return endpoints

    def _generate_file_list(self, architecture: Dict[str, Any]) -> List[str]:
        """生成文件列表

        Args:
            architecture: 架构信息

        Returns:
            List[str]: 文件路径列表
        """
        structure = architecture["structure"]
        files = []

        # 解析目录结构
        for line in structure.split('\n'):
            line = line.strip()
            if line.endswith('.py') or line.endswith('.txt') or line.endswith('.md'):
                # 提取文件路径
                file_path = line.split('|')[-1].strip()
                if file_path and not file_path.startswith('#'):
                    files.append(file_path)

        return files

    def _sanitize_filename(self, name: str, max_length: int = 50) -> str:
        """清理文件名 (增强版)"""
        if not name or name.isspace():
            return "unnamed_feature"
            
        # 移除不合法字符
        sanitized = re.sub(r'[<>:"/\\|?*]', '', name)
        # 替换空格为下划线
        sanitized = sanitized.replace(' ', '_')
        # 截断长度
        return sanitized[:max_length] or "feature"

    def _estimate_complexity(self, description: str) -> int:
        """估算代码复杂度(行数)

        Args:
            description: 功能描述

        Returns:
            int: 估算的代码行数
        """
        base = 200
        # 基于描述长度
        length_multiplier = len(description) // 50
        # 基于关键词
        keyword_multiplier = 0
        complexity_keywords = {
            "API": 1,
            "数据库": 2,
            "缓存": 1,
            "权限": 2,
            "日志": 1
        }
        for keyword, multiplier in complexity_keywords.items():
            if keyword in description:
                keyword_multiplier += multiplier

        return base + (length_multiplier * 50) + (keyword_multiplier * 100)

