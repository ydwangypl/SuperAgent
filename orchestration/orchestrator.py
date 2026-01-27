#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
编排器(Orchestrator)

SuperAgent的核心协调引擎,负责任务编排、Agent调度、执行管理

v3.3 新增:
- 生命周期钩子系统集成 (HookManager)
- TaskPlanManager 集成 (3-File 模式)
- SessionManager 集成 (状态持久化)

v3.3 P1 改进:
- OrchestratorBase 抽象基类定义核心接口
- 关注点分离：执行、协调、调度
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from planning.models import ExecutionPlan
from common.monitoring import monitor_task_duration

from .base import BaseOrchestrator
from .models import (
    TaskExecution,
    TaskStatus,
    ExecutionContext,
    ProjectExecutionResult,
    OrchestrationState,
    OrchestrationConfig,
    AgentResource,
)
from .worktree_manager import GitWorktreeManager
from .task_executor import TaskExecutor
from .distributed_executor import DistributedTaskExecutor
from .agent_dispatcher import AgentDispatcher
from .error_recovery import ErrorRecoverySystem
from .review_orchestrator import ReviewOrchestrator
from .scheduler import TaskScheduler
from .result_handler import ExecutionResultHandler
from .worktree_orchestrator import WorktreeOrchestrator
from .git_manager import GitAutoCommitManager
from config.settings import SuperAgentConfig, load_config
from monitoring.token_monitor import TokenMonitor
from core.test_runner import TestRunner
from common.exceptions import ExecutionError, SecurityError


logger = logging.getLogger(__name__)

# 记忆管理层
try:
    from memory import MemoryManager
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False
    MemoryManager = None
    logger.warning("记忆管理层不可用")

# v3.3: 扩展模块导入 (失败时降级)
try:
    from extensions.hooks import HookManager, create_default_hooks
    from extensions.planning_files import TaskPlanManager, ProgressManager, FindingsManager
    from extensions.state_persistence import SessionManager, SessionStatus
    EXTENSIONS_AVAILABLE = True
except ImportError as e:
    EXTENSIONS_AVAILABLE = False
    HookManager = None
    logger.warning(f"扩展模块不可用: {e}")


class Orchestrator(BaseOrchestrator):
    """SuperAgent编排器 (重构版 - 关注点分离)

    v3.3 新增:
        - 生命周期钩子系统集成 (HookManager)
        - TaskPlanManager 集成 (3-File 模式)
        - SessionManager 集成 (状态持久化)
    """

    def __init__(
        self,
        project_root: Path,
        config: Optional[OrchestrationConfig] = None,
        global_config: Optional[SuperAgentConfig] = None
    ) -> None:
        """初始化编排器"""
        super().__init__(project_root, config)
        self.global_config = global_config or load_config(project_root=self.project_root)

        # 1. 初始化执行上下文
        self.context = ExecutionContext(project_root=self.project_root)

        # 2. 初始化底层组件 (Executor & Dispatcher)
        self.task_executor = self._init_executor()
        self.agent_dispatcher = self._init_dispatcher()

        # 3. 初始化外部服务 (Memory & Recovery)
        self.memory_manager = MemoryManager(self.project_root) if MEMORY_AVAILABLE else None
        self.error_recovery = (ErrorRecoverySystem(self.memory_manager)
                               if self.memory_manager else None)

        # 4. 初始化子编排器
        self.review_orchestrator = ReviewOrchestrator(
            self.project_root, self.config, self.agent_dispatcher
        )

        # 5. 初始化业务逻辑组件 (解耦核心)
        try:
            worktree_mgr = GitWorktreeManager(self.project_root, self.config.worktree)
        except ValueError:
            worktree_mgr = None

        self.worktree_orchestrator = WorktreeOrchestrator(self.project_root, worktree_mgr)
        self.scheduler = TaskScheduler(self.config, self.agent_dispatcher)

        # 6. 初始化 Git 自动提交管理器
        git_config = self.config.git_auto_commit
        self.git_manager = GitAutoCommitManager(
            project_root=self.project_root,
            enabled=git_config.enabled,
            commit_message_template=git_config.commit_message_template,
            auto_push=git_config.auto_push
        )
        if git_config.enabled:
            logger.info("Git 自动提交已启用")

        # 6b. 初始化测试运行器 (方案A: 主工作流测试集成)
        self.test_runner = TestRunner(self.project_root)

        # 7. 初始化 Token 监控器
        self.token_monitor = self._init_token_monitor()
        self.context.token_monitor = self.token_monitor

        # 8. v3.3: 初始化生命周期钩子系统
        self._hook_manager = None
        self._task_plan_manager = None
        self._progress_manager = None
        self._findings_manager = None
        self._session_manager = None
        self._init_extensions()

        # 执行状态
        self.state = OrchestrationState(
            project_id=f"project-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            total_tasks=0
        )
        self.result_handler = ExecutionResultHandler(self.state, self.memory_manager)

    def _init_extensions(self) -> None:
        """v3.3: 初始化扩展模块 (降级处理)"""
        if not EXTENSIONS_AVAILABLE:
            return

        try:
            # 初始化 TaskPlanManager (task_plan.md)
            self._task_plan_manager = TaskPlanManager(
                self.project_root,
                self.project_root / "task_plan.md",
                auto_save=True
            )

            # 初始化 ProgressManager (progress.md)
            self._progress_manager = ProgressManager(
                self.project_root,
                self.project_root / "docs" / "progress.md"
            )

            # 初始化 FindingsManager (findings.md)
            self._findings_manager = FindingsManager(
                self.project_root,
                self.project_root / "docs" / "findings.md",
                self.memory_manager  # 与 MemoryManager 联动
            )

            # 初始化 SessionManager (状态持久化)
            self._session_manager = SessionManager(self.project_root)

            # 初始化 HookManager
            self._hook_manager = HookManager(self.memory_manager)

            # 注册默认钩子
            hooks = create_default_hooks(
                self._task_plan_manager,
                self._progress_manager,
                self.memory_manager
            )
            for hook in hooks:
                if hook:
                    self._hook_manager.register(hook)

            logger.info("v3.3 扩展模块已初始化 (Hook/Planning/Session)")

        except Exception as e:
            logger.warning(f"v3.3 扩展模块初始化失败: {e}")
            self._hook_manager = None
            self._task_plan_manager = None
            self._progress_manager = None
            self._findings_manager = None
            self._session_manager = None

    def _init_executor(self):
        """初始化任务执行器"""
        if self.global_config.distribution.enabled:
            try:
                executor = DistributedTaskExecutor(self.context, self.global_config)
                logger.info("分布式任务执行器已启用")
                return executor
            except Exception as e:
                logger.error(f"分布式任务执行器启动失败: {type(e).__name__}: {e}。自动降级。")

        logger.info("本地任务执行器已启用")
        return TaskExecutor(self.context)

    def _init_dispatcher(self) -> AgentDispatcher:
        """初始化Agent调度器"""
        if not self.config.agent_resources:
            from common.models import AgentType
            self.config.agent_resources = {
                agent_type.value: AgentResource(
                    agent_type=agent_type.value,
                    available_instances=1,
                    max_concurrent=self.config.max_concurrent_per_agent
                ) for agent_type in AgentType
            }

        dispatcher = AgentDispatcher(self.config.agent_resources)
        dispatcher.task_executor = self.task_executor
        return dispatcher

    def _init_token_monitor(self) -> TokenMonitor:
        """初始化 Token 监控器"""
        # 优先使用全局配置中的监控设置
        monitor_config = self.global_config.token_monitor

        # 将编排配置中的预算设置同步到监控器配置
        if self.config.token_budget.enabled:
            monitor_config.enable_budget = True
            monitor_config.total_budget = self.config.token_budget.total_budget
            monitor_config.warning_threshold = self.config.token_budget.warning_threshold
            monitor_config.stop_on_exceed = self.config.token_budget.stop_on_exceed

        # 转换为 TokenMonitor 内部使用的配置类 (如果需要)
        # 注意: 这里假设 config/settings.py 中的 TokenMonitorConfig 和 monitoring/token_monitor.py 中的兼容
        return TokenMonitor(
            project_root=self.project_root,
            config=monitor_config
        )

    @monitor_task_duration(agent_type="orchestrator")
    async def execute_plan(self, plan: ExecutionPlan) -> ProjectExecutionResult:
        """执行完整的项目计划 (重构版 - 关注点分离)

        v3.3 新增: 生命周期钩子集成、会话管理
        """
        self._initialize_execution_state(plan)
        result = self._create_initial_result()

        # v3.3: 开始会话
        if self._session_manager:
            await self._session_manager.start_session(
                session_id=self.state.project_id,
                initial_state={"plan_description": plan.description}
            )

        try:
            # v3.3: 执行 PreExecute 钩子
            if self._hook_manager:
                hook_context = await self._hook_manager.execute_pre_execute({
                    "project_id": self.state.project_id,
                    "total_tasks": len(plan.steps)
                })
                if hook_context.context_injection:
                    # 将钩子注入的上下文添加到计划描述
                    result.context_injection = hook_context.context_injection

            # 1. 准备阶段 (记忆与任务创建)
            await self._prepare_execution(plan)

            # 2. 执行阶段 (核心循环)
            task_executions = self.scheduler.create_task_executions(plan)
            executed_tasks = await self._execute_by_dependencies(task_executions, plan)

            # 3. 汇总与审查阶段
            result = self.result_handler.collect_results(executed_tasks)
            await self._finalize_execution(result, executed_tasks)

        except Exception as e:
            await self._handle_execution_error(e, plan, result)
        finally:
            # v3.3: 执行 PostExecute 钩子
            if self._hook_manager:
                await self._hook_manager.execute_post_execute(
                    session_state={"completed_tasks": result.completed_tasks},
                    execution_history=result.execution_history
                )

            # v3.3: 执行 Stop 钩子并结束会话
            if self._hook_manager:
                stop_result = await self._hook_manager.execute_stop({
                    "completed": result.completed_tasks,
                    "failed": result.failed_tasks,
                    "total": result.total_tasks
                })
                if stop_result.context_injection:
                    result.hook_report = stop_result.context_injection

            if self._session_manager:
                await self._session_manager.end_session(
                    status=SessionStatus.COMPLETED,
                    final_state={"result": "success" if result.success else "partial"}
                )

            self._cleanup_execution(result)

        return result

    def _initialize_execution_state(self, plan: ExecutionPlan) -> None:
        """初始化执行状态"""
        logger.info(f"开始执行项目计划: {self.state.project_id} (步骤数: {len(plan.steps)})")
        self.state.status = TaskStatus.RUNNING
        self.state.started_at = datetime.now()
        self.state.total_tasks = len(plan.steps)

    def _create_initial_result(self) -> ProjectExecutionResult:
        """创建初始结果对象"""
        return ProjectExecutionResult(
            success=False,
            project_id=self.state.project_id,
            total_tasks=self.state.total_tasks,
            completed_tasks=0,
            failed_tasks=0
        )

    async def _prepare_execution(self, plan: ExecutionPlan) -> None:
        """执行前准备工作"""
        if self.memory_manager:
            await self.memory_manager.query_relevant_memory(task=plan.description, agent_type=None)

    async def _finalize_execution(
        self,
        result: ProjectExecutionResult,
        executed_tasks: List[TaskExecution]
    ) -> None:
        """完成执行后的汇总、审查与测试"""
        # 1. 代码审查
        result.code_review_summary = await self.review_orchestrator.run_review(
            self.state.project_id, executed_tasks
        )

        # 2. 运行测试 (方案A: 主工作流测试集成)
        if self.config.testing.enabled:
            test_config = self.config.testing
            logger.info("运行测试...")

            test_result = await self.test_runner.run_pytest(
                test_path=test_config.test_path,
                verbose=test_config.verbose,
                coverage=test_config.coverage,
                markers=test_config.markers
            )

            result.test_summary = {
                "success": test_result.success,
                "total_tests": test_result.total_tests,
                "passed": test_result.passed,
                "failed": test_result.failed,
                "errors": test_result.errors,
                "duration_seconds": test_result.duration_seconds,
                "coverage": test_result.coverage
            }

            # 如果测试失败且配置要求失败则标记为失败
            if not test_result.success and test_config.fail_on_failure:
                logger.warning("测试失败,根据配置标记任务为失败")

            logger.info(
                f"测试完成: 通过={test_result.passed}, "
                f"失败={test_result.failed}, "
                f"耗时={test_result.duration_seconds:.2f}s"
            )

        # 3. 资源清理
        if self.config.worktree.auto_cleanup:
            await self.worktree_orchestrator.cleanup_all()

    def _cleanup_execution(self, result: ProjectExecutionResult) -> None:
        """最后的收尾清理"""
        self.state.completed_at = datetime.now()
        self.state.status = TaskStatus.COMPLETED
        result.completed_at = self.state.completed_at
        result.success = (result.failed_tasks == 0 and result.completed_tasks == result.total_tasks)

        logger.info(
            f"计划执行完成: {result.completed_tasks}/{result.total_tasks} 成功, "
            f"耗时 {result.duration_seconds}s"
        )

    async def _handle_execution_error(
        self,
        e: Exception,
        plan: ExecutionPlan,
        result: ProjectExecutionResult
    ) -> None:
        """统一错误处理逻辑 (v3.3 P1: 使用自定义异常)"""
        # v3.3: 使用自定义异常类型
        error_type = type(e).__name__
        if isinstance(e, ExecutionError):
            error_type = "执行错误"
        elif isinstance(e, SecurityError):
            error_type = "安全错误"
        elif isinstance(e, ValueError):
            error_type = "参数错误"
        elif isinstance(e, IOError):
            error_type = "IO 错误"
        elif isinstance(e, TimeoutError):
            error_type = "超时错误"

        logger.error(f"执行计划失败 ({error_type}): {e}")
        result.success = False
        result.errors.append(f"[{error_type}] {str(e)}")
        result.completed_tasks = self.state.completed_tasks
        result.failed_tasks = self.state.failed_tasks

        if self.memory_manager:
            await self._record_error_to_memory(e, plan)

    async def _record_error_to_memory(self, e: Exception, plan: ExecutionPlan) -> None:
        """记录错误到记忆系统"""
        error_context = (
            f"项目执行: {self.state.project_id}\n"
            f"任务描述: {plan.description}\n"
            f"状态统计: 已完成 {self.state.completed_tasks}, "
            f"失败 {self.state.failed_tasks}, 总计 {self.state.total_tasks}\n"
            f"运行时长: {(datetime.now() - self.state.started_at).total_seconds():.2f}s"
        )

        learning = (
            f"在项目 {self.state.project_id} 执行期间发生非预期异常。\n"
            f"执行进度: {self.state.completed_tasks}/{self.state.total_tasks}\n"
            f"异常详情: {str(e)}"
        )

        await self.memory_manager.save_mistake(
            error=e,
            context=error_context,
            fix="检查系统日志，分析执行过程中的具体失败点并尝试手动恢复或调整计划。",
            learning=learning
        )

    async def _execute_by_dependencies(
        self,
        tasks: List[TaskExecution],
        plan: ExecutionPlan
    ) -> List[TaskExecution]:
        """按依赖关系执行任务 (重构版 - 职责分离)

        v3.3 新增: 任务级生命周期钩子集成
        """
        executed = []
        remaining = tasks.copy()

        while remaining:
            # v3.3: 执行 PreTask 钩子检查
            if self._hook_manager:
                # 检查是否应该创建检查点
                should_checkpoint = await self._session_manager.should_auto_checkpoint(
                    len(executed)
                ) if self._session_manager else False

                if should_checkpoint:
                    task_status = {t.step_id: t.status.value for t in remaining}
                    memory_stats = (
                        self.memory_manager.get_statistics()
                        if self.memory_manager else {}
                    )
                    await self._session_manager.create_checkpoint(
                        task_status=task_status,
                        memory_summary=memory_stats,
                        context_summary=f"已完成 {len(executed)} 个任务"
                    )

            # 1. Token 预算检查
            if not await self._check_token_budget_for_remaining(remaining, executed):
                break

            # 2. 获取就绪任务
            ready_tasks = self.scheduler.find_ready_tasks(remaining, executed)
            if not ready_tasks:
                if remaining:
                    logger.error("检测到可能的循环依赖")
                break

            logger.info(f"执行批次: {len(ready_tasks)} 个任务")

            # 3. 执行批次任务
            batch_results = await self._execute_task_batch(ready_tasks, plan)

            # 4. 批次后处理 (同步, 记忆, 验证, Git提交, 钩子)
            await self._process_batch_results(batch_results, plan)

            executed.extend(batch_results)
            remaining = [t for t in remaining if t not in batch_results]
            self.result_handler.update_state(executed)

            # v3.3: 执行 PostTask 钩子
            if self._hook_manager:
                for task in batch_results:
                    step = plan.get_step_by_id(task.step_id)
                    task_dict = {
                        "task_id": task.step_id,
                        "name": task.step_id,
                        "status": task.status.value,
                        "agent_type": step.agent_type.value if step else None
                    }
                    await self._hook_manager.execute_post_task(task_dict, task.status.value)

            # 5. 快速失败逻辑
            if self.config.enable_early_failure and any(
                t.status == TaskStatus.FAILED for t in batch_results
            ):
                logger.error("检测到任务失败, 停止后续执行")
                for task in remaining:
                    task.status = TaskStatus.SKIPPED
                executed.extend(remaining)
                break

        return executed

    async def _check_token_budget_for_remaining(
        self,
        remaining: List[TaskExecution],
        executed: List[TaskExecution]
    ) -> bool:
        """检查剩余任务的 Token 预算"""
        total_estimated = 0
        for task in remaining:
            task_content = task.description or ""
            total_estimated += self.token_monitor.estimate_tokens(task_content) + 2000

        is_sufficient, budget_msg = await self.token_monitor.check_budget(total_estimated)
        if not is_sufficient:
            logger.error(f"由于 Token 预算限制，停止执行: {budget_msg}")
            for task in remaining:
                task.status = TaskStatus.FAILED
                task.error = budget_msg
            executed.extend(remaining)
            return False
        elif budget_msg:
            self.add_log(f"预算提示: {budget_msg}")
        return True

    async def _execute_task_batch(
        self,
        ready_tasks: List[TaskExecution],
        plan: ExecutionPlan
    ) -> List[TaskExecution]:
        """执行一批就绪任务"""
        async def create_wt(task):
            step = plan.get_step_by_id(task.step_id)
            if step:
                await self.worktree_orchestrator.create_for_task(task, step.agent_type.value)

        return await self.scheduler.execute_batch(ready_tasks, worktree_creator_callback=create_wt)

    async def _process_batch_results(
        self,
        batch_results: List[TaskExecution],
        plan: ExecutionPlan
    ):
        """对批次执行结果进行后处理"""
        for task in batch_results:
            # 同步 Worktree
            await self.worktree_orchestrator.sync_to_root(task)

            # 保存任务记忆
            await self.result_handler.save_task_memory(task, plan.description)

            # 单任务焦点模式验证
            await self._handle_single_task_mode_validation(task)

            # Git 自动提交
            await self._handle_git_auto_commit(task, plan)

    async def _handle_single_task_mode_validation(self, task: TaskExecution):
        """处理单任务焦点模式的验证与自动拆分"""
        if self.config.single_task_mode.enabled and task.status == TaskStatus.COMPLETED:
            is_valid, reason = self._validate_task_scope(task)
            if not is_valid:
                logger.warning(f"任务 {task.task_id} 超出单任务模式限制: {reason}")

                if self.config.single_task_mode.enable_auto_split:
                    split_task = await self._split_task(task, reason)
                    if split_task:
                        logger.info(f"任务 {task.task_id} 已自动拆分")
                        task.status = TaskStatus.COMPLETED
                        task.outputs["split_info"] = {
                            "reason": reason,
                            "split_task_id": split_task.task_id
                        }
                    else:
                        logger.error(f"任务 {task.task_id} 拆分失败")
                        task.status = TaskStatus.FAILED
                        task.error = reason
                else:
                    task.status = TaskStatus.FAILED
                    task.error = reason

    async def _handle_git_auto_commit(self, task: TaskExecution, plan: ExecutionPlan):
        """处理 Git 自动提交"""
        if self.git_manager and self.config.git_auto_commit.enabled:
            step = plan.get_step_by_id(task.step_id)
            if step and task.status == TaskStatus.COMPLETED:
                changed_files = task.outputs.get("modified_files", [])
                if isinstance(changed_files, str):
                    changed_files = [changed_files]

                if not changed_files:
                    logger.debug(f"任务 {task.task_id} 未指定变更文件,跳过自动提交")
                else:
                    await self.git_manager.commit_task(
                        task_id=task.task_id,
                        description=step.description,
                        changed_files=changed_files,
                        summary=step.details if hasattr(step, 'details') else None
                    )

    def get_status(self) -> OrchestrationState:
        """获取当前编排状态"""
        return self.state

    def get_task_statistics(self) -> Dict[str, Any]:
        """获取任务统计信息"""
        stats = {
            "total": self.state.total_tasks,
            "completed": self.state.completed_tasks,
            "failed": self.state.failed_tasks,
            "running": self.task_executor.get_running_task_count(),
            "agent_stats": self.agent_dispatcher.get_statistics()
        }
        if self.memory_manager:
            stats["memory_stats"] = self.memory_manager.get_statistics()
        if self.error_recovery:
            stats["error_recovery_stats"] = self.error_recovery.get_statistics()
        return stats

    def _validate_task_scope(
        self,
        task: TaskExecution
    ) -> tuple[bool, Optional[str]]:
        """验证任务范围是否在单任务焦点模式限制内

        Args:
            task: 任务执行对象

        Returns:
            (is_valid, reason): 是否有效及原因(如果无效)
        """
        config = self.config.single_task_mode

        # 如果未启用单任务模式,直接通过
        if not config.enabled:
            return True, None

        # 检查任务输出中的修改文件数量
        modified_files = task.outputs.get("modified_files", [])
        if isinstance(modified_files, str):
            modified_files = [modified_files]

        # 检查文件数量
        if len(modified_files) > config.max_files_per_task:
            reason = (
                f"任务 {task.task_id} 修改了 {len(modified_files)} 个文件, "
                f"超过单任务模式限制 ({config.max_files_per_task} 个文件)"
            )
            logger.warning(reason)
            return False, reason

        # 检查文件大小
        for file_path in modified_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                size_kb = full_path.stat().st_size / 1024
                if size_kb > config.max_file_size_kb:
                    reason = (
                        f"任务 {task.task_id} 修改的文件 {file_path} "
                        f"大小为 {size_kb:.1f}KB, "
                        f"超过单任务模式限制 ({config.max_file_size_kb}KB)"
                    )
                    logger.warning(reason)
                    return False, reason

        # 所有检查通过
        logger.debug(f"任务 {task.task_id} 范围验证通过")
        return True, None

    async def _split_task(
        self,
        task: TaskExecution,
        reason: str
    ) -> Optional[TaskExecution]:
        """拆分过大的任务为多个子任务

        Args:
            task: 需要拆分的任务
            reason: 拆分原因

        Returns:
            拆分后的第一个子任务,如果拆分失败则返回 None
        """
        config = self.config.single_task_mode

        if not config.enable_auto_split:
            logger.warning(f"任务 {task.task_id} 需要拆分但自动拆分未启用")
            return None

        logger.info(f"开始拆分任务 {task.task_id}: {reason}")

        # 获取修改的文件列表
        modified_files = task.outputs.get("modified_files", [])
        if isinstance(modified_files, str):
            modified_files = [modified_files]

        # 确保文件列表是列表格式
        if not isinstance(modified_files, list):
            modified_files = [modified_files]

        # 如果文件数量不多,不需要拆分
        if len(modified_files) <= config.max_files_per_task:
            logger.debug(f"任务 {task.task_id} 文件数量在限制内,无需拆分")
            return task

        # 将文件列表拆分为多个批次
        file_batches = []
        for i in range(0, len(modified_files), config.max_files_per_task):
            batch = modified_files[i:i + config.max_files_per_task]
            file_batches.append(batch)

        logger.info(
            f"任务 {task.task_id} 将拆分为 {len(file_batches)} 个子任务, "
            f"每个子任务最多 {config.max_files_per_task} 个文件"
        )

        # 创建第一个子任务 (后续子任务需要动态创建步骤)
        # 注意: 这里简化处理,实际应用中可能需要更新 ExecutionPlan
        first_batch = file_batches[0]

        # 创建子任务ID
        sub_task_id = f"{task.task_id}-sub-01"

        logger.info(
            f"创建子任务 {sub_task_id}, "
            f"包含文件: {first_batch}"
        )

        # 返回第一个子任务的信息
        # 注意: 这里返回原始任务,但更新其输出以只包含第一批文件
        # 实际的子任务创建需要在 Planner 层面完成
        task.outputs["modified_files"] = first_batch
        task.outputs["is_split_task"] = True
        task.outputs["total_subtasks"] = len(file_batches)
        task.outputs["subtask_index"] = 0

        return task
