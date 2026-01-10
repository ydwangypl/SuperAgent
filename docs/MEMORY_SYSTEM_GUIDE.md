# SuperAgent v3.1 记忆系统使用指南

> **版本**: v1.0
> **更新日期**: 2026-01-08

---

## 📋 目录

1. [系统概述](#系统概述)
2. [3层记忆架构](#3层记忆架构)
3. [使用示例](#使用示例)
4. [最佳实践](#最佳实践)
5. [API参考](#api参考)
6. [故障排除](#故障排除)

---

## 🎯 系统概述

### 设计理念

SuperAgent v3.1的3层记忆系统基于认知科学原理,模拟人类记忆的三个层次:

- **情节记忆 (Episodic Memory)**: 记录"发生了什么" - 任务执行历史
- **语义记忆 (Semantic Memory)**: 存储"知道什么" - 项目知识和架构决策
- **程序记忆 (Procedural Memory)**: 保持"如何做" - 最佳实践和工作流程

### 核心价值

1. **防止重复错误**: 从历史错误中学习,避免重蹈覆辙
2. **加速开发**: 复用已有的架构决策和最佳实践
3. **知识积累**: 项目知识持续积累,形成组织记忆
4. **上下文连续**: 跨会话保持项目上下文

### 文件结构

```
.superagent/memory/
├── episodic/                    # 情节记忆目录
│   ├── episodic_20260108_120000.json
│   ├── episodic_20260108_120530.json
│   └── ...
├── semantic/                    # 语义记忆目录
│   ├── semantic_architecture_20260108_120000.json
│   ├── semantic_design_20260108_120500.json
│   └── ...
├── procedural/                  # 程序记忆目录
│   ├── procedural_coding_20260108_120000.json
│   ├── procedural_testing_20260108_120500.json
│   └── ...
├── CONTINUITY.md                # 人类可读的持续记忆
└── memory_index.json            # 记忆索引
```

---

## 🧠 3层记忆架构

### 第1层: 情节记忆 (Episodic Memory)

#### 用途

记录项目中的每一次任务执行,包括:
- 任务开始和结束时间
- 执行的Agent类型
- 任务状态(成功/失败)
- 错误信息(如果有)
- 任务执行时长

#### 数据结构

```python
@dataclass
class MemoryEntry:
    memory_id: str              # 记忆ID
    memory_type: str            # "episodic"
    timestamp: str              # 时间戳
    content: str                # 事件描述
    metadata: Dict[str, Any]    # 元数据
    tags: List[str]             # 标签
```

#### 何时使用

- ✅ 任务完成后自动记录
- ✅ 错误发生时记录上下文
- ✅ 项目里程碑事件

#### 使用示例

```python
from memory import MemoryManager
from pathlib import Path

# 初始化记忆管理器
memory_manager = MemoryManager(Path("."))

# 保存情节记忆
memory_id = await memory_manager.save_episodic_memory(
    event="任务执行: 开发用户管理API\n状态: completed\n描述: 实现了CRUD接口",
    task_id="task-1",
    agent_type="backend-dev",
    metadata={
        "status": "completed",
        "duration": 120.5,
        "files_created": 5
    }
)

print(f"已保存情节记忆: {memory_id}")
```

#### 查询示例

```python
# 获取最近的10条情节记忆
memories = await memory_manager.get_episodic_memories(limit=10)

for memory in memories:
    print(f"[{memory['timestamp']}] {memory['content']}")
```

---

### 第2层: 语义记忆 (Semantic Memory)

#### 用途

存储项目知识,包括:
- 架构决策
- 技术选型理由
- 设计模式选择
- 领域知识

#### 分类

| 分类 | 说明 | 示例 |
|------|------|------|
| `architecture` | 架构决策 | "采用微服务架构" |
| `design` | 设计模式 | "使用工厂模式创建Agent" |
| `tech_stack` | 技术栈 | "选择FastAPI作为Web框架" |
| `domain` | 领域知识 | "用户权限模型基于RBAC" |

#### 何时使用

- ✅ 重要架构决策时
- ✅ 技术选型确定后
- ✅ 设计模式应用时
- ✅ 领域知识梳理后

#### 使用示例

```python
# 保存架构决策
memory_id = await memory_manager.save_semantic_memory(
    knowledge="""项目架构决策

采用微服务架构,理由:
1. 模块独立性: 每个服务独立开发和部署
2. 可扩展性: 可根据需求单独扩展服务
3. 技术异构: 不同服务可使用不同技术栈

服务划分:
- 用户服务 (User Service)
- 认证服务 (Auth Service)
- 业务服务 (Business Service)
""",
    category="architecture",
    tags=["microservices", "scalability", "service-mesh"]
)

print(f"已保存架构决策: {memory_id}")
```

#### 查询示例

```python
# 查询所有架构相关的记忆
memories = await memory_manager.query_semantic_memory(
    category="architecture"
)

# 按关键词查询
memories = await memory_manager.query_semantic_memory(
    keywords=["微服务", "API", "REST"]
)

# 组合查询
memories = await memory_manager.query_semantic_memory(
    category="design",
    keywords=["工厂", "单例"]
)
```

---

### 第3层: 程序记忆 (Procedural Memory)

#### 用途

存储最佳实践和工作流程,包括:
- 编码规范
- 测试流程
- 部署步骤
- 调试技巧

#### 分类

| 分类 | 说明 | 示例 |
|------|------|------|
| `coding` | 编码规范 | "PEP 8规范检查清单" |
| `testing` | 测试流程 | "单元测试三步法" |
| `deployment` | 部署流程 | "蓝绿部署步骤" |
| `debugging` | 调试技巧 | "常见错误排查方法" |

#### 何时使用

- ✅ 发现好的实践时
- ✅ 优化工作流程后
- ✅ 总结调试经验时
- ✅ 团队规范制定时

#### 使用示例

```python
# 保存编码最佳实践
memory_id = await memory_manager.save_procedural_memory(
    practice="""Python编码最佳实践

1. 遵循PEP 8规范
   - 使用4空格缩进
   - 每行不超过79字符
   - 使用空行分隔函数和类

2. 使用类型注解
   def calculate_price(quantity: int, unit_price: float) -> float:
       return quantity * unit_price

3. 编写文档字符串
   def process_user(user_id: str) -> User:
       \"\"\"处理用户信息

       Args:
           user_id: 用户ID

       Returns:
           处理后的用户对象
       \"\"\"
       ...

4. 错误处理
   try:
       result = risky_operation()
   except SpecificError as e:
       logger.error(f"操作失败: {e}")
       raise
""",
    category="coding",
    agent_type="coding-agent"
)

print(f"已保存最佳实践: {memory_id}")
```

#### 查询示例

```python
# 查询编码相关的最佳实践
memories = await memory_manager.get_procedural_memories(
    category="coding"
)

for memory in memories:
    print(f"[{memory['timestamp']}] {memory['content'][:100]}...")
```

---

### CONTINUITY.md

#### 用途

人类可读的持续记忆文件,集中展示:
- 📝 错误与教训
- 🎯 最佳实践
- 🏗️ 架构决策
- 📊 项目统计

#### 格式

```markdown
# SuperAgent v3.1 - 持续记忆 (CONTINUITY)

> 此文件由SuperAgent自动维护

---

## 📝 错误与教训 (Mistakes & Learnings)

### 2026-01-08 12:00:00

**错误类型**: ValueError

**上下文**: 任务 task-1 (后端API开发) 执行失败

**修复方案**: 添加输入验证,检查数据类型

**经验教训**:
- 外部输入必须验证
- 使用类型注解可以预防此类错误
- 添加单元测试覆盖边界情况

---

## 🎯 最佳实践 (Best Practices)

### coding - 2026-01-08 12:05:00

Python编码最佳实践:
1. 遵循PEP 8规范
2. 使用类型注解
3. 编写文档字符串
4. 添加单元测试

---

## 🏗️ 架构决策 (Architecture Decisions)

### architecture - 2026-01-08 12:10:00

项目采用微服务架构,理由:
1. 模块独立性
2. 可扩展性
3. 技术异构性

---

## 📊 项目统计 (Project Statistics)

- **总记忆条目**: 150
- **情节记忆**: 80
- **语义记忆**: 45
- **程序记忆**: 25
- **最后更新**: 2026-01-08 12:10:00
```

#### 自动更新

CONTINUITY.md会在以下情况自动更新:
1. 保存语义记忆时
2. 保存程序记忆时
3. 保存错误教训时
4. 统计信息实时更新

---

## 💡 使用示例

### 示例1: 完整的记忆管理流程

```python
import asyncio
from pathlib import Path
from memory import MemoryManager

async def memory_example():
    # 1. 初始化
    memory_manager = MemoryManager(Path("."))

    # 2. 执行任务前,查询相关记忆
    relevant = await memory_manager.query_relevant_memory(
        task="开发用户管理API",
        agent_type="backend-dev"
    )

    print(f"找到 {len(relevant['mistakes'])} 个相关错误教训")
    print(f"找到 {len(relevant['best_practices'])} 个相关最佳实践")

    # 3. 执行任务...

    # 4. 任务完成后,保存情节记忆
    await memory_manager.save_episodic_memory(
        event="任务执行: 开发用户管理API\n状态: completed",
        task_id="task-1",
        agent_type="backend-dev"
    )

    # 5. 如果有重要架构决策,保存语义记忆
    await memory_manager.save_semantic_memory(
        knowledge="用户管理API采用RESTful设计",
        category="architecture"
    )

    # 6. 如果发现好的实践,保存程序记忆
    await memory_manager.save_procedural_memory(
        practice="API设计遵循RESTful原则",
        category="coding"
    )

    # 7. 查看统计信息
    stats = memory_manager.get_statistics()
    print(f"总记忆数: {stats['total_memories']}")

asyncio.run(memory_example())
```

### 示例2: 错误学习和改进

```python
async def error_learning_example():
    memory_manager = MemoryManager(Path("."))

    try:
        # 执行某个操作
        result = risky_operation()
    except Exception as e:
        # 保存错误教训
        await memory_manager.save_mistake(
            error=e,
            context="执行数据迁移任务时发生错误",
            fix="1. 备份数据 2. 使用事务 3. 添加回滚机制",
            learning="数据操作必须使用事务,确保原子性"
        )

        # 下次执行类似任务时,会自动提醒避免重复错误
```

### 示例3: 项目知识积累

```python
async def knowledge_accumulation_example():
    memory_manager = MemoryManager(Path("."))

    # 项目启动时的架构决策
    await memory_manager.save_semantic_memory(
        knowledge="""技术栈选择

后端框架: FastAPI
理由:
- 高性能(基于Starlette和Pydantic)
- 自动API文档生成
- 原生异步支持
- 类型验证

数据库: PostgreSQL
理由:
- ACID事务支持
- 复杂查询能力
- JSON字段支持
""",
        category="tech_stack",
        tags=["fastapi", "postgresql", "backend"]
    )

    # 后续团队成员可以查询这些决策
    decisions = await memory_manager.query_semantic_memory(
        category="tech_stack"
    )

    for decision in decisions:
        print(f"技术决策: {decision['content']}")
```

---

## ✅ 最佳实践

### 1. 及时保存

```python
# ❌ 不好: 批量保存,容易遗漏
async def bad_example():
    # 执行10个任务
    for i in range(10):
        execute_task(i)

    # 最后统一保存(中间出错可能丢失)
    save_memories()

# ✅ 好: 每个任务完成后立即保存
async def good_example():
    for i in range(10):
        execute_task(i)
        # 立即保存
        await memory_manager.save_episodic_memory(
            event=f"任务 {i} 完成",
            task_id=f"task-{i}"
        )
```

### 2. 合理分类

```python
# ❌ 不好: 分类混乱
await memory_manager.save_semantic_memory(
    knowledge="如何编写单元测试",  # 这是实践,不是知识
    category="architecture"
)

# ✅ 好: 正确分类
await memory_manager.save_procedural_memory(
    practice="单元测试三步法: 1. 准备 2. 执行 3. 断言",
    category="testing"
)
```

### 3. 使用标签

```python
# ✅ 好: 使用标签方便查询
await memory_manager.save_semantic_memory(
    knowledge="微服务架构设计",
    category="architecture",
    tags=["microservices", "scalability", "distributed-systems"]
)
```

### 4. 定期回顾

```python
async def review_memories():
    memory_manager = MemoryManager(Path("."))

    # 1. 查看最近的错误
    episodic = await memory_manager.get_episodic_memories(limit=20)
    errors = [m for m in episodic if "失败" in m["content"]]

    print(f"最近的错误: {len(errors)} 个")

    # 2. 查看架构决策
    decisions = await memory_manager.query_semantic_memory(
        category="architecture"
    )

    print(f"架构决策: {len(decisions)} 个")

    # 3. 查看最佳实践
    practices = await memory_manager.get_procedural_memories()

    print(f"最佳实践: {len(practices)} 个")

    # 4. 查看统计
    stats = memory_manager.get_statistics()
    print(f"总记忆: {stats['total_memories']} 条")
```

### 5. 与团队共享

```bash
# .superagent/memory/ 目录可以纳入Git仓库
# 团队成员可以共享项目知识

git add .superagent/memory/
git commit -m "更新项目记忆"
git push
```

---

## 📚 API参考

### MemoryManager

#### 初始化

```python
def __init__(self, project_root: Path):
    """初始化记忆管理器

    Args:
        project_root: 项目根目录
    """
```

#### 情节记忆API

```python
async def save_episodic_memory(
    self,
    event: str,
    task_id: Optional[str] = None,
    agent_type: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """保存情节记忆

    Args:
        event: 事件描述
        task_id: 任务ID
        agent_type: Agent类型
        metadata: 额外元数据

    Returns:
        str: 记忆ID
    """

async def get_episodic_memories(
    self,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """获取最近的情节记忆

    Args:
        limit: 返回数量限制

    Returns:
        List[Dict[str, Any]]: 记忆列表
    """
```

#### 语义记忆API

```python
async def save_semantic_memory(
    self,
    knowledge: str,
    category: str,
    tags: Optional[List[str]] = None
) -> str:
    """保存语义记忆

    Args:
        knowledge: 知识内容
        category: 分类
        tags: 标签

    Returns:
        str: 记忆ID
    """

async def query_semantic_memory(
    self,
    category: Optional[str] = None,
    keywords: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """查询语义记忆

    Args:
        category: 分类过滤
        keywords: 关键词过滤

    Returns:
        List[Dict[str, Any]]: 相关记忆
    """
```

#### 程序记忆API

```python
async def save_procedural_memory(
    self,
    practice: str,
    category: str,
    agent_type: Optional[str] = None
) -> str:
    """保存程序记忆

    Args:
        practice: 最佳实践内容
        category: 分类
        agent_type: Agent类型

    Returns:
        str: 记忆ID
    """

async def get_procedural_memories(
    self,
    category: Optional[str] = None
) -> List[Dict[str, Any]]:
    """获取程序记忆

    Args:
        category: 分类过滤

    Returns:
        List[Dict[str, Any]]: 记忆列表
    """
```

#### 错误教训API

```python
async def save_mistake(
    self,
    error: Exception,
    context: str,
    fix: str,
    learning: str
):
    """保存错误教训

    Args:
        error: 错误对象
        context: 上下文信息
        fix: 修复方案
        learning: 学到的经验
    """
```

#### 综合查询API

```python
async def query_relevant_memory(
    self,
    task: str,
    agent_type: Optional[str] = None
) -> Dict[str, List[str]]:
    """查询相关记忆,避免重复错误

    Args:
        task: 任务描述
        agent_type: Agent类型

    Returns:
        Dict[str, List[str]]: 分类记忆列表
        {
            "mistakes": [...],
            "best_practices": [...],
            "architecture_decisions": [...]
        }
    """
```

#### 统计API

```python
def get_statistics(self) -> Dict[str, Any]:
    """获取记忆统计信息

    Returns:
        Dict[str, Any]: 统计信息
        {
            "total_memories": int,
            "episodic_count": int,
            "semantic_count": int,
            "procedural_count": int,
            "memory_dir": str,
            "continuity_file": str
        }
    """
```

---

## 🔧 故障排除

### 问题1: 记忆目录未创建

**症状**:
```
FileNotFoundError: .superagent/memory/
```

**解决**:
```python
# MemoryManager会自动创建目录
# 如果仍然出错,手动创建:
from pathlib import Path
memory_dir = Path(".superagent/memory")
memory_dir.mkdir(parents=True, exist_ok=True)
```

### 问题2: CONTINUITY.md未更新

**症状**: 保存记忆后CONTINUITY.md没有更新

**解决**:
```python
# 检查日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 确认保存成功
memory_id = await memory_manager.save_semantic_memory(...)
print(f"保存成功: {memory_id}")

# 手动触发更新
memory_manager._append_to_continuity(
    memory_type="semantic",
    content="测试内容",
    category="test"
)
```

### 问题3: 记忆索引损坏

**症状**:
```
JSONDecodeError: memory_index.json
```

**解决**:
```python
# 删除索引文件,会自动重建
from pathlib import Path
index_file = Path(".superagent/memory/memory_index.json")
if index_file.exists():
    index_file.unlink()
    print("索引已删除,将自动重建")
```

### 问题4: 查询结果为空

**症状**: `query_semantic_memory()` 返回空列表

**解决**:
```python
# 1. 检查是否有记忆
stats = memory_manager.get_statistics()
print(f"总记忆数: {stats['total_memories']}")

# 2. 检查查询条件
# 如果没有记忆,先保存一些
await memory_manager.save_semantic_memory(
    knowledge="测试知识",
    category="test"
)

# 3. 使用更宽松的查询条件
memories = await memory_manager.query_semantic_memory(
    # 不指定category和keywords,返回所有
)
```

---

## 📊 性能优化

### 1. 批量操作

```python
# ❌ 不好: 多次单独保存
for item in items:
    await memory_manager.save_semantic_memory(...)

# ✅ 好: 批量保存(如果API支持)
# 或使用异步并发
import asyncio

tasks = [
    memory_manager.save_semantic_memory(...)
    for item in items
]
await asyncio.gather(*tasks)
```

### 2. 缓存查询结果

```python
# 使用缓存避免重复查询
from functools import lru_cache

@lru_cache(maxsize=128)
def get_architecture_decisions():
    return asyncio.run(
        memory_manager.query_semantic_memory(
            category="architecture"
        )
    )
```

### 3. 定期清理

```python
# 清理旧的记忆(可选)
async def cleanup_old_memories(days=90):
    from datetime import datetime, timedelta

    cutoff = datetime.now() - timedelta(days=days)

    # 遍历记忆文件
    for memory_file in episodic_dir.glob("*.json"):
        # 读取并检查时间戳
        # 如果超过90天,删除或归档
        ...
```

---

## 🎯 总结

### 记忆系统的价值

1. **防止重复错误**: 从历史中学习
2. **加速开发**: 复用已有知识
3. **知识积累**: 形成组织记忆
4. **上下文连续**: 跨会话保持

### 使用建议

- ✅ 及时保存每次任务执行
- ✅ 记录重要的架构决策
- ✅ 总结最佳实践
- ✅ 定期回顾CONTINUITY.md
- ✅ 与团队共享记忆

### 下一步

1. 在项目中集成MemoryManager
2. 配置自动记忆保存
3. 定期回顾和整理记忆
4. 根据项目需求定制分类和标签

---

**记住**: 记忆系统是项目的"大脑",持续积累会让项目越来越"聪明"!
