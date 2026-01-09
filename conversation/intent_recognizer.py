#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
智能意图识别器

增强的意图识别,支持Agent类型自动映射
"""

import re
from typing import List, Dict, Any
from dataclasses import dataclass
from functools import lru_cache

from common.security import sanitize_input
from common.models import AgentType
from orchestration.registry import AgentRegistry
from .models import Intent, IntentType

class IntentRecognizer:
    """智能意图识别器"""

    def __init__(self, llm_provider: Any = None) -> None:
        """初始化意图识别器
        
        Args:
            llm_provider: LLM提供者,用于低置信度时的二次确认
        """
        self.llm_provider = llm_provider
        
        # Agent类型关键词映射 (Phase 3 重构：从 Registry 获取)
        self.agent_keywords = AgentRegistry.get_all_keywords()

        # 功能关键词 (泛化处理)
        self.feature_keywords = {
            "用户管理": [r"用户|注册|登录|认证|权限|账号|auth|identity"],
            "数据持久化": [r"存储|数据库|保存|缓存|persistence|database|sql|nosql"],
            "网络通信": [r"网络|http|tcp|udp|socket|通信|协议|protocol|grpc"],
            "业务逻辑": [r"逻辑|处理|计算|算法|流程|workflow|business|logic|管理|处理|评论|发布"],
            "人机交互": [r"界面|ui|页面|交互|控制台|cli|terminal|frontend|frontend"],
            "文件操作": [r"文件|读写|上传|下载|目录|fs|io"],
            "安全防护": [r"加密|解密|安全|漏洞|防护|security|encryption"],
            "任务调度": [r"定时|队列|调度|并发|async|concurrency|queue"],
            "内容管理": [r"文章|博客|内容|商品|订单|管理|评论"]
        }

        # 技术栈关键词 (扩展非 Web 领域)
        self.tech_stack_keywords = {
            "python": [r"python", r"pip", r"pytest"],
            "web_frameworks": [r"flask", r"django", r"fastapi", r"react", r"vue", r"express"],
            "systems": [r"rust", r"c\+\+", r"c#", r"golang", r"asm", r"llvm"],
            "mobile": [r"flutter", r"swift", r"kotlin", r"android", r"ios"],
            "scripting": [r"bash", r"shell", r"powershell", r"lua", r"perl"],
            "database": [r"mysql", r"postgresql", r"mongodb", r"redis", r"sqlite", r"database"]
        }

        # 预编译正则表达式以提升性能 (P1 优化)
        self._compiled_agent_patterns = {
            at: [re.compile(p, re.IGNORECASE) for p in patterns]
            for at, patterns in self.agent_keywords.items()
        }
        self._compiled_feature_patterns = {
            feat: [re.compile(p, re.IGNORECASE) for p in patterns]
            for feat, patterns in self.feature_keywords.items()
        }
        self._compiled_tech_patterns = {
            tech: [re.compile(p, re.IGNORECASE) for p in patterns]
            for tech, patterns in self.tech_stack_keywords.items()
        }

    async def recognize(self, user_input: str) -> Intent:
        """识别用户意图(异步版)

        Args:
            user_input: 用户输入

        Returns:
            Intent: 意图识别结果
        """
        # 1. 安全清理
        sanitized = sanitize_input(user_input)
        
        # 2. 规范化输入(去除多余空格,统一大小写)
        normalized = " ".join(sanitized.strip().split())

        # 3. 如果为空
        if not normalized:
            return Intent(
                type=IntentType.UNKNOWN,
                confidence=0.0,
                reasoning="输入为空,无法识别"
            )

        # 4. 执行识别 (带缓存)
        return self._recognize_cached(normalized)

    @lru_cache(maxsize=100)
    def _recognize_cached(self, user_input: str) -> Intent:
        """带缓存的识别逻辑"""
        return self._recognize_impl(user_input)

    def clear_cache(self) -> None:
        """清除识别缓存"""
        self._recognize_cached.cache_clear()

    def _recognize_impl(self, user_input: str) -> Intent:
        """实际的识别逻辑(同步,供 to_thread 调用)"""
        text_lower = user_input.lower()

        # 1. 提取关键词
        keywords = self._extract_keywords(user_input)

        # 2. 匹配Agent类型
        agent_types = self._match_agent_types(text_lower)

        # 3. 识别意图类型
        intent_type = self._map_to_intent_type(text_lower, agent_types)

        # 4. 计算置信度
        confidence = self._calculate_confidence(user_input, agent_types, keywords)

        # 5. 生成推理过程
        reasoning = self._generate_reasoning(user_input, agent_types, keywords)

        # 6. 生成建议步骤
        suggested_steps = self._generate_suggested_steps(agent_types, keywords)
        
        return Intent(
            type=intent_type,
            confidence=confidence,
            agent_types=agent_types,
            reasoning=reasoning,
            keywords=keywords,
            suggested_steps=suggested_steps
        )

    def _map_to_intent_type(self, text_lower: str, agent_types: List[AgentType]) -> IntentType:
        """将输入映射到 IntentType"""
        # 优先级: BUG > FEATURE > QUERY > NEW_PROJECT
        if any(word in text_lower for word in ["修复", "bug", "报错", "失败", "fix", "error"]):
            return IntentType.FIX_BUG
        
        if any(word in text_lower for word in ["添加", "增加", "新增", "add", "feature", "实现"]):
            return IntentType.ADD_FEATURE
            
        if any(word in text_lower for word in ["查看", "查询", "显示", "list", "show", "query"]):
            return IntentType.QUERY
            
        if agent_types or any(word in text_lower for word in ["开发", "创建", "新建", "build", "create", "系统", "应用"]):
            return IntentType.NEW_PROJECT
            
        return IntentType.UNKNOWN



    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词

        Args:
            text: 输入文本

        Returns:
            List[str]: 关键词列表
        """
        keywords = set()
        text_lower = text.lower()

        # 1. 提取功能关键词
        for feature, patterns in self._compiled_feature_patterns.items():
            for pattern in patterns:
                match = pattern.search(text_lower)
                if match:
                    keywords.add(feature)
                    if match.group(0):
                        keywords.add(match.group(0))
                    break

        # 2. 提取技术栈关键词
        for tech, patterns in self._compiled_tech_patterns.items():
            for pattern in patterns:
                match = pattern.search(text_lower)
                if match:
                    keywords.add(tech)
                    if match.group(0):
                        keywords.add(match.group(0))

        # 3. 提取 Agent 相关的关键词
        for patterns in self._compiled_agent_patterns.values():
            for pattern in patterns:
                # 处理正则中的 | 
                match = pattern.search(text_lower)
                if match and match.group(0):
                    matched_text = match.group(0)
                    if len(matched_text) > 1:
                        keywords.add(matched_text.lower())

        return sorted(list(keywords))  # 排序并去重

    def _match_agent_types(self, text_lower: str) -> List[AgentType]:
        """匹配Agent类型

        Args:
            text_lower: 小写输入文本

        Returns:
            List[AgentType]: 匹配的Agent类型列表
        """
        matched_agents = set()

        for agent_type, patterns in self._compiled_agent_patterns.items():
            for pattern in patterns:
                if pattern.search(text_lower):
                    matched_agents.add(agent_type)
                    break

        # 如果匹配到多个具体开发类型,可能需要全栈Agent
        dev_types = {AgentType.BACKEND_DEV, AgentType.FRONTEND_DEV, AgentType.DATABASE_DESIGN}
        if len(matched_agents.intersection(dev_types)) >= 2:
            matched_agents.add(AgentType.FULL_STACK_DEV)

        return list(matched_agents)

    async def get_agent_type_suggestions(self, user_input: str) -> List[Dict[str, Any]]:
        """获取Agent类型建议(异步版)

        Args:
            user_input: 用户输入

        Returns:
            List[Dict]: Agent类型建议列表
        """
        intent = await self.recognize(user_input)

        suggestions = []
        for agent_type in intent.agent_types:
            suggestions.append({
                "agent_type": agent_type.value,
                "reason": self._get_agent_reason(agent_type, intent.keywords)
            })

        return suggestions

    def _get_agent_reason(self, agent_type: AgentType, keywords: List[str]) -> str:
        """获取Agent类型推荐理由 (Phase 3 重构版：基于 Registry)"""
        return AgentRegistry.get_description(agent_type)

    def _calculate_confidence(self, user_input: str, agent_types: List[AgentType], keywords: List[str]) -> float:
        """计算识别置信度"""
        if not user_input:
            return 0.0
        
        score = 0.0
        # 1. 关键词权重
        if keywords:
            score += min(len(keywords) * 0.1, 0.4)
        
        # 2. Agent类型匹配权重
        if agent_types:
            score += 0.3
        
        # 3. 长度权重
        if len(user_input) > 20:
            score += 0.2
        
        return min(score + 0.1, 1.0)

    def _generate_reasoning(self, user_input: str, agent_types: List[AgentType], keywords: List[str]) -> str:
        """生成推理过程"""
        reasons = []
        if keywords:
            reasons.append(f"识别到关键词: {', '.join(keywords)}")
        if agent_types:
            agents = [at.value for at in agent_types]
            reasons.append(f"匹配到 Agent 类型: {', '.join(agents)}")
        
        if not reasons:
            return "未能识别到明确特征,置信度较低"
            
        return " | ".join(reasons)

    def _generate_suggested_steps(self, agent_types: List[AgentType], keywords: List[str]) -> List[str]:
        """生成建议执行步骤"""
        steps = ["产品需求分析"]
        
        # 转换 keywords 为集合以便快速查找
        kw_set = {k.lower() for k in keywords}
        
        if AgentType.DATABASE_DESIGN in agent_types or any(k in kw_set for k in ["数据库", "存储", "sql", "db", "数据表", "schema"]):
            steps.append("数据库设计")
            
        if AgentType.BACKEND_DEV in agent_types or AgentType.FULL_STACK_DEV in agent_types or any(k in kw_set for k in ["后端", "api", "接口", "服务端", "server"]):
            steps.append("后端API开发")
            
        if AgentType.FRONTEND_DEV in agent_types or AgentType.FULL_STACK_DEV in agent_types or any(k in kw_set for k in ["前端", "界面", "ui", "页面", "展示", "frontend"]):
            steps.append("前端界面开发")
            
        if AgentType.QA_ENGINEERING in agent_types or "测试" in kw_set:
            steps.append("测试用例编写")
            
        return steps
