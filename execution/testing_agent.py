#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试生成Agent

负责分析代码并生成测试需求
"""

import asyncio
import logging
import re
import aiofiles
from typing import List, Dict, Any, Set, Optional
from pathlib import Path
from datetime import datetime

from .base_agent import BaseAgent
from .models import (
    AgentCapability,
    AgentResult,
    AgentContext,
    AgentConfig,
    AgentStatus,
    Artifact,
    AgentThought
)
from .agent_output_builder import AgentOutputBuilder


logger = logging.getLogger(__name__)


class TestingAgent(BaseAgent):
    """测试生成Agent"""

    def __init__(
        self,
        agent_id: str = "testing-agent",
        config: Optional[AgentConfig] = None
    ):
        """初始化测试生成Agent

        Args:
            agent_id: Agent ID
            config: Agent配置
        """
        super().__init__(agent_id, config)

    @property
    def name(self) -> str:
        """返回Agent名称"""
        return "测试生成Agent"

    @classmethod
    def get_capabilities(cls) -> Set[AgentCapability]:
        """返回Agent能力"""
        return {
            AgentCapability.TEST_GENERATION,
            AgentCapability.DEBUGGING
        }

    async def plan(
        self,
        context: AgentContext,
        task_input: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """规划测试生成步骤"""
        self.add_step("analyze_code", "分析代码结构", "代码结构信息")
        self.add_step("design_test_cases", "设计测试用例", "测试场景和覆盖范围")
        self.add_step("generate_test_requirements", "生成测试需求", "测试需求文档")
        return self.steps

    async def execute_impl(
        self,
        context: AgentContext,
        task_input: Dict[str, Any]
    ) -> List[Artifact]:
        """执行测试生成任务的内部实现

        Args:
            context: 执行上下文
            task_input: 任务输入,包含:
                - target_files: 需要测试的目标文件列表
                - code_content: 目标代码内容

        Returns:
            List[Artifact]: 生成的工件列表
        """
        # 步骤1: 分析代码结构
        logger.info(f"[{self.agent_id}] 步骤1: 分析代码结构")
        code_structure = await self._analyze_code(context, task_input)
        self.add_log(f"代码分析完成,发现 {len(code_structure['functions'])} 个函数, {len(code_structure['classes'])} 个类")

        # 步骤2: 设计测试用例
        logger.info(f"[{self.agent_id}] 步骤2: 设计测试用例")
        test_cases = await self._design_test_cases(context, code_structure)
        self.add_log(f"测试用例设计完成,共 {len(test_cases)} 个测试场景")

        # 步骤3: 生成测试需求文档
        logger.info(f"[{self.agent_id}] 步骤3: 生成测试需求")
        artifacts = await self._generate_test_requirements(context, code_structure, test_cases)
        self.add_log(f"测试需求生成完成,生成 {len(artifacts)} 个需求文档")

        # 设置指标
        self.set_metric("functions_count", len(code_structure['functions']))
        self.set_metric("classes_count", len(code_structure['classes']))
        self.set_metric("test_cases_count", len(test_cases))
        self.set_metric("requirements_count", len(artifacts))

        return artifacts

    async def _analyze_code(
        self,
        context: AgentContext,
        task_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """分析代码结构

        Args:
            context: 执行上下文
            task_input: 任务输入

        Returns:
            Dict[str, Any]: 代码结构
        """
        target_files = task_input.get('target_files', [])
        code_content = task_input.get('code_content', {})

        structure = {
            'files': target_files,
            'functions': [],
            'classes': [],
            'methods': [],
            'imports': []
        }

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

            # 查找类定义
            classes = re.findall(r'class\s+(\w+).*?:', content)
            for cls in classes:
                structure['classes'].append({
                    'name': cls,
                    'file': file_path
                })

                # 查找类方法
                class_pattern = rf'class\s+{cls}.*?:(.*?)(?=\nclass|\Z)'
                class_match = re.search(class_pattern, content, re.DOTALL)
                if class_match:
                    methods = re.findall(r'def\s+(\w+)\s*\(', class_match.group(1))
                    for method in methods:
                        if not method.startswith('_'):
                            structure['methods'].append({
                                'name': method,
                                'class': cls,
                                'file': file_path
                            })

            # 查找函数定义
            functions = re.findall(r'^def\s+(\w+)\s*\(', content, re.MULTILINE)
            for func in functions:
                structure['functions'].append({
                    'name': func,
                    'file': file_path
                })

            # 查找导入
            imports = re.findall(r'^import\s+(\w+)|^from\s+(\w+)', content, re.MULTILINE)
            for imp in imports:
                module = imp[0] or imp[1]
                if module not in structure['imports']:
                    structure['imports'].append(module)

        return structure

    async def _design_test_cases(
        self,
        context: AgentContext,
        code_structure: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """设计测试用例

        Args:
            context: 执行上下文
            code_structure: 代码结构

        Returns:
            List[Dict[str, Any]]: 测试用例列表
        """
        test_cases = []

        # 为每个函数生成测试场景
        for func in code_structure['functions']:
            test_cases.append({
                'type': 'unit',
                'target': func['name'],
                'target_type': 'function',
                'scenarios': [
                    '正常情况测试',
                    '边界情况测试',
                    '错误情况测试',
                    '异常处理测试'
                ]
            })

        # 为每个方法生成测试场景
        for method in code_structure['methods']:
            test_cases.append({
                'type': 'unit',
                'target': f"{method['class']}.{method['name']}",
                'target_type': 'method',
                'scenarios': [
                    '正常情况测试',
                    '边界情况测试',
                    '错误情况测试'
                ]
            })

        return test_cases

    async def _generate_test_requirements(
        self,
        context: AgentContext,
        code_structure: Dict[str, Any],
        test_cases: List[Dict[str, Any]]
    ) -> List[Artifact]:
        """生成测试需求文档

        Args:
            context: 执行上下文
            code_structure: 代码结构
            test_cases: 测试用例

        Returns:
            List[Artifact]: 测试需求工件
        """
        target_name = "Code Test"
        if code_structure.get('files'):
            target_name = Path(code_structure['files'][0]).stem

        test_artifact = AgentOutputBuilder.create_test_artifact(
            target_name=target_name,
            test_cases=test_cases,
            code_structure=code_structure,
            base_dir=context.project_root,
            worktree_path=context.worktree_path
        )

        return [test_artifact]
