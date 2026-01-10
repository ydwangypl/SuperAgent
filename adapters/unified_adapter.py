#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
统一适配器

提供一致的接口访问Executor和Reviewer功能,整合执行和审查流程。
"""

import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

from .executor_adapter import ExecutorAdapter
from .reviewer_adapter import ReviewerAdapter


logger = logging.getLogger(__name__)


class UnifiedAdapter:
    """
    统一适配器 - 提供一致的接口访问Executor和Reviewer功能

    这个适配器作为新抽象层和现有Agent系统之间的桥梁,
    提供高级的执行和审查接口。

    示例:
        adapter = UnifiedAdapter(project_root)

        # 仅执行
        result = await adapter.execute_task("code", {"description": "创建API"})

        # 仅审查
        result = await adapter.review_code({"content": "..."})

        # 执行并审查
        result = await adapter.execute_and_review("code", {"description": "创建API"})
    """

    def __init__(self, project_root: Path):
        """
        初始化统一适配器

        Args:
            project_root: 项目根目录
        """
        self.project_root = project_root
        self.executor = ExecutorAdapter(project_root)
        self.reviewer = ReviewerAdapter(project_root)

    async def execute_task(
        self,
        task_type: str,
        task_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        统一的任务执行接口

        Args:
            task_type: 任务类型 ("code", "test", "refactor", etc.)
            task_data: 任务数据
            context: 执行上下文

        Returns:
            执行结果字典,包含:
                - success: bool
                - content: Any
                - status: str
                - error: Optional[str]
                - metadata: Dict
                - execution_time: float
        """
        logger.info(f"Executing task: type={task_type}")

        return await self.executor.execute(
            task_type=task_type,
            task_data=task_data,
            context=context
        )

    def execute_task_sync(
        self,
        task_type: str,
        task_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        同步版本的任务执行接口

        Args:
            task_type: 任务类型
            task_data: 任务数据
            context: 执行上下文

        Returns:
            执行结果字典
        """
        logger.info(f"Executing task (sync): type={task_type}")

        return self.executor.execute_sync(
            task_type=task_type,
            task_data=task_data,
            context=context
        )

    async def review_code(
        self,
        artifact_data: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        统一的代码审查接口

        Args:
            artifact_data: 产物数据
                - content: Union[str, Dict[str, str], List[Path]]
            config: 审查配置

        Returns:
            审查结果字典,包含:
                - status: str
                - overall_score: float
                - metrics: List[Dict]
                - feedback: str
                - approved: bool
                - metadata: Dict
                - review_time: float
        """
        logger.info("Reviewing code artifact")

        return await self.reviewer.review(
            artifact_type="code",
            artifact_data=artifact_data,
            config=config
        )

    def review_code_sync(
        self,
        artifact_data: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        同步版本的代码审查接口

        Args:
            artifact_data: 产物数据
            config: 审查配置

        Returns:
            审查结果字典
        """
        logger.info("Reviewing code artifact (sync)")

        return self.reviewer.review_sync(
            artifact_type="code",
            artifact_data=artifact_data,
            config=config
        )

    async def execute_and_review(
        self,
        task_type: str,
        task_data: Dict[str, Any],
        review_config: Optional[Dict[str, Any]] = None,
        execution_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        执行任务并自动审查结果

        这是最常用的高级接口,它:
        1. 执行任务生成产物
        2. 提取生成的文件/代码
        3. 自动进行代码审查
        4. 返回综合结果

        Args:
            task_type: 任务类型
            task_data: 任务数据
            review_config: 审查配置 (可选)
            execution_context: 执行上下文 (可选)

        Returns:
            综合结果字典,包含:
                - execution: Dict (执行结果)
                - review: Optional[Dict] (审查结果)
                - summary: str (总结)
        """
        logger.info(f"Executing and reviewing: task_type={task_type}")

        # 1. 执行任务
        exec_result = await self.execute_task(task_type, task_data, execution_context)

        # 2. 提取生成的文件/代码用于审查
        code_content = self._extract_code_for_review(exec_result)

        # 3. 如果有可审查的内容,执行审查
        review_result = None
        if code_content:
            logger.info("Executing review on generated content")
            review_result = await self.review_code(
                artifact_data={"content": code_content},
                config=review_config
            )

        # 4. 生成总结
        summary = self._generate_summary(exec_result, review_result)

        return {
            "execution": exec_result,
            "review": review_result,
            "summary": summary
        }

    def execute_and_review_sync(
        self,
        task_type: str,
        task_data: Dict[str, Any],
        review_config: Optional[Dict[str, Any]] = None,
        execution_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        同步版本的执行和审查接口

        Args:
            task_type: 任务类型
            task_data: 任务数据
            review_config: 审查配置
            execution_context: 执行上下文

        Returns:
            综合结果字典
        """
        logger.info(f"Executing and reviewing (sync): task_type={task_type}")

        # 1. 执行任务
        exec_result = self.execute_task_sync(task_type, task_data, execution_context)

        # 2. 提取生成的文件/代码用于审查
        code_content = self._extract_code_for_review(exec_result)

        # 3. 如果有可审查的内容,执行审查
        review_result = None
        if code_content:
            logger.info("Executing review on generated content")
            review_result = self.review_code_sync(
                artifact_data={"content": code_content},
                config=review_config
            )

        # 4. 生成总结
        summary = self._generate_summary(exec_result, review_result)

        return {
            "execution": exec_result,
            "review": review_result,
            "summary": summary
        }

    def _extract_code_for_review(self, exec_result: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """
        从执行结果中提取代码用于审查

        Args:
            exec_result: 执行结果

        Returns:
            代码内容字典 {filename: content},如果没有可审查的内容返回None
        """
        if not exec_result.get("success"):
            return None

        content = exec_result.get("content")

        # 如果content是列表,尝试提取文件内容
        if isinstance(content, list):
            code_content = {}

            for item in content:
                if isinstance(item, dict):
                    # 有路径字段,尝试读取文件
                    if "path" in item and item["path"]:
                        file_path = Path(item["path"])
                        if file_path.exists():
                            try:
                                code_content[file_path.name] = file_path.read_text()
                            except Exception as e:
                                logger.warning(f"Failed to read {file_path}: {e}")

                    # 有content字段,直接使用
                    elif "content" in item and item["content"]:
                        # 使用artifact_id或索引作为key
                        key = item.get("id", f"file_{len(code_content)}")
                        if isinstance(item["content"], str):
                            code_content[f"{key}.py"] = item["content"]

            return code_content if code_content else None

        # 如果content是字符串,直接使用
        elif isinstance(content, str):
            return {"generated_code.py": content}

        # 如果content是字典,假设已经是正确格式
        elif isinstance(content, dict):
            return content

        return None

    def _generate_summary(
        self,
        exec_result: Dict[str, Any],
        review_result: Optional[Dict[str, Any]]
    ) -> str:
        """
        生成执行和审查的总结

        Args:
            exec_result: 执行结果
            review_result: 审查结果 (可选)

        Returns:
            总结文本
        """
        lines = []

        # 执行总结
        if exec_result.get("success"):
            lines.append("✅ 任务执行成功")

            # 添加执行时间
            exec_time = exec_result.get("execution_time", 0)
            if exec_time > 0:
                lines.append(f"   执行时间: {exec_time:.2f}秒")

            # 添加产物信息
            content = exec_result.get("content")
            if isinstance(content, list):
                lines.append(f"   生成产物: {len(content)}个")
            elif content:
                lines.append(f"   已生成内容")
        else:
            lines.append(f"❌ 任务执行失败: {exec_result.get('error', 'Unknown error')}")

        # 审查总结
        if review_result:
            lines.append("")  # 空行

            if review_result.get("approved"):
                lines.append(f"✅ 代码审查通过 (评分: {review_result.get('overall_score', 0):.1f})")
            else:
                lines.append(f"⚠️  代码需要改进 (评分: {review_result.get('overall_score', 0):.1f})")

            # 添加问题数量
            metadata = review_result.get("metadata", {})
            issue_count = metadata.get("issue_count", 0)
            if issue_count > 0:
                lines.append(f"   发现问题: {issue_count}个")
                critical_count = metadata.get("critical_count", 0)
                major_count = metadata.get("major_count", 0)
                if critical_count > 0:
                    lines.append(f"   - 严重: {critical_count}个")
                if major_count > 0:
                    lines.append(f"   - 重要: {major_count}个")

        return "\n".join(lines)
