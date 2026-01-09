import unittest
import sys
from pathlib import Path
import tempfile
import asyncio

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

class TestRalphWiggumIntegration(unittest.IsolatedAsyncioTestCase):
    """Ralph Wiggum 集成测试"""

    async def test_orchestrator_ralph_wiggum_init(self):
        """测试Orchestrator中Ralph Wiggum初始化"""
        from orchestration.orchestrator import Orchestrator
        from orchestration.models import OrchestrationConfig

        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建配置 - 启用Ralph Wiggum
            config = OrchestrationConfig(
                enable_code_review=True,
                enable_ralph_wiggum=True,
                max_critical_issues=0
            )

            orchestrator = Orchestrator(
                project_root=Path(tmpdir),
                config=config
            )

            # 验证结果
            self.assertIsNotNone(orchestrator.review_orchestrator, "Review orchestrator should be initialized")
            self.assertIsNotNone(orchestrator.review_orchestrator.ralph_wiggum_loop, "Ralph Wiggum loop should be initialized")

    async def test_orchestrator_code_review_disabled(self):
        """测试禁用Ralph Wiggum时的行为"""
        from orchestration.orchestrator import Orchestrator
        from orchestration.models import OrchestrationConfig

        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建配置 - 禁用代码审查
            config = OrchestrationConfig(
                enable_code_review=False
            )

            orchestrator = Orchestrator(
                project_root=Path(tmpdir),
                config=config
            )

            # 验证结果
            self.assertIsNone(orchestrator.review_orchestrator.ralph_wiggum_loop, "Ralph Wiggum loop should be None when disabled")

    async def test_ralph_wiggum_improvement_callback(self):
        """测试Ralph Wiggum改进回调"""
        from review.ralph_wiggum import RalphWiggumLoop
        from review.reviewer import CodeReviewer
        from review.models import ReviewConfig

        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建配置
            review_config = ReviewConfig(
                enable_ralph_wiggum=True,
                max_iterations=3,
                min_overall_score=70.0
            )

            # 创建审查器和Ralph Wiggum循环
            reviewer = CodeReviewer(review_config)
            ralph = RalphWiggumLoop(reviewer, review_config)

            # 验证结果
            self.assertIsNotNone(ralph, "Ralph Wiggum loop should be created")
            self.assertTrue(ralph.config.enable_ralph_wiggum, "Ralph Wiggum should be enabled")

    async def test_ralph_wiggum_meets_threshold(self):
        """测试质量阈值检查"""
        from review.ralph_wiggum import RalphWiggumLoop
        from review.reviewer import CodeReviewer
        from review.models import ReviewConfig, ReviewResult, QualityMetrics, ReviewStatus

        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建配置
            review_config = ReviewConfig(
                enable_ralph_wiggum=True,
                max_iterations=3,
                min_overall_score=70.0,
                max_critical_issues=0
            )

            # 创建Ralph Wiggum循环
            reviewer = CodeReviewer(review_config)
            ralph = RalphWiggumLoop(reviewer, review_config)

            # 创建模拟结果
            result = ReviewResult(
                review_id="test-review",
                task_id="test",
                status=ReviewStatus.COMPLETED,
                summary="Test result",
                issues=[],
                metrics=QualityMetrics(
                    issue_count=0,
                    critical_count=0,
                    major_count=0,
                    minor_count=0,
                    file_count=1,
                    total_lines=10
                )
            )

            # 测试阈值检查
            meets_threshold = ralph._meets_quality_threshold(result)
            self.assertTrue(meets_threshold, "Should meet threshold with score 100.0")

    async def test_ralph_wiggum_generate_improvements(self):
        """测试改进建议生成"""
        from review.ralph_wiggum import RalphWiggumLoop
        from review.reviewer import CodeReviewer
        from review.models import (
            ReviewConfig, ReviewResult, QualityMetrics,
            CodeIssue, ReviewSeverity, ReviewStatus, IssueCategory
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建配置
            review_config = ReviewConfig(
                enable_ralph_wiggum=True,
                max_iterations=3,
                min_overall_score=70.0
            )

            # 创建Ralph Wiggum循环
            reviewer = CodeReviewer(review_config)
            ralph = RalphWiggumLoop(reviewer, review_config)

            issues = [
                CodeIssue(
                    issue_id="issue-1",
                    category=IssueCategory.DOCUMENTATION,
                    severity=ReviewSeverity.CRITICAL,
                    title="Missing docstring",
                    description="Function is missing a docstring",
                    file_path=Path("test.py"),
                    line_number=1,
                    suggestion="Add a docstring to the function"
                ),
                CodeIssue(
                    issue_id="issue-2",
                    category=IssueCategory.CODE_STYLE,
                    severity=ReviewSeverity.MAJOR,
                    title="Long line",
                    description="Line is too long",
                    file_path=Path("test.py"),
                    line_number=2,
                    suggestion="Split the line"
                )
            ]

            result = ReviewResult(
                review_id="test-review",
                task_id="test",
                status=ReviewStatus.COMPLETED,
                summary="Test result",
                issues=issues,
                metrics=QualityMetrics(
                    issue_count=2,
                    critical_count=1,
                    major_count=1,
                    minor_count=0,
                    file_count=1,
                    total_lines=10
                )
            )

            # 生成改进建议
            improvements = ralph._generate_improvements(result)
            self.assertGreaterEqual(len(improvements), 1, "Should generate at least one improvement")
            self.assertTrue(any(imp['priority'] == 'critical' for imp in improvements), "Should have critical improvements")

    async def test_async_review_with_loop(self):
        """测试异步审查循环"""
        from review.ralph_wiggum import RalphWiggumLoop
        from review.reviewer import CodeReviewer
        from review.models import ReviewConfig

        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建配置
            review_config = ReviewConfig(
                enable_ralph_wiggum=True,
                max_iterations=2,  # 少量迭代用于测试
                min_overall_score=70.0
            )

            # 创建Ralph Wiggum循环
            reviewer = CodeReviewer(review_config)
            ralph = RalphWiggumLoop(reviewer, review_config)

            # 测试代码
            code = {
                "test.py": "def hello():\n    print('Hello world!')\n"
            }

            test_file = Path(tmpdir) / "test.py"
            test_file.write_text(code["test.py"])

            # 跟踪改进次数
            improvement_count = 0

            async def mock_improvement_callback(current_code, improvements):
                """模拟改进回调"""
                nonlocal improvement_count
                improvement_count += len(improvements)
                return current_code  # 返回原代码表示无实际改进

            # 执行审查循环
            result = await ralph.review_with_loop(
                task_id="test-task",
                files=[test_file],
                code_content=code,
                llm_callback=mock_improvement_callback
            )

            self.assertIsNotNone(result, "Result should not be None")
            self.assertGreater(result.metrics.overall_score, 0, "Score should be greater than 0")

if __name__ == "__main__":
    unittest.main()
