#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Agent输出生成器

帮助Agent生成符合规范的输出文档和工件
"""

import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from .models import Artifact, AgentResult, AgentStatus
from common.security import validate_path


logger = logging.getLogger(__name__)


class AgentOutputBuilder:
    """Agent输出构建器 - 帮助生成符合规范的输出"""

    @staticmethod
    def create_artifact(
        artifact_type: str,
        path: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        base_dir: Optional[Path] = None,
        worktree_path: Optional[Path] = None
    ) -> Artifact:
        """创建标准Artifact对象
        审计优化: 增加 worktree_path 参数，优先在工作区内验证和生成路径

        Args:
            artifact_type: 工件类型(requirements, architecture, test_plan等)
            path: 文件路径
            content: 文件内容
            metadata: 额外元数据
            base_dir: 基础目录(用于路径验证)
            worktree_path: 工作区路径(优先用于路径验证)

        Returns:
            Artifact: 标准化的工件对象
        """
        artifact_path = Path(path)
        
        # 路径安全性检查: 优先使用 worktree_path，如果不存在则退回到 base_dir
        target_dir = worktree_path or base_dir
        if target_dir:
            try:
                artifact_path = validate_path(artifact_path, target_dir)
            except Exception as e:
                logger.error(f"工件路径验证失败 (target_dir={target_dir}): {e}")
                # 如果验证失败，我们可以选择抛出异常或重置为安全路径
                # 这里我们先抛出异常，因为这是P0级别的安全性要求
                raise

        return Artifact(
            artifact_id=f"{artifact_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            artifact_type=artifact_type,
            path=artifact_path,
            content=content,
            metadata=metadata or {}
        )

    @staticmethod
    def create_requirements_artifact(
        feature_name: str,
        functional_requirements: List[str],
        non_functional_requirements: List[str],
        technical_constraints: Optional[List[str]] = None,
        base_dir: Optional[Path] = None,
        worktree_path: Optional[Path] = None
    ) -> Artifact:
        """生成需求文档Artifact
        审计优化: 增加 worktree_path 参数
        """
        content = f"""# {feature_name} - 功能需求

## 功能需求

"""
        for i, req in enumerate(functional_requirements, 1):
            content += f"### {i}. {req}\n"

        content += "\n## 非功能需求\n\n"
        for req in non_functional_requirements:
            content += f"- {req}\n"

        if technical_constraints:
            content += "\n## 技术约束\n\n"
            for constraint in technical_constraints:
                content += f"- {constraint}\n"

        return AgentOutputBuilder.create_artifact(
            artifact_type="requirements",
            path="REQUIREMENTS.md",
            content=content,
            metadata={
                "feature_name": feature_name,
                "functional_count": len(functional_requirements),
                "non_functional_count": len(non_functional_requirements)
            },
            base_dir=base_dir,
            worktree_path=worktree_path
        )

    @staticmethod
    def create_test_artifact(
        target_name: str,
        test_cases: List[Dict[str, Any]],
        code_structure: Dict[str, Any],
        base_dir: Optional[Path] = None,
        worktree_path: Optional[Path] = None
    ) -> Artifact:
        """生成测试需求文档Artifact
        审计优化: 增加 worktree_path 参数
        """
        content = f"""# {target_name} - 测试需求文档

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**生成Agent**: SuperAgent v3.2

---

## 一、测试目标

为以下代码生成完整的单元测试:

**目标文件**:
"""
        for file_path in code_structure.get('files', []):
            content += f"- `{file_path}`\n"

        content += f"""
**测试覆盖范围**:
- 函数: {len(code_structure.get('functions', []))} 个
- 类: {len(code_structure.get('classes', []))} 个
- 方法: {len(code_structure.get('methods', []))} 个

---

## 二、代码结构分析

### 2.1 函数列表

"""
        for func in code_structure.get('functions', []):
            content += f"- **{func['name']}()** in `{func['file']}`\n"

        if code_structure.get('classes'):
            content += "\n### 2.2 类列表\n\n"
            for cls in code_structure['classes']:
                content += f"- **{cls['name']}** in `{cls['file']}`\n"

        if code_structure.get('methods'):
            content += "\n### 2.3 方法列表\n\n"
            for method in code_structure['methods']:
                content += f"- **{method['class']}.{method['name']}()** in `{method['file']}`\n"

        content += "\n---\n\n## 三、测试用例设计\n\n"

        for i, test_case in enumerate(test_cases, 1):
            content += f"### 3.{i} {test_case['target']}\n\n"
            content += f"**类型**: {test_case['target_type']}\n\n"
            content += "**测试场景**:\n\n"

            for scenario in test_case.get('scenarios', []):
                content += f"- {scenario}\n"

            content += "\n"

        content += """---

## 四、测试要求

请根据上述需求生成完整的单元测试代码:

1. **测试框架**: 使用 `unittest` 框架
2. **测试组织**: 每个目标文件对应一个测试文件
3. **断言使用**: 使用合适的 `assertEqual`, `assertTrue`, `assertRaises` 等断言
4. **Mock使用**: 对外部依赖、文件IO等进行适当的 Mock 处理
"""

        return AgentOutputBuilder.create_artifact(
            artifact_type="test_requirements",
            path=f"docs/test_requirements_{target_name.lower().replace(' ', '_')}.md",
            content=content,
            base_dir=base_dir,
            worktree_path=worktree_path
        )

    @staticmethod
    def create_documentation_artifact(
        doc_type: str,
        title: str,
        content: str,
        base_dir: Optional[Path] = None,
        worktree_path: Optional[Path] = None
    ) -> Artifact:
        """生成通用文档Artifact
        审计优化: 增加 worktree_path 参数
        """
        # 如果内容不包含标题，则添加
        if not content.strip().startswith("#"):
            full_content = f"# {title}\n\n{content}"
        else:
            full_content = content

        # 添加生成信息
        if "> 由 SuperAgent v3.2" not in full_content:
            generation_info = f"\n\n> 由 SuperAgent v3.2 自动生成\n> 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            # 插入到标题下面
            lines = full_content.split('\n')
            if lines:
                lines.insert(1, generation_info)
                full_content = '\n'.join(lines)

        filename = f"{doc_type.lower().replace(' ', '_')}.md"
        
        return AgentOutputBuilder.create_artifact(
            artifact_type="documentation",
            path=f"docs/{filename}",
            content=full_content,
            base_dir=base_dir,
            worktree_path=worktree_path
        )

    @staticmethod
    def create_refactored_code_artifact(
        file_path: str,
        content: str,
        changes_count: int,
        metadata: Optional[Dict[str, Any]] = None,
        base_dir: Optional[Path] = None,
        worktree_path: Optional[Path] = None
    ) -> Artifact:
        """生成重构后的代码Artifact
        审计优化: 增加 worktree_path 参数
        """
        meta = metadata or {}
        meta.update({'changes_count': changes_count})
        
        return AgentOutputBuilder.create_artifact(
            artifact_type="refactored_code",
            path=file_path,
            content=content,
            metadata=meta,
            base_dir=base_dir,
            worktree_path=worktree_path
        )

    @staticmethod
    def create_architecture_artifact(
        feature_name: str,
        pattern: str,
        layers: List[str],
        dependencies: List[str],
        directory_structure: str,
        base_dir: Optional[Path] = None,
        worktree_path: Optional[Path] = None
    ) -> Artifact:
        """生成架构文档Artifact
        审计优化: 增加 worktree_path 参数
        """
        content = f"""# {feature_name} - 架构设计

## 架构模式
采用 **{pattern}** 模式

## 目录结构
```
{directory_structure}
```

## 技术栈
"""
        for dep in dependencies:
            content += f"- {dep}\n"

        content += "\n## 层次结构\n\n"
        for i, layer in enumerate(layers, 1):
            content += f"{i}. {layer}\n"

        content += "\n## 依赖关系\n\n"
        content += "各层之间通过接口进行依赖,确保松耦合:\n"
        content += "- 上层依赖下层接口\n"
        content += "- 下层实现上层定义的接口\n"
        content += "- 使用依赖注入管理依赖关系\n"

        return AgentOutputBuilder.create_artifact(
            artifact_type="architecture",
            path="ARCHITECTURE.md",
            content=content,
            metadata={
                "feature_name": feature_name,
                "pattern": pattern,
                "layers_count": len(layers),
                "dependencies_count": len(dependencies)
            },
            base_dir=base_dir,
            worktree_path=worktree_path
        )

    @staticmethod
    def create_api_spec_artifact(
        feature_name: str,
        endpoints: List[Dict[str, Any]],
        base_dir: Optional[Path] = None,
        worktree_path: Optional[Path] = None
    ) -> Artifact:
        """生成API规范Artifact
        审计优化: 增加 worktree_path 参数
        """
        content = f"""# {feature_name} - API 规范

## 概述
本文档定义了{feature_name}的RESTful API接口规范。

## 基础信息
- **Base URL**: `/api/v1`
- **认证方式**: JWT Bearer Token
- **数据格式**: JSON

## API端点

"""

        for endpoint in endpoints:
            method = endpoint.get("method", "GET").upper()
            path = endpoint.get("path", "/")
            description = endpoint.get("description", "")

            content += f"### {method} {path}\n\n"
            content += f"{description}\n\n"

            # 请求示例
            if "request" in endpoint:
                content += "**请求**:\n```json\n"
                content += json.dumps(endpoint["request"], indent=2, ensure_ascii=False)
                content += "\n```\n\n"

            # 响应示例
            if "response" in endpoint:
                content += "**响应(200)**:\n```json\n"
                content += json.dumps(endpoint["response"], indent=2, ensure_ascii=False)
                content += "\n```\n\n"

            # 错误响应
            content += "**错误响应(400)**:\n```json\n"
            content += '{"error": "error_message", "code": "ERROR_CODE"}'
            content += "\n```\n\n"

            content += "---\n\n"

        return AgentOutputBuilder.create_artifact(
            artifact_type="api_spec",
            path="API_SPEC.md",
            content=content,
            metadata={
                "feature_name": feature_name,
                "endpoints_count": len(endpoints)
            },
            base_dir=base_dir,
            worktree_path=worktree_path
        )

    @staticmethod
    def create_test_plan_artifact(
        feature_name: str,
        test_types: List[str],
        coverage_targets: Dict[str, int],
        test_frameworks: List[str],
        base_dir: Optional[Path] = None,
        worktree_path: Optional[Path] = None
    ) -> Artifact:
        """生成测试计划Artifact
        审计优化: 增加 base_dir 和 worktree_path 参数
        """
        content = f"""# {feature_name} - 测试计划

## 测试范围
- 功能名称: {feature_name}
- 测试类型: {", ".join(test_types)}

## 测试策略

### 1. 单元测试
**目标**: 测试独立的功能模块

**覆盖范围**:
- 所有业务逻辑函数
- 数据验证逻辑
- 错误处理

### 2. 集成测试
**目标**: 测试模块间交互

**覆盖范围**:
- API端点集成
- 数据库交互
- 外部服务调用

### 3. 端到端测试
**目标**: 测试完整用户流程

**覆盖范围**:
- 用户注册流程
- 用户登录流程
- 数据CRUD操作

## 测试工具

"""
        for framework in test_frameworks:
            content += f"- **{framework}**: 用途说明\n"

        content += "\n## 覆盖率目标\n\n"
        for metric, target in coverage_targets.items():
            content += f"- {metric}: ≥ {target}%\n"

        content += """
## 测试执行

### 本地测试
```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_specific.py

# 生成覆盖率报告
pytest --cov=src --cov-report=html
```

### CI/CD集成
测试将在以下时机自动运行:
- Pull Request创建
- 代码合并到主分支
- 每日定时构建

## 测试数据管理

- 使用工厂模式生成测试数据
- 测试数据与生产数据隔离
- 每次测试后清理测试数据
"""

        return AgentOutputBuilder.create_artifact(
            artifact_type="test_plan",
            path="TEST_PLAN.md",
            content=content,
            metadata={
                "feature_name": feature_name,
                "test_types": test_types,
                "coverage_targets": coverage_targets
            },
            base_dir=base_dir,
            worktree_path=worktree_path
        )

    @staticmethod
    def create_test_cases_artifact(
        feature_name: str,
        unit_tests: List[Dict[str, Any]],
        integration_tests: Optional[List[Dict[str, Any]]] = None,
        base_dir: Optional[Path] = None,
        worktree_path: Optional[Path] = None
    ) -> Artifact:
        """生成测试用例Artifact
        审计优化: 增加 base_dir 和 worktree_path 参数
        """
        content = f"""# {feature_name} - 测试用例

## 单元测试用例

"""

        for test_case in unit_tests:
            content += f"### {test_case['name']}\n\n"
            content += f"**描述**: {test_case['description']}\n\n"

            if "test_data" in test_case:
                content += "**测试数据**:\n"
                for i, data in enumerate(test_case["test_data"], 1):
                    content += f"{i}. 输入: {data.get('input')}, "
                    content += f"预期: {data.get('expected')}\n"

            content += "\n"

        if integration_tests:
            content += "## 集成测试用例\n\n"

            for test_case in integration_tests:
                content += f"### {test_case['name']}\n\n"
                content += f"**描述**: {test_case['description']}\n\n"

                if "endpoints" in test_case:
                    content += "**测试端点**:\n"
                    for endpoint in test_case["endpoints"]:
                        content += f"- `{endpoint}`\n"

                content += "\n"

        return AgentOutputBuilder.create_artifact(
            artifact_type="test_cases",
            path="TEST_CASES.md",
            content=content,
            metadata={
                "feature_name": feature_name,
                "unit_tests_count": len(unit_tests),
                "integration_tests_count": len(integration_tests or [])
            },
            base_dir=base_dir,
            worktree_path=worktree_path
        )

    @staticmethod
    def build_agent_result(
        agent_id: str,
        task_id: str,
        step_id: str,
        artifacts: List[Artifact],
        success: bool = True,
        message: str = "",
        metadata: Optional[Dict[str, Any]] = None,
        next_steps: Optional[List[str]] = None
    ) -> AgentResult:
        """构建标准AgentResult

        Args:
            agent_id: Agent ID
            task_id: 任务ID
            step_id: 步骤ID
            artifacts: 生成的工件列表
            success: 是否成功
            message: 执行消息
            metadata: 元数据
            next_steps: 建议的下一步

        Returns:
            AgentResult: 标准化的执行结果
        """
        result = AgentResult(
            agent_id=agent_id,
            task_id=task_id,
            step_id=step_id,
            status=AgentStatus.COMPLETED if success else AgentStatus.FAILED,
            success=success,
            message=message,
            artifacts=artifacts,
            metadata=metadata or {}
        )

        # 添加next_steps到metadata
        if next_steps:
            result.metadata["next_steps"] = next_steps

        return result

    @staticmethod
    def create_file_list_artifact(
        files: List[str],
        description: str,
        base_dir: Optional[Path] = None,
        worktree_path: Optional[Path] = None
    ) -> Artifact:
        """生成文件列表Artifact
        审计优化: 增加 worktree_path 参数
        """
        content = f"""# 待创建文件列表

{description}

## 文件列表

"""
        for file in files:
            content += f"- {file}\n"

        return AgentOutputBuilder.create_artifact(
            artifact_type="file_list",
            path="FILES.md",
            content=content,
            metadata={
                "file_count": len(files)
            },
            base_dir=base_dir,
            worktree_path=worktree_path
        )
