"""
ParallelExecutor 单元测试 - P1 Task 2.4

测试并行执行器的核心功能:
1. 依赖图构建
2. 并行分组识别
3. 并行执行
4. 资源管理
"""

import pytest
import time
from orchestration.parallel_executor import (
    ParallelExecutor,
    ResourceManager,
    Step,
    StepExecutionResult,
    StepExecutionStatus
)


class TestResourceManager:
    """测试资源管理器"""

    def test_initialization(self):
        """测试初始化"""
        manager = ResourceManager()

        assert manager.file_locks == {}
        assert manager.resource_locks == {}
        assert manager.global_lock is not None

    def test_acquire_file(self):
        """测试获取文件锁"""
        manager = ResourceManager()

        lock1 = manager.acquire_file("test.py")
        lock2 = manager.acquire_file("test.py")

        # 同一个文件应该返回同一个锁
        assert lock1 is lock2
        assert "test.py" in manager.file_locks

    def test_acquire_resource(self):
        """测试获取资源锁"""
        manager = ResourceManager()

        lock1 = manager.acquire_resource("database")
        lock2 = manager.acquire_resource("database")

        # 同一个资源应该返回同一个锁
        assert lock1 is lock2
        assert "database" in manager.resource_locks

    def test_different_resources(self):
        """测试不同资源有不同的锁"""
        manager = ResourceManager()

        lock1 = manager.acquire_file("file1.py")
        lock2 = manager.acquire_file("file2.py")
        lock3 = manager.acquire_resource("resource1")

        # 不同的资源应该有不同的锁
        assert lock1 is not lock2
        assert lock1 is not lock3
        assert lock2 is not lock3

    def test_lock_and_unlock(self):
        """测试锁定和解锁"""
        manager = ResourceManager()

        # 锁定资源
        manager.lock_resource("test_resource", "step_1")

        # 验证历史记录
        assert "step_1" in manager.lock_history["test_resource"]

        # 解锁资源
        manager.unlock_resource("test_resource")

    def test_get_lock_statistics(self):
        """测试获取锁统计信息"""
        manager = ResourceManager()

        # 创建一些锁
        manager.acquire_file("file1.py")
        manager.acquire_file("file2.py")
        manager.acquire_resource("resource1")

        stats = manager.get_lock_statistics()

        assert stats["total_files"] == 2
        assert stats["total_resources"] == 1
        assert stats["total_locks"] == 3


class TestDependencyGraph:
    """测试依赖图构建"""

    def test_build_dependency_graph_empty(self):
        """测试空列表"""
        executor = ParallelExecutor()
        graph = executor._build_dependency_graph([])

        assert graph == {}

    def test_build_dependency_graph_no_deps(self):
        """测试无依赖的步骤"""
        executor = ParallelExecutor()
        steps = [
            Step(step_id="1", description="Step 1"),
            Step(step_id="2", description="Step 2"),
        ]

        graph = executor._build_dependency_graph(steps)

        assert graph["1"] == []
        assert graph["2"] == []

    def test_build_dependency_graph_with_deps(self):
        """测试有依赖的步骤"""
        executor = ParallelExecutor()
        steps = [
            Step(step_id="1", description="Step 1", dependencies=[]),
            Step(step_id="2", description="Step 2", dependencies=["1"]),
            Step(step_id="3", description="Step 3", dependencies=["1", "2"]),
        ]

        graph = executor._build_dependency_graph(steps)

        assert graph["1"] == []
        assert graph["2"] == ["1"]
        assert graph["3"] == ["1", "2"]

    def test_build_dependency_graph_invalid_deps(self):
        """测试无效的依赖"""
        executor = ParallelExecutor()
        steps = [
            Step(step_id="1", description="Step 1", dependencies=["999"]),  # 不存在
        ]

        graph = executor._build_dependency_graph(steps)

        # 无效依赖应该被忽略
        assert graph["1"] == []


class TestDependencyValidation:
    """测试依赖验证"""

    def test_validate_no_cycle(self):
        """测试无循环依赖"""
        executor = ParallelExecutor()
        graph = {
            "1": [],
            "2": ["1"],
            "3": ["2"],
        }

        assert executor._validate_dependencies(graph) is True

    def test_validate_simple_cycle(self):
        """测试简单循环依赖"""
        executor = ParallelExecutor()
        graph = {
            "1": ["2"],
            "2": ["1"],
        }

        assert executor._validate_dependencies(graph) is False

    def test_validate_complex_cycle(self):
        """测试复杂循环依赖"""
        executor = ParallelExecutor()
        graph = {
            "1": ["2"],
            "2": ["3"],
            "3": ["1"],  # 形成环
        }

        assert executor._validate_dependencies(graph) is False

    def test_validate_dag(self):
        """测试 DAG (有向无环图)"""
        executor = ParallelExecutor()
        graph = {
            "1": [],
            "2": ["1"],
            "3": ["1"],
            "4": ["2", "3"],
        }

        assert executor._validate_dependencies(graph) is True


class TestParallelGroupIdentification:
    """测试并行分组识别"""

    def test_identify_no_deps(self):
        """测试无依赖的步骤 - 全部可并行"""
        executor = ParallelExecutor()
        steps = [
            Step(step_id="1", description="Step 1"),
            Step(step_id="2", description="Step 2"),
            Step(step_id="3", description="Step 3"),
        ]
        graph = executor._build_dependency_graph(steps)

        groups = executor._identify_parallel_groups(graph, steps)

        # 应该只有一组,包含所有步骤
        assert len(groups) == 1
        assert len(groups[0]) == 3

    def test_identify_chain_deps(self):
        """测试链式依赖 - 串行执行"""
        executor = ParallelExecutor()
        steps = [
            Step(step_id="1", description="Step 1"),
            Step(step_id="2", description="Step 2", dependencies=["1"]),
            Step(step_id="3", description="Step 3", dependencies=["2"]),
        ]
        graph = executor._build_dependency_graph(steps)

        groups = executor._identify_parallel_groups(graph, steps)

        # 应该有 3 组,每组 1 个步骤
        assert len(groups) == 3
        assert all(len(group) == 1 for group in groups)

        # 验证顺序
        assert groups[0][0].step_id == "1"
        assert groups[1][0].step_id == "2"
        assert groups[2][0].step_id == "3"

    def test_identify_mixed_deps(self):
        """测试混合依赖 - 部分并行"""
        executor = ParallelExecutor()
        steps = [
            Step(step_id="1", description="Step 1"),
            Step(step_id="2", description="Step 2", dependencies=["1"]),
            Step(step_id="3", description="Step 3", dependencies=["1"]),
            Step(step_id="4", description="Step 4", dependencies=["2", "3"]),
        ]
        graph = executor._build_dependency_graph(steps)

        groups = executor._identify_parallel_groups(graph, steps)

        # 第 1 组: 步骤 1
        # 第 2 组: 步骤 2, 3 (可并行)
        # 第 3 组: 步骤 4
        assert len(groups) == 3
        assert len(groups[0]) == 1  # 步骤 1
        assert len(groups[1]) == 2  # 步骤 2, 3
        assert len(groups[2]) == 1  # 步骤 4

    def test_identify_diamond_deps(self):
        """测试钻石形依赖"""
        executor = ParallelExecutor()
        steps = [
            Step(step_id="1", description="Step 1"),
            Step(step_id="2", description="Step 2", dependencies=["1"]),
            Step(step_id="3", description="Step 3", dependencies=["1"]),
            Step(step_id="4", description="Step 4", dependencies=["2", "3"]),
            Step(step_id="5", description="Step 5", dependencies=["4"]),
        ]
        graph = executor._build_dependency_graph(steps)

        groups = executor._identify_parallel_groups(graph, steps)

        # 应该有 4 组
        assert len(groups) == 4
        assert len(groups[1]) == 2  # 步骤 2 和 3 可并行


class TestSingleExecution:
    """测试单步执行"""

    def test_execute_single_success(self):
        """测试成功执行单步"""
        executor = ParallelExecutor()

        step = Step(step_id="test", description="Test step")

        def mock_executor(step):
            time.sleep(0.001)  # 模拟极短的执行时间
            return StepExecutionResult(
                step_id=step.step_id,
                status=StepExecutionStatus.COMPLETED,
                output="Success"
            )

        result = executor._execute_single(step, mock_executor)

        assert result.step_id == "test"
        assert result.status == StepExecutionStatus.COMPLETED
        assert result.output == "Success"
        assert result.success is True
        assert result.duration >= 0  # duration 可能为 0,但应该是非负数

    def test_execute_single_failure(self):
        """测试执行失败"""
        executor = ParallelExecutor()

        step = Step(step_id="test", description="Test step")

        def mock_executor(step):
            raise ValueError("Test error")

        result = executor._execute_single(step, mock_executor)

        assert result.step_id == "test"
        assert result.status == StepExecutionStatus.FAILED
        assert "Test error" in result.error
        assert result.success is False

    def test_execute_single_with_resources(self):
        """测试带资源锁的执行"""
        executor = ParallelExecutor()

        step = Step(
            step_id="test",
            description="Test step",
            required_resources=["file1.py", "file2.py"]
        )

        def mock_executor(step):
            # 执行期间资源应该被锁定
            assert "file1.py" in executor.resource_manager.lock_history
            assert "file2.py" in executor.resource_manager.lock_history
            return StepExecutionResult(
                step_id=step.step_id,
                status=StepExecutionStatus.COMPLETED,
                output="Success"
            )

        result = executor._execute_single(step, mock_executor)

        assert result.success is True

        # 执行后资源应该被释放


class TestParallelExecution:
    """测试并行执行"""

    def test_execute_parallel_no_deps(self):
        """测试并行执行无依赖任务"""
        executor = ParallelExecutor(max_workers=3)

        steps = [
            Step(step_id=str(i), description=f"Step {i}")
            for i in range(5)
        ]

        def mock_executor(step):
            time.sleep(0.1)  # 模拟耗时
            return StepExecutionResult(
                step_id=step.step_id,
                status=StepExecutionStatus.COMPLETED,
                output=f"Result {step.step_id}"
            )

        results = executor.execute_steps_parallel(steps, mock_executor)

        assert len(results) == 5
        assert all(r.success for r in results)

    def test_execute_parallel_with_deps(self):
        """测试并行执行有依赖任务"""
        executor = ParallelExecutor(max_workers=2)

        steps = [
            Step(step_id="1", description="Step 1"),
            Step(step_id="2", description="Step 2", dependencies=["1"]),
            Step(step_id="3", description="Step 3", dependencies=["1"]),
            Step(step_id="4", description="Step 4", dependencies=["2", "3"]),
        ]

        execution_order = []

        def mock_executor(step):
            execution_order.append(step.step_id)
            return StepExecutionResult(
                step_id=step.step_id,
                status=StepExecutionStatus.COMPLETED,
                output=f"Result {step.step_id}"
            )

        results = executor.execute_steps_parallel(steps, mock_executor)

        assert len(results) == 4
        assert all(r.success for r in results)

        # 验证依赖顺序
        assert execution_order.index("1") < execution_order.index("2")
        assert execution_order.index("1") < execution_order.index("3")
        assert execution_order.index("2") < execution_order.index("4")
        assert execution_order.index("3") < execution_order.index("4")

    def test_execute_parallel_with_failures(self):
        """测试并行执行中的失败"""
        executor = ParallelExecutor(max_workers=2)

        steps = [
            Step(step_id="1", description="Step 1"),
            Step(step_id="2", description="Step 2"),
            Step(step_id="3", description="Step 3"),
        ]

        def mock_executor(step):
            if step.step_id == "2":
                raise ValueError("Step 2 failed")
            return StepExecutionResult(
                step_id=step.step_id,
                status=StepExecutionStatus.COMPLETED,
                output=f"Result {step.step_id}"
            )

        results = executor.execute_steps_parallel(steps, mock_executor)

        assert len(results) == 3

        # 创建结果映射
        result_map = {r.step_id: r for r in results}

        assert result_map["1"].success is True  # 步骤 1
        assert result_map["2"].success is False  # 步骤 2 失败
        assert result_map["3"].success is True  # 步骤 3


class TestExecutionStatistics:
    """测试执行统计"""

    def test_statistics_empty(self):
        """测试空历史统计"""
        executor = ParallelExecutor()

        stats = executor.get_execution_statistics()

        assert stats["total_executions"] == 0
        assert stats["success_rate"] == 0.0

    def test_statistics_after_execution(self):
        """测试执行后的统计"""
        executor = ParallelExecutor()

        steps = [
            Step(step_id=str(i), description=f"Step {i}")
            for i in range(5)
        ]

        def mock_executor(step):
            if step.step_id == "3":
                raise ValueError("Failed")
            return StepExecutionResult(
                step_id=step.step_id,
                status=StepExecutionStatus.COMPLETED,
                output="Success"
            )

        executor.execute_steps_parallel(steps, mock_executor)

        stats = executor.get_execution_statistics()

        assert stats["total_executions"] == 5
        assert stats["successful"] == 4
        assert stats["failed"] == 1
        assert stats["success_rate"] == 0.8
        assert stats["average_duration"] >= 0  # 可能为 0

    def test_reset(self):
        """测试重置"""
        executor = ParallelExecutor()

        steps = [Step(step_id="1", description="Step 1")]

        def mock_executor(step):
            return StepExecutionResult(
                step_id=step.step_id,
                status=StepExecutionStatus.COMPLETED,
                output="Success"
            )

        executor.execute_steps_parallel(steps, mock_executor)

        # 重置
        executor.reset()

        # 历史应该被清空
        stats = executor.get_execution_statistics()
        assert stats["total_executions"] == 0


class TestCompleteWorkflow:
    """测试完整工作流"""

    def test_complex_workflow(self):
        """测试复杂工作流"""
        executor = ParallelExecutor(max_workers=3)

        # 构建复杂的依赖图
        # 1 -> 2, 3, 4 (并行)
        # 2 -> 5
        # 3 -> 5
        # 4 -> 6
        # 5, 6 -> 7
        steps = [
            Step(step_id="1", description="Initial setup"),
            Step(step_id="2", description="Task A", dependencies=["1"]),
            Step(step_id="3", description="Task B", dependencies=["1"]),
            Step(step_id="4", description="Task C", dependencies=["1"]),
            Step(step_id="5", description="Merge A&B", dependencies=["2", "3"]),
            Step(step_id="6", description="Task D", dependencies=["4"]),
            Step(step_id="7", description="Final", dependencies=["5", "6"]),
        ]

        execution_log = []

        def mock_executor(step):
            execution_log.append(step.step_id)
            time.sleep(0.05)  # 模拟耗时
            return StepExecutionResult(
                step_id=step.step_id,
                status=StepExecutionStatus.COMPLETED,
                output=f"Completed {step.step_id}"
            )

        results = executor.execute_steps_parallel(steps, mock_executor)

        # 验证所有步骤都执行了
        assert len(results) == 7
        assert all(r.success for r in results)

        # 验证依赖顺序
        pos = {sid: execution_log.index(sid) for sid in [s.step_id for s in steps]}

        assert pos["1"] < pos["2"]
        assert pos["1"] < pos["3"]
        assert pos["1"] < pos["4"]
        assert pos["2"] < pos["5"]
        assert pos["3"] < pos["5"]
        assert pos["4"] < pos["6"]
        assert pos["5"] < pos["7"]
        assert pos["6"] < pos["7"]

        # 验证并行性
        # 2, 3, 4 应该几乎同时执行(都在 1 之后)
        group_1_time = [pos["2"], pos["3"], pos["4"]]
        assert max(group_1_time) - min(group_1_time) <= 2  # 应该在很短时间内完成

    def test_workflow_with_resources(self):
        """测试带资源管理的工作流"""
        executor = ParallelExecutor(max_workers=2)

        steps = [
            Step(
                step_id="1",
                description="Read file1",
                required_resources=["file1.py"]
            ),
            Step(
                step_id="2",
                description="Read file2",
                required_resources=["file2.py"]
            ),
            Step(
                step_id="3",
                description="Write both",
                dependencies=["1", "2"],
                required_resources=["file1.py", "file2.py"]
            ),
        ]

        def mock_executor(step):
            return StepExecutionResult(
                step_id=step.step_id,
                status=StepExecutionStatus.COMPLETED,
                output="Done"
            )

        results = executor.execute_steps_parallel(steps, mock_executor)

        assert len(results) == 3
        assert all(r.success for r in results)

        # 验证资源使用
        stats = executor.resource_manager.get_lock_statistics()
        assert stats["total_files"] == 2
