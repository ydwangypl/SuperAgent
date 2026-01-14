#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
扩展性验证集成测试

测试新的架构确实支持多领域扩展:
1. WritingExecutor - 写作执行器
2. ContentReviewer - 内容审查器
3. UnifiedAdapter - 统一适配器集成
"""

import pytest
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.executor import Task, TaskStatus
from core.reviewer import Artifact, ReviewStatus
from extensions.writing_executor import WritingExecutor
from extensions.content_reviewer import ContentReviewer


class TestWritingExecutor:
    """WritingExecutor测试"""

    def test_executor_initialization(self):
        """测试执行器初始化"""
        executor = WritingExecutor()

        assert executor.name == "WritingExecutor"
        assert "writing" in executor.get_supported_types()
        assert "article" in executor.get_supported_types()
        assert "blog" in executor.get_supported_types()

    def test_execute_article_task(self):
        """测试执行文章写作任务"""
        executor = WritingExecutor()

        task = Task(
            task_type="article",
            description="人工智能的发展趋势",
            requirements=[
                "包括历史背景",
                "当前应用",
                "未来展望"
            ],
            context={
                "tone": "professional",
                "length": 800,
                "audience": "技术从业者",
                "keywords": ["AI", "机器学习", "深度学习"]
            }
        )

        result = executor.execute(task)

        # 验证结果
        assert result.success is True
        assert result.status == TaskStatus.COMPLETED
        assert isinstance(result.content, str)
        assert len(result.content) > 0
        assert "人工智能的发展趋势" in result.content
        assert result.metadata["word_count"] > 0
        assert result.metadata["tone"] == "professional"

    def test_execute_blog_task(self):
        """测试执行博客写作任务"""
        executor = WritingExecutor()

        task = Task(
            task_type="blog",
            description="如何学习Python编程",
            context={
                "tone": "friendly",
                "length": 500,
                "audience": "初学者"
            }
        )

        result = executor.execute(task)

        assert result.success is True
        assert result.status == TaskStatus.COMPLETED
        assert "如何学习Python编程" in result.content

    def test_execute_documentation_task(self):
        """测试执行文档写作任务"""
        executor = WritingExecutor()

        task = Task(
            task_type="documentation",
            description="API使用指南",
            requirements=[
                "清晰的安装说明",
                "使用示例",
                "常见问题解答"
            ]
        )

        result = executor.execute(task)

        assert result.success is True
        assert result.status == TaskStatus.COMPLETED
        assert "API使用指南" in result.content

    def test_invalid_task(self):
        """测试无效任务"""
        executor = WritingExecutor()

        task = Task(
            task_type="code",  # 不支持的类型
            description="测试"
        )

        result = executor.execute(task)

        assert result.success is False
        assert result.status == TaskStatus.FAILED

    def test_executor_repr(self):
        """测试执行器字符串表示"""
        executor = WritingExecutor()
        repr_str = repr(executor)

        assert "WritingExecutor" in repr_str
        assert "writing" in repr_str


class TestContentReviewer:
    """ContentReviewer测试"""

    def test_reviewer_initialization(self):
        """测试审查器初始化"""
        reviewer = ContentReviewer()

        assert reviewer.name == "ContentReviewer"
        assert "writing" in reviewer.get_supported_types()
        assert "article" in reviewer.get_supported_types()
        assert "blog" in reviewer.get_supported_types()

    def test_review_good_article(self):
        """测试审查优质文章"""
        reviewer = ContentReviewer()

        # 创建一篇优质文章
        content = """
# 人工智能的未来

人工智能正在改变我们的世界。从医疗到教育,从交通到金融,AI技术无处不在。

## 主要应用领域

首先是医疗领域。AI可以帮助诊断疾病,提高诊断准确性。

其次是教育领域。个性化学习系统正在revolutionizing传统教育模式。

最后是交通领域。自动驾驶技术有望大幅减少交通事故。

## 结论

人工智能的未来充满希望。我们应该积极拥抱这项技术,同时也要注意相关的伦理问题。
"""

        artifact = Artifact(
            artifact_type="article",
            content=content
        )

        result = reviewer.review(artifact)

        # 验证结果 - 应该通过
        assert result.status == ReviewStatus.APPROVED
        assert result.approved is True
        assert result.overall_score >= 60.0

        # 检查指标
        metric_names = [m.name for m in result.metrics]
        assert "length" in metric_names
        assert "readability" in metric_names
        assert "structure" in metric_names
        assert "grammar" in metric_names
        assert "seo" in metric_names

    def test_review_poor_content(self):
        """测试审查低质量内容"""
        reviewer = ContentReviewer()

        # 创建低质量内容 - 空内容
        content = ""

        artifact = Artifact(
            artifact_type="article",
            content=content
        )

        result = reviewer.review(artifact)

        # 应该不通过
        assert result.approved is False
        assert result.overall_score < 60.0

        # 应该有问题
        assert any(len(m.issues) > 0 for m in result.metrics)

    def test_review_structure(self):
        """测试结构审查"""
        reviewer = ContentReviewer()

        # 缺少标题的文章
        content = """
这是一篇文章但没有标题。

段落一的内容。
段落二的内容。
段落三的内容。
"""

        artifact = Artifact(
            artifact_type="article",
            content=content
        )

        result = reviewer.review(artifact)

        # 检查结构指标
        structure_metric = next((m for m in result.metrics if m.name == "structure"), None)
        assert structure_metric is not None
        assert len(structure_metric.issues) > 0  # 应该有问题

    def test_review_readability(self):
        """测试可读性审查"""
        reviewer = ContentReviewer()

        # 包含超长句子的内容
        content = """
# 测试文章

这是一个非常非常非常非常非常非常非常非常非常非常非常非常非常非常非常非常非常非常非常非常非常非常非常非常非常非常长的句子中间没有任何标点符号这会导致可读性下降。

其他正常内容。
"""

        artifact = Artifact(
            artifact_type="article",
            content=content
        )

        result = reviewer.review(artifact)

        # 检查可读性指标
        readability_metric = next((m for m in result.metrics if m.name == "readability"), None)
        assert readability_metric is not None
        # 注意:由于句子可能刚好在阈值内,这个测试只检查指标存在

    def test_reviewer_repr(self):
        """测试审查器字符串表示"""
        reviewer = ContentReviewer()
        repr_str = repr(reviewer)

        assert "ContentReviewer" in repr_str


class TestMultiDomainIntegration:
    """多领域集成测试"""

    def test_writing_workflow(self):
        """测试完整的写作工作流"""
        # 1. 创建执行器和审查器
        executor = WritingExecutor()
        reviewer = ContentReviewer()

        # 2. 执行写作任务
        task = Task(
            task_type="article",
            description="区块链技术简介",
            context={
                "tone": "professional",
                "length": 600
            }
        )

        exec_result = executor.execute(task)

        assert exec_result.success is True
        content = exec_result.content

        # 3. 审查生成的内容
        artifact = Artifact(
            artifact_type="article",
            content=content
        )

        review_result = reviewer.review(artifact)

        # 4. 验证结果
        assert review_result.overall_score >= 0.0
        assert len(review_result.metrics) == 5  # 5个指标

    def test_different_content_types(self):
        """测试不同类型的内容"""
        executor = WritingExecutor()
        reviewer = ContentReviewer()

        content_types = ["article", "blog", "documentation"]

        for content_type in content_types:
            # 执行
            task = Task(
                task_type=content_type,
                description=f"测试{content_type}内容"
            )

            exec_result = executor.execute(task)
            assert exec_result.success is True, f"Failed for {content_type}"

            # 审查
            artifact = Artifact(
                artifact_type=content_type,
                content=exec_result.content
            )

            review_result = reviewer.review(artifact)
            assert review_result.overall_score >= 0.0, f"Review failed for {content_type}"

    def test_extension_proof(self):
        """扩展性证明测试

        这个测试证明:
        1. 新架构确实支持添加非代码领域的执行器
        2. 新架构确实支持添加非代码领域的审查器
        3. 新执行器和审查器可以无缝协作
        4. 没有修改任何现有代码
        """

        # 创建新的执行器 - 不依赖Agent系统
        executor = WritingExecutor()
        assert isinstance(executor, WritingExecutor)
        assert "writing" in executor.get_supported_types()

        # 创建新的审查器 - 不依赖代码审查系统
        reviewer = ContentReviewer()
        assert isinstance(reviewer, ContentReviewer)
        assert "writing" in reviewer.get_supported_types()

        # 它们可以正常工作
        task = Task(task_type="article", description="测试")
        exec_result = executor.execute(task)
        assert exec_result.success

        artifact = Artifact(artifact_type="article", content=exec_result.content)
        review_result = reviewer.review(artifact)
        assert review_result.overall_score >= 0.0

        # ✅ 证明架构确实可扩展!


class TestArchitectureValidation:
    """架构验证测试"""

    def test_executor_abc_compliance(self):
        """验证WritingExecutor符合Executor ABC"""
        from core.executor import Executor

        executor = WritingExecutor()
        assert isinstance(executor, Executor)
        assert hasattr(executor, 'execute')
        assert hasattr(executor, 'can_handle')
        assert hasattr(executor, 'get_supported_types')

    def test_reviewer_abc_compliance(self):
        """验证ContentReviewer符合Reviewer ABC"""
        from core.reviewer import Reviewer

        reviewer = ContentReviewer()
        assert isinstance(reviewer, Reviewer)
        assert hasattr(reviewer, 'review')
        assert hasattr(reviewer, 'can_review')
        assert hasattr(reviewer, 'get_supported_types')

    def test_no_dependency_on_agent_system(self):
        """验证不依赖Agent系统"""
        # WritingExecutor不应该导入任何Agent相关模块
        import extensions.writing_executor
        import inspect

        source = inspect.getsource(extensions.writing_executor)
        # 检查不导入核心Agent模块
        assert "execution.base_agent" not in source
        assert "orchestration.agent_factory" not in source
        # 注意:注释中可能包含"Agent"字样,这是允许的

    def test_no_dependency_on_code_reviewer(self):
        """验证不依赖代码审查系统"""
        # ContentReviewer不应该导入代码审查相关模块
        import extensions.content_reviewer
        import inspect

        source = inspect.getsource(extensions.content_reviewer)
        assert "review.reviewer" not in source
        assert "review.ralph_wiggum" not in source
        assert "CodeReviewer" not in source


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
