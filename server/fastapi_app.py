#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SuperAgent FastAPI REST API 服务

提供 HTTP 接口供外部系统调用 SuperAgent 功能，包括：
- 自然语言对话 (带项目引导)
- 任务执行
- 代码审查
- 测试运行
- 会话管理

使用方式:
    python -m server.fastapi_app
    或
    uvicorn server.fastapi_app:app --host 0.0.0.0 --port 8000
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Any, Dict, List
from contextlib import asynccontextmanager
import logging
import uuid
import os
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
import sys
sys.path.insert(0, str(PROJECT_ROOT))

from adapters.unified_adapter import UnifiedAdapter
from conversation.intent_recognizer import IntentRecognizer
from server.interaction_service import ProjectGuide
from security.validators import validate_path, validate_filename
from common.exceptions import ValidationError, SecurityError

logger = logging.getLogger(__name__)

# ============ 数据模型 ============

class ChatRequest(BaseModel):
    """聊天请求 - 自然语言输入"""
    message: str = Field(..., description="用户自然语言输入")
    session_id: Optional[str] = Field(None, description="会话ID")
    enable_guide: bool = Field(False, description="启用项目引导模式")
    context: Optional[Dict[str, Any]] = Field(None, description="附加上下文")


class ChatResponse(BaseModel):
    """聊天响应"""
    success: bool
    session_id: str
    intent: str
    response: str
    phase: Optional[str] = None  # 当前项目阶段
    action: Optional[str] = None  # 下一步动作
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class ExecuteTaskRequest(BaseModel):
    """执行任务请求"""
    task_type: str = Field(..., description="任务类型: coding, research, review, planning...")
    description: str = Field(..., description="任务描述")
    config: Optional[Dict[str, Any]] = Field(None, description="执行配置")

    # P0 Security: 验证任务类型
    _VALID_TASK_TYPES = {"coding", "research", "review", "planning", "analysis"}

    def validate_task_type(self):
        if self.task_type not in self._VALID_TASK_TYPES:
            raise ValidationError(
                message=f"Invalid task_type: {self.task_type}",
                field="task_type",
                value=self.task_type
            )


class TaskResponse(BaseModel):
    """任务响应"""
    success: bool
    task_id: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class ReviewRequest(BaseModel):
    """代码审查请求"""
    content: str = Field(..., description="代码内容")
    language: str = Field("python", description="编程语言")
    config: Optional[Dict[str, Any]] = Field(None, description="审查配置")


class ProjectInfoResponse(BaseModel):
    """项目信息响应"""
    session_id: str
    phase: str
    project_info: Dict[str, Any]
    current_question: Optional[str] = None


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    version: str
    service: str


# ============ 会话管理 ============

class SessionManager:
    """会话管理器 - 管理项目引导会话"""

    def __init__(self):
        # 内存存储 (生产环境可替换为 Redis)
        self._sessions: Dict[str, Dict] = {}
        self._guides: Dict[str, ProjectGuide] = {}

    def create_session(self, session_id: Optional[str] = None) -> str:
        """创建新会话"""
        sid = session_id or str(uuid.uuid4())
        self._sessions[sid] = {
            "created_at": datetime.now().isoformat(),
            "last_active": datetime.now().isoformat(),
            "message_history": [],
        }
        self._guides[sid] = ProjectGuide(project_root=PROJECT_ROOT)
        return sid

    def get_session(self, session_id: str) -> Optional[Dict]:
        """获取会话"""
        return self._sessions.get(session_id)

    def get_guide(self, session_id: str) -> Optional[ProjectGuide]:
        """获取项目引导器"""
        return self._guides.get(session_id)

    def update_session(self, session_id: str, message: str, response: str):
        """更新会话历史"""
        if session_id in self._sessions:
            self._sessions[session_id]["last_active"] = datetime.now().isoformat()
            self._sessions[session_id]["message_history"].append({
                "user": message,
                "assistant": response,
                "timestamp": datetime.now().isoformat()
            })

    def delete_session(self, session_id: str):
        """删除会话"""
        self._sessions.pop(session_id, None)
        self._guides.pop(session_id, None)


# 全局会话管理器
session_manager = SessionManager()


# ============ FastAPI 应用 ============

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("Starting SuperAgent API Server v3.4.0...")
    logger.info("Features: Natural Language Chat, Project Guide, Task Execution")
    yield
    logger.info("Shutting down SuperAgent API Server...")


app = FastAPI(
    title="SuperAgent API",
    description="AI Agent 任务编排平台 API - 提供自然语言接口、项目引导、任务执行、代码审查等功能",
    version="3.4.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# ============ CORS 安全配置 ============

def get_allowed_origins() -> List[str]:
    """获取安全的 CORS 白名单来源

    P0 Fix: 从环境变量读取，并验证不使用通配符+凭据组合
    """
    env_origins = os.getenv("ALLOWED_ORIGINS", "")
    if env_origins:
        origins = [o.strip() for o in env_origins.split(",") if o.strip()]
    else:
        # 默认仅允许本地开发
        origins = ["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000"]

    # P0 Security: 生产环境禁止通配符 + 凭据
    if os.getenv("ENVIRONMENT") == "production":
        if "*" in origins:
            raise RuntimeError(
                "CORS Security Error: Wildcard origin '*' is forbidden in production. "
                "Set ALLOWED_ORIGINS environment variable with specific origins."
            )
        if len(origins) > 1:
            raise RuntimeError(
                "CORS Security Error: Multiple origins are forbidden in production. "
                "Set ALLOWED_ORIGINS with a single origin."
            )

    return origins


# P0 Fix: 安全 CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),  # 不再使用通配符
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局适配器实例 (懒加载)
_adapter: Optional[UnifiedAdapter] = None
_intent_recognizer: Optional[IntentRecognizer] = None


def get_adapter() -> UnifiedAdapter:
    """获取适配器实例"""
    global _adapter
    if _adapter is None:
        _adapter = UnifiedAdapter(project_root=PROJECT_ROOT)
    return _adapter


def get_intent_recognizer() -> IntentRecognizer:
    """获取意图识别器"""
    global _intent_recognizer
    if _intent_recognizer is None:
        _intent_recognizer = IntentRecognizer()
    return _intent_recognizer


# ============ API 路由 ============

@app.get("/", response_model=HealthResponse)
async def root():
    """服务状态检查"""
    return HealthResponse(
        status="healthy",
        version="3.4.0",
        service="SuperAgent API"
    )


@app.get("/health")
async def health_check():
    """健康检查端点 (P3: 增强健康检查)

    返回服务健康状态和关键组件状态。
    用于负载均衡器和服务发现。
    """
    health_info = {
        "status": "healthy",
        "version": "3.4.0",
        "timestamp": datetime.now().isoformat(),
        "components": {}
    }

    # 检查 MemoryManager 状态
    try:
        from memory.memory_manager import MemoryManager
        mm = MemoryManager.get_instance()
        health_info["components"]["memory_manager"] = {
            "status": "healthy",
            "memory_dir": str(mm.memory_dir),
            "cache_size": mm.get_cache_stats()["total_entries"]
        }
    except Exception as e:
        health_info["components"]["memory_manager"] = {
            "status": "unhealthy",
            "error": str(e) if os.getenv("ENVIRONMENT") != "production" else "error"
        }
        health_info["status"] = "degraded"

    # 检查适配器状态
    try:
        adapter = get_adapter()
        health_info["components"]["adapter"] = {
            "status": "healthy",
            "has_executor": hasattr(adapter, 'executor'),
            "has_reviewer": hasattr(adapter, 'reviewer'),
            "has_tester": hasattr(adapter, 'tester')
        }
    except Exception as e:
        health_info["components"]["adapter"] = {
            "status": "unhealthy",
            "error": str(e) if os.getenv("ENVIRONMENT") != "production" else "error"
        }
        health_info["status"] = "degraded"

    return health_info


@app.get("/health/live")
async def liveness_probe():
    """存活探针

    仅检查服务是否存活，用于 Kubernetes liveness probe。
    """
    return {"status": "alive"}


@app.get("/health/ready")
async def readiness_probe():
    """就绪探针

    检查服务是否准备好接收流量，用于 Kubernetes readiness probe。
    """
    try:
        # 检查关键依赖
        from memory.memory_manager import MemoryManager
        mm = MemoryManager.get_instance()

        # 尝试访问 memory_dir
        if not mm.memory_dir.exists():
            raise Exception("Memory directory not accessible")

        return {"status": "ready"}
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Service not ready: {str(e)}"
        )


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """自然语言对话接口

    处理自然语言输入，支持两种模式：
    1. 普通模式：识别意图并执行任务
    2. 项目引导模式：分阶段引导大型项目

    示例 (普通模式):
        curl -X POST http://localhost:8000/api/chat \\
            -H "Content-Type: application/json" \\
            -d '{"message": "创建一个用户登录功能"}'

    示例 (项目引导模式):
        curl -X POST http://localhost:8000/api/chat \\
            -H "Content-Type: application/json" \\
            -d '{"message": "开发一个电商网站", "enable_guide": true}'
    """
    try:
        adapter = get_adapter()

        # 处理会话
        session_id = request.session_id
        if request.enable_guide:
            # 项目引导模式
            if not session_id:
                session_id = session_manager.create_session()
            else:
                # 确保会话存在
                if not session_manager.get_session(session_id):
                    session_id = session_manager.create_session(session_id)

            guide = session_manager.get_guide(session_id)
            if not guide:
                guide = ProjectGuide(project_root=PROJECT_ROOT)
                session_manager._guides[session_id] = guide

            # 处理项目引导
            guide_result = guide.handle_input(request.message)

            # 执行相应动作
            result_data = None
            if guide_result.get("action") == "research":
                # 执行产品研究
                research_result = await guide.execute_research()
                result_data = research_result.to_dict() if hasattr(research_result, 'to_dict') else research_result

            elif guide_result.get("action") == "develop":
                # 执行开发
                dev_result = await guide.execute_development()
                result_data = dev_result.to_dict() if hasattr(dev_result, 'to_dict') else dev_result

            elif guide_result.get("action") == "test":
                # 执行测试
                test_result = await guide.execute_testing()
                result_data = test_result

            # 更新会话历史
            session_manager.update_session(
                session_id,
                request.message,
                guide_result["message"]
            )

            return ChatResponse(
                success=True,
                session_id=session_id,
                intent="project_guide",
                response=guide_result["message"],
                phase=guide_result.get("phase"),
                action=guide_result.get("action"),
                data=result_data
            )

        else:
            # 普通模式
            recognizer = get_intent_recognizer()

            # 1. 识别意图
            intent_result = recognizer.recognize(request.message)
            logger.info(f"Detected intent: {intent_result.intent_type.value}")

            # 2. 根据意图处理
            result = None
            response_text = ""

            if intent_result.intent_type.value == "NEW_PROJECT":
                # 新项目创建
                result = await adapter.execute_task(
                    task_type="planning",
                    task_data={"description": request.message}
                )
                response_text = "已为您创建项目计划。"

            elif intent_result.intent_type.value == "ADD_FEATURE":
                # 添加功能
                result = await adapter.execute_task(
                    task_type="coding",
                    task_data={"description": request.message}
                )
                response_text = "功能开发任务已创建。"

            elif intent_result.intent_type.value == "FIX_BUG":
                # 修复 bug
                result = await adapter.execute_task(
                    task_type="coding",
                    task_data={"description": request.message}
                )
                response_text = "Bug 修复任务已创建。"

            elif intent_result.intent_type.value == "CLARIFY":
                # 需要澄清
                response_text = intent_result.suggestion or "请提供更多信息以便我更好地帮助您。"

            elif intent_result.intent_type.value == "QUERY":
                # 查询状态
                response_text = f"我理解了您的查询：{request.message}"

            else:
                # 默认处理
                response_text = f"理解您的需求：{request.message}"
                result = await adapter.execute_task(
                    task_type="coding",
                    task_data={"description": request.message}
                )

            return ChatResponse(
                success=True,
                session_id=request.session_id or "default",
                intent=intent_result.intent_type.value,
                response=response_text,
                data=result.to_dict() if result else None
            )

    except Exception as e:
        # P0 Security: 生成唯一错误ID用于日志追踪
        error_id = str(uuid.uuid4())[:8]
        logger.error(f"[Error-{error_id}] Chat error: {e}", exc_info=True)

        # P0 Security: 生产环境不返回详细错误
        detail = str(e)
        if os.getenv("ENVIRONMENT") == "production":
            detail = f"Internal server error [ID: {error_id}]"

        return ChatResponse(
            success=False,
            session_id=request.session_id or "default",
            intent="error",
            response="",
            error=detail
        )


@app.post("/api/execute", response_model=TaskResponse)
async def execute_task(request: ExecuteTaskRequest):
    """直接执行任务

    跳过意图识别，直接执行指定类型的任务。

    示例:
        curl -X POST http://localhost:8000/api/execute \\
            -H "Content-Type: application/json" \\
            -d '{"task_type": "coding", "description": "创建用户认证模块"}'
    """
    try:
        # P0 Security: 验证任务类型
        request.validate_task_type()

        adapter = get_adapter()

        logger.info(f"Executing task: type={request.task_type}, description={request.description[:50]}...")

        result = await adapter.execute_task(
            task_type=request.task_type,
            task_data={
                "description": request.description,
                **(request.config or {})
            }
        )

        return TaskResponse(
            success=result.success,
            task_id=result.execution_id,
            result=result.to_dict()
        )

    except ValidationError as ve:
        logger.warning(f"Task validation failed: {ve}")
        return TaskResponse(success=False, error=str(ve))
    except Exception as e:
        error_id = str(uuid.uuid4())[:8]
        logger.error(f"[Error-{error_id}] Execute error: {e}", exc_info=True)
        detail = str(e)
        if os.getenv("ENVIRONMENT") == "production":
            detail = f"Internal server error [ID: {error_id}]"
        return TaskResponse(success=False, error=detail)


@app.post("/api/review")
async def review_code(request: ReviewRequest):
    """代码审查接口

    对提供的代码进行质量审查。

    示例:
        curl -X POST http://localhost:8000/api/review \\
            -H "Content-Type: application/json" \\
            -d '{"content": "def hello(): pass", "language": "python"}'
    """
    try:
        adapter = get_adapter()

        logger.info(f"Reviewing code: language={request.language}")

        result = await adapter.review_code(
            artifact_data={"content": request.content},
            config={
                "language": request.language,
                **(request.config or {})
            }
        )

        return {"success": True, "result": result}

    except Exception as e:
        error_id = str(uuid.uuid4())[:8]
        logger.error(f"[Error-{error_id}] Review error: {e}", exc_info=True)
        detail = str(e)
        if os.getenv("ENVIRONMENT") == "production":
            detail = f"Internal server error [ID: {error_id}]"
        return {"success": False, "error": detail}


@app.post("/api/test")
async def run_tests(test_path: str = "tests"):
    """运行测试接口

    执行测试用例并返回结果。

    示例:
        curl -X POST http://localhost:8000/api/test?test_path=tests/
    """
    try:
        # P0 Security: 验证 test_path 防止路径遍历
        safe_test_path = validate_path(test_path, PROJECT_ROOT)
        if safe_test_path is None:
            raise SecurityError(
                message="Invalid test path",
                reason="Path traversal attempt detected",
                path=test_path
            )

        adapter = get_adapter()

        logger.info(f"Running tests: path={safe_test_path}")

        result = await adapter.run_tests(test_path=str(safe_test_path))

        return {"success": True, "result": result}

    except SecurityError as se:
        error_id = str(uuid.uuid4())[:8]
        logger.warning(f"[Security-{error_id}] Path validation failed: {se}")
        return {"success": False, "error": "Invalid test path"}
    except Exception as e:
        error_id = str(uuid.uuid4())[:8]
        logger.error(f"[Error-{error_id}] Test error: {e}", exc_info=True)
        detail = str(e)
        if os.getenv("ENVIRONMENT") == "production":
            detail = f"Internal server error [ID: {error_id}]"
        return {"success": False, "error": detail}


@app.get("/api/intent/recognize")
async def recognize_intent(message: str):
    """意图识别接口

    识别自然语言输入的意图，但不执行任务。

    示例:
        curl "http://localhost:8000/api/intent/recognize?message=创建用户登录功能"
    """
    try:
        recognizer = get_intent_recognizer()
        result = recognizer.recognize(message)

        return {
            "success": True,
            "intent": result.intent_type.value,
            "confidence": result.confidence,
            "entities": result.entities,
            "suggestion": result.suggestion
        }

    except Exception as e:
        error_id = str(uuid.uuid4())[:8]
        logger.error(f"[Error-{error_id}] Intent recognition error: {e}", exc_info=True)
        detail = str(e)
        if os.getenv("ENVIRONMENT") == "production":
            detail = f"Internal server error [ID: {error_id}]"
        return {"success": False, "error": detail}


# ============ 项目引导相关 API ============

@app.post("/api/project/start", response_model=ProjectInfoResponse)
async def start_project(session_id: Optional[str] = None):
    """开始新项目

    创建一个新的项目引导会话。

    示例:
        curl -X POST http://localhost:8000/api/project/start
    """
    try:
        sid = session_manager.create_session(session_id)
        guide = session_manager.get_guide(sid)

        return ProjectInfoResponse(
            session_id=sid,
            phase=guide.current_phase.value,
            project_info=guide.project_info,
            current_question=guide.get_current_question()
        )
    except Exception as e:
        error_id = str(uuid.uuid4())[:8]
        logger.error(f"[Error-{error_id}] Start project error: {e}", exc_info=True)
        detail = str(e)
        if os.getenv("ENVIRONMENT") == "production":
            detail = f"Internal server error [ID: {error_id}]"
        raise HTTPException(status_code=500, detail=detail)


@app.get("/api/project/status/{session_id}", response_model=ProjectInfoResponse)
async def get_project_status(session_id: str):
    """获取项目状态

    查询项目引导会话的当前状态。

    示例:
        curl http://localhost:8000/api/project/status/{session_id}
    """
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    guide = session_manager.get_guide(session_id)
    if not guide:
        raise HTTPException(status_code=404, detail="Project guide not found")

    return ProjectInfoResponse(
        session_id=session_id,
        phase=guide.current_phase.value,
        project_info=guide.project_info,
        current_question=guide.get_current_question()
    )


@app.delete("/api/project/end/{session_id}")
async def end_project(session_id: str):
    """结束项目

    结束项目引导会话，清理资源。

    示例:
        curl -X DELETE http://localhost:8000/api/project/end/{session_id}
    """
    session_manager.delete_session(session_id)
    return {"success": True, "message": "Project session ended"}


@app.post("/api/project/reset/{session_id}", response_model=ProjectInfoResponse)
async def reset_project(session_id: str):
    """重置项目

    重置项目引导会话到初始状态。

    示例:
        curl -X POST http://localhost:8000/api/project/reset/{session_id}
    """
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # 创建新的引导器
    guide = ProjectGuide(project_root=PROJECT_ROOT)
    session_manager._guides[session_id] = guide

    return ProjectInfoResponse(
        session_id=session_id,
        phase=guide.current_phase.value,
        project_info={},
        current_question=guide.get_current_question()
    )


@app.get("/api/project/phases")
async def get_project_phases():
    """获取项目阶段列表

    返回所有可用的项目阶段及其描述。

    示例:
        curl http://localhost:8000/api/project/phases
    """
    return {
        "phases": [
            {"id": "init", "name": "项目初始化", "description": "确定项目目标和范围"},
            {"id": "requirement", "name": "需求收集", "description": "收集详细的功能需求"},
            {"id": "research", "name": "产品研究", "description": "竞品分析和用户调研"},
            {"id": "design", "name": "架构设计", "description": "技术选型和系统设计"},
            {"id": "development", "name": "代码开发", "description": "生成项目代码"},
            {"id": "testing", "name": "测试验收", "description": "运行测试并验证功能"},
        ]
    }


# ============ 启动命令 ============

if __name__ == "__main__":
    import uvicorn

    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    print("=" * 60)
    print("  SuperAgent API Server v3.4.0")
    print("=" * 60)
    print("  API Docs: http://localhost:8000/docs")
    print("  Health:   http://localhost:8000/health")
    print("  Chat:     POST /api/chat")
    print("  Project:  POST /api/project/start")
    print("=" * 60)

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
