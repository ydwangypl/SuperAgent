# SuperAgent v3.2 重构后使用指南

**版本**: 3.2
**更新日期**: 2026-01-14

---

## 📚 快速开始

### 方式1: 使用统一适配器 (推荐)

最简单的方式 - 一行代码完成执行和审查:

```python
from pathlib import Path
from adapters import UnifiedAdapter

# 初始化
adapter = UnifiedAdapter(Path("/path/to/project"))

# 执行任务并自动审查
result = await adapter.execute_and_review(
    task_type="code",
    task_data={
        "description": "创建用户管理API",
        "requirements": ["RESTful", "JWT认证"]
    },
    review_config={
        "enable_iterative": True  # 启用Ralph Wiggum循环改进
    }
)

# 查看结果
print(result['summary'])
# 输出:
# ✅ 任务执行成功
#    执行时间: 2.50秒
#    生成产物: 3个
#
# ✅ 代码审查通过 (评分: 85.0)
#    发现问题: 2个
#    - 重要: 1个
```

---

### 方式2: 分别使用执行器和审查器

更灵活的方式 - 单独控制执行和审查:

```python
from adapters import ExecutorAdapter, ReviewerAdapter
from pathlib import Path

# 初始化
executor_adapter = ExecutorAdapter(Path("/path/to/project"))
reviewer_adapter = ReviewerAdapter(Path("/path/to/project"))

# 1. 执行任务
exec_result = await executor_adapter.execute(
    task_type="code",
    task_data={"description": "创建订单处理系统"}
)

# 2. 审查结果
if exec_result['success']:
    review_result = await reviewer_adapter.review(
        artifact_type="code",
        artifact_data={"content": exec_result['content']}
    )

    print(f"评分: {review_result['overall_score']}")
```

---

### 方式3: 直接使用底层实现

最灵活的方式 - 直接使用执行器和审查器:

```python
from adapters.executor_adapter import AgentExecutor
from common.models import AgentType
from core.executor import Task
from pathlib import Path

# 创建执行器
executor = AgentExecutor(
    project_root=Path("/path/to/project"),
    agent_type=AgentType.BACKEND_DEV
)

# 创建任务
task = Task(
    task_type="code",
    description="创建用户认证系统",
    requirements=["JWT", "密码加密"],
    context={"language": "python"}
)

# 执行任务
result = executor.execute(task)

print(f"成功: {result.success}")
print(f"状态: {result.status}")
print(f"内容: {result.content}")
```

---

## 🎯 支持的任务类型

### 代码生成任务

| 任务类型 | Agent类型 | 说明 |
|---------|----------|------|
| `code` | BACKEND_DEV | 通用代码生成 |
| `backend` | BACKEND_DEV | 后端代码 |
| `api` | API_DESIGN | API设计 |
| `frontend` | FRONTEND_DEV | 前端代码 |
| `fullstack` | FULL_STACK_DEV | 全栈代码 |
| `test` | QA_ENGINEERING | 测试代码 |
| `testing` | QA_ENGINEERING | 测试代码 |
| `refactor` | CODE_REFACTORING | 代码重构 |
| `database` | DATABASE_DESIGN | 数据库设计 |
| `documentation` | TECHNICAL_WRITING | 技术文档 |

### 内容生成任务 (✨ 新功能)

| 任务类型 | 执行器 | 说明 |
|---------|--------|------|
| `article` | WritingExecutor | 文章生成 |
| `blog` | WritingExecutor | 博客生成 |
| `documentation` | WritingExecutor | 文档生成 |

---

## 🔧 高级用法

### 1. 自定义上下文参数

```python
result = await adapter.execute_and_review(
    task_type="code",
    task_data={
        "description": "创建微服务API",
        "context": {
            "language": "python",
            "framework": "FastAPI",
            "database": "PostgreSQL",
            "authentication": "OAuth2"
        }
    }
)
```

### 2. 批量处理任务

```python
tasks = [
    ("code", "创建用户模型", {"language": "python"}),
    ("code", "创建订单模型", {"language": "python"}),
    ("test", "创建用户测试", {"framework": "pytest"}),
]

results = []
for task_type, description, context in tasks:
    result = await adapter.execute_task(
        task_type=task_type,
        task_data={"description": description, "context": context}
    )
    results.append(result)

print(f"完成 {len(results)} 个任务")
```

### 3. 同步模式 (在非异步环境中)

```python
# 使用同步接口
result = adapter.execute_and_review_sync(
    task_type="code",
    task_data={"description": "创建配置管理"}
)
```

### 4. 仅执行,不审查

```python
result = await adapter.execute_task(
    task_type="code",
    task_data={"description": "快速原型"}
)
```

### 5. 仅审查现有代码

```python
result = await adapter.review_code(
    artifact_data={
        "content": {
            "user.py": "...",
            "order.py": "..."
        }
    },
    config={
        "enable_iterative": False  # 单次审查
    }
)
```

---

## 📝 内容生成示例

### 文章生成

```python
from extensions.writing_executor import WritingExecutor
from core.executor import Task

executor = WritingExecutor()

task = Task(
    task_type="article",
    description="区块链技术在供应链管理中的应用",
    context={
        "tone": "professional",      # 语调
        "length": 1000,              # 目标字数
        "audience": "企业管理者",    # 目标受众
        "keywords": [                # 关键词
            "区块链",
            "供应链",
            "透明度",
            "可追溯性"
        ]
    }
)

result = executor.execute(task)

print(f"生成了 {result.metadata['word_count']} 字")
print(f"语调: {result.metadata['tone']}")
print("\n内容预览:")
print(result.content[:200] + "...")
```

**输出示例**:
```
生成了 1023 字
语调: professional

内容预览:
# 区块链技术在供应链管理中的应用

随着全球化贸易的不断发展,供应链管理面临着日益复杂的挑战。区块链技术作为一种分布式账本技术,为供应链管理带来了革命性的变革...

## 1. 提高透明度

区块链技术的核心优势在于其不可篡改的特性...
```

---

### 内容审查

```python
from extensions.content_reviewer import ContentReviewer
from core.reviewer import Artifact

reviewer = ContentReviewer()

artifact = Artifact(
    artifact_type="article",
    content=article_content  # 上面生成的文章
)

review = reviewer.review(artifact)

print(f"总体评分: {review.overall_score:.1f}")
print(f"是否通过: {review.approved}")
print("\n详细指标:")
for metric in review.metrics:
    print(f"\n{metric.name.upper()}:")
    print(f"  评分: {metric.score:.1f}")
    print(f"  说明: {metric.description}")
    if metric.issues:
        print(f"  问题: {', '.join(metric.issues)}")
    if metric.suggestions:
        print(f"  建议: {', '.join(metric.suggestions)}")
```

**输出示例**:
```
总体评分: 78.5
是否通过: True

详细指标:

LENGTH:
  评分: 85.0
  说明: 长度适中,符合要求

READABILITY:
  评分: 72.0
  说明: 可读性良好
  问题: 发现2个超长句子

STRUCTURE:
  评分: 80.0
  说明: 结构清晰,有标题和段落

GRAMMAR:
  评分: 70.0
  说明: 少量语法问题

SEO:
  评分: 82.0
  说明: SEO友好,包含关键词
  建议: 可以添加更多关键词变体
```

---

## 🔍 结果对象说明

### ExecutionResult (执行结果)

```python
@dataclass
class ExecutionResult:
    success: bool              # 是否成功
    content: Any              # 生成的内容
    status: TaskStatus        # 任务状态
    error: Optional[str]      # 错误信息 (如果失败)
    metadata: Dict            # 元数据
    execution_time: float     # 执行时间 (秒)
    timestamp: datetime       # 时间戳
```

**使用示例**:
```python
result = executor.execute(task)

if result.success:
    print(f"✅ 执行成功")
    print(f"状态: {result.status.value}")
    print(f"内容: {result.content}")
    print(f"元数据: {result.metadata}")
    print(f"耗时: {result.execution_time:.2f}秒")
else:
    print(f"❌ 执行失败: {result.error}")
```

---

### ReviewResult (审查结果)

```python
@dataclass
class ReviewResult:
    status: ReviewStatus         # 审查状态
    overall_score: float         # 总体评分 (0-100)
    metrics: List[QualityMetric] # 质量指标列表
    feedback: str                # 反馈意见
    approved: bool              # 是否通过
    metadata: Dict              # 元数据
    review_time: float          # 审查时间 (秒)
    timestamp: datetime         # 时间戳
```

**使用示例**:
```python
review = reviewer.review(artifact)

print(f"审查状态: {review.status.value}")
print(f"总体评分: {review.overall_score:.1f}")
print(f"是否通过: {review.approved}")
print(f"反馈: {review.feedback}")
print(f"\n质量指标:")
for metric in review.metrics:
    print(f"  - {metric.name}: {metric.score:.1f}")
```

---

## 🎨 统一接口设计

### 多领域任务处理

```python
from typing import Union
from core.executor import Executor, Task
from adapters.executor_adapter import AgentExecutor
from extensions.writing_executor import WritingExecutor

def process_task(
    executor: Executor,
    task_type: str,
    description: str,
    **context
):
    """统一的任务处理函数 - 支持任何领域"""

    task = Task(
        task_type=task_type,
        description=description,
        context=context
    )

    result = executor.execute(task)

    return result

# ✅ 处理代码任务
code_executor = AgentExecutor(project_root, AgentType.BACKEND_DEV)
code_result = process_task(
    executor=code_executor,
    task_type="code",
    description="创建用户API",
    language="python"
)

# ✅ 处理写作任务
writing_executor = WritingExecutor()
writing_result = process_task(
    executor=writing_executor,
    task_type="article",
    description="AI技术发展",
    tone="professional",
    length=800
)

# 同一个函数,支持多领域!
```

---

## ⚙️ 配置选项

### Ralph Wiggum 循环改进配置

```python
review_config = {
    "enable_iterative": True,    # 启用循环改进
    "max_iterations": 3,         # 最大迭代次数
    "min_score": 70.0,          # 最低通过分数
    "target_score": 85.0        # 目标分数
}

result = await adapter.execute_and_review(
    task_type="code",
    task_data={"description": "..."},
    review_config=review_config
)
```

### Agent配置

```python
from execution.models import AgentConfig

config = AgentConfig(
    max_retries=3,
    timeout=300,
    enable_ralph_wiggum=True,
    ralph_config={
        "max_iterations": 3,
        "min_score": 70.0
    }
)

executor = AgentExecutor(
    project_root=Path("/project"),
    agent_type=AgentType.BACKEND_DEV,
    config=config
)
```

---

## 🧪 测试和调试

### 启用详细日志

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logging.getLogger("superagent").setLevel(logging.DEBUG)
```

### 性能监控

```python
import time

start = time.time()
result = await adapter.execute_and_review(...)
elapsed = time.time() - start

print(f"执行+审查总耗时: {elapsed:.2f}秒")
print(f"  - 执行: {result['execution']['execution_time']:.2f}秒")
print(f"  - 审查: {result['review']['review_time']:.2f}秒")
```

---

## 📚 最佳实践

### 1. 使用统一适配器

推荐使用 `UnifiedAdapter` 作为主要接口:
- ✅ 简单易用
- ✅ 自动集成执行和审查
- ✅ 生成综合总结

### 2. 合理设置上下文

提供详细的上下文可以提高生成质量:
```python
task_data = {
    "description": "创建用户认证API",
    "context": {
        "language": "python",
        "framework": "FastAPI",
        "database": "PostgreSQL",
        "security": ["JWT", "OAuth2"],
        "performance": ["缓存", "连接池"]
    }
}
```

### 3. 利用循环改进

对于重要任务,启用Ralph Wiggum循环改进:
```python
review_config = {
    "enable_iterative": True,
    "max_iterations": 3,
    "target_score": 85.0  # 设置较高目标
}
```

### 4. 处理错误

始终检查执行结果并处理错误:
```python
result = await adapter.execute_and_review(...)

if not result['execution']['success']:
    error = result['execution']['error']
    print(f"执行失败: {error}")
    # 重试或回退
elif not result['review']['approved']:
    score = result['review']['overall_score']
    print(f"审查未通过,评分: {score}")
    # 根据反馈调整
else:
    print("✅ 任务成功完成")
```

---

## 🚀 迁移指南

### 从旧代码迁移

**旧代码**:
```python
from orchestration.agent_factory import AgentFactory
from execution.models import AgentContext

agent = AgentFactory.create_agent(AgentType.BACKEND_DEV)
context = AgentContext(...)
result = await agent.run(context, input_data)
```

**新代码 (兼容)**:
```python
# 方式1: 继续使用旧代码 (完全兼容)
agent = AgentFactory.create_agent(AgentType.BACKEND_DEV)
context = AgentContext(...)
result = await agent.run(context, input_data)

# 方式2: 使用新抽象 (推荐)
from adapters import UnifiedAdapter
adapter = UnifiedAdapter(project_root)
result = await adapter.execute_and_review(
    task_type="code",
    task_data={"description": "..."}
)
```

**迁移优势**:
- ✅ 无需立即修改现有代码
- ✅ 可以渐进式迁移
- ✅ 新旧代码可以共存
- ✅ 保持100%兼容性

---

## 📖 相关文档

- [重构设计文档](REFACTOR_DESIGN.md)
- [架构对比](ARCHITECTURE_COMPARISON.md)
- [第1阶段完成报告](../STEP_1_COMPLETION_REPORT.md)
- [第2阶段完成报告](../STEP_2_COMPLETION_REPORT.md)
- [第3阶段完成报告](../STEP_3_COMPLETION_REPORT.md)
- [重构进度总结](../REFACTOR_PROGRESS_SUMMARY.md)

---

**文档版本**: 1.0
**最后更新**: 2026-01-10
**作者**: Claude Code Agent
