# SuperAgent v3.0 Agent 实现完善指南

## 📋 概述

本文档提供Agent实现的详细指南和示例,确保所有Agent都符合输出格式规范。

**核心原则**: Agent返回的是**需求/框架文档**,不是**完整代码**。代码生成由Claude Code完成。

---

## 🎯 当前实现状态

### 已完成

1. ✅ **数据模型定义** ([execution/models.py](../execution/models.py))
   - `AgentResult` - Agent执行结果
   - `Artifact` - 生成的工件
   - `AgentContext` - 执行上下文
   - `AgentConfig` - Agent配置

2. ✅ **基础Agent类** ([execution/base_agent.py](../execution/base_agent.py))
   - `BaseAgent` - 所有Agent的基类
   - 标准化接口定义
   - 重试机制

3. ✅ **具体Agent实现**
   - `CodingAgent` - 代码生成
   - `TestingAgent` - 测试生成
   - `DocumentationAgent` - 文档生成
   - `RefactoringAgent` - 代码重构

4. ✅ **输出格式规范** ([docs/AGENT_OUTPUT_FORMAT.md](AGENT_OUTPUT_FORMAT.md))
   - 统一的输出结构
   - JSON格式定义
   - 文档模板

### 待完善

1. ⏳ **Agent输出实现** - 需要按照规范生成需求文档
2. ⏳ **示例验证** - 需要实际测试与Claude Code的集成
3. ⏳ **错误处理** - 完善错误处理和降级方案

---

## 🔧 完善方案

### 方案1: 创建Agent输出生成器

创建一个辅助类来帮助Agent生成符合规范的输出:

```python
# execution/agent_output_builder.py

from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from .models import Artifact, AgentResult, AgentStatus


class AgentOutputBuilder:
    """Agent输出构建器 - 帮助生成符合规范的输出"""

    @staticmethod
    def create_artifact(
        artifact_type: str,
        path: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Artifact:
        """创建标准Artifact对象"""
        return Artifact(
            artifact_id=f"{artifact_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            artifact_type=artifact_type,
            path=Path(path),
            content=content,
            metadata=metadata or {}
        )

    @staticmethod
    def create_requirements_artifact(
        feature_name: str,
        functional_requirements: List[str],
        non_functional_requirements: List[str]
    ) -> Artifact:
        """生成需求文档Artifact"""
        content = f"""# {feature_name} - 功能需求

## 功能需求

"""
        for i, req in enumerate(functional_requirements, 1):
            content += f"### {i}. {req}\n"

        content += "\n## 非功能需求\n\n"
        for req in non_functional_requirements:
            content += f"- {req}\n"

        return AgentOutputBuilder.create_artifact(
            artifact_type="requirements",
            path="REQUIREMENTS.md",
            content=content
        )

    @staticmethod
    def create_architecture_artifact(
        feature_name: str,
        pattern: str,
        layers: List[str],
        dependencies: List[str],
        directory_structure: str
    ) -> Artifact:
        """生成架构文档Artifact"""
        content = f"""# {feature_name} - 架构设计

## 架构模式
采用 {pattern} 模式

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

        return AgentOutputBuilder.create_artifact(
            artifact_type="architecture",
            path="ARCHITECTURE.md",
            content=content
        )

    @staticmethod
    def build_agent_result(
        agent_id: str,
        task_id: str,
        step_id: str,
        artifacts: List[Artifact],
        success: bool = True,
        message: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> AgentResult:
        """构建标准AgentResult"""
        return AgentResult(
            agent_id=agent_id,
            task_id=task_id,
            step_id=step_id,
            status=AgentStatus.COMPLETED if success else AgentStatus.FAILED,
            success=success,
            message=message,
            artifacts=artifacts,
            metadata=metadata or {}
        )
```

### 方案2: 更新CodingAgent实现

展示如何使用输出构建器:

```python
# execution/coding_agent.py (更新后)

from .agent_output_builder import AgentOutputBuilder

class CodingAgent(BaseAgent):
    """代码生成Agent - 返回需求框架而非完整代码"""

    async def execute(
        self,
        context: AgentContext,
        task_input: Dict[str, Any]
    ) -> AgentResult:
        """执行代码生成任务

        Args:
            context: 执行上下文
            task_input: 任务输入

        Returns:
            AgentResult: 包含需求文档的执行结果
        """
        self.status = AgentStatus.WORKING

        try:
            # 步骤1: 分析需求
            description = task_input.get("description", "")
            functional_reqs = self._extract_functional_requirements(description)
            non_functional_reqs = self._extract_non_functional_requirements(description)

            self.add_thought(
                step=1,
                thought=f"分析需求: {description}",
                action=f"提取了{len(functional_reqs)}个功能需求"
            )

            # 步骤2: 设计架构
            tech_stack = task_input.get("tech_stack", ["Python", "FastAPI"])
            architecture = self._design_architecture(description, tech_stack)

            self.add_thought(
                step=2,
                thought="设计系统架构",
                action=f"选择了{len(tech_stack)}个技术组件"
            )

            # 步骤3: 生成需求文档
            artifacts = []

            # 生成需求文档
            req_artifact = AgentOutputBuilder.create_requirements_artifact(
                feature_name=description[:30],
                functional_requirements=functional_reqs,
                non_functional_requirements=non_functional_reqs
            )
            artifacts.append(req_artifact)

            # 生成架构文档
            arch_artifact = AgentOutputBuilder.create_architecture_artifact(
                feature_name=description[:30],
                pattern=architecture["pattern"],
                layers=architecture["layers"],
                dependencies=tech_stack,
                directory_structure=architecture["structure"]
            )
            artifacts.append(arch_artifact)

            # 生成API规范(如果需要)
            if "API" in description or "api" in description.lower():
                api_artifact = self._create_api_spec(functional_reqs)
                artifacts.append(api_artifact)

            self.add_thought(
                step=3,
                thought="生成需求文档",
                action=f"创建了{len(artifacts)}个文档工件"
            )

            # 构建结果
            result = AgentOutputBuilder.build_agent_result(
                agent_id=self.agent_id,
                task_id=context.task_id,
                step_id=context.step_id,
                artifacts=artifacts,
                success=True,
                message=f"成功生成{len(artifacts)}个需求文档",
                metadata={
                    "functional_requirements_count": len(functional_reqs),
                    "non_functional_requirements_count": len(non_functional_reqs),
                    "tech_stack": tech_stack,
                    "estimated_code_lines": self._estimate_complexity(description)
                }
            )

            self.status = AgentStatus.COMPLETED
            return result

        except Exception as e:
            logger.error(f"CodingAgent执行失败: {e}")
            self.status = AgentStatus.FAILED
            return AgentOutputBuilder.build_agent_result(
                agent_id=self.agent_id,
                task_id=context.task_id,
                step_id=context.step_id,
                artifacts=[],
                success=False,
                message=f"执行失败: {str(e)}"
            )

    def _extract_functional_requirements(self, description: str) -> List[str]:
        """从描述中提取功能需求"""
        # 简化实现: 基于关键词提取
        requirements = []

        # 常见功能模式
        patterns = {
            r"用户.*注册": "用户注册功能 - 验证邮箱格式和密码强度",
            r"登录|认证": "用户登录功能 - 支持邮箱/密码登录",
            r"数据库|存储": "数据持久化 - 使用数据库存储用户数据",
            r"API|接口": "RESTful API - 提供标准化的API接口"
        }

        import re
        for pattern, requirement in patterns.items():
            if re.search(pattern, description, re.IGNORECASE):
                requirements.append(requirement)

        return requirements if requirements else ["基本功能实现"]

    def _extract_non_functional_requirements(self, description: str) -> List[str]:
        """提取非功能需求"""
        return [
            "性能: API响应时间 < 200ms",
            "安全: 密码使用bcrypt加密",
            "可用性: 99.9% uptime",
            "可扩展性: 支持水平扩展"
        ]

    def _design_architecture(
        self,
        description: str,
        tech_stack: List[str]
    ) -> Dict[str, Any]:
        """设计架构"""
        return {
            "pattern": "MVC",
            "layers": [
                "API层 (FastAPI路由)",
                "服务层 (业务逻辑)",
                "数据访问层 (数据库操作)"
            ],
            "structure": """src/
├── api/
│   └── endpoints.py      # API路由定义
├── services/
│   └── business.py       # 业务逻辑
├── repositories/
│   └── database.py       # 数据访问
├── models/
│   └── schemas.py        # 数据模型
└── main.py               # 应用入口"""
        }

    def _create_api_spec(self, functional_reqs: List[str]) -> Artifact:
        """创建API规范文档"""
        content = """# API 规范

## 端点列表

### POST /api/users/register
注册新用户

**请求**:
```json
{
  "email": "user@example.com",
  "password": "secure_password",
  "username": "johndoe"
}
```

**响应**:
```json
{
  "user_id": "123",
  "email": "user@example.com",
  "created_at": "2026-01-09T00:00:00Z"
}
```

### POST /api/users/login
用户登录

**请求**:
```json
{
  "email": "user@example.com",
  "password": "secure_password"
}
```

**响应**:
```json
{
  "token": "jwt_token_here",
  "expires_in": 3600
}
```
"""

        return AgentOutputBuilder.create_artifact(
            artifact_type="api_spec",
            path="API_SPEC.md",
            content=content
        )

    def _estimate_complexity(self, description: str) -> int:
        """估算代码复杂度(行数)"""
        # 简化实现: 基于描述长度
        base = 200
        multiplier = len(description) // 50
        return base + (multiplier * 100)
```

---

## 📝 示例: 完整的Agent执行流程

### 输入

```python
context = AgentContext(
    project_root=Path("/project"),
    task_id="task-001",
    step_id="step-1"
)

task_input = {
    "description": "开发用户管理API,支持注册和登录功能",
    "tech_stack": ["Python", "FastAPI", "PostgreSQL"]
}
```

### Agent输出

```python
AgentResult(
    agent_id="coding-agent",
    task_id="task-001",
    step_id="step-1",
    status=AgentStatus.COMPLETED,
    success=True,
    message="成功生成3个需求文档",
    artifacts=[
        Artifact(
            artifact_id="requirements_20260109_120000",
            artifact_type="requirements",
            path=Path("REQUIREMENTS.md"),
            content="# 用户管理API - 功能需求\n..."
        ),
        Artifact(
            artifact_id="architecture_20260109_120001",
            artifact_type="architecture",
            path=Path("ARCHITECTURE.md"),
            content="# 用户管理API - 架构设计\n..."
        ),
        Artifact(
            artifact_id="api_spec_20260109_120002",
            artifact_type="api_spec",
            path=Path("API_SPEC.md"),
            content="# API 规范\n..."
        )
    ],
    metadata={
        "functional_requirements_count": 3,
        "tech_stack": ["Python", "FastAPI", "PostgreSQL"],
        "estimated_code_lines": 400
    }
)
```

### Claude Code的工作

Claude Code读取这些文档后:

1. **阅读REQUIREMENTS.md** → 了解功能需求
2. **阅读ARCHITECTURE.md** → 理解架构设计
3. **阅读API_SPEC.md** → 明确API接口
4. **生成实际代码**:
   - `src/api/endpoints.py`
   - `src/services/business.py`
   - `src/repositories/database.py`
   - `src/models/schemas.py`
   - `main.py`
5. **编写测试**:
   - `tests/test_api.py`
   - `tests/test_services.py`

---

## ✅ 验证清单

Agent实现应该满足:

- [ ] 继承自`BaseAgent`
- [ ] 实现`capabilities`属性
- [ ] 实现`name`属性
- [ ] 实现`execute`方法
- [ ] 返回`AgentResult`对象
- [ ] `AgentResult.success`正确设置
- [ ] `AgentResult.artifacts`至少包含一个工件
- [ ] 工件内容符合Markdown格式
- [ ] 工件路径相对项目根目录
- [ ] 包含思考过程记录
- [ ] 错误处理完善
- [ ] 日志记录完整

---

## 🎯 后续工作

### 立即实施

1. **创建`AgentOutputBuilder`类**
   - 文件: `execution/agent_output_builder.py`
   - 提供标准化的输出构建方法

2. **更新现有Agent实现**
   - `CodingAgent` - 使用输出构建器
   - `TestingAgent` - 使用输出构建器
   - `DocumentationAgent` - 使用输出构建器
   - `RefactoringAgent` - 使用输出构建器

3. **创建单元测试**
   - 文件: `tests/test_agent_output.py`
   - 验证输出格式符合规范

### 可选改进

4. **添加智能需求提取**
   - 使用LLM分析用户描述
   - 自动生成更详细的需求

5. **添加架构模板**
   - 预定义常见架构模式
   - 根据技术栈自动选择

6. **添加代码估算**
   - 更准确的代码量估算
   - 基于历史数据学习

---

## 📚 参考资料

- [AGENT_OUTPUT_FORMAT.md](AGENT_OUTPUT_FORMAT.md) - 输出格式规范
- [execution/models.py](../execution/models.py) - 数据模型定义
- [execution/base_agent.py](../execution/base_agent.py) - Agent基类
- [ARCHITECTURE_V3_FINAL.md](../ARCHITECTURE_V3_FINAL.md) - 系统架构

---

**SuperAgent v3.0 - Agent实现完善指南**

**版本**: 3.0.0
**日期**: 2026-01-09
**状态**: 规划阶段
