"""
并行执行器 - P1 Task 2.4

支持安全的并行任务执行:
1. 依赖分析和并行分组
2. 资源竞争控制
3. 执行性能监控
4. 错误处理和重试
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import threading
import logging
import time
from collections import defaultdict

logger = logging.getLogger(__name__)


class StepExecutionStatus(Enum):
    """步骤执行状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class Step:
    """执行步骤"""
    step_id: str
    description: str
    dependencies: List[str] = field(default_factory=list)
    estimated_duration: int = 60  # 预计耗时(秒)
    required_resources: List[str] = field(default_factory=list)  # 需要的资源(如文件路径)


@dataclass
class StepExecutionResult:
    """步骤执行结果"""
    step_id: str
    status: StepExecutionStatus
    output: str = ""
    error: Optional[str] = None
    start_time: float = 0.0
    end_time: float = 0.0
    duration: float = 0.0

    @property
    def success(self) -> bool:
        return self.status == StepExecutionStatus.COMPLETED


class ResourceManager:
    """资源管理器 - 避免竞争"""

    def __init__(self):
        self.file_locks: Dict[str, threading.Lock] = {}
        self.resource_locks: Dict[str, threading.Lock] = {}
        self.global_lock = threading.Lock()
        self.lock_history: Dict[str, List[str]] = defaultdict(list)

    def acquire_file(self, file_path: str) -> threading.Lock:
        """获取文件锁"""
        with self.global_lock:
            if file_path not in self.file_locks:
                self.file_locks[file_path] = threading.Lock()
                logger.debug(f"创建文件锁: {file_path}")

        return self.file_locks[file_path]

    def acquire_resource(self, resource_id: str) -> threading.Lock:
        """获取资源锁"""
        with self.global_lock:
            if resource_id not in self.resource_locks:
                self.resource_locks[resource_id] = threading.Lock()
                logger.debug(f"创建资源锁: {resource_id}")

        return self.resource_locks[resource_id]

    def lock_resource(self, resource_id: str, step_id: str):
        """锁定资源 (支持文件和通用资源)"""
        # 先尝试作为文件
        is_file = (
            resource_id.endswith('.py') or
            resource_id.endswith('.txt') or
            '/' in resource_id or
            '\\' in resource_id
        )

        if is_file:
            lock = self.acquire_file(resource_id)
            lock.acquire()
            self.lock_history[resource_id].append(step_id)
            logger.debug(f"步骤 {step_id} 锁定文件 {resource_id}")
        else:
            lock = self.acquire_resource(resource_id)
            lock.acquire()
            self.lock_history[resource_id].append(step_id)
            logger.debug(f"步骤 {step_id} 锁定资源 {resource_id}")

    def unlock_resource(self, resource_id: str):
        """释放资源 (支持文件和通用资源)"""
        # 先尝试从 file_locks 释放
        if resource_id in self.file_locks:
            self.file_locks[resource_id].release()
            logger.debug(f"释放文件 {resource_id}")
        # 再尝试从 resource_locks 释放
        elif resource_id in self.resource_locks:
            self.resource_locks[resource_id].release()
            logger.debug(f"释放资源 {resource_id}")

    def get_lock_statistics(self) -> Dict[str, int]:
        """获取锁统计信息"""
        return {
            "total_files": len(self.file_locks),
            "total_resources": len(self.resource_locks),
            "total_locks": len(self.file_locks) + len(self.resource_locks)
        }


class ParallelExecutor:
    """并行执行器 - 核心逻辑"""

    def __init__(self, max_workers: int = 3):
        self.max_workers = max_workers
        self.resource_manager = ResourceManager()
        self.execution_history: List[StepExecutionResult] = []
        self.stop_event = threading.Event()
        self.lock = threading.Lock()

    def execute_steps_parallel(
        self,
        steps: List[Step],
        executor_func: callable
    ) -> List[StepExecutionResult]:
        """并行执行步骤

        Args:
            steps: 要执行的步骤列表
            executor_func: 执行函数,接收 Step 对象,返回 StepExecutionResult

        Returns:
            List[StepExecutionResult]: 执行结果列表
        """
        logger.info(f"开始并行执行 {len(steps)} 个步骤")

        # 1. 构建依赖图
        dependency_graph = self._build_dependency_graph(steps)

        # 2. 验证依赖(检测循环)
        if not self._validate_dependencies(dependency_graph):
            raise ValueError("检测到循环依赖,无法执行")

        # 3. 识别可并行组
        parallel_groups = self._identify_parallel_groups(dependency_graph, steps)

        logger.info(f"识别出 {len(parallel_groups)} 个并行组")
        for i, group in enumerate(parallel_groups):
            logger.info(f"  组 {i+1}: {len(group)} 个步骤 - {[s.step_id for s in group]}")

        # 4. 按组执行
        all_results = []

        for group_index, group in enumerate(parallel_groups):
            logger.info(f"\n执行组 {group_index + 1}/{len(parallel_groups)}")

            if len(group) == 1:
                # 单个任务,直接执行
                result = self._execute_single(group[0], executor_func)
                all_results.append(result)
            else:
                # 多个任务,并行执行
                group_results = self._execute_parallel(group, executor_func)
                all_results.extend(group_results)

            # 检查是否有失败的任务
            failed = [r for r in all_results if not r.success]
            if failed:
                logger.warning(f"检测到 {len(failed)} 个失败的任务")
                # 可以选择停止或继续

        # 保存历史
        with self.lock:
            self.execution_history.extend(all_results)

        logger.info(f"\n并行执行完成: {len(all_results)} 个结果")
        return all_results

    def _build_dependency_graph(self, steps: List[Step]) -> Dict[str, List[str]]:
        """构建依赖图

        Args:
            steps: 步骤列表

        Returns:
            Dict[str, List[str]]: step_id -> 依赖的 step_id 列表
        """
        graph = {}

        # 创建所有步骤的映射
        step_map = {step.step_id: step for step in steps}

        for step in steps:
            # 验证依赖是否存在
            valid_deps = []
            for dep_id in step.dependencies:
                if dep_id in step_map:
                    valid_deps.append(dep_id)
                else:
                    logger.warning(f"步骤 {step.step_id} 的依赖 {dep_id} 不存在,忽略")

            graph[step.step_id] = valid_deps

        return graph

    def _validate_dependencies(self, graph: Dict[str, List[str]]) -> bool:
        """验证依赖图(检测循环依赖)

        使用 DFS 检测环
        """
        WHITE, GRAY, BLACK = 0, 1, 2
        color = {node: WHITE for node in graph}

        def dfs(node):
            color[node] = GRAY
            for neighbor in graph[node]:
                if color[neighbor] == GRAY:
                    return False  # 发现环
                if color[neighbor] == WHITE:
                    if not dfs(neighbor):
                        return False
            color[node] = BLACK
            return True

        for node in graph:
            if color[node] == WHITE:
                if not dfs(node):
                    return False

        return True

    def _identify_parallel_groups(
        self,
        graph: Dict[str, List[str]],
        steps: List[Step]
    ) -> List[List[Step]]:
        """识别可并行执行的组

        使用拓扑排序,将步骤分层:
        - 第 1 层: 无依赖的任务
        - 第 2 层: 只依赖第 1 层的任务
        - 第 N 层: 只依赖 1..N-1 层的任务

        Args:
            graph: 依赖图
            steps: 步骤列表

        Returns:
            List[List[Step]]: 分层的步骤组
        """
        step_map = {step.step_id: step for step in steps}

        groups = []
        remaining: Set[str] = set(graph.keys())
        executed: Set[str] = set()

        while remaining:
            # 找出所有依赖已满足的步骤
            ready_step_ids = [
                step_id for step_id in remaining
                if all(dep in executed for dep in graph[step_id])
            ]

            if not ready_step_ids:
                # 应该不会发生,因为已经验证过
                logger.error("无法识别下一组任务,可能存在未检测的循环依赖")
                break

            # 转换为 Step 对象
            ready_steps = [step_map[sid] for sid in ready_step_ids]

            groups.append(ready_steps)
            executed.update(ready_step_ids)
            remaining -= set(ready_step_ids)

        return groups

    def _execute_single(
        self,
        step: Step,
        executor_func: callable
    ) -> StepExecutionResult:
        """执行单个步骤

        Args:
            step: 要执行的步骤
            executor_func: 执行函数

        Returns:
            StepExecutionResult: 执行结果
        """
        logger.info(f"执行步骤: {step.step_id} - {step.description}")

        # 获取资源锁
        for resource_id in step.required_resources:
            self.resource_manager.lock_resource(resource_id, step.step_id)

        start_time = time.time()

        try:
            # 执行步骤
            result = executor_func(step)

            # 如果返回的是 StepExecutionResult,更新时间并返回
            if isinstance(result, StepExecutionResult):
                result.start_time = start_time
                result.end_time = time.time()
                result.duration = result.end_time - start_time
                return result

            # 否则包装为 StepExecutionResult
            return StepExecutionResult(
                step_id=step.step_id,
                status=StepExecutionStatus.COMPLETED,
                output=str(result),
                start_time=start_time,
                end_time=time.time(),
                duration=time.time() - start_time
            )
        except Exception as e:
            logger.error(f"执行步骤 {step.step_id} 失败: {e}")
            return StepExecutionResult(
                step_id=step.step_id,
                status=StepExecutionStatus.FAILED,
                error=str(e),
                start_time=start_time,
                end_time=time.time(),
                duration=time.time() - start_time
            )
        finally:
            # 释放资源锁
            for resource_id in step.required_resources:
                self.resource_manager.unlock_resource(resource_id)

    def _execute_parallel(
        self,
        steps: List[Step],
        executor_func: callable
    ) -> List[StepExecutionResult]:
        """并行执行一组步骤"""
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [
                executor.submit(self._execute_single, step, executor_func)
                for step in steps
            ]
            return [f.result() for f in as_completed(futures)]

    def get_execution_statistics(self) -> Dict:
        """获取执行统计信息

        Returns:
            Dict: 统计信息
        """
        if not self.execution_history:
            return {
                "total_executions": 0,
                "success_rate": 0.0,
                "average_duration": 0.0
            }

        total = len(self.execution_history)
        successful = sum(1 for r in self.execution_history if r.success)
        total_duration = sum(r.duration for r in self.execution_history)

        return {
            "total_executions": total,
            "successful": successful,
            "failed": total - successful,
            "success_rate": successful / total if total > 0 else 0.0,
            "total_duration": total_duration,
            "average_duration": total_duration / total if total > 0 else 0.0,
            "lock_statistics": self.resource_manager.get_lock_statistics()
        }

    def reset(self):
        """重置执行器"""
        self.execution_history.clear()
        logger.info("并行执行器已重置")
