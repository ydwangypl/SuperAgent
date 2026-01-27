# SuperAgent Agent 开发指南

> **版本**: v3.2+
> **更新日期**: 2026-01-14
> **目标读者**: 希望为 SuperAgent 创建自定义 Agent 的开发者

---

## 📋 目录

1. [简介](#简介)
2. [Agent 基础概念](#agent-基础概念)
3. [开发环境准备](#开发环境准备)
4. [创建你的第一个 Agent](#创建你的第一个-agent)
5. [Agent 架构详解](#agent-架构详解)
6. [高级特性](#高级特性)
7. [最佳实践](#最佳实践)
8. [测试指南](#测试指南)
9. [部署与注册](#部署与注册)
10. [常见问题](#常见问题)

---

## 📖 简介

### 什么是 SuperAgent Agent?

SuperAgent Agent 是一个负责执行特定类型任务的独立模块。每个 Agent 都继承自 `BaseAgent` 基类,实现特定的能力集合,并通过 `AgentRegistry` 注册到系统中。

### Agent 的核心价值

- **单一职责**: 每个 Agent 专注于特定领域的任务
- **可组合性**: 多个 Agent 可以协作完成复杂任务
- **可扩展性**: 轻松添加新的 Agent 类型
- **可测试性**: 统一的接口便于单元测试

### Agent 示例

SuperAgent 内置了多种 Agent 类型:

- **CodingAgent**: 代码生成和架构设计
- **TestingAgent**: 单元测试和集成测试生成
- **DocumentationAgent**: 技术文档编写
- **RefactoringAgent**: 代码重构和优化

---

## 🎯 Agent 基础概念

### Agent 核心组件

```python
from execution.base_agent import BaseAgent
from execution.models import AgentCapability, AgentContext, Artifact

class MyAgent(BaseAgent):
    """自定义 Agent 示例"""

    @property
    def name(self) -> str:
        """Agent 名称"""
        return "我的Agent"

    @classmethod
    def get_capabilities(cls) -> Set[AgentCapability]:
        """Agent 能力集合"""
        return {AgentCapability.CODE_GENERATION}

    async def execute_impl(
        self,
        context: AgentContext,
        task_input: Dict[str, Any]
    ) -> List[Artifact]:
        """核心执行逻辑"""
        # 你的实现代码
        pass
```

### Agent 能力 (Capabilities)

Agent 能力定义了 Agent 可以做什么:

```python
from execution.models import AgentCapability

class AgentCapability(Enum):
    """Agent 能力枚举"""
    CODE_GENERATION = "code_generation"      # 代码生成
    TESTING = "testing"                      # 测试生成
    DOCUMENTATION = "documentation"          # 文档编写
    REFACTORING = "refactoring"              # 代码重构
    ARCHITECTURE = "architecture"            # 架构设计
    DEBUGGING = "debugging"                  # 调试分析
    OPTIMIZATION = "optimization"            # 性能优化
```

### Agent 生命周期

```
初始化 → 规划 → 执行 → 生成工件 → 完成
  ↓        ↓       ↓         ↓         ↓
IDLE   PLANNING  WORKING  ARTIFACTS  COMPLETED
```

---

## 🛠️ 开发环境准备

### 1. 环境要求

```bash
# Python 版本
Python 3.11+

# 必需依赖
pip install -r requirements.txt

# 开发依赖
pip install -r requirements-dev.txt
```

### 2. 项目结构

```
SuperAgent/
├── execution/
│   ├── base_agent.py        # Agent 基类
│   ├── models.py            # 数据模型
│   ├── coding_agent.py      # 代码生成 Agent
│   ├── testing_agent.py     # 测试 Agent
│   └── your_agent.py        # 你的 Agent (新增)
├── orchestration/
│   └── registry.py          # Agent 注册中心
└── tests/
    ├── test_base_agent.py
    └── test_your_agent.py   # 你的测试 (新增)
```

### 3. 开发工具

推荐使用以下工具:

- **IDE**: VSCode / PyCharm
- **代码格式化**: Black
- **Import 排序**: isort
- **类型检查**: mypy
- **代码检查**: flake8
- **测试框架**: pytest

---

## 🚀 创建你的第一个 Agent

### 步骤 1: 定义 Agent 类

创建文件 `execution/my_custom_agent.py`:

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自定义 Agent 示例
"""

import logging
from typing import List, Dict, Any, Set
from execution.base_agent import BaseAgent
from execution.models import (
    AgentCapability,
    AgentContext,
    AgentResult,
    Artifact
)

logger = logging.getLogger(__name__)


class MyCustomAgent(BaseAgent):
    """自定义 Agent - 实现特定功能"""

    def __init__(
        self,
        agent_id: str = "my-custom-agent",
        config: Optional[AgentConfig] = None
    ):
        """初始化 Agent"""
        super().__init__(agent_id, config)
        # 添加自定义初始化逻辑
        self.custom_property = "default_value"

    @property
    def name(self) -> str:
        """返回 Agent 名称"""
        return "自定义Agent"

    @classmethod
    def get_capabilities(cls) -> Set[AgentCapability]:
        """定义 Agent 能力"""
        return {
            AgentCapability.CODE_GENERATION,
            AgentCapability.DOCUMENTATION
        }

    async def execute_impl(
        self,
        context: AgentContext,
        task_input: Dict[str, Any]
    ) -> List[Artifact]:
        """核心执行逻辑"""
        self.add_log("开始执行自定义任务")

        # 1. 解析输入
        description = task_input.get("description", "")
        tech_stack = task_input.get("tech_stack", ["Python"])

        # 2. 添加思考过程
        self.add_thought(
            step=1,
            thought=f"分析需求: {description}",
            action=f"使用技术栈: {', '.join(tech_stack)}"
        )

        # 3. 执行业务逻辑
        artifacts = []

        # 生成工件 (例如: 文档、代码、配置等)
        artifact = Artifact(
            type="documentation",
            path="docs/my_custom_document.md",
            content="# 自定义文档\n\n这是生成的文档内容。",
            metadata={"source": "MyCustomAgent"}
        )
        artifacts.append(artifact)

        # 4. 记录日志
        self.add_log(f"生成了 {len(artifacts)} 个工件")

        # 5. 设置指标
        self.set_metric("artifacts_count", len(artifacts))
        self.set_metric("tech_stack", tech_stack)

        return artifacts
```

### 步骤 2: 注册 Agent

在 `orchestration/registry.py` 中注册你的 Agent:

```python
from execution.my_custom_agent import MyCustomAgent

@dataclass
class AgentMetadata:
    """Agent 元数据"""
    # ... 现有字段 ...

class AgentRegistry:
    """Agent 注册中心"""

    @classmethod
    def initialize(cls):
        """初始化注册表"""
        # ... 现有注册代码 ...

        # 添加你的 Agent
        agents.append(
            AgentMetadata(
                AgentType.MY_CUSTOM_TYPE,  # 需要在 common/models.py 中定义
                MyCustomAgent,
                "我的自定义 Agent - 实现特定功能",
                priority=10,  # 优先级 (1-99, 数字越小优先级越高)
                max_concurrent=5,  # 最大并发数
                keywords=[r"自定义|custom|特定功能"]
            )
        )

        for meta in agents:
            cls._metadata[meta.agent_type] = meta
```

### 步骤 3: 定义 Agent 类型

在 `common/models.py` 中添加新的 Agent 类型:

```python
class AgentType(str, Enum):
    """Agent 类型枚举"""
    # ... 现有类型 ...

    MY_CUSTOM_TYPE = "my_custom_type"  # 新增类型
```

### 步骤 4: 测试 Agent

创建测试文件 `tests/test_my_custom_agent.py`:

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自定义 Agent 测试
"""

import pytest
import asyncio
from execution.my_custom_agent import MyCustomAgent
from execution.models import AgentContext, AgentConfig
from common.models import AgentType


@pytest.mark.asyncio
async def test_my_custom_agent_basic():
    """测试 Agent 基本功能"""
    # 创建 Agent
    agent = MyCustomAgent(
        agent_id="test-agent-1",
        config=AgentConfig()
    )

    # 验证基本属性
    assert agent.name == "自定义Agent"
    assert AgentCapability.CODE_GENERATION in agent.capabilities

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
    assert result.artifacts[0].type == "documentation"


@pytest.mark.asyncio
async def test_my_custom_agent_with_retry():
    """测试 Agent 重试机制"""
    agent = MyCustomAgent(
        agent_id="test-agent-2",
        config=AgentConfig(max_retries=2, retry_delay=0.1)
    )

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


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
```

### 步骤 5: 运行测试

```bash
# 运行你的测试
pytest tests/test_my_custom_agent.py -v

# 运行所有测试
pytest -v

# 查看测试覆盖率
pytest --cov=execution.my_custom_agent --cov-report=html
```

---

## 🏗️ Agent 架构详解

### BaseAgent 核心方法

#### 1. 必须实现的抽象方法

```python
from abc import abstractmethod

class BaseAgent(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Agent 名称 (必须实现)"""
        pass

    @classmethod
    @abstractmethod
    def get_capabilities(cls) -> Set[AgentCapability]:
        """能力集合 (必须实现)"""
        pass

    @abstractmethod
    async def execute_impl(
        self,
        context: AgentContext,
        task_input: Dict[str, Any]
    ) -> List[Artifact]:
        """核心执行逻辑 (必须实现)"""
        pass
```

#### 2. 可选的重写方法

```python
class BaseAgent(ABC):
    async def plan(
        self,
        context: AgentContext,
        task_input: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """规划执行步骤 (可选重写)"""
        # 默认返回空列表
        return []

    def validate_input(self, task_input: Dict[str, Any]) -> bool:
        """验证输入数据 (可选重写)"""
        # 默认返回 True
        return True
```

#### 3. 生命周期钩子方法

```python
class BaseAgent(ABC):
    def on_start(self):
        """任务开始前的钩子"""
        pass

    def on_complete(self):
        """任务完成后的钩子"""
        pass

    def on_error(self, error: Exception):
        """发生错误时的钩子"""
        pass
```

### AgentContext 上下文对象

```python
@dataclass
class AgentContext:
    """Agent 执行上下文"""
    task_id: str                    # 任务 ID
    step_id: str                    # 步骤 ID
    project_root: str               # 项目根目录
    worktree_path: Optional[str]    # Git worktree 路径
    metadata: Dict[str, Any]        # 额外元数据
```

### Artifact 工件对象

```python
@dataclass
class Artifact:
    """Agent 产出物"""
    type: str                       # 工件类型 (code, doc, config 等)
    path: str                       # 文件路径
    content: str                    # 文件内容
    metadata: Dict[str, Any]        # 元数据
    created_at: datetime = field(default_factory=datetime.now)
```

### AgentResult 结果对象

```python
@dataclass
class AgentResult:
    """Agent 执行结果"""
    agent_id: str                   # Agent ID
    task_id: str                    # 任务 ID
    step_id: str                    # 步骤 ID
    status: AgentStatus             # 执行状态
    success: bool                   # 是否成功
    artifacts: List[Artifact]       # 产出物列表
    logs: List[str]                 # 日志列表
    steps: List[Dict[str, Any]]     # 执行步骤
    metrics: Dict[str, Any]         # 指标数据
    error: Optional[str]            # 错误信息
    message: Optional[str]          # 结果消息
    started_at: Optional[datetime]  # 开始时间
    completed_at: Optional[datetime] # 完成时间
    duration_seconds: Optional[float] # 执行时长
```

### AgentConfig 配置对象

```python
@dataclass
class AgentConfig:
    """Agent 配置"""
    max_retries: int = 3            # 最大重试次数
    retry_delay: float = 1.0        # 重试延迟(秒)
    timeout: int = 300              # 超时时间(秒)
    save_intermediate: bool = True  # 是否保存中间结果
    enable_metrics: bool = True     # 是否启用指标收集
```

---

## 🎓 高级特性

### 1. 思考过程记录

```python
# 在 execute_impl 中记录思考过程
self.add_thought(
    step=1,
    thought="分析用户需求",
    action="提取功能点和技术栈",
    result="发现 3 个核心功能"
)

self.add_thought(
    step=2,
    thought="设计系统架构",
    action="选择分层架构模式",
    result="确定 3 层结构: 接口层、业务层、数据层"
)
```

### 2. 步骤规划

```python
async def plan(
    self,
    context: AgentContext,
    task_input: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """规划执行步骤"""
    steps = []

    # 添加步骤
    self.add_step(
        step_id="analyze_requirements",
        description="分析功能需求",
        expected_output="需求列表"
    )

    self.add_step(
        step_id="design_architecture",
        description="设计系统架构",
        expected_output="架构文档"
    )

    self.add_step(
        step_id="generate_code",
        description="生成代码框架",
        expected_output="代码文件"
    )

    return self.steps
```

### 3. 日志记录

```python
# 记录信息日志
self.add_log("开始处理任务")

# 记录警告日志
self.add_log("发现潜在的性能问题", level="warning")

# 记录错误日志
self.add_log("处理失败: 文件不存在", level="error")
```

### 4. 指标收集

```python
# 设置指标
self.set_metric("artifacts_count", 5)
self.set_metric("code_lines", 1250)
self.set_metric("test_coverage", 85.5)

# 设置复杂指标
self.set_metric("performance", {
    "cpu_usage": 45.2,
    "memory_usage": 256.8,
    "execution_time": 3.5
})
```

### 5. 错误处理

```python
async def execute_impl(
    self,
    context: AgentContext,
    task_input: Dict[str, Any]
) -> List[Artifact]:
    """带错误处理的执行"""
    try:
        # 尝试执行业务逻辑
        artifacts = await self._generate_artifacts(task_input)

    except ValueError as e:
        # 输入验证错误
        self.add_log(f"输入验证失败: {e}", level="error")
        raise  # 重新抛出,让 BaseAgent 处理

    except FileNotFoundError as e:
        # 文件不存在错误
        self.add_log(f"文件不存在: {e}", level="error")
        # 返回空列表而不是抛出异常
        return []

    except Exception as e:
        # 未预期的错误
        self.add_log(f"未预期的错误: {type(e).__name__}: {e}", level="error")
        raise
```

### 6. 输入验证

```python
def validate_input(self, task_input: Dict[str, Any]) -> bool:
    """验证输入数据"""
    # 检查必需字段
    required_fields = ["description", "tech_stack"]
    for field in required_fields:
        if field not in task_input:
            self.add_log(f"缺少必需字段: {field}", level="error")
            return False

    # 验证字段类型
    if not isinstance(task_input["description"], str):
        self.add_log("description 必须是字符串", level="error")
        return False

    if not isinstance(task_input["tech_stack"], list):
        self.add_log("tech_stack 必须是列表", level="error")
        return False

    # 验证字段值
    if len(task_input["description"]) == 0:
        self.add_log("description 不能为空", level="error")
        return False

    if len(task_input["tech_stack"]) == 0:
        self.add_log("tech_stack 不能为空", level="error")
        return False

    return True
```

### 7. 重试机制

```python
# 配置重试
config = AgentConfig(
    max_retries=3,          # 最多重试 3 次
    retry_delay=2.0         # 每次重试间隔 2 秒
)

agent = MyCustomAgent(
    agent_id="my-agent",
    config=config
)

# 使用 run() 方法自动重试
result = await agent.run(context, task_input)
```

### 8. 超时控制

```python
# 配置超时
config = AgentConfig(
    timeout=300  # 300 秒超时
)

agent = MyCustomAgent(
    agent_id="my-agent",
    config=config
)

# 使用 asyncio.wait_for 添加超时控制
try:
    result = await asyncio.wait_for(
        agent.run(context, task_input),
        timeout=300.0
    )
except asyncio.TimeoutError:
    self.add_log("执行超时", level="error")
```

### 9. 中间结果保存

```python
# 启用中间结果保存
config = AgentConfig(
    save_intermediate=True
)

# BaseAgent 会在每次重试后自动保存中间结果
# 保存位置: {project_root}/.superagent/intermediate/{task_id}.json
```

### 10. Agent 协作

```python
async def execute_impl(
    self,
    context: AgentContext,
    task_input: Dict[str, Any]
) -> List[Artifact]:
    """Agent 协作示例"""
    from orchestration.agent_factory import AgentFactory

    # 创建子 Agent
    coding_agent = AgentFactory.create_agent(AgentType.BACKEND_DEV)
    testing_agent = AgentFactory.create_agent(AgentType.QA_ENGINEERING)

    # 执行子 Agent 任务
    code_result = await coding_agent.run(context, {
        "description": "开发用户管理API",
        "tech_stack": ["Python", "FastAPI"]
    })

    if code_result.success:
        self.add_log("代码生成成功")

        # 使用代码生成结果创建测试
        test_result = await testing_agent.run(context, {
            "description": "为用户管理API生成测试",
            "tech_stack": ["Python", "pytest"]
        })

        # 合并工件
        artifacts = code_result.artifacts + test_result.artifacts
        return artifacts
    else:
        self.add_log(f"代码生成失败: {code_result.error}", level="error")
        return []
```

---

## ✨ 最佳实践

### 1. 单一职责原则

每个 Agent 应该只负责一个特定领域的任务:

```python
# ❌ 不好的做法 - 一个 Agent 做太多事情
class FullStackAgent(BaseAgent):
    async def execute_impl(self, context, task_input):
        # 生成需求
        # 设计数据库
        # 开发后端
        # 开发前端
        # 编写测试
        # 部署应用
        pass

# ✅ 好的做法 - 每个 Agent 专注一个领域
class RequirementsAgent(BaseAgent):
    async def execute_impl(self, context, task_input):
        # 只负责需求分析
        pass

class DatabaseAgent(BaseAgent):
    async def execute_impl(self, context, task_input):
        # 只负责数据库设计
        pass
```

### 2. 输入验证

始终验证输入数据:

```python
def validate_input(self, task_input: Dict[str, Any]) -> bool:
    """验证输入"""
    # 检查必需字段
    if "description" not in task_input:
        self.add_log("缺少 description 字段", level="error")
        return False

    # 验证字段类型
    if not isinstance(task_input["description"], str):
        self.add_log("description 必须是字符串", level="error")
        return False

    # 验证字段值
    if len(task_input["description"].strip()) == 0:
        self.add_log("description 不能为空", level="error")
        return False

    return True
```

### 3. 错误处理

优雅地处理错误:

```python
async def execute_impl(
    self,
    context: AgentContext,
    task_input: Dict[str, Any]
) -> List[Artifact]:
    """带错误处理的执行"""
    try:
        # 业务逻辑
        artifacts = await self._generate_artifacts(task_input)

    except ValueError as e:
        # 输入验证错误 - 重新抛出
        self.add_log(f"输入错误: {e}", level="error")
        raise

    except FileNotFoundError as e:
        # 文件不存在 - 返回空列表
        self.add_log(f"文件不存在: {e}", level="warning")
        return []

    except Exception as e:
        # 未预期错误 - 记录并重新抛出
        self.add_log(f"未预期错误: {type(e).__name__}: {e}", level="error")
        logger.exception("详细错误信息:")
        raise

    return artifacts
```

### 4. 日志记录

记录足够的日志用于调试:

```python
async def execute_impl(self, context, task_input):
    """详细的日志记录"""

    # 开始日志
    self.add_log(f"开始执行任务: {context.task_id}")

    # 进度日志
    self.add_log("步骤 1: 分析需求")
    requirements = self._analyze_requirements(task_input)
    self.add_log(f"提取了 {len(requirements)} 个需求")

    self.add_log("步骤 2: 设计架构")
    architecture = self._design_architecture(requirements)
    self.add_log(f"选择了 {architecture['pattern']} 架构模式")

    self.add_log("步骤 3: 生成工件")
    artifacts = self._generate_artifacts(architecture)
    self.add_log(f"生成了 {len(artifacts)} 个工件")

    # 完成日志
    self.add_log(f"任务完成: {context.task_id}")

    return artifacts
```

### 5. 指标收集

收集有意义的指标:

```python
async def execute_impl(self, context, task_input):
    """收集指标"""

    # 记录开始时间
    import time
    start_time = time.time()

    # 执行业务逻辑
    artifacts = await self._generate_artifacts(task_input)

    # 收集指标
    self.set_metric("artifacts_count", len(artifacts))
    self.set_metric("execution_time", time.time() - start_time)
    self.set_metric("success_rate", 1.0)

    # 收集详细指标
    code_artifacts = [a for a in artifacts if a.type == "code"]
    doc_artifacts = [a for a in artifacts if a.type == "documentation"]

    self.set_metric("code_artifacts", len(code_artifacts))
    self.set_metric("doc_artifacts", len(doc_artifacts))

    return artifacts
```

### 6. 文档字符串

为 Agent 编写完整的文档字符串:

```python
class MyCustomAgent(BaseAgent):
    """自定义 Agent - 实现特定功能

    这个 Agent 负责实现特定的功能,包括:
    - 功能 1: xxx
    - 功能 2: xxx
    - 功能 3: xxx

    使用示例:
        agent = MyCustomAgent(agent_id="my-agent")
        result = await agent.execute(context, {
            "description": "任务描述",
            "tech_stack": ["Python", "FastAPI"]
        })

    注意事项:
    - 注意 1
    - 注意 2

    性能:
    - 平均执行时间: 2-5 秒
    - 内存占用: ~50MB
    """

    async def execute_impl(
        self,
        context: AgentContext,
        task_input: Dict[str, Any]
    ) -> List[Artifact]:
        """执行自定义任务

        Args:
            context: 执行上下文
            task_input: 任务输入,包含:
                - description (str): 任务描述
                - tech_stack (List[str]): 技术栈

        Returns:
            List[Artifact]: 生成的工件列表

        Raises:
            ValueError: 如果输入验证失败
            FileNotFoundError: 如果依赖文件不存在

        Example:
            >>> result = await agent.execute(context, {
            ...     "description": "开发用户API",
            ...     "tech_stack": ["Python", "FastAPI"]
            ... })
            >>> assert len(result.artifacts) > 0
        """
        pass
```

### 7. 类型提示

使用类型提示提高代码可读性:

```python
from typing import List, Dict, Any, Set, Optional

class MyCustomAgent(BaseAgent):
    """使用类型提示的 Agent"""

    # 方法返回类型
    async def execute_impl(
        self,
        context: AgentContext,
        task_input: Dict[str, Any]
    ) -> List[Artifact]:
        """完整类型提示的执行方法"""

        # 变量类型提示
        description: str = task_input.get("description", "")
        tech_stack: List[str] = task_input.get("tech_stack", [])

        # 复杂类型提示
        artifacts: List[Artifact] = []

        # 可选类型提示
        metadata: Optional[Dict[str, Any]] = task_input.get("metadata")

        # 类型断言
        if isinstance(description, str):
            # 使用 description
            pass

        return artifacts
```

### 8. 配置管理

使用配置对象管理 Agent 参数:

```python
@dataclass
class MyCustomAgentConfig(AgentConfig):
    """自定义 Agent 配置"""
    max_artifacts: int = 10         # 最大工件数
    enable_validation: bool = True  # 启用验证
    output_format: str = "markdown" # 输出格式
    custom_timeout: int = 300       # 自定义超时

class MyCustomAgent(BaseAgent):
    """使用配置的 Agent"""

    def __init__(
        self,
        agent_id: str,
        config: Optional[MyCustomAgentConfig] = None
    ):
        super().__init__(agent_id, config)

        # 使用配置
        self.max_artifacts = self.config.max_artifacts if self.config else 10
        self.enable_validation = self.config.enable_validation if self.config else True
```

### 9. 异步操作

正确使用异步编程:

```python
import asyncio

class MyCustomAgent(BaseAgent):
    """异步操作示例"""

    async def execute_impl(
        self,
        context: AgentContext,
        task_input: Dict[str, Any]
    ) -> List[Artifact]:
        """异步执行"""

        # 并发执行多个异步操作
        artifacts = await asyncio.gather(
            self._generate_code(task_input),
            self._generate_tests(task_input),
            self._generate_docs(task_input)
        )

        # 展平结果
        all_artifacts = []
        for artifact_list in artifacts:
            all_artifacts.extend(artifact_list)

        return all_artifacts

    async def _generate_code(self, task_input: Dict[str, Any]) -> List[Artifact]:
        """生成代码"""
        await asyncio.sleep(0.1)  # 模拟异步操作
        return [Artifact(...)]

    async def _generate_tests(self, task_input: Dict[str, Any]) -> List[Artifact]:
        """生成测试"""
        await asyncio.sleep(0.1)
        return [Artifact(...)]

    async def _generate_docs(self, task_input: Dict[str, Any]) -> List[Artifact]:
        """生成文档"""
        await asyncio.sleep(0.1)
        return [Artifact(...)]
```

### 10. 测试覆盖

编写全面的测试:

```python
@pytest.mark.asyncio
async def test_agent_success():
    """测试成功场景"""
    agent = MyCustomAgent()
    result = await agent.execute(context, valid_input)
    assert result.success is True
    assert len(result.artifacts) > 0

@pytest.mark.asyncio
async def test_agent_invalid_input():
    """测试无效输入"""
    agent = MyCustomAgent()
    result = await agent.execute(context, invalid_input)
    assert result.success is False

@pytest.mark.asyncio
async def test_agent_retry():
    """测试重试机制"""
    config = AgentConfig(max_retries=3)
    agent = MyCustomAgent(config=config)
    # 模拟失败后重试的场景

@pytest.mark.asyncio
async def test_agent_timeout():
    """测试超时处理"""
    config = AgentConfig(timeout=1)
    agent = MyCustomAgent(config=config)
    # 模拟超时场景

@pytest.mark.asyncio
async def test_agent_metrics():
    """测试指标收集"""
    agent = MyCustomAgent()
    result = await agent.execute(context, valid_input)
    assert "artifacts_count" in result.metrics
```

---

## 🧪 测试指南

### 单元测试

```python
import pytest
from execution.my_custom_agent import MyCustomAgent

@pytest.mark.asyncio
async def test_my_custom_agent():
    """测试 Agent 基本功能"""
    agent = MyCustomAgent(agent_id="test-agent")

    # 测试属性
    assert agent.name == "自定义Agent"
    assert AgentCapability.CODE_GENERATION in agent.capabilities

    # 测试执行
    result = await agent.execute(context, task_input)

    # 验证结果
    assert result.success is True
    assert len(result.artifacts) > 0
```

### 集成测试

```python
@pytest.mark.asyncio
async def test_agent_integration():
    """测试 Agent 与其他组件的集成"""
    from orchestration.agent_factory import AgentFactory
    from orchestration.agent_dispatcher import AgentDispatcher

    # 创建 Agent
    agent = AgentFactory.create_agent(AgentType.MY_CUSTOM_TYPE)

    # 创建 Dispatcher
    dispatcher = AgentDispatcher()

    # 执行任务
    task = TaskExecution(
        task_id="integration-test-1",
        agent_type=AgentType.MY_CUSTOM_TYPE,
        inputs={"description": "测试任务"}
    )

    result = await dispatcher.execute_with_agent(task)
    assert result.status == TaskStatus.COMPLETED
```

### 测试覆盖率

```bash
# 运行测试并查看覆盖率
pytest --cov=execution.my_custom_agent --cov-report=html

# 查看覆盖率报告
open htmlcov/index.html
```

---

## 🚀 部署与注册

### 1. 提交代码

```bash
# 1. 创建分支
git checkout -b feature/my-custom-agent

# 2. 提交代码
git add execution/my_custom_agent.py
git add tests/test_my_custom_agent.py
git add orchestration/registry.py
git add common/models.py

git commit -m "feat: 添加自定义 Agent

- 实现 MyCustomAgent
- 添加单元测试
- 注册到 AgentRegistry"

# 3. 推送到远程
git push origin feature/my-custom-agent

# 4. 创建 Pull Request
# 在 GitHub 上创建 PR,填写模板
```

### 2. 代码审查

确保你的代码:
- ✅ 遵循代码风格规范 (Black, isort, flake8)
- ✅ 通过所有测试 (pytest)
- ✅ 测试覆盖率 > 80%
- ✅ 有完整的文档字符串
- ✅ 有详细的注释

### 3. 合并到主分支

```bash
# 等待代码审查通过后,合并到 main 分支
git checkout main
git merge feature/my-custom-agent
git push origin main
```

---

## ❓ 常见问题

### Q1: Agent 执行失败,如何调试?

**A**: 检查以下几点:

1. 查看日志: `result.logs`
2. 查看错误信息: `result.error`
3. 查看思考过程: `agent.thoughts`
4. 启用详细日志: `logging.basicConfig(level=logging.DEBUG)`

```python
# 调试示例
result = await agent.execute(context, task_input)

if not result.success:
    print(f"错误: {result.error}")
    print(f"日志: {result.logs}")
    print(f"思考: {agent.thoughts}")
```

### Q2: 如何让 Agent 支持新的技术栈?

**A**: 在 Agent 中添加技术栈识别和处理逻辑:

```python
def _detect_tech_stack(self, description: str) -> List[str]:
    """检测技术栈"""
    tech_keywords = {
        "Python": ["python", "django", "flask", "fastapi"],
        "JavaScript": ["javascript", "node", "react", "vue"],
        "Java": ["java", "spring", "maven"],
        "Go": ["go", "golang"]
    }

    detected = []
    for tech, keywords in tech_keywords.items():
        if any(keyword in description.lower() for keyword in keywords):
            detected.append(tech)

    return detected or ["Python"]  # 默认 Python
```

### Q3: Agent 如何与其他 Agent 协作?

**A**: 使用 AgentFactory 创建子 Agent:

```python
from orchestration.agent_factory import AgentFactory

# 创建子 Agent
coding_agent = AgentFactory.create_agent(AgentType.BACKEND_DEV)
testing_agent = AgentFactory.create_agent(AgentType.QA_ENGINEERING)

# 执行子 Agent 任务
code_result = await coding_agent.run(context, code_input)
test_result = await testing_agent.run(context, test_input)

# 合并结果
artifacts = code_result.artifacts + test_result.artifacts
```

### Q4: 如何优化 Agent 性能?

**A**: 几个优化方向:

1. **并发执行**: 使用 `asyncio.gather` 并发执行多个操作
2. **缓存结果**: 缓存重复计算的结果
3. **减少 I/O**: 批量读写文件
4. **异步 I/O**: 使用 `aiofiles` 异步读写文件

```python
# 性能优化示例
import asyncio
import aiofiles

async def execute_impl(self, context, task_input):
    """性能优化"""

    # 1. 并发执行
    artifacts = await asyncio.gather(
        self._task1(),
        self._task2(),
        self._task3()
    )

    # 2. 异步 I/O
    async with aiofiles.open("output.md", "w") as f:
        await f.write(content)

    return artifacts
```

### Q5: Agent 如何处理大型任务?

**A**: 将大型任务分解为多个小任务:

```python
async def execute_impl(self, context, task_input):
    """处理大型任务"""

    # 1. 分解任务
    subtasks = self._break_down_task(task_input)

    # 2. 逐个执行
    all_artifacts = []
    for i, subtask in enumerate(subtasks):
        self.add_log(f"执行子任务 {i+1}/{len(subtasks)}")
        artifacts = await self._execute_subtask(subtask)
        all_artifacts.extend(artifacts)

    return all_artifacts

def _break_down_task(self, task_input: Dict[str, Any]) -> List[Dict[str, Any]]:
    """将大任务分解为小任务"""
    # 实现任务分解逻辑
    pass
```

### Q6: 如何添加 Agent 配置选项?

**A**: 创建自定义配置类:

```python
@dataclass
class MyCustomAgentConfig(AgentConfig):
    """自定义配置"""
    max_artifacts: int = 10
    output_format: str = "markdown"
    enable_validation: bool = True

class MyCustomAgent(BaseAgent):
    """使用自定义配置"""

    def __init__(
        self,
        agent_id: str,
        config: Optional[MyCustomAgentConfig] = None
    ):
        super().__init__(agent_id, config)
        # 使用配置
        self.max_artifacts = config.max_artifacts if config else 10
```

### Q7: Agent 如何返回结构化数据?

**A**: 使用 Artifact 的 metadata 字段:

```python
artifact = Artifact(
    type="structured_data",
    path="output/data.json",
    content=json.dumps(structured_data),
    metadata={
        "schema": "v1.0",
        "format": "json",
        "fields": ["field1", "field2", "field3"]
    }
)
```

### Q8: 如何测试 Agent 的错误处理?

**A**: 使用 pytest 的异常处理:

```python
@pytest.mark.asyncio
async def test_agent_error_handling():
    """测试错误处理"""
    agent = MyCustomAgent()

    # 测试无效输入
    with pytest.raises(ValueError):
        await agent.execute(context, invalid_input)

    # 测试文件不存在
    result = await agent.execute(context, {"file": "nonexistent.txt"})
    assert result.success is False
    assert "文件不存在" in result.error
```

---

## 📚 相关资源

### 内部文档

- [Agent 架构说明](AGENT_ARCHITECTURE.md)
- [API 参考](AGENT_API_REFERENCE.md)
- [Agent 模板](AGENT_TEMPLATES.md)
- [交互式教程](INTERACTIVE_TUTORIAL.md)

### 外部资源

- [Python 异步编程指南](https://docs.python.org/3/library/asyncio.html)
- [pytest 文档](https://docs.pytest.org/)
- [Black 代码格式化](https://black.readthedocs.io/)
- [mypy 类型检查](https://mypy.readthedocs.io/)

---

## 🤝 贡献指南

欢迎为 SuperAgent 贡献新的 Agent!

1. Fork 项目
2. 创建特性分支: `git checkout -b feature/my-agent`
3. 提交更改: `git commit -m 'Add my agent'`
4. 推送到分支: `git push origin feature/my-agent`
5. 创建 Pull Request

详细贡献指南请参阅: [CONTRIBUTING.md](CONTRIBUTING.md)

---

**文档版本**: v1.0
**最后更新**: 2026-01-14
**维护者**: SuperAgent v3.2+ 开发团队

---

## 附录

### A. 完整 Agent 示例

参见: [Agent 模板](AGENT_TEMPLATES.md)

### B. API 快速参考

参见: [API 参考](AGENT_API_REFERENCE.md)

### C. 交互式教程

参见: [交互式教程](INTERACTIVE_TUTORIAL.md)

---

**祝开发愉快!** 🎉
