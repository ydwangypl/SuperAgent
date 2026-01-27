#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
基础Agent类

定义所有Agent的通用接口和行为
"""

import asyncio
import logging
import json
import aiofiles
from datetime import datetime
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Set, TYPE_CHECKING
from pathlib import Path

from .models import (
    AgentCapability,
    AgentResult,
    AgentContext,
    AgentConfig,
    AgentStatus,
    Artifact,
    AgentThought
)
from common.security import sanitize_input, check_sensitive_data

# 动态导入 SmartContextCompressor (避免循环依赖)
try:
    from context.smart_compressor import SmartContextCompressor
    COMPRESSOR_AVAILABLE = True
except ImportError:
    COMPRESSOR_AVAILABLE = False
    SmartContextCompressor = None

# TDD Validator 动态导入 (DRY 优化)
try:
    from execution.tdd_validator import TDDValidator
    TDD_AVAILABLE = True
except ImportError:
    TDD_AVAILABLE = False
    TDDValidator = None

# SystematicDebugger 动态导入 (DRY 优化)
try:
    from execution.systematic_debugger import SystematicDebugger
    DEBUGGER_AVAILABLE = True
except ImportError:
    DEBUGGER_AVAILABLE = False
    SystematicDebugger = None

# v3.3: FindingsManager 动态导入 (Planning Files 模块)
try:
    from extensions.planning_files import FindingsManager
    FINDINGS_AVAILABLE = True
except ImportError:
    FINDINGS_AVAILABLE = False
    FindingsManager = None  # type: ignore

# v3.3: ProgressManager 动态导入 (Planning Files 模块)
try:
    from extensions.planning_files import ProgressManager
    PROGRESS_AVAILABLE = True
except ImportError:
    PROGRESS_AVAILABLE = False
    ProgressManager = None  # type: ignore


logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Agent基类"""

    def __init__(
        self,
        agent_id: str,
        config: Optional[AgentConfig] = None
    ):
        """初始化Agent

        Args:
            agent_id: Agent唯一标识
            config: Agent配置
        """
        self.agent_id = agent_id
        self.config = config or AgentConfig()
        self.status = AgentStatus.IDLE

        # 思考过程记录
        self.thoughts: List[AgentThought] = []
        
        # 步骤规划记录 (Phase 3 优化)
        self.steps: List[Dict[str, Any]] = []
        
        # 运行时日志和指标 (Phase 3 优化)
        self._current_logs: List[str] = []
        self._current_metrics: Dict[str, Any] = {}

        # 核心组件初始化 (DRY 优化)
        self.tdd_validator: Optional[TDDValidator] = None
        self.debugger: Optional[SystematicDebugger] = None

        # v3.3: Planning Files 组件 (Findings & Progress)
        self.findings_manager: Any = None
        self.progress_manager: Any = None

        logger.info(f"Agent {self.agent_id} 初始化完成")

    def setup_tdd(self, enabled: bool = True, strict_mode: bool = False):
        """设置 TDD 验证组件"""
        if enabled and TDD_AVAILABLE:
            self.tdd_validator = TDDValidator(strict_mode=strict_mode)
            logger.info(f"Agent {self.agent_id}: TDD Validator 已启用")
        else:
            self.tdd_validator = None

    def setup_debugger(self, enabled: bool = True):
        """设置调试器组件"""
        if enabled and DEBUGGER_AVAILABLE:
            self.debugger = SystematicDebugger()
            logger.info(f"Agent {self.agent_id}: SystematicDebugger 已启用")
        else:
            self.debugger = None

    def setup_findings_manager(self, project_root: Path, memory_manager = None):
        """设置 FindingsManager (v3.3)

        用于将研究发现写入 findings.md 并与 MemoryManager 联动
        """
        if FINDINGS_AVAILABLE:
            self.findings_manager = FindingsManager(
                project_root=project_root,
                findings_file=project_root / "docs" / "findings.md",
                memory_manager=memory_manager
            )
            logger.info(f"Agent {self.agent_id}: FindingsManager 已启用")
        else:
            self.findings_manager = None

    def setup_progress_manager(self, project_root: Path, session_id: str = None):
        """设置 ProgressManager (v3.3)

        用于记录会话进度到 progress.md
        """
        if PROGRESS_AVAILABLE:
            self.progress_manager = ProgressManager(
                project_root=project_root,
                progress_file=project_root / "docs" / "progress.md",
                session_id=session_id
            )
            logger.info(f"Agent {self.agent_id}: ProgressManager 已启用")
        else:
            self.progress_manager = None

    async def write_finding(
        self,
        content: str,
        category: str = "general",
        impact: str = "",
        source: str = ""
    ) -> Optional[str]:
        """记录研究发现 (v3.3)

        将研究发现写入 findings.md 并同步到 MemoryManager

        Args:
            content: 发现内容
            category: 分类 (architecture, implementation, testing, etc.)
            impact: 影响范围
            source: 来源

        Returns:
            finding_id 或 None (如果失败)
        """
        if self.findings_manager:
            try:
                return await self.findings_manager.add_finding(
                    content=content,
                    category=category,
                    impact=impact,
                    source=source or self.agent_id
                )
            except Exception as e:
                logger.error(f"记录研究发现失败: {e}")
        return None

    async def log_progress(
        self,
        action: str,
        status: str,
        details: str = ""
    ) -> None:
        """记录进度到 progress.md (v3.3)

        Args:
            action: 操作名称
            status: 状态 (started, completed, failed, etc.)
            details: 详细信息
        """
        if self.progress_manager:
            try:
                await self.progress_manager.log_progress(
                    action=action,
                    status=status,
                    details=details
                )
            except Exception as e:
                logger.error(f"记录进度失败: {e}")

    @classmethod
    @abstractmethod
    def get_capabilities(cls) -> Set[AgentCapability]:
        """获取Agent的能力集合(无需实例化)

        Returns:
            Set[AgentCapability]: 能力集合
        """
        pass

    @property
    def capabilities(self) -> Set[AgentCapability]:
        """实例化的能力访问

        Returns:
            Set[AgentCapability]: 能力集合
        """
        return self.get_capabilities()

    @property
    @abstractmethod
    def name(self) -> str:
        """返回Agent名称

        Returns:
            str: Agent名称
        """
        pass

    def _optimize_context(self, context: AgentContext) -> AgentContext:
        """优化执行上下文，减少 Token 消耗"""
        if not COMPRESSOR_AVAILABLE:
            return context

        try:
            # 智能截断过长的任务描述和之前的结果
            # 获取当前 Agent 类型 (从 class name 或 type 属性)
            agent_type_str = self.__class__.__name__.lower().replace("agent", "")
            
            # 使用 SmartContextCompressor 进行压缩
            # 这里的规则可以根据 Agent 类型定制
            if len(context.description) > 1000 or (context.previous_results and len(str(context.previous_results)) > 2000):
                self.add_log(f"检测到上下文过大，正在进行智能 Token 优化...")
                
                # 任务描述压缩
                if len(context.description) > 1000:
                    context.description = SmartContextCompressor.compress_semantic(context.description)
                
                # 历史结果压缩 (如果是 List[AgentResult])
                if context.previous_results and len(context.previous_results) > 3:
                    # 仅保留最近 3 个结果的关键信息
                    context.previous_results = context.previous_results[-3:]
            
            return context
        except Exception as e:
            logger.warning(f"上下文优化失败: {e}")
            return context

    async def execute(
        self,
        context: AgentContext,
        task_input: Dict[str, Any]
    ) -> AgentResult:
        """执行任务 (模板方法 - Phase 3 优化)

        Args:
            context: 执行上下文
            task_input: 任务输入

        Returns:
            AgentResult: 执行结果
        """
        self.status = AgentStatus.WORKING
        self._current_logs = []  # 重置日志
        self._current_metrics = {}  # 重置指标
        self.clear_thoughts()  # 重置思考过程
        self.steps = []  # 重置步骤

        # 1. 优化上下文 (Token 优化)
        context = self._optimize_context(context)
        
        result = AgentResult(
            agent_id=self.agent_id,
            task_id=context.task_id,
            step_id=context.step_id,
            status=AgentStatus.WORKING
        )

        # v3.3: 记录任务开始进度
        await self.log_progress(
            action=f"任务开始: {context.task_id}",
            status="started",
            details=f"Agent: {self.name}"
        )

        self.add_log(f"开始执行任务: {context.task_id} ({self.name})")

        try:
            # 1. 自动执行规划 (如果子类没手动调用的的话)
            if hasattr(self, 'plan') and callable(self.plan):
                await self.plan(context, task_input)

            # 2. 执行子类具体实现
            artifacts = await self.execute_impl(context, task_input)
            
            result.artifacts = artifacts
            result.logs = self._current_logs
            result.steps = self.steps
            result.metrics = self._current_metrics
            result.success = True
            result.status = AgentStatus.COMPLETED
            result.message = "任务执行成功"
            self.add_log(f"任务执行成功，生成了 {len(artifacts)} 个工件")

        except (ValueError, TypeError, KeyError) as e:
            error_msg = f"输入数据错误: {str(e)}"
            self.add_log(f"执行失败: {error_msg}")
            result.success = False
            result.status = AgentStatus.FAILED
            result.error = error_msg
            result.message = f"任务执行失败 (输入错误): {str(e)}"
        except asyncio.TimeoutError:
            error_msg = "执行超时"
            self.add_log(f"执行失败: {error_msg}")
            result.success = False
            result.status = AgentStatus.FAILED
            result.error = error_msg
            result.message = "任务执行超时，请重试"
        except Exception as e:
            error_msg = f"系统异常 ({type(e).__name__}): {str(e)}"
            self.add_log(f"执行失败: {error_msg}")
            result.success = False
            result.status = AgentStatus.FAILED
            result.error = error_msg
            result.message = f"任务执行失败 (系统异常): {str(e)}"
        finally:
            # v3.3: 记录任务结束进度
            status = "completed" if result.status == AgentStatus.COMPLETED else "failed"
            await self.log_progress(
                action=f"任务结束: {context.task_id}",
                status=status,
                details=result.message or ""
            )

            if result.status != AgentStatus.COMPLETED:
                self.status = AgentStatus.FAILED
            else:
                self.status = AgentStatus.IDLE

        return result

    @abstractmethod
    async def execute_impl(
        self,
        context: AgentContext,
        task_input: Dict[str, Any]
    ) -> List[Artifact]:
        """子类实现的具体执行逻辑 (Phase 3 抽象接口)

        Args:
            context: 执行上下文
            task_input: 任务输入

        Returns:
            List[Artifact]: 生成的产出物列表
        """
        pass

    async def run(
        self,
        context: AgentContext,
        task_input: Dict[str, Any]
    ) -> AgentResult:
        """运行Agent(带重试机制)

        Args:
            context: 执行上下文
            task_input: 任务输入

        Returns:
            AgentResult: 执行结果
        """
        from datetime import datetime

        result = None
        last_error = None

        for attempt in range(self.config.max_retries + 1):
            try:
                if attempt > 0:
                    logger.info(f"重试第 {attempt} 次 (Agent: {self.agent_id})...")
                    await asyncio.sleep(self.config.retry_delay)

                # 更新状态
                self.status = AgentStatus.WORKING

                # 1. 验证输入
                if not self.validate_input(task_input):
                    error_msg = f"Agent {self.agent_id}: 输入验证失败"
                    logger.error(error_msg)
                    return AgentResult(
                        agent_id=self.agent_id,
                        task_id=context.task_id,
                        step_id=context.step_id,
                        status=AgentStatus.FAILED,
                        success=False,
                        error=error_msg
                    )

                # 记录开始时间
                started_at = datetime.now()

                # 执行任务
                result = await self.execute(context, task_input)

                # 记录结束时间
                completed_at = datetime.now()
                result.started_at = started_at
                result.completed_at = completed_at
                result.duration_seconds = (completed_at - started_at).total_seconds()

                # 检查是否成功
                if result.success:
                    self.status = AgentStatus.COMPLETED
                    logger.info(
                        f"Agent {self.agent_id} 执行成功, "
                        f"耗时 {result.duration_seconds:.2f}秒"
                    )

                    # 保存中间结果(如果配置)
                    if self.config.save_intermediate:
                        await self._save_intermediate_result(context, result)

                    return result  # 成功直接返回
                else:
                    # 执行失败但无异常，记录错误并判断是否需要重试
                    last_error = result.message or result.error or "业务执行失败"
                    logger.warning(f"Agent {self.agent_id} 第 {attempt + 1} 次尝试失败: {last_error}")
                    
                    if attempt == self.config.max_retries:
                        self.status = AgentStatus.FAILED
                        return result

            except asyncio.CancelledError:
                self.status = AgentStatus.FAILED
                error_msg = f"Agent {self.agent_id} 任务被物理取消"
                logger.warning(error_msg)
                return AgentResult(
                    agent_id=self.agent_id,
                    task_id=context.task_id,
                    step_id=context.step_id,
                    status=AgentStatus.FAILED,
                    success=False,
                    error=error_msg
                )
            except (TimeoutError, ConnectionError, RuntimeError) as e:
                last_error = f"运行时异常: {str(e)}"
                logger.error(f"Agent {self.agent_id} 第 {attempt + 1} 次尝试发生错误: {e}")
                if attempt == self.config.max_retries:
                    self.status = AgentStatus.FAILED
                    return AgentResult(
                        agent_id=self.agent_id,
                        task_id=context.task_id,
                        step_id=context.step_id,
                        status=AgentStatus.FAILED,
                        success=False,
                        error=last_error
                    )
            except Exception as e:
                last_error = f"非预期异常 ({type(e).__name__}): {str(e)}"
                logger.exception(f"Agent {self.agent_id} 第 {attempt + 1} 次尝试发生非预期异常 ({type(e).__name__}): {e}")

                if attempt == self.config.max_retries:
                    self.status = AgentStatus.FAILED
                    return AgentResult(
                        agent_id=self.agent_id,
                        task_id=context.task_id,
                        step_id=context.step_id,
                        status=AgentStatus.FAILED,
                        success=False,
                        error=last_error,
                        error_details={"exception_type": type(e).__name__, "attempts": attempt + 1}
                    )
        
        return result

    @abstractmethod
    async def plan(
        self,
        context: AgentContext,
        task_input: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """规划执行步骤

        Args:
            context: 执行上下文
            task_input: 任务输入

        Returns:
            List[Dict[str, Any]]: 执行步骤列表
        """
        pass

    async def think(
        self,
        context: AgentContext,
        task_input: Dict[str, Any]
    ) -> AgentResult:
        """思考过程(可选实现)

        Args:
            context: 执行上下文
            task_input: 任务输入

        Returns:
            AgentResult: 思考结果
        """
        # 默认实现:直接调用execute
        return await self.execute(context, task_input)

    def add_thought(
        self,
        step: int,
        thought: str,
        action: Optional[str] = None,
        observation: Optional[str] = None
    ):
        """添加思考记录

        Args:
            step: 思考步骤
            thought: 思考内容
            action: 计划采取的行动
            observation: 观察结果
        """
        thought_record = AgentThought(
            step=step,
            thought=thought,
            action=action,
            observation=observation
        )
        self.thoughts.append(thought_record)
        logger.debug(f"思考步骤 {step}: {thought}")

    def get_thoughts(self) -> List[AgentThought]:
        """获取所有思考记录

        Returns:
            List[AgentThought]: 思考记录列表
        """
        return self.thoughts

    def clear_thoughts(self):
        """清空思考记录"""
        self.thoughts.clear()

    def add_log(self, message: str):
        """添加执行日志 (Phase 3 优化)"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self._current_logs.append(log_entry)
        logger.info(f"[{self.agent_id}] {message}")

    def add_step(self, action: str, description: str, output: str):
        """添加规划步骤 (Phase 3 优化)
        
        Args:
            action: 行动标识
            description: 步骤描述
            output: 预期输出内容
        """
        step_num = len(self.steps) + 1
        self.steps.append({
            "step": step_num,
            "action": action,
            "description": description,
            "output": output
        })
        logger.debug(f"添加规划步骤 {step_num}: {description}")

    def set_metric(self, key: str, value: Any):
        """设置执行指标 (Phase 3 优化)"""
        self._current_metrics[key] = value

    async def log_usage(
        self,
        context: AgentContext,
        original_tokens: int,
        compressed_tokens: int = 0,
        incremental_tokens: int = 0,
        files_processed: int = 0,
        files_incremental: int = 0,
        compression_method: str = ""
    ):
        """记录 Token 使用情况 (Phase 3 优化)
        
        通过 context 中的 token_monitor 记录使用量。
        如果 monitor 不可用, 则仅记录日志。
        """
        if context.token_monitor:
            try:
                await context.token_monitor.log_usage(
                    agent_type=self.agent_id,
                    task_id=context.task_id,
                    original_tokens=original_tokens,
                    compressed_tokens=compressed_tokens,
                    incremental_tokens=incremental_tokens,
                    files_processed=files_processed,
                    files_incremental=files_incremental,
                    compression_method=compression_method
                )
                # 同时更新内部指标
                self.set_metric("tokens_original", original_tokens)
                self.set_metric("tokens_compressed", compressed_tokens or original_tokens)
            except Exception as e:
                logger.error(f"记录 Token 使用失败: {e}")
        else:
            logger.debug(f"Agent {self.agent_id} 使用了 {original_tokens} tokens (监控器不可用)")

    async def _save_intermediate_result(
        self,
        context: AgentContext,
        result: AgentResult
    ):
        """保存中间结果 (异步IO实现)
        
        Args:
            context: 执行上下文
            result: 执行结果
        """
        try:
            # 创建输出目录
            output_dir = self.config.output_dir or context.project_root / ".superagent" / "intermediate"
            output_dir = Path(output_dir)
            
            # 确保目录存在 (使用 to_thread 防止阻塞)
            await asyncio.to_thread(output_dir.mkdir, parents=True, exist_ok=True)

            # 保存结果JSON
            result_file = output_dir / f"{context.task_id}_{self.agent_id}_{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"

            result_data = {
                "agent_id": result.agent_id,
                "task_id": result.task_id,
                "step_id": result.step_id,
                "status": result.status.value,
                "success": result.success,
                "message": result.message,
                "artifacts": [
                    {
                        "artifact_id": a.artifact_id,
                        "artifact_type": a.artifact_type,
                        "path": str(a.path) if a.path else None,
                        "quality_score": a.quality_score
                    }
                    for a in result.artifacts
                ],
                "logs": result.logs,
                "metrics": result.metrics,
                "error": result.error
            }

            async with aiofiles.open(result_file, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(result_data, indent=2, ensure_ascii=False))

            logger.info(f"中间结果已保存到: {result_file}")
        except (OSError, IOError) as e:
            logger.error(f"保存中间结果失败 (IO错误) ({type(e).__name__}): {e}")
        except Exception as e:
            logger.error(f"保存中间结果遇到非预期错误 ({type(e).__name__}): {e}")

    def validate_input(self, task_input: Dict[str, Any]) -> bool:
        """验证输入

        Args:
            task_input: 任务输入

        Returns:
            bool: 是否有效
        """
        # 1. 基本验证
        if not task_input:
            logger.warning(f"Agent {self.agent_id}: 任务输入为空")
            return False

        # 2. 安全清理与敏感数据检查
        for key, value in task_input.items():
            if isinstance(value, str):
                # 清理输入
                task_input[key] = sanitize_input(value)
                
                # 检查敏感数据
                sensitive_findings = check_sensitive_data(value)
                if sensitive_findings:
                    logger.warning(f"Agent {self.agent_id}: 输入字段 '{key}' 可能包含敏感数据: {', '.join(sensitive_findings)}")
                    # 注意：这里我们只记录警告，不拦截，除非安全策略要求严格拦截

        # 子类可以覆盖此方法添加特定验证
        return True

    def can_handle(self, task_input: Dict[str, Any]) -> bool:
        """检查是否能处理该任务

        Args:
            task_input: 任务输入

        Returns:
            bool: 是否能处理
        """
        # 默认实现:检查输入有效性
        return self.validate_input(task_input)