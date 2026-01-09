#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
文档生成Agent

负责生成项目文档、API文档、使用指南等
"""

import asyncio
import logging
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
    Artifact
)
from .agent_output_builder import AgentOutputBuilder


logger = logging.getLogger(__name__)


class DocumentationAgent(BaseAgent):
    """文档生成Agent"""

    def __init__(
        self,
        agent_id: str = "documentation-agent",
        config: Optional[AgentConfig] = None
    ):
        """初始化文档生成Agent

        Args:
            agent_id: Agent ID
            config: Agent配置
        """
        super().__init__(agent_id, config)

    @property
    def name(self) -> str:
        """返回Agent名称"""
        return "文档生成Agent"

    @classmethod
    def get_capabilities(cls) -> Set[AgentCapability]:
        """返回Agent能力"""
        return {
            AgentCapability.DOCUMENTATION
        }

    async def plan(
        self,
        context: AgentContext,
        task_input: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """规划文档生成步骤

        Args:
            context: 执行上下文
            task_input: 任务输入

        Returns:
            List[Dict[str, Any]]: 执行步骤
        """
        steps = []

        # 步骤1: 分析项目结构
        self.add_thought(
            step=1,
            thought="分析项目结构和代码",
            action="识别模块、类、函数"
        )
        steps.append({
            "step": 1,
            "action": "analyze_project",
            "description": "分析项目"
        })

        # 步骤2: 生成API文档
        self.add_thought(
            step=2,
            thought="生成API文档",
            action="提取函数签名和docstring"
        )
        steps.append({
            "step": 2,
            "action": "generate_api_docs",
            "description": "生成API文档"
        })

        # 步骤3: 生成用户指南
        self.add_thought(
            step=3,
            thought="生成用户使用指南",
            action="编写安装、配置、使用说明"
        )
        steps.append({
            "step": 3,
            "action": "generate_user_guide",
            "description": "生成用户指南"
        })

        # 步骤4: 生成开发文档
        self.add_thought(
            step=4,
            thought="生成开发文档",
            action="编写架构设计、开发指南"
        )
        steps.append({
            "step": 4,
            "action": "generate_dev_docs",
            "description": "生成开发文档"
        })

        return steps

    async def execute_impl(
        self,
        context: AgentContext,
        task_input: Dict[str, Any]
    ) -> List[Artifact]:
        """执行文档生成任务的内部实现

        Args:
            context: 执行上下文
            task_input: 任务输入,包含:
                - project_structure: 项目结构
                - code_files: 代码文件列表
                - doc_type: 文档类型(api, user, dev, all)

        Returns:
            List[Artifact]: 生成的工件列表
        """
        doc_type = task_input.get('doc_type', 'all')
        code_files = task_input.get('code_files', [])

        # 步骤1: 分析项目
        logger.info(f"[{self.agent_id}] 步骤1: 分析项目结构")
        project_info = await self._analyze_project(context, code_files)
        self.add_log(f"项目分析完成")

        artifacts = []

        # 根据文档类型生成不同文档
        if doc_type in ['all', 'api']:
            # 步骤2: 生成API文档
            logger.info(f"[{self.agent_id}] 步骤2: 生成API文档")
            api_docs = await self._generate_api_docs(context, project_info)
            artifacts.extend(api_docs)
            self.add_log(f"API文档生成完成,共 {len(api_docs)} 个文件")

        if doc_type in ['all', 'user']:
            # 步骤3: 生成用户指南
            logger.info(f"[{self.agent_id}] 步骤3: 生成用户指南")
            user_guide = await self._generate_user_guide(context, project_info)
            artifacts.extend(user_guide)
            self.add_log(f"用户指南生成完成,共 {len(user_guide)} 个文件")

        if doc_type in ['all', 'dev']:
            # 步骤4: 生成开发文档
            logger.info(f"[{self.agent_id}] 步骤4: 生成开发文档")
            dev_docs = await self._generate_dev_docs(context, project_info)
            artifacts.extend(dev_docs)
            self.add_log(f"开发文档生成完成,共 {len(dev_docs)} 个文件")

        # 设置指标
        self.set_metric('api_docs_count', len([a for a in artifacts if 'api' in a.artifact_id]))
        self.set_metric('user_docs_count', len([a for a in artifacts if 'user' in a.artifact_id]))
        self.set_metric('dev_docs_count', len([a for a in artifacts if 'dev' in a.artifact_id]))
        self.set_metric('total_docs', len(artifacts))

        return artifacts

    async def _analyze_project(
        self,
        context: AgentContext,
        code_files: List[str]
    ) -> Dict[str, Any]:
        """分析项目结构

        Args:
            context: 执行上下文
            code_files: 代码文件列表

        Returns:
            Dict[str, Any]: 项目信息
        """
        import re

        project_info = {
            'name': context.project_root.name,
            'modules': [],
            'classes': [],
            'functions': [],
            'imports': set()
        }

        for file_path in code_files:
            abs_path = Path(file_path)
            # 审计优化: 优先从 worktree_path 读取，解决并行执行时读取旧版本代码的问题
            target_root = context.worktree_path or context.project_root
            if not abs_path.is_absolute() and target_root:
                abs_path = target_root / file_path
                
            if not abs_path.exists():
                continue

            async with aiofiles.open(abs_path, 'r', encoding='utf-8') as f:
                content = await f.read()

            # 提取模块docstring
            module_doc = re.search(r'"""(.*?)"""', content, re.DOTALL)
            project_info['modules'].append({
                'file': file_path,
                'docstring': module_doc.group(1).strip() if module_doc else ''
            })

            # 提取类和函数
            # 类
            classes = re.findall(r'class\s+(\w+).*?:.*?"""(.*?)"""', content, re.DOTALL)
            for cls_name, cls_doc in classes:
                project_info['classes'].append({
                    'name': cls_name,
                    'docstring': cls_doc.strip(),
                    'file': file_path
                })

            # 函数
            functions = re.findall(r'def\s+(\w+)\s*\([^)]*\).*?:.*?"""(.*?)"""', content, re.DOTALL)
            for func_name, func_doc in functions:
                project_info['functions'].append({
                    'name': func_name,
                    'docstring': func_doc.strip(),
                    'file': file_path
                })

            # 导入
            imports = re.findall(r'^import\s+(\w+)|^from\s+(\w+)', content, re.MULTILINE)
            for imp in imports:
                module = imp[0] or imp[1]
                project_info['imports'].add(module)

        project_info['imports'] = list(project_info['imports'])

        return project_info

    async def _generate_api_docs(
        self,
        context: AgentContext,
        project_info: Dict[str, Any]
    ) -> List[Artifact]:
        """生成API文档

        Args:
            context: 执行上下文
            project_info: 项目信息

        Returns:
            List[Artifact]: API文档工件
        """
        # 生成API文档内容
        api_content = f"本文档描述了 {project_info['name']} 的API接口。\n\n"
        api_content += "## 模块列表\n\n"

        for module in project_info['modules']:
            module_name = Path(module['file']).stem
            api_content += f"### [{module_name}]({module['file']})\n\n"
            if module['docstring']:
                api_content += f"{module['docstring']}\n\n"

        if project_info['classes']:
            api_content += "## 类\n\n"
            for cls in project_info['classes']:
                api_content += f"### {cls['name']}\n\n"
                if cls['docstring']:
                    api_content += f"{cls['docstring']}\n\n"
                api_content += f"**定义位置**: `{cls['file']}`\n\n"

        if project_info['functions']:
            api_content += "## 函数\n\n"
            for func in project_info['functions']:
                api_content += f"### {func['name']}()\n\n"
                if func['docstring']:
                    api_content += f"{func['docstring']}\n\n"
                api_content += f"**定义位置**: `{func['file']}`\n\n"

        if project_info['imports']:
            api_content += "## 依赖项\n\n"
            for imp in project_info['imports']:
                api_content += f"- `{imp}`\n"

        artifact = AgentOutputBuilder.create_documentation_artifact(
            doc_type="api",
            title="API 文档",
            content=api_content,
            base_dir=context.project_root,
            worktree_path=context.worktree_path
        )
        return [artifact]

    async def _generate_user_guide(
        self,
        context: AgentContext,
        project_info: Dict[str, Any]
    ) -> List[Artifact]:
        """生成用户指南

        Args:
            context: 执行上下文
            project_info: 项目信息

        Returns:
            List[Artifact]: 用户指南工件
        """
        user_guide_content = f"欢迎使用 {project_info['name']}!\n\n"
        user_guide_content += "## 快速开始\n\n### 安装\n\n```bash\n# 克隆仓库\ngit clone <repository-url>\ncd " + project_info['name'] + "\n\n# 安装依赖\npip install -r requirements.txt\n```\n\n"
        user_guide_content += "### 基本使用\n\n```python\n# 导入模块\n# TODO: 添加导入示例\n\n# 使用\n# TODO: 添加使用示例\n```\n\n"
        user_guide_content += "## 功能特性\n\n- 功能1: 描述\n- 功能2: 描述\n- 功能3: 描述\n\n"
        user_guide_content += "## 常见问题\n\n### Q: 如何安装?\n\nA: 请参考上面的安装说明。\n\n### Q: 如何配置?\n\nA: 配置文件位于 `config.yaml`,根据需要修改。\n\n"
        user_guide_content += "## 获取帮助\n\n如有问题,请:\n1. 查看文档\n2. 提交Issue\n3. 联系支持\n\n## 许可证\n\nMIT License"

        artifact = AgentOutputBuilder.create_documentation_artifact(
            doc_type="user_guide",
            title="用户指南",
            content=user_guide_content,
            base_dir=context.project_root,
            worktree_path=context.worktree_path
        )
        return [artifact]

    async def _generate_dev_docs(
        self,
        context: AgentContext,
        project_info: Dict[str, Any]
    ) -> List[Artifact]:
        """生成开发文档

        Args:
            context: 执行上下文
            project_info: 项目信息

        Returns:
            List[Artifact]: 开发文档工件
        """
        # 生成架构文档
        arch_content = f"{project_info['name']} 采用模块化设计,主要包含以下组件:\n\n### 模块概览\n\n"
        for module in project_info['modules']:
            module_name = Path(module['file']).stem
            arch_content += f"#### {module_name}\n\n**文件**: `{module['file']}`\n\n"
            if module['docstring']:
                arch_content += f"{module['docstring']}\n\n"

        if project_info['classes']:
            arch_content += "### 类设计\n\n"
            for cls in project_info['classes']:
                arch_content += f"#### {cls['name']}\n\n- **文件**: `{cls['file']}`\n- **描述**: {cls['docstring'] or '无'}\n\n"

        arch_content += "## 技术栈\n\n- Python 3.x\n"
        for imp in project_info['imports'][:5]:
            arch_content += f"- {imp}\n"

        arch_artifact = AgentOutputBuilder.create_documentation_artifact(
            doc_type="architecture",
            title="架构设计文档",
            content=arch_content,
            base_dir=context.project_root,
            worktree_path=context.worktree_path
        )

        # 开发指南
        dev_guide_content = "## 开发环境设置\n\n```bash\n# 克隆仓库\ngit clone <repository-url>\ncd <project-name>\n\n# 创建虚拟环境\npython -m venv venv\nsource venv/bin/activate  # Linux/Mac\n# 或\nvenv\\Scripts\\activate  # Windows\n\n# 安装开发依赖\npip install -r requirements-dev.txt\n```\n\n"
        dev_guide_content += "## 代码风格\n\n本项目遵循 PEP 8 代码风格规范。\n\n```bash\n# 运行代码检查\nflake8 .\nblack .\n```\n\n"
        dev_guide_content += "## 运行测试\n\n```bash\n# 运行所有测试\npytest\n\n# 运行特定测试\npytest tests/test_specific.py\n\n# 生成覆盖率报告\npytest --cov=src --cov-report=html\n```\n\n"
        dev_guide_content += "## 提交代码\n\n1. Fork本仓库\n2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)\n3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)\n4. 推送到分支 (`git push origin feature/AmazingFeature`)\n5. 开启Pull Request\n\n## 项目结构\n\n```\n.\n├── src/               # 源代码\n├── tests/             # 测试代码\n├── docs/              # 文档\n├── examples/          # 示例代码\n└── scripts/           # 工具脚本\n```"

        dev_guide_artifact = AgentOutputBuilder.create_documentation_artifact(
            doc_type="development",
            title="开发指南",
            content=dev_guide_content,
            base_dir=context.project_root,
            worktree_path=context.worktree_path
        )

        return [arch_artifact, dev_guide_artifact]
