#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
代码生成Agent (v3.2 - 完善版)

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

    # --- 常量定义 ---
    DEFAULT_TECH_STACK = ["Python", "FastAPI"]
    
    # 步骤标识
    STEP_ANALYZE = 1
    STEP_DESIGN = 2
    STEP_FINALIZE = 3
    
    # 模拟 Token 范围
    TOKEN_SIM_MIN = 1000
    TOKEN_SIM_MAX = 3000

    # 复杂度估算常量
    COMPLEXITY_BASE = 200
    COMPLEXITY_LEN_DIVISOR = 50
    COMPLEXITY_LEN_MULTIPLIER = 50
    COMPLEXITY_KEYWORD_MULTIPLIER = 100
    
    # 非功能性需求阈值
    WEB_RESPONSE_TIME_P95_MS = 200
    WEB_QPS_THRESHOLD = 100
    TEST_COVERAGE_THRESHOLD = 0.8  # 80%
    
    # 默认 API 参数
    DEFAULT_TOKEN_EXPIRY = 3600
    DEFAULT_PAGE_SIZE = 20

    def __init__(
        self,
        agent_id: str = "coding-agent",
        config: Optional[AgentConfig] = None,
        enable_tdd_validation: bool = True
    ):
        """初始化代码生成Agent

        Args:
            agent_id: Agent ID
            config: Agent配置
            enable_tdd_validation: 启用TDD验证 (P0 v3.2)
        """
        super().__init__(agent_id, config)

        # 使用基类方法初始化组件 (DRY 优化)
        self.setup_tdd(enabled=enable_tdd_validation, strict_mode=False)
        self.setup_debugger(enabled=True)

    @property
    def tdd_enabled(self) -> bool:
        """检查 TDD 是否启用 (兼容性属性)"""
        return self.tdd_validator is not None

    @property
    def debugging_enabled(self) -> bool:
        """检查调试器是否启用 (兼容性属性)"""
        return self.debugger is not None

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
        """实现代码生成任务的具体逻辑 (重构版 - 关注点分离)"""
        self.thoughts = []

        # 1. 分析与设计阶段
        description = task_input.get("description", "")
        tech_stack = task_input.get("tech_stack", self.DEFAULT_TECH_STACK)
        
        functional_reqs, non_functional_reqs = self._perform_requirement_analysis(description, tech_stack)
        architecture = self._perform_architecture_design(description, tech_stack)

        # 2. 工件生成阶段
        artifacts = self._generate_all_artifacts(context, description, tech_stack, functional_reqs, non_functional_reqs, architecture)

        # 3. 后处理与监控
        await self._finalize_agent_execution(context, len(functional_reqs), len(non_functional_reqs), len(artifacts))

        return artifacts

    def _perform_requirement_analysis(self, description: str, tech_stack: List[str]) -> tuple[List[str], List[str]]:
        """执行需求分析"""
        self.add_thought(step=1, thought=f"分析需求: {description}", action=f"技术栈: {', '.join(tech_stack)}")
        
        functional_reqs = self._extract_functional_requirements(description)
        self.add_log(f"提取了{len(functional_reqs)}个功能需求")
        
        non_functional_reqs = self._extract_non_functional_requirements(description, tech_stack)
        self.add_log(f"提取了{len(non_functional_reqs)}个非功能需求")
        
        return functional_reqs, non_functional_reqs

    def _perform_architecture_design(self, description: str, tech_stack: List[str]) -> Dict[str, Any]:
        """执行架构设计"""
        architecture = self._design_architecture(description, tech_stack)
        self.add_thought(
            step=2,
            thought="设计系统架构",
            action=f"架构模式: {architecture['pattern']}, 层数: {len(architecture['layers'])}"
        )
        return architecture

    def _generate_all_artifacts(
        self, 
        context: AgentContext, 
        description: str, 
        tech_stack: List[str],
        functional_reqs: List[str],
        non_functional_reqs: List[str],
        architecture: Dict[str, Any]
    ) -> List[Artifact]:
        """统一生成所有工件"""
        artifacts = []
        feature_name = self._sanitize_filename(description)

        # 1. 需求文档
        req_artifact = AgentOutputBuilder.create_requirements_artifact(
            feature_name=feature_name,
            functional_requirements=functional_reqs,
            non_functional_requirements=non_functional_reqs,
            technical_constraints=tech_stack,
            base_dir=context.project_root,
            worktree_path=context.worktree_path
        )
        artifacts.append(req_artifact)

        # 2. 架构文档
        arch_artifact = AgentOutputBuilder.create_architecture_artifact(
            feature_name=feature_name,
            pattern=architecture["pattern"],
            layers=architecture["layers"],
            dependencies=tech_stack,
            directory_structure=architecture["structure"],
            base_dir=context.project_root,
            worktree_path=context.worktree_path
        )
        artifacts.append(arch_artifact)

        # 3. API 规范 (可选)
        if self._needs_api(description):
            api_endpoints = self._design_api_endpoints(functional_reqs)
            api_artifact = AgentOutputBuilder.create_api_spec_artifact(
                feature_name=feature_name,
                endpoints=api_endpoints,
                base_dir=context.project_root,
                worktree_path=context.worktree_path
            )
            artifacts.append(api_artifact)

        # 4. 文件列表
        file_list = self._generate_file_list(architecture)
        file_list_artifact = AgentOutputBuilder.create_file_list_artifact(
            files=file_list,
            description=f"{feature_name} - 文件列表",
            base_dir=context.project_root,
            worktree_path=context.worktree_path
        )
        artifacts.append(file_list_artifact)

        self.add_log(f"已生成 {len(artifacts)} 个工件文档")
        return artifacts

    async def _finalize_agent_execution(self, context: AgentContext, func_count: int, non_func_count: int, artifact_count: int) -> None:
        """完成 Agent 执行后的指标记录与监控"""
        self.add_thought(step=self.STEP_FINALIZE, thought="生成工件和后续计划", action=f"生成了{artifact_count}个文档工件")
        
        self.set_metric("functional_requirements_count", func_count)
        self.set_metric("non_functional_requirements_count", non_func_count)
        self.set_metric("artifacts_count", artifact_count)

        # 记录模拟的 Token 使用 (此处应保留直到接入真实监控)
        import random
        simulated_tokens = random.randint(self.TOKEN_SIM_MIN, self.TOKEN_SIM_MAX)
        await self.log_usage(context, original_tokens=simulated_tokens)

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
        """提取非功能需求 (通用化升级: 避免默认假设为 Web 项目)"""
        # 1. 识别项目类型以匹配非功能性需求
        is_web = any(kw in description.lower() or kw in str(tech_stack).lower() 
                    for kw in ["web", "api", "http", "server", "fastapi", "flask", "django"])
        
        requirements = []

        if is_web:
            requirements.extend([
                f"性能: API 响应时间 < {self.WEB_RESPONSE_TIME_P95_MS}ms (P95)",
                f"并发: 支持至少 {self.WEB_QPS_THRESHOLD} QPS 的并发处理",
                "安全: API 接口支持 JWT 或 API Key 认证",
                "规范: 遵循 RESTful API 设计原则"
            ])
        else:
            # 针对 CLI/工具/库的通用需求
            requirements.extend([
                "健壮性: 完善的错误处理与用户友好的错误提示",
                f"可测试性: 核心逻辑单元测试覆盖率 > {int(self.TEST_COVERAGE_THRESHOLD * 100)}%",
                "可维护性: 遵循清晰的代码风格规范 (如 PEP8)",
                "性能: 启动时间与内存占用需控制在合理范围"
            ])

        # 根据技术栈添加特定需求 (保留部分有价值的推断)
        if any("PostgreSQL" in tech or "MySQL" in tech for tech in tech_stack):
            requirements.append("数据一致性: 确保数据库操作满足事务 ACID 特性")

        if "FastAPI" in tech_stack:
            requirements.append("文档自动化: 自动生成 Swagger/OpenAPI 文档")

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
            dir_structure = """src/
├── api/          # 接口定义
├── services/     # 业务逻辑
├── models/       # 数据模型
└── core/         # 核心配置"""
        elif is_system or is_cli:
            pattern = "模块化架构 (Modular Architecture)"
            layers = ["核心引擎 (Core Engine)", "适配器/驱动 (Adapters)", "工具集 (Utils)"]
            dir_structure = """src/
├── core/         # 核心逻辑
├── modules/      # 功能模块
├── utils/        # 通用工具
└── main.py       # 入口文件"""
        else:
            pattern = "通用分层架构"
            layers = ["呈现层", "逻辑层", "数据层"]
            dir_structure = """src/
├── domain/       # 领域模型
├── app/          # 应用逻辑
└── infra/         # 基础设施"""

        return {
            "pattern": pattern,
            "layers": layers,
            "structure": dir_structure
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
                    "expires_in": self.DEFAULT_TOKEN_EXPIRY
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
                "page_size": self.DEFAULT_PAGE_SIZE
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
        dir_structure = architecture["structure"]
        files = []

        # 解析目录结构
        for line in dir_structure.split('\n'):
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
        base = self.COMPLEXITY_BASE
        # 基于描述长度
        length_multiplier = len(description) // self.COMPLEXITY_LEN_DIVISOR
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

        return base + (length_multiplier * self.COMPLEXITY_LEN_MULTIPLIER) + (keyword_multiplier * self.COMPLEXITY_KEYWORD_MULTIPLIER)

    # ========== P0 v3.2: TDD 验证集成 ==========

    def validate_tdd_execution(self, task_result: Any) -> tuple[bool, List[str]]:
        """验证任务执行的 TDD 工作流

        Args:
            task_result: ExecutionResult 对象,必须包含 tdd_trace 字段
                        tdd_trace 应该是 List[TDDTraceEntry]

        Returns:
            tuple[bool, List[str]]: (是否通过, 违规列表)
        """
        if not self.tdd_enabled or not self.tdd_validator:
            return True, []  # TDD 未启用,直接通过

        try:
            # 使用实际的 TDD Validator API
            is_valid = self.tdd_validator.validate_execution_flow(task_result)
            violations = self.tdd_validator.get_violations()

            if not is_valid:
                logger.warning(f"TDD 工作流验证失败，发现 {len(violations)} 个违规")
                for violation in violations:
                    logger.warning(f"  - {violation}")
            else:
                logger.info("TDD 工作流验证通过")

            return is_valid, violations
        except Exception as e:
            logger.error(f"TDD 验证过程出错: {e}")
            return False, [f"验证异常: {str(e)}"]

    def has_tdd_violations(self) -> bool:
        """检查是否有 TDD 违规

        Returns:
            bool: 如果有违规返回 True
        """
        if not self.tdd_enabled or not self.tdd_validator:
            return False

        return self.tdd_validator.has_violations()

    def get_tdd_violations(self) -> List[str]:
        """获取 TDD 违规列表

        Returns:
            List[str]: 违规描述列表
        """
        if not self.tdd_enabled or not self.tdd_validator:
            return []

        return self.tdd_validator.get_violations()

    # ========== P1 Task 2.2: SystematicDebugger 集成 ==========

    def debug_error(
        self,
        error_type: str,
        error_message: str,
        stack_trace: List[str],
        code_context: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """对错误进行系统化调试

        Args:
            error_type: 错误类型 (例如: "ValueError", "ImportError")
            error_message: 错误消息
            stack_trace: 堆栈跟踪列表
            code_context: 代码上下文 (可选)

        Returns:
            Optional[Dict[str, Any]]: 调试报告字典,如果调试失败返回 None
        """
        if not self.debugging_enabled or not self.debugger:
            logger.warning("SystematicDebugger 未启用,跳过调试")
            return None

        try:
            # 阶段 1: 观察错误
            error_info = {
                "error_type": error_type,
                "error_message": error_message,
                "stack_trace": stack_trace,
                "code_context": code_context or {}
            }

            observation = self.debugger.start_debugging(error_info)
            logger.info(f"【调试阶段 1】错误观察完成: {observation.error_type}")

            # 阶段 2: 生成假设
            hypotheses = self.debugger.generate_hypotheses(observation)
            logger.info(f"【调试阶段 2】生成 {len(hypotheses)} 个假设")

            # 阶段 3: 验证假设 (自动验证第一个假设)
            # 在实际使用中,这里应该由用户提供测试结果
            # 现在我们模拟一个简单的验证过程
            first_hypothesis = hypotheses[0]
            test_results = [
                "检查错误类型匹配",
                "验证错误消息一致性"
            ]

            verification = self.debugger.verify_hypothesis(first_hypothesis, test_results)
            logger.info(
                f"【调试阶段 3】假设验证完成: "
                f"{'成立' if verification.is_valid else '不成立'} "
                f"(置信度: {verification.confidence:.2f})"
            )

            # 阶段 4: 确认根因
            root_cause = self.debugger.confirm_root_cause(first_hypothesis.hypothesis_id)
            logger.info(f"【调试阶段 4】根因确认完成: {root_cause.root_cause_id}")

            # 获取完整调试报告
            report = self.debugger.get_debugging_report()

            # 转换为字典格式返回
            return {
                "error_type": report.observation.error_type,
                "error_message": report.observation.error_message,
                "hypotheses": [
                    {
                        "id": h.hypothesis_id,
                        "title": h.title,
                        "description": h.description,
                        "likelihood": h.likelihood
                    }
                    for h in report.hypotheses
                ],
                "root_cause": {
                    "id": root_cause.root_cause_id,
                    "description": root_cause.description,
                    "fix_suggestions": root_cause.fix_suggestions,
                    "prevention_strategies": root_cause.prevention_strategies
                },
                "debugging_phase": report.phase.value,
                "created_at": report.created_at,
                "completed_at": report.completed_at
            }

        except Exception as e:
            logger.error(f"调试过程出错: {e}")
            import traceback
            traceback.print_exc()
            return None

    def is_debugging_enabled(self) -> bool:
        """检查调试功能是否启用

        Returns:
            bool: 如果调试功能启用返回 True
        """
        return self.debugging_enabled and self.debugger is not None

    def get_current_debugging_phase(self) -> Optional[str]:
        """获取当前调试阶段

        Returns:
            Optional[str]: 当前调试阶段名称,如果未启动调试返回 None
        """
        if not self.debugging_enabled or not self.debugger:
            return None

        return self.debugger.get_current_phase().value

    def reset_debugger(self):
        """重置调试器状态"""
        if self.debugging_enabled and self.debugger:
            self.debugger.reset()
            logger.info("SystematicDebugger 已重置")

