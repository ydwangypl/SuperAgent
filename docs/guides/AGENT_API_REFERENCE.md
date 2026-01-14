# SuperAgent Agent API 参考

> **版本**: v3.2+
> **更新日期**: 2026-01-14
> **目标读者**: 需要 Agent 详细 API 文档的开发者

---

## 📋 目录

1. [BaseAgent API](#baseagent-api)
2. [AgentFactory API](#agentfactory-api)
3. [AgentRegistry API](#agentregistry-api)
4. [AgentDispatcher API](#agentdispatcher-api)
5. [数据模型 API](#数据模型-api)
6. [枚举类型 API](#枚举类型-api)
7. [工具函数 API](#工具函数-api)

---

## 🎯 BaseAgent API

### 类定义

```python
class BaseAgent(ABC):
    """Agent 基类 - 所有 Agent 的抽象基类"""
```

### 构造函数

#### `__init__`

```python
def __init__(
    self,
    agent_id: str,
    config: Optional[AgentConfig] = None
) -> None
```

**描述**: 初始化 Agent 实例

**参数**:
- `agent_id` (str): Agent 唯一标识符
- `config` (Optional[AgentConfig]): Agent 配置对象,默认为 `None`

**异常**: 无

**示例**:
```python
agent = MyAgent(agent_id="my-agent-1")
agent = MyAgent(agent_id="my-agent-2", config=AgentConfig(max_retries=5))
```

### 抽象属性和方法

#### `name` (属性)

```python
@property
@abstractmethod
def name(self) -> str:
    """返回 Agent 名称

    Returns:
        str: Agent 名称
    """
    pass
```

**示例**:
```python
class MyAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "我的Agent"
```

#### `get_capabilities` (类方法)

```python
@classmethod
@abstractmethod
def get_capabilities(cls) -> Set[AgentCapability]:
    """获取 Agent 能力集合(无需实例化)

    Returns:
        Set[AgentCapability]: 能力集合
    """
    pass
```

**示例**:
```python
class MyAgent(BaseAgent):
    @classmethod
    def get_capabilities(cls) -> Set[AgentCapability]:
        return {
            AgentCapability.CODE_GENERATION,
            AgentCapability.DOCUMENTATION
        }
```

#### `execute_impl` (异步方法)

```python
@abstractmethod
async def execute_impl(
    self,
    context: AgentContext,
    task_input: Dict[str, Any]
) -> List[Artifact]:
    """子类实现的具体执行逻辑

    Args:
        context: 执行上下文
        task_input: 任务输入

    Returns:
        List[Artifact]: 生成的产出物列表

    Raises:
        ValueError: 如果输入验证失败
        FileNotFoundError: 如果依赖文件不存在
        Exception: 其他未预期错误
    """
    pass
```

**示例**:
```python
async def execute_impl(
    self,
    context: AgentContext,
    task_input: Dict[str, Any]
) -> List[Artifact]:
    # 业务逻辑
    artifacts = []
    artifact = Artifact(
        type="code",
        path="output.py",
        content="print('Hello')",
        metadata={}
    )
    artifacts.append(artifact)
    return artifacts
```

### 核心方法

#### `execute` (异步方法)

```python
async def execute(
    self,
    context: AgentContext,
    task_input: Dict[str, Any]
) -> AgentResult:
    """执行任务 (模板方法)

    自动处理:
    - 状态管理
    - 日志记录
    - 错误处理
    - 结果构建

    Args:
        context: 执行上下文
        task_input: 任务输入

    Returns:
        AgentResult: 执行结果
    """
```

**执行流程**:
1. 设置状态为 `WORKING`
2. 重置日志、指标、思考过程
3. 调用 `plan()` 进行规划(如果实现了)
4. 调用 `execute_impl()` 执行业务逻辑
5. 构建结果对象
6. 处理异常并返回结果

**示例**:
```python
result = await agent.execute(context, task_input)
if result.success:
    print(f"成功生成 {len(result.artifacts)} 个工件")
else:
    print(f"执行失败: {result.error}")
```

#### `run` (异步方法)

```python
async def run(
    self,
    context: AgentContext,
    task_input: Dict[str, Any]
) -> AgentResult:
    """运行 Agent (带重试机制)

    自动处理:
    - 输入验证
    - 重试逻辑
    - 超时控制
    - 中间结果保存

    Args:
        context: 执行上下文
        task_input: 任务输入

    Returns:
        AgentResult: 执行结果
    """
```

**重试逻辑**:
- 最多重试 `config.max_retries` 次
- 每次重试间隔 `config.retry_delay` 秒
- 重试前会记录日志

**示例**:
```python
config = AgentConfig(max_retries=3, retry_delay=2.0)
agent = MyAgent(agent_id="my-agent", config=config)

result = await agent.run(context, task_input)
```

### 可选方法

#### `plan` (异步方法)

```python
async def plan(
    self,
    context: AgentContext,
    task_input: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """规划执行步骤 (可选重写)

    Args:
        context: 执行上下文
        task_input: 任务输入

    Returns:
        List[Dict[str, Any]]: 执行步骤列表
    """
    return []
```

**示例**:
```python
async def plan(
    self,
    context: AgentContext,
    task_input: Dict[str, Any]
) -> List[Dict[str, Any]]:
    steps = []

    self.add_step(
        step_id="analyze",
        description="分析需求",
        expected_output="需求列表"
    )

    self.add_step(
        step_id="design",
        description="设计架构",
        expected_output="架构文档"
    )

    return self.steps
```

#### `validate_input`

```python
def validate_input(self, task_input: Dict[str, Any]) -> bool:
    """验证输入数据 (可选重写)

    Args:
        task_input: 任务输入

    Returns:
        bool: 验证是否通过
    """
    return True
```

**示例**:
```python
def validate_input(self, task_input: Dict[str, Any]) -> bool:
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
```

### 辅助方法

#### `add_thought`

```python
def add_thought(
    self,
    step: int,
    thought: str,
    action: Optional[str] = None,
    result: Optional[str] = None
) -> None:
    """添加思考过程记录

    Args:
        step (int): 步骤编号
        thought (str): 思考内容
        action (Optional[str]): 采取的行动
        result (Optional[str]): 行动结果
    """
```

**示例**:
```python
self.add_thought(
    step=1,
    thought="分析用户需求",
    action="提取功能点和技术栈",
    result="发现 3 个核心功能"
)
```

#### `add_step`

```python
def add_step(
    self,
    step_id: str,
    description: str,
    expected_output: str
) -> None:
    """添加执行步骤

    Args:
        step_id (str): 步骤 ID
        description (str): 步骤描述
        expected_output (str): 预期输出
    """
```

**示例**:
```python
self.add_step(
    step_id="generate_code",
    description="生成代码框架",
    expected_output="Python 代码文件"
)
```

#### `add_log`

```python
def add_log(
    self,
    message: str,
    level: str = "info"
) -> None:
    """添加日志记录

    Args:
        message (str): 日志消息
        level (str): 日志级别 (info/warning/error)
    """
```

**示例**:
```python
self.add_log("开始执行任务")
self.add_log("发现潜在问题", level="warning")
self.add_log("执行失败", level="error")
```

#### `set_metric`

```python
def set_metric(
    self,
    key: str,
    value: Any
) -> None:
    """设置指标数据

    Args:
        key (str): 指标键
        value (Any): 指标值
    """
```

**示例**:
```python
self.set_metric("artifacts_count", 5)
self.set_metric("execution_time", 3.5)
self.set_metric("success_rate", 0.95)
```

### 属性

#### `capabilities` (属性)

```python
@property
def capabilities(self) -> Set[AgentCapability]:
    """实例化的能力访问

    Returns:
        Set[AgentCapability]: 能力集合
    """
    return self.get_capabilities()
```

**示例**:
```python
agent = MyAgent()
print(agent.capabilities)
# Output: {<AgentCapability.CODE_GENERATION: 'code_generation'>}
```

#### `status` (属性)

```python
self.status: AgentStatus
```

**可能的值**:
- `AgentStatus.IDLE`: 空闲
- `AgentStatus.WORKING`: 工作中
- `AgentStatus.COMPLETED`: 已完成
- `AgentStatus.FAILED`: 失败
- `AgentStatus.CANCELLED`: 已取消

---

## 🏭 AgentFactory API

### 类定义

```python
class AgentFactory:
    """Agent 工厂类 - 负责创建和管理 Agent 实例"""
```

### 类方法

#### `create_agent`

```python
@classmethod
def create_agent(
    cls,
    agent_type: AgentType,
    agent_id: Optional[str] = None,
    config: Optional[AgentConfig] = None
) -> BaseAgent:
    """创建 Agent 实例

    Args:
        agent_type (AgentType): Agent 类型
        agent_id (Optional[str]): Agent ID,如果不提供则自动生成
        config (Optional[AgentConfig]): Agent 配置

    Returns:
        BaseAgent: Agent 实例

    Raises:
        ValueError: 如果 Agent 类型不支持

    Example:
        >>> agent = AgentFactory.create_agent(
        ...     AgentType.BACKEND_DEV,
        ...     agent_id="my-backend-agent"
        ... )
        >>> assert isinstance(agent, BaseAgent)
    """
```

**示例**:
```python
# 使用默认 agent_id
agent1 = AgentFactory.create_agent(AgentType.BACKEND_DEV)

# 指定 agent_id
agent2 = AgentFactory.create_agent(
    AgentType.QA_ENGINEERING,
    agent_id="my-qa-agent"
)

# 带配置
config = AgentConfig(max_retries=5, timeout=600)
agent3 = AgentFactory.create_agent(
    AgentType.DOCUMENTATION,
    config=config
)
```

#### `get_agent_capabilities`

```python
@classmethod
def get_agent_capabilities(
    cls,
    agent_type: AgentType
) -> Set[AgentCapability]:
    """获取 Agent 能力

    Args:
        agent_type (AgentType): Agent 类型

    Returns:
        Set[AgentCapability]: 能力集合

    Example:
        >>> caps = AgentFactory.get_agent_capabilities(AgentType.BACKEND_DEV)
        >>> assert AgentCapability.CODE_GENERATION in caps
    """
```

**示例**:
```python
capabilities = AgentFactory.get_agent_capabilities(AgentType.BACKEND_DEV)
print(capabilities)
# Output: {<AgentCapability.CODE_GENERATION>, <AgentCapability.ARCHITECTURE>}
```

#### `get_supported_agent_types`

```python
@classmethod
def get_supported_agent_types(cls) -> List[AgentType]:
    """获取支持的 Agent 类型列表

    Returns:
        List[AgentType]: Agent 类型列表

    Example:
        >>> types = AgentFactory.get_supported_agent_types()
        >>> assert AgentType.BACKEND_DEV in types
    """
```

**示例**:
```python
types = AgentFactory.get_supported_agent_types()
for agent_type in types:
    print(f"- {agent_type.value}")
```

#### `is_agent_type_supported`

```python
@classmethod
def is_agent_type_supported(cls, agent_type: AgentType) -> bool:
    """检查 Agent 类型是否支持

    Args:
        agent_type (AgentType): Agent 类型

    Returns:
        bool: 是否支持

    Example:
        >>> assert AgentFactory.is_agent_type_supported(AgentType.BACKEND_DEV)
    """
```

**示例**:
```python
if AgentFactory.is_agent_type_supported(AgentType.BACKEND_DEV):
    agent = AgentFactory.create_agent(AgentType.BACKEND_DEV)
else:
    print("Agent type not supported")
```

#### `create_agent_pool` (异步方法)

```python
@classmethod
async def create_agent_pool(
    cls,
    agent_types: Dict[AgentType, int],
    config: Optional[AgentConfig] = None
) -> Dict[str, BaseAgent]:
    """异步并发创建 Agent 池

    Args:
        agent_types (Dict[AgentType, int]): Agent 类型和数量的映射
        config (Optional[AgentConfig]): Agent 配置

    Returns:
        Dict[str, BaseAgent]: Agent 实例映射

    Example:
        >>> pool = await AgentFactory.create_agent_pool(
        ...     {AgentType.BACKEND_DEV: 3, AgentType.QA_ENGINEERING: 2}
        ... )
        >>> assert len(pool) == 5
    """
```

**示例**:
```python
import asyncio

async def main():
    pool = await AgentFactory.create_agent_pool({
        AgentType.BACKEND_DEV: 3,
        AgentType.QA_ENGINEERING: 2,
        AgentType.DOCUMENTATION: 1
    })

    print(f"创建了 {len(pool)} 个 Agent")
    for agent_id, agent in pool.items():
        print(f"- {agent_id}: {agent.name}")

asyncio.run(main())
```

---

## 📋 AgentRegistry API

### 类定义

```python
class AgentRegistry:
    """Agent 注册中心 - 管理 Agent 元数据和映射"""
```

### 类方法

#### `initialize`

```python
@classmethod
def initialize(cls) -> None:
    """初始化注册表

    建立所有 Agent 的统一映射

    Note:
        此方法采用惰性初始化,会在第一次调用任何需要元数据的方法时自动调用
    """
```

**示例**:
```python
# 手动初始化(可选)
AgentRegistry.initialize()

# 或自动初始化(推荐)
types = AgentRegistry.get_all_types()  # 自动调用 initialize()
```

#### `get_metadata`

```python
@classmethod
def get_metadata(cls, agent_type: AgentType) -> Optional[AgentMetadata]:
    """获取 Agent 元数据

    Args:
        agent_type (AgentType): Agent 类型

    Returns:
        Optional[AgentMetadata]: Agent 元数据,如果不存在返回 None

    Example:
        >>> meta = AgentRegistry.get_metadata(AgentType.BACKEND_DEV)
        >>> assert meta.description == "负责服务端业务逻辑、数据处理和系统集成"
    """
```

**示例**:
```python
meta = AgentRegistry.get_metadata(AgentType.BACKEND_DEV)
if meta:
    print(f"描述: {meta.description}")
    print(f"优先级: {meta.priority}")
    print(f"最大并发: {meta.max_concurrent}")
```

#### `get_impl_class`

```python
@classmethod
def get_impl_class(cls, agent_type: AgentType) -> Optional[Type[BaseAgent]]:
    """获取 Agent 实现类

    Args:
        agent_type (AgentType): Agent 类型

    Returns:
        Optional[Type[BaseAgent]]: Agent 实现类,如果不存在返回 None

    Example:
        >>> cls = AgentRegistry.get_impl_class(AgentType.BACKEND_DEV)
        >>> assert cls == CodingAgent
    """
```

**示例**:
```python
impl_class = AgentRegistry.get_impl_class(AgentType.BACKEND_DEV)
if impl_class:
    print(f"实现类: {impl_class.__name__}")
    # 创建实例
    agent = impl_class(agent_id="test-agent")
```

#### `get_description`

```python
@classmethod
def get_description(cls, agent_type: AgentType) -> str:
    """获取 Agent 描述

    Args:
        agent_type (AgentType): Agent 类型

    Returns:
        str: Agent 描述

    Example:
        >>> desc = AgentRegistry.get_description(AgentType.BACKEND_DEV)
        >>> assert "服务端业务逻辑" in desc
    """
```

**示例**:
```python
desc = AgentRegistry.get_description(AgentType.BACKEND_DEV)
print(desc)
# Output: 负责服务端业务逻辑、数据处理和系统集成
```

#### `get_priority`

```python
@classmethod
def get_priority(cls, agent_type: AgentType) -> int:
    """获取 Agent 优先级

    Args:
        agent_type (AgentType): Agent 类型

    Returns:
        int: 优先级 (1-99, 数字越小优先级越高)

    Example:
        >>> priority = AgentRegistry.get_priority(AgentType.PRODUCT_MANAGEMENT)
        >>> assert priority == 1
    """
```

**示例**:
```python
priority = AgentRegistry.get_priority(AgentType.BACKEND_DEV)
print(f"优先级: {priority}")
# Output: 优先级: 3
```

#### `get_max_concurrent`

```python
@classmethod
def get_max_concurrent(cls, agent_type: AgentType) -> int:
    """获取 Agent 最大并发数

    Args:
        agent_type (AgentType): Agent 类型

    Returns:
        int: 最大并发数

    Example:
        >>> max_c = AgentRegistry.get_max_concurrent(AgentType.BACKEND_DEV)
        >>> assert max_c == 10
    """
```

**示例**:
```python
max_concurrent = AgentRegistry.get_max_concurrent(AgentType.BACKEND_DEV)
print(f"最大并发: {max_concurrent}")
# Output: 最大并发: 10
```

#### `get_all_types`

```python
@classmethod
def get_all_types(cls) -> List[AgentType]:
    """获取所有已注册的 Agent 类型

    Returns:
        List[AgentType]: Agent 类型列表

    Example:
        >>> types = AgentRegistry.get_all_types()
        >>> assert len(types) > 0
    """
```

**示例**:
```python
all_types = AgentRegistry.get_all_types()
print(f"已注册 {len(all_types)} 种 Agent 类型:")
for agent_type in all_types:
    print(f"  - {agent_type.value}")
```

#### `from_string`

```python
@classmethod
def from_string(cls, type_str: str) -> Optional[AgentType]:
    """从字符串转换到 AgentType

    Args:
        type_str (str): Agent 类型字符串

    Returns:
        Optional[AgentType]: AgentType 枚举,如果转换失败返回 None

    Example:
        >>> atype = AgentRegistry.from_string("backend_dev")
        >>> assert atype == AgentType.BACKEND_DEV
    """
```

**示例**:
```python
# 标准格式
atype1 = AgentRegistry.from_string("backend_dev")
print(atype1)  # AgentType.BACKEND_DEV

# 带下划线格式
atype2 = AgentRegistry.from_string("backend-dev")
print(atype2)  # AgentType.BACKEND_DEV

# 无效格式
atype3 = AgentRegistry.from_string("invalid_type")
print(atype3)  # None
```

#### `get_keywords`

```python
@classmethod
def get_keywords(cls, agent_type: AgentType) -> List[str]:
    """获取 Agent 识别关键词

    Args:
        agent_type (AgentType): Agent 类型

    Returns:
        List[str]: 关键词列表(正则表达式)

    Example:
        >>> keywords = AgentRegistry.get_keywords(AgentType.BACKEND_DEV)
        >>> assert r"后端|backend" in keywords
    """
```

**示例**:
```python
keywords = AgentRegistry.get_keywords(AgentType.BACKEND_DEV)
print("关键词:")
for keyword in keywords:
    print(f"  - {keyword}")
```

#### `get_all_keywords`

```python
@classmethod
def get_all_keywords(cls) -> Dict[AgentType, List[str]]:
    """获取所有 Agent 的关键词映射

    Returns:
        Dict[AgentType, List[str]]: Agent 类型到关键词的映射

    Example:
        >>> all_keywords = AgentRegistry.get_all_keywords()
        >>> assert AgentType.BACKEND_DEV in all_keywords
    """
```

**示例**:
```python
all_keywords = AgentRegistry.get_all_keywords()
for agent_type, keywords in all_keywords.items():
    print(f"{agent_type.value}:")
    for keyword in keywords:
        print(f"  - {keyword}")
```

---

## 🎯 AgentDispatcher API

### 类定义

```python
class AgentDispatcher:
    """Agent 调度器 - 负责任务到 Agent 的分配、负载均衡、资源管理"""
```

### 构造函数

#### `__init__`

```python
def __init__(
    self,
    agent_resources: Optional[Dict[str, AgentResource]] = None
) -> None:
    """初始化 Agent 调度器

    Args:
        agent_resources (Optional[Dict[str, AgentResource]]): Agent 资源配置
            如果不提供,则从 AgentRegistry 自动初始化
    """
```

**示例**:
```python
# 使用默认资源配置
dispatcher1 = AgentDispatcher()

# 使用自定义资源配置
custom_resources = {
    "backend_dev": AgentResource(
        agent_type="backend_dev",
        max_concurrent=20
    )
}
dispatcher2 = AgentDispatcher(agent_resources=custom_resources)
```

### 实例方法

#### `assign_agent` (异步方法)

```python
async def assign_agent(
    self,
    task: TaskExecution,
    preferred_agent: Optional[str] = None,
    timeout: Optional[int] = 300
) -> Optional[AgentAssignment]:
    """为任务分配 Agent

    Args:
        task (TaskExecution): 任务执行对象
        preferred_agent (Optional[str]): 优先使用的 Agent 类型
        timeout (Optional[int]): 等待超时时间(秒),默认 300 秒

    Returns:
        Optional[AgentAssignment]: Agent 分配结果,如果超时返回 None

    Example:
        >>> assignment = await dispatcher.assign_agent(task)
        >>> if assignment:
        ...     print(f"分配到: {assignment.agent_id}")
    """
```

**示例**:
```python
task = TaskExecution(
    task_id="task-123",
    agent_type="backend_dev",
    inputs={"description": "开发用户API"}
)

# 分配 Agent
assignment = await dispatcher.assign_agent(task)

if assignment:
    print(f"成功分配到: {assignment.agent_id}")
    print(f"Agent 类型: {assignment.agent_type}")
    print(f"分配时间: {assignment.assigned_at}")
else:
    print("分配失败或超时")
```

#### `release_agent` (异步方法)

```python
async def release_agent(
    self,
    task_id: str,
    success: bool = True,
    duration: float = 0.0
) -> None:
    """释放 Agent 资源并更新统计信息

    Args:
        task_id (str): 任务 ID
        success (bool): 任务是否执行成功
        duration (float): 任务执行时长(秒)

    Example:
        >>> await dispatcher.release_agent("task-123", success=True, duration=5.2)
    """
```

**示例**:
```python
# 任务完成后释放资源
await dispatcher.release_agent(
    task_id="task-123",
    success=True,
    duration=5.2
)
```

#### `execute_with_agent` (异步方法)

```python
async def execute_with_agent(
    self,
    task: TaskExecution,
    preferred_agent: Optional[str] = None
) -> TaskExecution:
    """使用分配的 Agent 执行任务 (带资源生命周期管理)

    自动处理:
    - 分配 Agent
    - 执行任务
    - 释放 Agent
    - 更新统计信息

    Args:
        task (TaskExecution): 任务执行对象
        preferred_agent (Optional[str]): 优先使用的 Agent 类型

    Returns:
        TaskExecution: 更新后的任务执行对象

    Example:
        >>> result = await dispatcher.execute_with_agent(task)
        >>> assert result.status == TaskStatus.COMPLETED
    """
```

**示例**:
```python
task = TaskExecution(
    task_id="task-123",
    agent_type="backend_dev",
    inputs={"description": "开发用户API"}
)

# 执行任务
result = await dispatcher.execute_with_agent(task)

print(f"状态: {result.status}")
print(f"成功: {result.status == TaskStatus.COMPLETED}")
```

#### `execute_batch` (异步方法)

```python
async def execute_batch(
    self,
    tasks: List[TaskExecution],
    max_concurrent: int = 3
) -> List[TaskExecution]:
    """批量执行任务 (尊重资源限制和优先级)

    Args:
        tasks (List[TaskExecution]): 任务列表
        max_concurrent (int): 总最大并行任务数,默认 3

    Returns:
        List[TaskExecution]: 更新后的任务列表

    Example:
        >>> results = await dispatcher.execute_batch([task1, task2, task3])
        >>> assert len(results) == 3
    """
```

**示例**:
```python
tasks = [
    TaskExecution(task_id="task-1", agent_type="backend_dev", inputs={...}),
    TaskExecution(task_id="task-2", agent_type="qa_engineering", inputs={...}),
    TaskExecution(task_id="task-3", agent_type="documentation", inputs={...})
]

# 批量执行
results = await dispatcher.execute_batch(tasks, max_concurrent=2)

for result in results:
    print(f"{result.task_id}: {result.status}")
```

#### `get_available_agents`

```python
def get_available_agents(self) -> List[str]:
    """获取可用的 Agent 类型列表

    Returns:
        List[str]: 可用的 Agent 类型

    Example:
        >>> available = dispatcher.get_available_agents()
        >>> assert "backend_dev" in available
    """
```

**示例**:
```python
available = dispatcher.get_available_agents()
print("可用的 Agent 类型:")
for agent_type in available:
    print(f"  - {agent_type}")
```

#### `get_agent_load`

```python
def get_agent_load(self, agent_type: str) -> tuple[int, int]:
    """获取 Agent 负载情况

    Args:
        agent_type (str): Agent 类型

    Returns:
        tuple[int, int]: (当前负载, 最大并发数)

    Example:
        >>> current, max_c = dispatcher.get_agent_load("backend_dev")
        >>> print(f"负载: {current}/{max_c}")
    """
```

**示例**:
```python
current, max_c = dispatcher.get_agent_load("backend_dev")
print(f"负载: {current}/{max_c}")
print(f"利用率: {current/max_c*100:.1f}%")
```

#### `get_statistics`

```python
def get_statistics(self) -> Dict[str, Dict[str, Any]]:
    """获取 Agent 统计信息

    Returns:
        Dict[str, Dict[str, Any]]: Agent 统计信息

    Example:
        >>> stats = dispatcher.get_statistics()
        >>> print(stats["backend_dev"]["total_executions"])
    """
```

**示例**:
```python
stats = dispatcher.get_statistics()
for agent_type, stat in stats.items():
    print(f"\n{agent_type}:")
    print(f"  当前负载: {stat['current_load']}/{stat['max_concurrent']}")
    print(f"  利用率: {stat['utilization']}")
    print(f"  总执行次数: {stat['total_executions']}")
    print(f"  成功次数: {stat['successful_executions']}")
    print(f"  失败次数: {stat['failed_executions']}")
    print(f"  平均时长: {stat['average_duration']}")
```

---

## 📦 数据模型 API

### AgentContext

```python
@dataclass
class AgentContext:
    """Agent 执行上下文"""

    task_id: str                    # 任务唯一标识
    step_id: str                    # 步骤标识
    project_root: str               # 项目根目录
    worktree_path: Optional[str]    # Git worktree 路径
    metadata: Dict[str, Any]        # 额外元数据
```

**示例**:
```python
context = AgentContext(
    task_id="task-123",
    step_id="step-1",
    project_root="/path/to/project",
    worktree_path="/path/to/worktree",
    metadata={"priority": "high", "deadline": "2026-01-15"}
)
```

### AgentConfig

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

**示例**:
```python
config = AgentConfig(
    max_retries=5,
    retry_delay=2.0,
    timeout=600,
    save_intermediate=True,
    enable_metrics=True
)
```

### AgentResult

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

**示例**:
```python
result = AgentResult(
    agent_id="coding-agent-1",
    task_id="task-123",
    step_id="step-1",
    status=AgentStatus.COMPLETED,
    success=True,
    artifacts=[artifact1, artifact2],
    logs=["开始执行", "生成代码", "任务完成"],
    steps=[step1, step2, step3],
    metrics={"code_lines": 1250, "files": 5},
    error=None,
    message="任务执行成功"
)
```

### Artifact

```python
@dataclass
class Artifact:
    """Agent 产出物"""

    type: str                       # 工件类型
    path: str                       # 文件路径
    content: str                    # 文件内容
    metadata: Dict[str, Any]        # 元数据
    created_at: datetime = field(default_factory=datetime.now)
```

**示例**:
```python
artifact = Artifact(
    type="code",
    path="src/api/users.py",
    content="def get_users():\n    return []",
    metadata={
        "language": "Python",
        "framework": "FastAPI",
        "lines": 10
    }
)
```

### AgentThought

```python
@dataclass
class AgentThought:
    """Agent 思考过程"""

    step: int                       # 步骤编号
    thought: str                    # 思考内容
    action: Optional[str] = None    # 采取的行动
    result: Optional[str] = None    # 行动结果
    timestamp: datetime = field(default_factory=datetime.now)
```

**示例**:
```python
thought = AgentThought(
    step=1,
    thought="分析用户需求",
    action="提取功能点和技术栈",
    result="发现 3 个核心功能"
)
```

### AgentMetadata

```python
@dataclass
class AgentMetadata:
    """Agent 元数据定义"""

    agent_type: AgentType           # Agent 类型
    impl_class: Type[BaseAgent]     # 实现类
    description: str                # 描述
    priority: int = 99              # 优先级 (1-99)
    max_concurrent: int = 5         # 最大并发数
    capabilities: List[str] = field(default_factory=list) # 能力列表
    keywords: List[str] = field(default_factory=list)     # 关键词
```

**示例**:
```python
metadata = AgentMetadata(
    agent_type=AgentType.BACKEND_DEV,
    impl_class=CodingAgent,
    description="负责服务端业务逻辑、数据处理和系统集成",
    priority=3,
    max_concurrent=10,
    capabilities=["code_generation", "architecture"],
    keywords=[r"后端|backend|服务端|server"]
)
```

---

## 🎨 枚举类型 API

### AgentType

```python
class AgentType(str, Enum):
    """Agent 类型枚举"""

    # 核心管理与设计
    PRODUCT_MANAGEMENT = "product_management"
    DATABASE_DESIGN = "database_design"
    API_DESIGN = "api_design"

    # 核心开发
    BACKEND_DEV = "backend_dev"
    FRONTEND_DEV = "frontend_dev"
    FULL_STACK_DEV = "full_stack_dev"
    MINI_PROGRAM_DEV = "mini_program_dev"

    # 质量与安全
    QA_ENGINEERING = "qa_engineering"
    SECURITY_AUDIT = "security_audit"
    CODE_REVIEW = "code_review"

    # 运维与优化
    DEVOPS_ENGINEERING = "devops_engineering"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    INFRA_SETUP = "infra_setup"

    # 专项处理
    TECHNICAL_WRITING = "technical_writing"
    CODE_REFACTORING = "code_refactoring"
    DATA_MIGRATION = "data_migration"
    UI_DESIGN = "ui_design"
```

### AgentCapability

```python
class AgentCapability(str, Enum):
    """Agent 能力枚举"""

    CODE_GENERATION = "code_generation"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    REFACTORING = "refactoring"
    ARCHITECTURE = "architecture"
    DEBUGGING = "debugging"
    OPTIMIZATION = "optimization"
```

### AgentStatus

```python
class AgentStatus(str, Enum):
    """Agent 状态枚举"""

    IDLE = "idle"
    WORKING = "working"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
```

---

## 🛠️ 工具函数 API

### sanitize_input

```python
def sanitize_input(input_data: Any) -> Any:
    """清理输入数据

    Args:
        input_data (Any): 输入数据

    Returns:
        Any: 清理后的数据
    """
```

### check_sensitive_data

```python
def check_sensitive_data(data: str) -> bool:
    """检查敏感数据

    Args:
        data (str): 待检查的数据

    Returns:
        bool: 是否包含敏感数据
    """
```

---

## 📚 相关资源

### 内部文档

- [Agent 开发指南](AGENT_DEVELOPMENT_GUIDE.md)
- [Agent 架构说明](AGENT_ARCHITECTURE.md)
- [Agent 模板](AGENT_TEMPLATES.md)

### 外部资源

- [Python 官方文档](https://docs.python.org/3/)
- [Python asyncio 文档](https://docs.python.org/3/library/asyncio.html)
- [Python dataclasses 文档](https://docs.python.org/3/library/dataclasses.html)

---

**文档版本**: v1.0
**最后更新**: 2026-01-14
**维护者**: SuperAgent v3.2+ 开发团队

---

**祝使用愉快!** 🎉
