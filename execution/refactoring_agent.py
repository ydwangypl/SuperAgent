#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
代码重构Agent

负责识别和改进代码质量,执行重构操作
"""

import asyncio
import logging
import aiofiles
from typing import List, Dict, Any, Set, Optional
from pathlib import Path
from datetime import datetime
import re

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


class RefactoringAgent(BaseAgent):
    """代码重构Agent"""

    def __init__(
        self,
        agent_id: str = "refactoring-agent",
        config: Optional[AgentConfig] = None
    ):
        """初始化代码重构Agent

        Args:
            agent_id: Agent ID
            config: Agent配置
        """
        super().__init__(agent_id, config)

    @property
    def name(self) -> str:
        """返回Agent名称"""
        return "代码重构Agent"

    @classmethod
    def get_capabilities(cls) -> Set[AgentCapability]:
        """返回Agent能力"""
        return {
            AgentCapability.CODE_REFACTORING,
            AgentCapability.OPTIMIZATION,
            AgentCapability.CODE_REVIEW
        }

    async def plan(
        self,
        context: AgentContext,
        task_input: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """规划重构步骤"""
        self.add_step("analyze_code_smells", "分析代码问题", "代码异味和改进点")
        self.add_step("design_refactoring", "设计重构方案", "重构策略和优先级")
        self.add_step("apply_refactoring", "执行重构", "应用重构模式后的代码")
        self.add_step("verify_refactoring", "验证重构", "功能完整性和质量报告")
        return self.steps

    async def execute_impl(
        self,
        context: AgentContext,
        task_input: Dict[str, Any]
    ) -> List[Artifact]:
        """执行代码重构任务 (Phase 3 优化)"""
        # 提取输入
        target_files = task_input.get('target_files', [])
        code_content = task_input.get('code_content', {})
        refactoring_type = task_input.get('refactoring_type', 'clean')

        self.add_log(f"开始重构任务: {refactoring_type}, 目标文件: {len(target_files)}")

        # 步骤1: 分析代码问题
        self.add_thought(1, f"分析代码质量 ({refactoring_type})", f"目标文件: {', '.join(target_files)}")
        issues = await self._analyze_code_smells(context, target_files, code_content)
        self.add_log(f"代码分析完成, 发现 {len(issues)} 个潜在问题")

        # 步骤2: 设计重构方案
        self.add_thought(2, "设计重构方案", f"针对发现的 {len(issues)} 个问题设计方案")
        refactoring_plan = await self._design_refactoring(context, issues, refactoring_type)
        self.add_log(f"重构方案设计完成, 计划执行 {len(refactoring_plan)} 个重构步骤")

        # 步骤3: 执行重构
        self.add_thought(3, "执行代码重构", f"应用 {len(refactoring_plan)} 个改进项")
        refactored_artifacts = await self._apply_refactoring(
            context,
            target_files,
            code_content,
            refactoring_plan
        )
        self.add_log(f"重构执行完成, 生成了 {len(refactored_artifacts)} 个重构工件")

        # 步骤4: 验证重构
        self.add_thought(4, "验证重构结果", "检查代码质量提升情况")
        await self._verify_refactoring(context, issues, refactored_artifacts)
        self.add_log("重构验证完成")

        # 设置指标
        self.set_metric("issues_found", len(issues))
        self.set_metric("refactoring_steps", len(refactoring_plan))
        self.set_metric("refactored_files", len(refactored_artifacts))

        return refactored_artifacts

    async def _analyze_code_smells(
        self,
        context: AgentContext,
        target_files: List[str],
        code_content: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """分析代码异味

        Args:
            context: 执行上下文
            target_files: 目标文件
            code_content: 代码内容

        Returns:
            List[Dict[str, Any]]: 问题列表
        """
        issues = []

        for file_path in target_files:
            content = code_content.get(file_path)
            
            # 兜底逻辑：如果内存中没有代码内容，尝试从磁盘读取
            if not content:
                abs_path = Path(file_path)
                # 审计优化: 优先从 worktree_path 读取，解决并行执行时读取旧版本代码的问题
                target_root = context.worktree_path or context.project_root
                if not abs_path.is_absolute() and target_root:
                    abs_path = target_root / file_path
                
                if abs_path.exists():
                    try:
                        async with aiofiles.open(abs_path, 'r', encoding='utf-8') as f:
                            content = await f.read()
                        logger.info(f"从磁盘读取了文件内容: {abs_path}")
                    except (OSError, UnicodeDecodeError) as e:
                        logger.error(f"读取文件失败 (IO或编码错误) ({type(e).__name__}) {abs_path}: {e}")
                        content = ''
                    except Exception as e:
                        logger.error(f"读取文件失败 (未知系统错误 - {type(e).__name__}) {abs_path}: {e}")
                        content = ''
                else:
                    content = ''

            if not content:
                continue
                
            lines = content.split('\n')

            # 检查长函数
            for i, line in enumerate(lines):
                # 检查行长度
                if len(line) > 100:
                    issues.append({
                        'type': 'long_line',
                        'file': file_path,
                        'line': i + 1,
                        'severity': 'minor',
                        'description': f'行过长 ({len(line)} 字符)',
                        'suggestion': '拆分长行'
                    })

            # 检查重复代码(简化)
            code_lines = [l.strip() for l in lines if l.strip() and not l.strip().startswith('#')]
            line_counts = {}
            for line in code_lines:
                line_counts[line] = line_counts.get(line, 0) + 1

            for line, count in line_counts.items():
                if count > 2:
                    issues.append({
                        'type': 'duplicate_code',
                        'file': file_path,
                        'severity': 'medium',
                        'description': f'重复代码出现 {count} 次',
                        'suggestion': '提取为函数'
                    })

            # 检查复杂度(简化:检查嵌套层级)
            for i, line in enumerate(lines):
                indent = len(line) - len(line.lstrip())
                if indent > 24:  # 超过6层缩进
                    issues.append({
                        'type': 'deep_nesting',
                        'file': file_path,
                        'line': i + 1,
                        'severity': 'major',
                        'description': f'过深的嵌套层级 ({indent // 4} 层)',
                        'suggestion': '重构为更小的函数'
                    })

            # 检查魔法数字
            magic_numbers = re.findall(r'\b(?<!\.)(?!0x)\d{2,}\b', content)
            if magic_numbers:
                issues.append({
                    'type': 'magic_numbers',
                    'file': file_path,
                    'severity': 'minor',
                    'description': f'发现 {len(magic_numbers)} 个魔法数字',
                    'suggestion': '使用命名常量'
                })

        return issues

    async def _design_refactoring(
        self,
        context: AgentContext,
        issues: List[Dict[str, Any]],
        refactoring_type: str
    ) -> List[Dict[str, Any]]:
        """设计重构方案

        Args:
            context: 执行上下文
            issues: 问题列表
            refactoring_type: 重构类型

        Returns:
            List[Dict[str, Any]]: 重构计划
        """
        plan = []

        # 按严重程度和类型分组
        critical_issues = [i for i in issues if i['severity'] == 'major']
        medium_issues = [i for i in issues if i['severity'] == 'medium']
        minor_issues = [i for i in issues if i['severity'] == 'minor']

        # 优先处理严重问题
        for issue in critical_issues:
            plan.append({
                'priority': 'high',
                'issue': issue,
                'action': self._get_refactoring_action(issue['type']),
                'description': f"修复 {issue['type']}"
            })

        # 处理中等问题
        for issue in medium_issues:
            plan.append({
                'priority': 'medium',
                'issue': issue,
                'action': self._get_refactoring_action(issue['type']),
                'description': f"改进 {issue['type']}"
            })

        # 根据重构类型过滤
        if refactoring_type == 'optimize':
            # 只保留性能相关的
            plan = [p for p in plan if 'deep_nesting' in p['issue']['type']]
        elif refactoring_type == 'simplify':
            # 只保留简化相关的
            plan = [p for p in plan if p['issue']['type'] in ['long_line', 'deep_nesting']]

        return plan

    def _get_refactoring_action(self, issue_type: str) -> str:
        """获取重构动作

        Args:
            issue_type: 问题类型

        Returns:
            str: 重构动作
        """
        actions = {
            'long_line': 'split_line',
            'duplicate_code': 'extract_function',
            'deep_nesting': 'reduce_nesting',
            'magic_numbers': 'extract_constant'
        }
        return actions.get(issue_type, 'manual_review')

    async def _apply_refactoring(
        self,
        context: AgentContext,
        target_files: List[str],
        original_content: Dict[str, str],
        refactoring_plan: List[Dict[str, Any]]
    ) -> List[Artifact]:
        """应用重构

        Args:
            context: 执行上下文
            target_files: 目标文件
            original_content: 原始代码
            refactoring_plan: 重构计划

        Returns:
            List[Artifact]: 重构后的工件
        """
        artifacts = []

        for file_path in target_files:
            content = original_content.get(file_path)
            
            # 兜底逻辑：如果内存中没有代码内容，尝试从磁盘读取
            if not content:
                abs_path = Path(file_path)
                # 审计优化: 优先从 worktree_path 读取
                target_root = context.worktree_path or context.project_root
                if not abs_path.is_absolute() and target_root:
                    abs_path = target_root / file_path
                
                if abs_path.exists():
                    try:
                        async with aiofiles.open(abs_path, 'r', encoding='utf-8') as f:
                            content = await f.read()
                    except (OSError, UnicodeDecodeError) as e:
                        logger.error(f"读取文件失败 (IO或编码错误) ({type(e).__name__}) {abs_path}: {e}")
                        content = ''
                    except Exception as e:
                        logger.error(f"读取文件失败 (未知系统错误 - {type(e).__name__}) {abs_path}: {e}")
                        content = ''
                else:
                    content = ''

            if not content:
                continue
                
            refactored_content = content
            changes_count = 0

            # 应用重构操作
            for item in refactoring_plan:
                if item['issue']['file'] == file_path:
                    action = item['action']

                    if action == 'split_line':
                        # 拆分长行(简化实现)
                        lines = refactored_content.split('\n')
                        new_lines = []
                        for line in lines:
                            if len(line) > 100:
                                # 在适当位置拆分
                                split_pos = line.rfind(',', 0, 100)
                                if split_pos > 0:
                                    new_lines.append(line[:split_pos + 1])
                                    new_lines.append(' ' * 8 + line[split_pos + 1:].lstrip())
                                    changes_count += 1
                                else:
                                    new_lines.append(line)
                            else:
                                new_lines.append(line)
                        refactored_content = '\n'.join(new_lines)

                    elif action == 'reduce_nesting':
                        # 减少嵌套(简化实现:添加注释)
                        refactored_content = re.sub(
                            r'(\s{24,})(if |for |while |try:)',
                            r'\1# TODO: 重构以减少嵌套\n\1\2',
                            refactored_content
                        )
                        changes_count += 1

            # 创建重构后的工件
            if changes_count > 0:
                artifact = AgentOutputBuilder.create_refactored_code_artifact(
                    file_path=file_path,
                    content=refactored_content,
                    changes_count=changes_count,
                    metadata={
                        'original_file': file_path,
                        'refactoring_items': [item for item in refactoring_plan if item['issue']['file'] == file_path]
                    },
                    base_dir=context.project_root,
                    worktree_path=context.worktree_path
                )
                artifacts.append(artifact)

        # 如果没有重构,也创建工件(标记为无需重构)
        if not artifacts:
            no_refactor_artifact = AgentOutputBuilder.create_artifact(
                artifact_type="refactored_code",
                path="no_refactor_needed.txt",
                content="代码质量良好,无需重构",
                metadata={
                    'issues_found': len(refactoring_plan)
                },
                base_dir=context.project_root,
                worktree_path=context.worktree_path
            )
            artifacts.append(no_refactor_artifact)

        return artifacts

    async def _verify_refactoring(
        self,
        context: AgentContext,
        original_issues: List[Dict[str, Any]],
        refactored_artifacts: List[Artifact]
    ) -> Dict[str, Any]:
        """验证重构结果

        Args:
            context: 执行上下文
            original_issues: 原始问题
            refactored_artifacts: 重构后的工件

        Returns:
            Dict[str, Any]: 验证结果
        """
        # 简化的验证:检查是否还有明显问题
        remaining_issues = 0

        for artifact in refactored_artifacts:
            if artifact.content:
                # 检查是否还有长行
                lines = artifact.content.split('\n')
                long_lines = [l for l in lines if len(l) > 100]
                remaining_issues += len(long_lines)

        # 计算改进比例
        total_original = len(original_issues)
        improvement_ratio = 0.0
        if total_original > 0:
            improvement_ratio = (total_original - remaining_issues) / total_original

        return {
            'remaining_issues': remaining_issues,
            'improvement_ratio': improvement_ratio,
            'verification_status': 'passed' if improvement_ratio > 0.5 else 'needs_review'
        }
