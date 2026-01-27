# SuperAgent v3.2 Agent 输出格式规范

> **规范定义** - 统一的 Agent 输出结构与 Claude Code 集成

本文档定义了 SuperAgent v3.2 中所有 Agent 的统一输出格式,确保与 Claude Code 的良好集成。

**核心原则**: Agent 返回的是**需求/框架**,不是**代码**。代码生成由 Claude Code 完成。

---

## 🎯 统一输出结构

所有 Agent 的输出都遵循以下基本结构:

```python
{
    "success": bool,           # 是否成功
    "agent_type": str,        # Agent 类型
    "task_id": str,           # 任务 ID
    "artifacts": dict,        # 产出的工件(文件/文档)
    "requirements": dict,     # 需求说明
    "metadata": dict,         # 元数据
    "next_steps": list,       # 建议的下一步
    "error": str | None       # 错误信息(如果有)
}
```

---

## 📝 各类 Agent 的具体输出格式

### 1. CodingAgent (编码 Agent)

**职责**: 返回代码需求和架构框架

**输出格式**:

```json
{
  "success": true,
  "agent_type": "coding-agent",
  "task_id": "task-1",
  "artifacts": {
    "requirements": "REQUIREMENTS.md",
    "architecture": "ARCHITECTURE.md",
    "api_spec": "API_SPEC.md",
    "data_models": "DATA_MODELS.md",
    "file_list": [
      "src/models/user.py",
      "src/api/user_api.py",
      "src/services/user_service.py"
    ]
  },
  "requirements": {
    "functional_requirements": [
      "用户注册功能",
      "用户登录功能",
      "密码加密存储"
    ],
    "non_functional_requirements": [
      "响应时间 < 200ms",
      "支持 1000 并发用户"
    ],
    "technical_constraints": [
      "使用 FastAPI 框架",
      "数据库使用 PostgreSQL",
      "认证使用 JWT"
    ]
  },
  "architecture": {
    "pattern": "MVC",
    "layers": [
      "API 层 (FastAPI)",
      "服务层 (Business Logic)",
      "数据访问层 (SQLAlchemy)"
    ],
    "dependencies": [
      "fastapi",
      "sqlalchemy",
      "pydantic"
    ]
  },
  "metadata": {
    "estimated_lines": 500,
    "estimated_time_hours": 4,
    "complexity": "medium"
  },
  "next_steps": [
    "Claude Code: 根据 ARCHITECTURE.md 生成项目结构",
    "Claude Code: 实现 API 端点",
    "Claude Code: 编写单元测试"
  ]
}
```

**示例输出文档**:

**REQUIREMENTS.md**:
```markdown
# 用户管理模块 - 功能需求

## 功能需求

### 1. 用户注册
- 输入: 用户名、邮箱、密码
- 验证: 邮箱格式、密码强度
- 输出: 用户 ID

### 2. 用户登录
- 输入: 邮箱、密码
- 验证: 密码匹配
- 输出: JWT Token

## 非功能需求
- 性能: API 响应时间 < 200ms
- 安全: 密码使用 bcrypt 加密
- 可用性: 99.9% uptime
```

**ARCHITECTURE.md**:
```markdown
# 用户管理模块 - 架构设计

## 架构模式
采用 MVC (Model-View-Controller) 模式

## 目录结构
```
src/
├── models/
│   └── user.py          # 用户数据模型
├── api/
│   └── user_api.py      # FastAPI 路由
├── services/
│   └── user_service.py  # 业务逻辑
└── repositories/
    └── user_repo.py     # 数据访问
```

## 技术栈
- Web 框架: FastAPI
- ORM: SQLAlchemy
- 数据验证: Pydantic
- 认证: JWT
```

---

### 2. TestingAgent (测试 Agent)

**职责**: 返回测试需求和测试用例框架

**输出格式**:

```json
{
  "success": true,
  "agent_type": "testing-agent",
  "task_id": "task-2",
  "artifacts": {
    "test_plan": "TEST_PLAN.md",
    "test_cases": "TEST_CASES.md",
    "test_structure": "tests/",
    "coverage_requirements": "COVERAGE.md"
  },
  "requirements": {
    "test_types": [
      "单元测试",
      "集成测试",
      "端到端测试"
    ],
    "coverage_target": {
      "line_coverage": 80,
      "branch_coverage": 70
    },
    "testing_frameworks": [
      "pytest",
      "pytest-cov",
      "pytest-asyncio"
    ]
  },
  "test_cases": {
    "unit_tests": [
      {
        "name": "test_user_registration",
        "description": "测试用户注册流程",
        "test_data": [
          {"input": {"username": "test"}, "expected": "success"},
          {"input": {"username": ""}, "expected": "validation_error"}
        ]
      }
    ],
    "integration_tests": [
      {
        "name": "test_user_api",
        "description": "测试用户 API 端点",
        "endpoints": ["/api/users/register", "/api/users/login"]
      }
    ]
  },
  "metadata": {
    "estimated_test_cases": 25,
    "estimated_time_hours": 3,
    "complexity": "low"
  },
  "next_steps": [
    "Claude Code: 根据 TEST_PLAN.md 生成测试文件",
    "Claude Code: 实现测试用例",
    "Claude Code: 配置 CI/CD 集成"
  ]
}
```

**示例输出文档**:

**TEST_PLAN.md**:
```markdown
# 用户管理模块 - 测试计划

## 测试范围
- 用户注册功能
- 用户登录功能
- 密码加密验证

## 测试策略
1. 单元测试: 覆盖所有业务逻辑
2. 集成测试: 测试 API 端点
3. 性能测试: 并发用户登录

## 测试工具
- pytest: 测试框架
- pytest-cov: 覆盖率报告
- pytest-asyncio: 异步测试支持

## 覆盖率目标
- 行覆盖率: ≥ 80%
- 分支覆盖率: ≥ 70%
```

---

### 3. DocumentationAgent (文档 Agent)

**职责**: 返回文档需求和文档结构

**输出格式**:

```json
{
  "success": true,
  "agent_type": "documentation-agent",
  "task_id": "task-3",
  "artifacts": {
    "api_docs": "docs/api/API.md",
    "user_guide": "docs/user/GUIDE.md",
    "developer_guide": "docs/developer/DEVELOPMENT.md",
    "readme": "README.md"
  },
  "requirements": {
    "documentation_types": [
      "API 文档",
      "用户指南",
      "开发者指南"
    ],
    "format": "Markdown",
    "tools": [
      "Sphinx",
      "MkDocs"
    ]
  },
  "documentation_structure": {
    "api_docs": {
      "sections": [
        "概述",
        "认证",
        "API 端点",
        "错误处理",
        "示例代码"
      ]
    },
    "user_guide": {
      "sections": [
        "快速开始",
        "功能说明",
        "常见问题",
        "故障排除"
      ]
    }
  },
  "metadata": {
    "estimated_pages": 15,
    "estimated_time_hours": 2,
    "complexity": "low"
  },
  "next_steps": [
    "Claude Code: 根据文档结构生成 Markdown 文件",
    "Claude Code: 添加代码示例",
    "Claude Code: 生成 API 文档"
  ]
}
```

---

### 4. RefactoringAgent (重构 Agent)

**职责**: 返回重构建议和重构计划

**输出格式**:

```json
{
  "success": true,
  "agent_type": "refactoring-agent",
  "task_id": "task-4",
  "artifacts": {
    "refactoring_plan": "REFACTORING_PLAN.md",
    "code_smells": "CODE_SMELLS.md",
    "suggestions": "SUGGESTIONS.md"
  },
  "requirements": {
    "refactoring_goals": [
      "提高代码可读性",
      "降低复杂度",
      "改善性能"
    ],
    "principles": [
      "SOLID 原则",
      "DRY 原则",
      "KISS 原则"
    ]
  },
  "code_smells": [
    {
      "type": "Long Method",
      "location": "src/services/user_service.py:45",
      "severity": "medium",
      "suggestion": "将长方法拆分为多个小方法"
    },
    {
      "type": "Duplicate Code",
      "location": "src/api/*.py",
      "severity": "high",
      "suggestion": "提取公共逻辑到基类"
    }
  ],
  "refactoring_suggestions": [
    {
      "priority": "high",
      "description": "提取重复的验证逻辑",
      "files": ["src/api/user_api.py", "src/api/auth_api.py"],
      "action": "创建 base_validator.py"
    }
  ],
  "metadata": {
    "estimated_refactorings": 8,
    "estimated_time_hours": 6,
    "complexity": "medium"
  },
  "next_steps": [
    "Claude Code: 根据重构计划修改代码",
    "Claude Code: 运行测试确保功能不变",
    "Claude Code: 提交重构后的代码"
  ]
}
```

---

## 🔧 与 Claude Code 的集成

### 典型工作流程

```
1. SuperAgent 生成计划
   ↓
2. Agent 执行任务,返回需求
   ↓
3. Claude Code 根据需求生成代码
   ↓
4. 代码审查层自动审查
   ↓
5. 保存到记忆系统
```

### 交互示例

**用户**: "开发一个用户管理 API"

**SuperAgent**:
1. 生成执行计划
2. 调用 CodingAgent
3. 返回需求文档

**Claude Code**:
1. 阅读 REQUIREMENTS.md
2. 阅读 ARCHITECTURE.md
3. 生成实际代码
4. 编写测试

---

## 📊 输出质量标准

### 1. 完整性
- ✅ 包含所有必需的字段
- ✅ 提供清晰的文件列表
- ✅ 明确的技术栈说明

### 2. 可读性
- ✅ 使用清晰的 Markdown 格式
- ✅ 提供代码示例
- ✅ 包含必要的注释

### 3. 可执行性
- ✅ 文档结构完整
- ✅ 技术选型合理
- ✅ 依赖关系明确

### 4. 一致性
- ✅ 格式统一
- ✅ 命名规范
- ✅ 风格一致

---

## 🚀 最佳实践

### Agent 输出设计原则

1. **YAGNI (You Aren't Gonna Need It)**
   - 只包含当前需要的信息
   - 避免过度设计
   - 保持简单实用

2. **KISS (Keep It Simple, Stupid)**
   - 使用简单的结构
   - 避免复杂的嵌套
   - 清晰的表达

3. **DRY (Don't Repeat Yourself)**
   - 复用通用模板
   - 避免重复内容
   - 统一格式标准

### 文档编写规范

1. **Markdown 格式**
   - 使用标准的 Markdown 语法
   - 添加适当的标题层级
   - 使用代码块展示示例

2. **代码示例**
   - 提供可运行的代码
   - 添加必要的注释
   - 说明使用场景

3. **结构化组织**
   - 逻辑清晰的章节划分
   - 表格和列表的使用
   - 图表的适当使用(如需要)

---

## 📝 输出示例模板

### CodingAgent 输出模板

```python
from execution.models import AgentResult, AgentOutput

def create_coding_agent_output(task_id: str, description: str) -> AgentResult:
    """创建 CodingAgent 标准输出"""
    return AgentResult(
        success=True,
        agent_type="coding-agent",
        task_id=task_id,
        artifacts={
            "requirements": "REQUIREMENTS.md",
            "architecture": "ARCHITECTURE.md",
            "api_spec": "API_SPEC.md"
        },
        requirements={
            "description": description,
            "functional": [...],
            "non_functional": [...]
        },
        metadata={
            "complexity": "medium",
            "estimated_hours": 4
        },
        next_steps=[
            "Claude Code: 生成项目结构",
            "Claude Code: 实现功能"
        ]
    )
```

---

## ✅ 验证清单

Agent 输出应该满足:

- [ ] 包含 `success` 字段
- [ ] 包含 `agent_type` 字段
- [ ] 包含 `task_id` 字段
- [ ] 包含 `artifacts` 字段(至少一个工件)
- [ ] 包含 `requirements` 字段(详细需求)
- [ ] 包含 `metadata` 字段(元数据)
- [ ] 包含 `next_steps` 字段(建议步骤)
- [ ] 格式符合 JSON 标准
- [ ] 文档使用 Markdown 格式
- [ ] 代码示例可运行
- [ ] 技术选型合理
- [ ] 依赖关系明确

---

## 🔗 相关文档

- [ARCHITECTURE_V3_FINAL.md](../ARCHITECTURE_V3_FINAL.md) - 架构文档
- [MEMORY_SYSTEM_GUIDE.md](MEMORY_SYSTEM_GUIDE.md) - 记忆系统指南
- [execution/models.py](../execution/models.py) - 数据模型定义

---

**SuperAgent v3.2 - 让开发更高效!** 🚀

---
**版本**: v3.2.0
**最后更新**: 2026-01-14
