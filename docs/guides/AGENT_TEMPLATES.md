# SuperAgent Agent 模板和示例

> **版本**: v3.2+
> **更新日期**: 2026-01-14
> **目标读者**: 需要 Agent 快速起点的开发者

---

## 📋 目录

1. [基础 Agent 模板](#基础-agent-模板)
2. [完整 Agent 模板](#完整-agent-模板)
3. [Agent 示例集合](#agent-示例集合)
4. [测试模板](#测试模板)
5. [配置模板](#配置模板)

---

## 🎯 基础 Agent 模板

### 最小化模板

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
最小化 Agent 模板
"""

from typing import List, Dict, Any, Set
from execution.base_agent import BaseAgent
from execution.models import (
    AgentCapability,
    AgentContext,
    Artifact
)


class MinimalAgent(BaseAgent):
    """最小化 Agent 示例"""

    @property
    def name(self) -> str:
        """返回 Agent 名称"""
        return "最小化Agent"

    @classmethod
    def get_capabilities(cls) -> Set[AgentCapability]:
        """定义 Agent 能力"""
        return {AgentCapability.CODE_GENERATION}

    async def execute_impl(
        self,
        context: AgentContext,
        task_input: Dict[str, Any]
    ) -> List[Artifact]:
        """核心执行逻辑"""
        # 生成工件
        artifact = Artifact(
            type="code",
            path="output.py",
            content="print('Hello, World!')",
            metadata={}
        )
        return [artifact]
```

### 标准模板

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
标准 Agent 模板
"""

import logging
from typing import List, Dict, Any, Set, Optional
from execution.base_agent import BaseAgent
from execution.models import (
    AgentCapability,
    AgentContext,
    AgentConfig,
    Artifact
)

logger = logging.getLogger(__name__)


class StandardAgent(BaseAgent):
    """标准 Agent 模板"""

    def __init__(
        self,
        agent_id: str = "standard-agent",
        config: Optional[AgentConfig] = None
    ):
        """初始化 Agent"""
        super().__init__(agent_id, config)
        # 自定义初始化
        self.custom_property = "default_value"

    @property
    def name(self) -> str:
        """返回 Agent 名称"""
        return "标准Agent"

    @classmethod
    def get_capabilities(cls) -> Set[AgentCapability]:
        """定义 Agent 能力"""
        return {
            AgentCapability.CODE_GENERATION,
            AgentCapability.DOCUMENTATION
        }

    def validate_input(self, task_input: Dict[str, Any]) -> bool:
        """验证输入数据"""
        # 检查必需字段
        if "description" not in task_input:
            self.add_log("缺少 description 字段", level="error")
            return False

        # 检查字段类型
        if not isinstance(task_input["description"], str):
            self.add_log("description 必须是字符串", level="error")
            return False

        # 检查字段值
        if len(task_input["description"].strip()) == 0:
            self.add_log("description 不能为空", level="error")
            return False

        return True

    async def plan(
        self,
        context: AgentContext,
        task_input: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """规划执行步骤"""
        # 步骤 1: 分析需求
        self.add_step(
            step_id="analyze_requirements",
            description="分析功能需求",
            expected_output="需求列表"
        )

        # 步骤 2: 生成工件
        self.add_step(
            step_id="generate_artifacts",
            description="生成工件",
            expected_output="工件列表"
        )

        return self.steps

    async def execute_impl(
        self,
        context: AgentContext,
        task_input: Dict[str, Any]
    ) -> List[Artifact]:
        """核心执行逻辑"""
        self.add_log("开始执行任务")

        # 步骤 1: 分析需求
        description = task_input.get("description", "")
        self.add_thought(
            step=1,
            thought=f"分析需求: {description}",
            action="提取核心功能点"
        )

        # 步骤 2: 生成工件
        artifacts = []

        # 生成代码工件
        code_artifact = Artifact(
            type="code",
            path="output/main.py",
            content=f"# {description}\nprint('Hello')",
            metadata={"language": "Python"}
        )
        artifacts.append(code_artifact)
        self.add_log("生成代码工件: output/main.py")

        # 生成文档工件
        doc_artifact = Artifact(
            type="documentation",
            path="docs/README.md",
            content=f"# {description}\n\n这是一个示例项目。",
            metadata={"format": "markdown"}
        )
        artifacts.append(doc_artifact)
        self.add_log("生成文档工件: docs/README.md")

        # 设置指标
        self.set_metric("artifacts_count", len(artifacts))
        self.set_metric("code_lines", 10)
        self.set_metric("doc_lines", 5)

        self.add_log(f"任务完成,生成了 {len(artifacts)} 个工件")

        return artifacts
```

---

## 🏗️ 完整 Agent 模板

### 带完整功能的模板

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
完整功能 Agent 模板
"""

import asyncio
import logging
from typing import List, Dict, Any, Set, Optional
from pathlib import Path
from execution.base_agent import BaseAgent
from execution.models import (
    AgentCapability,
    AgentContext,
    AgentConfig,
    Artifact
)

logger = logging.getLogger(__name__)


class FullFeaturedAgent(BaseAgent):
    """完整功能 Agent 模板"""

    def __init__(
        self,
        agent_id: str = "full-featured-agent",
        config: Optional[AgentConfig] = None,
        # 自定义配置
        enable_advanced_features: bool = True
    ):
        """初始化 Agent"""
        super().__init__(agent_id, config)

        # 自定义属性
        self.enable_advanced_features = enable_advanced_features
        self._cache = {}

        self.add_log(f"Agent 初始化完成 (高级功能: {enable_advanced_features})")

    @property
    def name(self) -> str:
        """返回 Agent 名称"""
        return "完整功能Agent"

    @classmethod
    def get_capabilities(cls) -> Set[AgentCapability]:
        """定义 Agent 能力"""
        return {
            AgentCapability.CODE_GENERATION,
            AgentCapability.DOCUMENTATION,
            AgentCapability.ARCHITECTURE
        }

    def validate_input(self, task_input: Dict[str, Any]) -> bool:
        """验证输入数据"""
        # 1. 检查必需字段
        required_fields = ["description"]
        for field in required_fields:
            if field not in task_input:
                self.add_log(f"缺少必需字段: {field}", level="error")
                return False

        # 2. 验证字段类型
        if not isinstance(task_input["description"], str):
            self.add_log("description 必须是字符串", level="error")
            return False

        # 3. 验证字段值
        description = task_input["description"].strip()
        if len(description) == 0:
            self.add_log("description 不能为空", level="error")
            return False

        if len(description) > 1000:
            self.add_log("description 过长 (最多 1000 字符)", level="warning")

        # 4. 验证可选字段
        if "tech_stack" in task_input:
            if not isinstance(task_input["tech_stack"], list):
                self.add_log("tech_stack 必须是列表", level="error")
                return False

            if len(task_input["tech_stack"]) == 0:
                self.add_log("tech_stack 不能为空", level="error")
                return False

        return True

    async def plan(
        self,
        context: AgentContext,
        task_input: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """规划执行步骤"""
        # 步骤 1: 验证输入
        self.add_step(
            step_id="validate_input",
            description="验证输入数据",
            expected_output="验证通过"
        )

        # 步骤 2: 分析需求
        self.add_step(
            step_id="analyze_requirements",
            description="分析功能需求",
            expected_output="需求列表"
        )

        # 步骤 3: 设计架构
        self.add_step(
            step_id="design_architecture",
            description="设计系统架构",
            expected_output="架构文档"
        )

        # 步骤 4: 生成代码
        self.add_step(
            step_id="generate_code",
            description="生成代码框架",
            expected_output="代码文件"
        )

        # 步骤 5: 生成文档
        self.add_step(
            step_id="generate_documentation",
            description="生成项目文档",
            expected_output="文档文件"
        )

        return self.steps

    async def execute_impl(
        self,
        context: AgentContext,
        task_input: Dict[str, Any]
    ) -> List[Artifact]:
        """核心执行逻辑"""
        self.add_log("=" * 50)
        self.add_log(f"开始执行任务: {context.task_id}")
        self.add_log("=" * 50)

        start_time = asyncio.get_event_loop().time()

        try:
            # 步骤 1: 解析输入
            description = task_input.get("description", "")
            tech_stack = task_input.get("tech_stack", ["Python"])

            self.add_thought(
                step=1,
                thought="解析输入参数",
                action=f"description={description[:50]}..., tech_stack={tech_stack}"
            )

            # 步骤 2: 分析需求
            requirements = self._analyze_requirements(description)

            self.add_thought(
                step=2,
                thought=f"分析需求: {description}",
                action=f"提取了 {len(requirements)} 个需求",
                result=f"需求: {', '.join(requirements[:3])}"
            )

            self.add_log(f"需求分析完成: {len(requirements)} 个需求")

            # 步骤 3: 设计架构
            architecture = self._design_architecture(description, tech_stack)

            self.add_thought(
                step=3,
                thought="设计系统架构",
                action=f"选择架构模式: {architecture['pattern']}",
                result=f"{len(architecture['layers'])} 层架构"
            )

            self.add_log(f"架构设计完成: {architecture['pattern']}")

            # 步骤 4: 生成代码
            code_artifacts = await self._generate_code(
                description,
                tech_stack,
                architecture
            )

            self.add_thought(
                step=4,
                thought="生成代码框架",
                action=f"生成 {len(code_artifacts)} 个代码文件",
                result=f"代码行数: {sum(a.metadata.get('lines', 0) for a in code_artifacts)}"
            )

            self.add_log(f"代码生成完成: {len(code_artifacts)} 个文件")

            # 步骤 5: 生成文档
            doc_artifacts = await self._generate_documentation(
                description,
                requirements,
                architecture
            )

            self.add_thought(
                step=5,
                thought="生成项目文档",
                action=f"生成 {len(doc_artifacts)} 个文档文件",
                result="文档生成完成"
            )

            self.add_log(f"文档生成完成: {len(doc_artifacts)} 个文件")

            # 合并所有工件
            all_artifacts = code_artifacts + doc_artifacts

            # 计算执行时间
            end_time = asyncio.get_event_loop().time()
            duration = end_time - start_time

            # 设置指标
            self.set_metric("artifacts_count", len(all_artifacts))
            self.set_metric("code_artifacts", len(code_artifacts))
            self.set_metric("doc_artifacts", len(doc_artifacts))
            self.set_metric("requirements_count", len(requirements))
            self.set_metric("execution_time", duration)

            self.add_log("=" * 50)
            self.add_log(f"任务完成: {len(all_artifacts)} 个工件, 耗时 {duration:.2f} 秒")
            self.add_log("=" * 50)

            return all_artifacts

        except Exception as e:
            self.add_log(f"执行失败: {type(e).__name__}: {str(e)}", level="error")
            logger.exception("详细错误信息:")
            raise

    def _analyze_requirements(self, description: str) -> List[str]:
        """分析需求 (私有方法)"""
        # 简单的需求提取逻辑
        requirements = []

        # 基于关键词提取
        if "API" in description or "接口" in description:
            requirements.append("API 接口设计")

        if "数据库" in description or "存储" in description:
            requirements.append("数据持久化")

        if "用户" in description or "权限" in description:
            requirements.append("用户管理")

        # 默认需求
        if not requirements:
            requirements = ["基本功能实现", "错误处理", "日志记录"]

        return requirements

    def _design_architecture(
        self,
        description: str,
        tech_stack: List[str]
    ) -> Dict[str, Any]:
        """设计架构 (私有方法)"""
        # 根据技术栈选择架构
        if any("web" in tech.lower() for tech in tech_stack):
            return {
                "pattern": "分层架构 (Layered Architecture)",
                "layers": ["接口层", "业务层", "数据层"],
                "structure": """src/
├── api/       # 接口定义
├── services/  # 业务逻辑
├── models/    # 数据模型
└── main.py    # 入口文件"""
            }
        else:
            return {
                "pattern": "模块化架构 (Modular Architecture)",
                "layers": ["核心引擎", "功能模块", "工具集"],
                "structure": """src/
├── core/      # 核心逻辑
├── modules/   # 功能模块
├── utils/     # 工具函数
└── main.py    # 入口文件"""
            }

    async def _generate_code(
        self,
        description: str,
        tech_stack: List[str],
        architecture: Dict[str, Any]
    ) -> List[Artifact]:
        """生成代码 (私有方法)"""
        artifacts = []

        # 生成主文件
        main_content = f'''#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
{description}
"""

def main():
    """主函数"""
    print("Hello, World!")

if __name__ == "__main__":
    main()
'''

        main_artifact = Artifact(
            type="code",
            path="main.py",
            content=main_content,
            metadata={
                "language": "Python",
                "lines": len(main_content.split('\\n'))
            }
        )
        artifacts.append(main_artifact)

        # 生成配置文件
        config_content = '''# Configuration
DEBUG = True
SECRET_KEY = "your-secret-key"
'''

        config_artifact = Artifact(
            type="config",
            path="config.py",
            content=config_content,
            metadata={"format": "python"}
        )
        artifacts.append(config_artifact)

        return artifacts

    async def _generate_documentation(
        self,
        description: str,
        requirements: List[str],
        architecture: Dict[str, Any]
    ) -> List[Artifact]:
        """生成文档 (私有方法)"""
        artifacts = []

        # 生成 README
        readme_content = f'''# {description}

## 功能需求

{chr(10).join(f"- {req}" for req in requirements)}

## 架构设计

**架构模式**: {architecture['pattern']}

**层次结构**:
{chr(10).join(f"- {layer}" for layer in architecture['layers'])}

## 目录结构

```
{architecture['structure']}
```

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 运行
python main.py
```

## 开发

...

## 许可证

MIT
'''

        readme_artifact = Artifact(
            type="documentation",
            path="README.md",
            content=readme_content,
            metadata={"format": "markdown"}
        )
        artifacts.append(readme_artifact)

        return artifacts
```

---

## 💡 Agent 示例集合

### 示例 1: 文档生成 Agent

```python
class DocumentationAgent(BaseAgent):
    """文档生成 Agent"""

    @property
    def name(self) -> str:
        return "文档生成Agent"

    @classmethod
    def get_capabilities(cls) -> Set[AgentCapability]:
        return {AgentCapability.DOCUMENTATION}

    async def execute_impl(
        self,
        context: AgentContext,
        task_input: Dict[str, Any]
    ) -> List[Artifact]:
        """生成文档"""
        title = task_input.get("title", "未命名文档")
        content = task_input.get("content", "")

        # 生成 Markdown 文档
        markdown_content = f"""# {title}

{content}

---

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

        artifact = Artifact(
            type="documentation",
            path=f"docs/{title.lower().replace(' ', '_')}.md",
            content=markdown_content,
            metadata={"format": "markdown"}
        )

        return [artifact]
```

### 示例 2: 代码重构 Agent

```python
class RefactoringAgent(BaseAgent):
    """代码重构 Agent"""

    @property
    def name(self) -> str:
        return "代码重构Agent"

    @classmethod
    def get_capabilities(cls) -> Set[AgentCapability]:
        return {AgentCapability.REFACTORING}

    async def execute_impl(
        self,
        context: AgentContext,
        task_input: Dict[str, Any]
    ) -> List[Artifact]:
        """重构代码"""
        source_code = task_input.get("source_code", "")
        refactoring_type = task_input.get("type", "simplify")

        # 重构代码
        if refactoring_type == "simplify":
            refactored_code = self._simplify_code(source_code)
        elif refactoring_type == "optimize":
            refactored_code = self._optimize_code(source_code)
        else:
            refactored_code = source_code

        # 生成重构报告
        report = f"""# 代码重构报告

**重构类型**: {refactoring_type}
**原始代码行数**: {len(source_code.split('\\n'))}
**重构后代码行数**: {len(refactored_code.split('\\n'))}
**减少行数**: {len(source_code.split('\\n')) - len(refactored_code.split('\\n'))}

## 重构后的代码

```python
{refactored_code}
```
"""

        artifacts = [
            Artifact(
                type="code",
                path="refactored_code.py",
                content=refactored_code,
                metadata={"refactoring_type": refactoring_type}
            ),
            Artifact(
                type="documentation",
                path="refactoring_report.md",
                content=report,
                metadata={"format": "markdown"}
            )
        ]

        return artifacts

    def _simplify_code(self, code: str) -> str:
        """简化代码"""
        # 简化逻辑
        lines = code.split('\\n')
        simplified = [line for line in lines if line.strip() and not line.strip().startswith('#')]
        return '\\n'.join(simplified)

    def _optimize_code(self, code: str) -> str:
        """优化代码"""
        # 优化逻辑
        return code.replace("print(", "logging.info(")
```

### 示例 3: 测试生成 Agent

```python
class TestingAgent(BaseAgent):
    """测试生成 Agent"""

    @property
    def name(self) -> str:
        return "测试生成Agent"

    @classmethod
    def get_capabilities(cls) -> Set[AgentCapability]:
        return {AgentCapability.TESTING}

    async def execute_impl(
        self,
        context: AgentContext,
        task_input: Dict[str, Any]
    ) -> List[Artifact]:
        """生成测试"""
        source_file = task_input.get("source_file", "")
        test_framework = task_input.get("framework", "pytest")

        # 生成测试代码
        test_code = f'''#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自动生成的测试文件
"""

import pytest
from {source_file.replace('.py', '')} import *


class TestGenerated:
    """自动生成的测试类"""

    def test_example_1(self):
        """测试用例 1"""
        assert True

    def test_example_2(self):
        """测试用例 2"""
        assert 1 + 1 == 2

    @pytest.mark.asyncio
    async def test_async_example(self):
        """异步测试用例"""
        await asyncio.sleep(0.1)
        assert True
'''

        artifact = Artifact(
            type="test",
            path=f"tests/test_{source_file.replace('/', '_').replace('.py', '')}.py",
            content=test_code,
            metadata={"framework": test_framework}
        )

        return [artifact]
```

---

## 🧪 测试模板

### 基础测试模板

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Agent 测试模板
"""

import pytest
from execution.my_agent import MyAgent
from execution.models import AgentContext, AgentConfig, AgentType


@pytest.mark.asyncio
async def test_agent_basic():
    """测试 Agent 基本功能"""
    # 创建 Agent
    agent = MyAgent(agent_id="test-agent-1")

    # 验证基本属性
    assert agent.name == "我的Agent"
    assert len(agent.capabilities) > 0

    # 创建上下文
    context = AgentContext(
        task_id="test-task-1",
        step_id="test-step-1",
        project_root="/tmp/test",
        worktree_path=None
    )

    # 创建输入
    task_input = {
        "description": "测试任务",
        "tech_stack": ["Python"]
    }

    # 执行任务
    result = await agent.execute(context, task_input)

    # 验证结果
    assert result.success is True
    assert len(result.artifacts) > 0
    assert result.status.value == "completed"


@pytest.mark.asyncio
async def test_agent_with_retry():
    """测试 Agent 重试机制"""
    config = AgentConfig(max_retries=2, retry_delay=0.1)
    agent = MyAgent(agent_id="test-agent-2", config=config)

    context = AgentContext(
        task_id="test-task-2",
        step_id="test-step-2",
        project_root="/tmp/test",
        worktree_path=None
    )

    task_input = {
        "description": "测试重试",
        "tech_stack": ["Python"]
    }

    result = await agent.run(context, task_input)

    assert result.success is True
    assert result.duration_seconds is not None


@pytest.mark.asyncio
async def test_agent_invalid_input():
    """测试无效输入"""
    agent = MyAgent(agent_id="test-agent-3")

    context = AgentContext(
        task_id="test-task-3",
        step_id="test-step-3",
        project_root="/tmp/test",
        worktree_path=None
    )

    # 无效输入
    task_input = {
        # 缺少 description
    }

    result = await agent.execute(context, task_input)

    assert result.success is False
    assert result.error is not None


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
```

### 集成测试模板

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Agent 集成测试模板
"""

import pytest
from orchestration.agent_factory import AgentFactory
from orchestration.agent_dispatcher import AgentDispatcher
from orchestration.models import TaskExecution, TaskStatus


@pytest.mark.asyncio
async def test_agent_factory_integration():
    """测试 AgentFactory 集成"""
    # 创建 Agent
    agent = AgentFactory.create_agent(AgentType.BACKEND_DEV)

    # 验证
    assert agent is not None
    assert agent.name == "代码生成Agent"


@pytest.mark.asyncio
async def test_dispatcher_integration():
    """测试 Dispatcher 集成"""
    # 创建 Dispatcher
    dispatcher = AgentDispatcher()

    # 创建任务
    task = TaskExecution(
        task_id="integration-test-1",
        agent_type="backend_dev",
        inputs={"description": "开发用户API"}
    )

    # 执行任务
    result = await dispatcher.execute_with_agent(task)

    # 验证结果
    assert result.status == TaskStatus.COMPLETED
```

---

## ⚙️ 配置模板

### AgentConfig 配置

```python
from execution.models import AgentConfig

# 基础配置
config1 = AgentConfig()

# 自定义配置
config2 = AgentConfig(
    max_retries=5,              # 最多重试 5 次
    retry_delay=2.0,            # 每次重试间隔 2 秒
    timeout=600,                # 超时时间 600 秒
    save_intermediate=True,     # 保存中间结果
    enable_metrics=True         # 启用指标收集
)

# 使用配置
agent = MyAgent(agent_id="my-agent", config=config2)
```

### AgentDispatcher 配置

```python
from orchestration.agent_dispatcher import AgentDispatcher
from orchestration.models import AgentResource

# 默认配置
dispatcher1 = AgentDispatcher()

# 自定义资源配置
custom_resources = {
    "backend_dev": AgentResource(
        agent_type="backend_dev",
        max_concurrent=20  # 最大并发 20
    ),
    "qa_engineering": AgentResource(
        agent_type="qa_engineering",
        max_concurrent=15
    )
}

dispatcher2 = AgentDispatcher(agent_resources=custom_resources)
```

---

## 📚 使用示例

### 示例 1: 基本使用

```python
import asyncio
from execution.my_agent import MyAgent
from execution.models import AgentContext


async def main():
    # 创建 Agent
    agent = MyAgent(agent_id="my-agent-1")

    # 创建上下文
    context = AgentContext(
        task_id="task-1",
        step_id="step-1",
        project_root="/path/to/project",
        worktree_path=None
    )

    # 准备输入
    task_input = {
        "description": "开发用户管理API",
        "tech_stack": ["Python", "FastAPI"]
    }

    # 执行任务
    result = await agent.execute(context, task_input)

    # 查看结果
    if result.success:
        print(f"成功生成 {len(result.artifacts)} 个工件:")
        for artifact in result.artifacts:
            print(f"  - {artifact.type}: {artifact.path}")
    else:
        print(f"执行失败: {result.error}")


if __name__ == "__main__":
    asyncio.run(main())
```

### 示例 2: 使用 AgentFactory

```python
import asyncio
from orchestration.agent_factory import AgentFactory
from execution.models import AgentContext


async def main():
    # 创建 Agent
    agent = AgentFactory.create_agent(
        AgentType.BACKEND_DEV,
        agent_id="my-backend-agent"
    )

    # 创建上下文
    context = AgentContext(
        task_id="task-2",
        step_id="step-1",
        project_root="/path/to/project",
        worktree_path=None
    )

    # 执行任务
    result = await agent.execute(context, {
        "description": "开发用户管理API",
        "tech_stack": ["Python", "FastAPI"]
    })

    print(f"状态: {result.status}")
    print(f"成功: {result.success}")


if __name__ == "__main__":
    asyncio.run(main())
```

### 示例 3: 使用 Dispatcher

```python
import asyncio
from orchestration.agent_dispatcher import AgentDispatcher
from orchestration.models import TaskExecution


async def main():
    # 创建 Dispatcher
    dispatcher = AgentDispatcher()

    # 创建任务
    task = TaskExecution(
        task_id="task-3",
        agent_type="backend_dev",
        inputs={
            "description": "开发用户管理API",
            "tech_stack": ["Python", "FastAPI"]
        }
    )

    # 执行任务
    result = await dispatcher.execute_with_agent(task)

    print(f"状态: {result.status}")
    print(f"分配的 Agent: {result.assignment.agent_id}")


if __name__ == "__main__":
    asyncio.run(main())
```

---

**文档版本**: v1.0
**最后更新**: 2026-01-14
**维护者**: SuperAgent v3.2+ 开发团队

---

**祝开发愉快!** 🎉
