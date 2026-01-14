#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
智能上下文压缩器

提供智能上下文压缩功能,减少Token消耗
基于V2.2.0的smart_compressor.py实现
"""

import re
import hashlib
import logging
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class CompressionStats:
    """压缩统计"""
    original_length: int = 0
    compressed_length: int = 0
    extraction_time: float = 0.0
    compression_ratio: float = 0.0
    method: str = ""

    def to_dict(self) -> Dict:
        return {
            "original_length": self.original_length,
            "compressed_length": self.compressed_length,
            "compression_ratio": self.compression_ratio,
            "method": self.method,
            "extraction_time": f"{self.extraction_time*1000:.2f}ms"
        }


@dataclass
class ExtractedInfo:
    """提取的关键信息"""
    product: List[str] = field(default_factory=list)
    tech: List[str] = field(default_factory=list)
    requirements: List[str] = field(default_factory=list)
    decisions: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    # 优先级映射 (数字越大优先级越高)
    IMPORTANCE_MAP = {
        "constraints": 5,
        "requirements": 4,
        "decisions": 3,
        "tech": 2,
        "product": 1
    }

    def to_dict(self) -> Dict:
        return {
            "product": self.product,
            "tech": self.tech,
            "requirements": self.requirements,
            "decisions": self.decisions,
            "constraints": self.constraints
        }

    def to_summary(self, max_length: int = None) -> str:
        """转换为摘要字符串(支持重要性剪裁)"""
        if not max_length:
            lines = []
            if self.product: lines.append(f"产品/Product: {'; '.join(self.product[:3])}")
            if self.tech: lines.append(f"技术/Tech: {'; '.join(self.tech[:3])}")
            if self.requirements: lines.append(f"需求/Requirements: {'; '.join(self.requirements[:5])}")
            if self.decisions: lines.append(f"决策/Decisions: {'; '.join(self.decisions[:3])}")
            if self.constraints: lines.append(f"约束/Constraints: {'; '.join(self.constraints[:3])}")
            return "\n".join(lines)

        # 带有重要性剪裁的逻辑
        categories = [
            ("constraints", self.constraints, "约束/Constraints"),
            ("requirements", self.requirements, "需求/Requirements"),
            ("decisions", self.decisions, "决策/Decisions"),
            ("tech", self.tech, "技术/Tech"),
            ("product", self.product, "产品/Product")
        ]
        
        # 按重要性降序排列
        categories.sort(key=lambda x: self.IMPORTANCE_MAP.get(x[0], 0), reverse=True)
        
        result_lines = []
        current_length = 0
        
        for cat_id, items, label in categories:
            if not items:
                continue
            
            # 尝试添加该分类
            cat_text = f"{label}: {'; '.join(items[:5])}"
            if current_length + len(cat_text) + 1 <= max_length:
                result_lines.append(cat_text)
                current_length += len(cat_text) + 1
            else:
                # 如果整类加不下，尝试只加一部分
                remaining = max_length - current_length - len(label) - 2
                if remaining > 10:
                    partial_items = []
                    temp_len = 0
                    for item in items:
                        if temp_len + len(item) + 2 <= remaining:
                            partial_items.append(item)
                            temp_len += len(item) + 2
                        else:
                            break
                    if partial_items:
                        result_lines.append(f"{label}: {'; '.join(partial_items)}...")
                break
                
        return "\n".join(result_lines)


class KeyInformationExtractor:
    """关键信息提取器 - 提取5类关键信息(支持中英文)"""

    def __init__(self):
        self.patterns = {
            "product": [
                # 中文模式 (更宽松的匹配)
                r"(?:产品|项目|应用)[名称]?\s*[:：]?\s*([^\n]+)",
                r"核心功能\s*[:：]?\s*([^\n]+)",
                # 英文模式
                r"Product[ ]?Name[:]\s*([^\n]+)",
                r"Project[ ]?Name[:]\s*([^\n]+)",
                r"Application[ ]?Name[:]\s*([^\n]+)",
                r"Core[ ]?Features?[:]\s*([^\n]+)",
                r"^#\s+(.+)$",  # Markdown heading as product name
            ],
            "tech": [
                # 中文模式
                r"(?:技术栈|框架|语言|数据库)[:：]\s*([^\n]+)",
                r"使用\s*(?:了|的)?\s*([^\n,，]+)",
                # 英文模式
                r"Tech[ ]?Stack[:]\s*([^\n]+)",
                r"Framework[s]?[:]\s*([^\n]+)",
                r"Language[s]?[:]\s*([^\n]+)",
                r"Database[s]?[:]\s*([^\n]+)",
                r"Using\s+([A-Za-z]+(?:\s*,\s*[A-Za-z]+)*)",
                # 技术关键词
                r"\b(Python|FastAPI|React|Vue|PostgreSQL|Redis|MongoDB|Node\.?js|Angular|Django|Flask|Spring)\b",
            ],
            "requirements": [
                # 中文模式
                r"(?:需求|功能)[:：]\s*([^\n]+)",
                r"需要[支持实现]?\s*([^\n]+)",
                r"(?:用户|客户)需求[:：]\s*([^\n]+)",
                # 英文模式
                r"Requirement[s]?[:]\s*([^\n]+)",
                r"Feature[s]?[:]\s*([^\n]+)",
                r"Need[s]?\s+(?:to\s+|support[s]?)?([^\n]+)",
                r"User[ ]?Requirement[s]?[:]\s*([^\n]+)",
            ],
            "decisions": [
                # 中文模式
                r"(?:决定|决策|选择)[:：]\s*([^\n]+)",
                r"采用[:：]\s*([^\n]+)",
                r"使用[:：]\s*([^\n]+)",
                # 英文模式
                r"Decision[s]?[:]\s*([^\n]+)",
                r"Choice[s]?[:]\s*([^\n]+)",
                r"Adopt(?:ed)?[:]\s*([^\n]+)",
                r"Use(?:s|d)?[:]\s*([^\n]+)",
                r"Using\s+(?:the\s+)?([A-Za-z\s]+?)(?:\s+for|\s+as|\s+pattern)",
            ],
            "constraints": [
                # 中文模式
                r"(?:约束|限制|要求)[:：]\s*([^\n]+)",
                r"必须[满足]?\s*([^\n]+)",
                r"(?:不能|不可)[^\n]+",
                # 英文模式
                r"Constraint[s]?[:]\s*([^\n]+)",
                r"Limit[s]?[:]\s*([^\n]+)",
                r"Requirement[s]?[:]\s*([^\n]+)",
                r"Must\s+(?:be|satisfy|support|handle)([^\n]+)",
                r"\b(support[s]?|handle[s]?|must\s+be|need[s]?\s+to)\s+(\d+[^\n]*)",
            ]
        }

    def extract(self, content: str) -> ExtractedInfo:
        """提取关键信息"""
        extracted_info = ExtractedInfo()

        for category, patterns in self.patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    # 处理元组情况(多捕获组)
                    if isinstance(match, tuple):
                        match = ' '.join(str(g) for g in match if g)
                    match = str(match).strip()
                    if match and len(match) < 500:  # 避免过长匹配
                        if match not in getattr(extracted_info, category):
                            getattr(extracted_info, category).append(match)

        return extracted_info

    def format_extracted(self, extracted_info: ExtractedInfo) -> str:
        """格式化提取的信息"""
        return extracted_info.to_summary()


class SemanticCompressor:
    """语义压缩器 - 基于语义进行压缩"""

    def __init__(self):
        self.kie = KeyInformationExtractor()
        self._seen_hashes = set()

    def compress(self, content: str, max_length: int = None) -> Tuple[str, CompressionStats]:
        """压缩内容"""
        import time
        start_time = time.time()

        # 1. 提取关键信息
        extracted = self.kie.extract(content)
        compressed = extracted.to_summary(max_length)

        # 2. 移除冗余
        compressed = self._remove_redundancy(compressed)

        # 3. 智能截断
        if max_length and len(compressed) > max_length:
            compressed = self._truncate_intelligently(compressed, max_length)

        stats = CompressionStats(
            original_length=len(content),
            compressed_length=len(compressed),
            compression_ratio=len(compressed) / max(1, len(content)),
            extraction_time=time.time() - start_time,
            method="semantic"
        )

        return compressed, stats

    def _remove_redundancy(self, content: str) -> str:
        """移除冗余内容"""
        lines = content.split('\n')
        unique_lines = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 跳过纯标点或过短的行
            if len(line) < 3 or re.match(r'^[\s\d\.\,\;\:\-\_]+$', line):
                continue

            # MD5去重
            line_hash = hashlib.md5(line.encode()).hexdigest()
            if line_hash not in self._seen_hashes:
                self._seen_hashes.add(line_hash)
                unique_lines.append(line)

        # 重置哈希集
        self._seen_hashes.clear()

        return '\n'.join(unique_lines)

    def _truncate_intelligently(self, content: str, max_length: int) -> str:
        """智能截断,保留重要部分"""
        if len(content) <= max_length:
            return content

        lines = content.split('\n')

        # 保留标题行(支持中英文)
        important_lines = []
        for line in lines:
            if line.startswith(('产品:', '技术:', '需求:', '决策:', '约束:',
                               'Product:', 'Tech:', 'Requirements:', 'Decisions:', 'Constraints:')):
                important_lines.append(line)

        # 如果重要内容已经超过限制,进一步截断
        important_text = '\n'.join(important_lines)
        if len(important_text) > max_length * 0.8:
            return important_text[:max_length - 10] + "..."

        return content[:max_length - 10] + "..."


class StructuredCompressor:
    """结构化压缩器 - 保留结构化内容"""

    def compress(self, content: str, max_length: int = None) -> Tuple[str, CompressionStats]:
        """压缩结构化内容"""
        import time
        start_time = time.time()

        # 1. 提取标题
        titles = re.findall(r'^(#{1,6}\s+.+)$', content, re.MULTILINE)

        # 2. 提取列表项
        list_items = re.findall(r'^[\-\*\s]*[\-\*]\s+.+$', content, re.MULTILINE)

        # 3. 提取表格结构 (更精确的匹配)
        tables = re.findall(r'^\|.+(?:\n\|[-:\s|]+)+\n(?:\|.+\n?)*', content, re.MULTILINE)

        # 4. 合并保留结构
        compressed = []
        compressed.extend(titles[:30])  # 增加标题保留数量
        compressed.extend(list_items[:100])  # 增加列表项保留数量
        
        # 处理表格
        for table in tables[:10]:
            # 对大型表格进行行压缩，只保留前5行和最后2行
            table_lines = table.strip().split('\n')
            if len(table_lines) > 10:
                compressed.append('\n'.join(table_lines[:7] + ["| ... |"] + table_lines[-2:]))
            else:
                compressed.append(table)

        result = '\n\n'.join(compressed)

        # 如果结果仍然过长，进行智能截断
        if max_length and len(result) > max_length:
            result = result[:max_length-10] + "..."

        stats = CompressionStats(
            original_length=len(content),
            compressed_length=len(result),
            compression_ratio=len(result) / max(1, len(content)),
            extraction_time=time.time() - start_time,
            method="structured"
        )

        return result, stats

class ContextCache:
    """上下文缓存 - 缓存压缩结果"""

    def __init__(self, max_size: int = 100):
        self.cache: Dict[str, Tuple[str, CompressionStats]] = {}
        self.max_size = max_size

    def get_or_compress(
        self,
        content: str,
        compressor: Any,
        target_ratio: float = 0.5
    ) -> Tuple[str, CompressionStats]:
        """获取缓存或执行压缩"""
        # 生成缓存键 (基于内容和目标压缩率)
        cache_key = hashlib.md5(f"{content}:{target_ratio}".encode()).hexdigest()

        if cache_key in self.cache:
            return self.cache[cache_key]

        # 执行压缩
        compressed, stats = compressor.compress(content)

        # 缓存结果
        if len(self.cache) >= self.max_size:
            # 简单清理：删除第一个
            first_key = next(iter(self.cache))
            del self.cache[first_key]

        self.cache[cache_key] = (compressed, stats)
        return compressed, stats

    def clear(self):
        """清空缓存"""
        self.cache.clear()


class SmartContextCompressor:
    """智能上下文压缩器 - 主类"""

    # Agent定制压缩规则
    AGENT_COMPRESSION_RULES = {
        "coding": {"target_ratio": 0.5, "focus": ["tech", "requirements", "decisions"]},
        "backend-dev": {"target_ratio": 0.4, "focus": ["tech", "api", "requirements"]},
        "frontend-dev": {"target_ratio": 0.4, "focus": ["ui", "ux", "requirements"]},
        "database-design": {"target_ratio": 0.4, "focus": ["tech", "decisions"]},
        "product-management": {"target_ratio": 0.3, "focus": ["product", "requirements"]},
        "testing": {"target_ratio": 0.5, "focus": ["requirements", "decisions"]},
        "documentation": {"target_ratio": 0.6, "focus": []},
        "refactoring": {"target_ratio": 0.5, "focus": ["requirements", "decisions"]},
    }

    def __init__(self):
        self.semantic_compressor = SemanticCompressor()
        self.structured_compressor = StructuredCompressor()

    async def compress_async(
        self,
        content: str,
        max_tokens: int = None,
        method: str = "auto"
    ) -> Tuple[str, CompressionStats]:
        """异步压缩上下文"""
        import asyncio
        return await asyncio.to_thread(self.compress, content, max_tokens, method)

    def compress(
        self,
        content: str,
        max_tokens: int = None,
        method: str = "auto"
    ) -> Tuple[str, CompressionStats]:

        """压缩上下文

        Args:
            content: 原始内容
            max_tokens: 最大Token数(可选)
            method: 压缩方法 ("auto", "semantic", "structured")

        Returns:
            Tuple[压缩内容, 统计信息]
        """
        if not content:
            return "", CompressionStats()

        # 估算Token数(粗略: 1 token ≈ 4字符)
        max_chars = max_tokens * 4 if max_tokens else None

        if method == "auto":
            # 自动选择压缩方法
            if self._has_structure(content):
                return self.structured_compressor.compress(content, max_chars)
            else:
                return self.semantic_compressor.compress(content, max_chars)
        elif method == "semantic":
            return self.semantic_compressor.compress(content, max_chars)
        elif method == "structured":
            return self.structured_compressor.compress(content, max_chars)
        else:
            # 默认使用语义压缩
            return self.semantic_compressor.compress(content, max_chars)

    async def compress_for_agent_async(
        self,
        content: str,
        agent_type: str = "coding"
    ) -> Tuple[str, CompressionStats]:
        """异步为特定Agent压缩内容"""
        import asyncio
        return await asyncio.to_thread(self.compress_for_agent, content, agent_type)

    def compress_for_agent(
        self,
        content: str,
        agent_type: str = "coding"
    ) -> Tuple[str, CompressionStats]:

        """为特定Agent压缩内容

        Args:
            content: 原始内容
            agent_type: Agent类型

        Returns:
            Tuple[压缩内容, 统计信息]
        """
        import time
        start_time = time.time()

        # 获取Agent规则
        rule = self.AGENT_COMPRESSION_RULES.get(agent_type, {})
        target_ratio = rule.get("target_ratio", 0.5)
        focus = rule.get("focus", [])

        # 1. 先对原始内容进行语义压缩
        compressed, _ = self.semantic_compressor.compress(content)

        # 2. 如果指定了focus,只保留相关信息
        if focus:
            info = KeyInformationExtractor().extract(compressed)
            filtered_info = ExtractedInfo()
            for field_name in focus:
                if hasattr(info, field_name):
                    setattr(filtered_info, field_name, getattr(info, field_name))
            
            # 计算目标字符数并使用重要性剪裁
            target_chars = int(len(content) * target_ratio)
            compressed = filtered_info.to_summary(max_length=target_chars)
        else:
            # 3. 估算目标长度并进一步截断
            target_chars = int(len(content) * target_ratio)
            if len(compressed) > target_chars:
                compressed = self.semantic_compressor._truncate_intelligently(compressed, target_chars)

        # 计算统计信息(相对于原始内容)
        stats = CompressionStats(
            original_length=len(content),
            compressed_length=len(compressed),
            compression_ratio=len(compressed) / max(1, len(content)),
            extraction_time=time.time() - start_time,
            method=f"agent_{agent_type}"
        )

        logger.debug(
            f"压缩内容 for {agent_type}: "
            f"{stats.compression_ratio*100:.1f}%"
        )

        return compressed, stats

    def extract_key_info(self, content: str) -> ExtractedInfo:
        """提取关键信息"""
        return KeyInformationExtractor().extract(content)

    def _has_structure(self, content: str) -> bool:
        """判断内容是否有结构"""
        has_titles = bool(re.search(r'^#{1,6}\s', content, re.MULTILINE))
        has_lists = bool(re.search(r'^[\-\*]\s', content, re.MULTILINE))
        has_tables = bool(re.search(r'\|.+\|', content))

        return has_titles or has_lists or has_tables

    def compress_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """压缩单条消息"""
        role = message.get("role", "")
        content = message.get("content", "")

        if isinstance(content, str):
            compressed_content, _ = self.compress(content)
            message["content"] = compressed_content
        elif isinstance(content, list):
            # 处理多模态内容
            new_content = []
            for item in content:
                if item.get("type") == "text":
                    compressed, _ = self.compress(item.get("text", ""))
                    item["text"] = compressed
                new_content.append(item)
            message["content"] = new_content

        return message

    async def compress_messages_async(
        self,
        messages: List[Dict[str, Any]],
        max_tokens: int = 8000
    ) -> Tuple[List[Dict[str, Any]], CompressionStats]:
        """异步压缩消息历史"""
        import asyncio
        return await asyncio.to_thread(self.compress_messages, messages, max_tokens)

    def compress_messages(
        self,
        messages: List[Dict[str, Any]],
        max_tokens: int = 8000
    ) -> Tuple[List[Dict[str, Any]], CompressionStats]:

        """压缩消息历史

        Args:
            messages: 消息列表
            max_tokens: 最大Token数

        Returns:
            Tuple[压缩后的消息列表, 统计信息]
        """
        import time
        start_time = time.time()

        compressed_messages = []
        current_tokens = 0

        for message in reversed(messages):
            # 估算消息Token
            content = message.get("content", "")
            if isinstance(content, str):
                message_tokens = len(content) // 4
            else:
                message_tokens = 100  # 多模态消息估算

            # 如果加入当前消息会超过限制,跳过
            if current_tokens + message_tokens > max_tokens:
                # 但保留最后一条用户消息
                if message.get("role") == "user" and not compressed_messages:
                    compressed_msg = self.compress_message(message.copy())
                    compressed_messages.insert(0, compressed_msg)
                continue

            # 压缩消息
            compressed_msg = self.compress_message(message.copy())
            compressed_messages.insert(0, compressed_msg)
            current_tokens += message_tokens

        # 构建摘要消息
        if messages and not compressed_messages:
            summary = self._create_summary_message(messages[-5:])
            compressed_messages.append(summary)

        stats = CompressionStats(
            original_length=sum(
                len(str(m.get("content", ""))) for m in messages
            ),
            compressed_length=sum(
                len(str(m.get("content", ""))) for m in compressed_messages
            ),
            compression_ratio=len(compressed_messages) / max(1, len(messages)),
            extraction_time=time.time() - start_time,
            method="message_history"
        )

        return compressed_messages, stats

    def _create_summary_message(self, recent_messages: List[Dict]) -> Dict[str, Any]:
        """为被截断的消息创建摘要"""
        # 提取关键信息
        all_content = "\n".join(
            str(m.get("content", "")) for m in recent_messages
        )
        key_info = self.extract_key_info(all_content)

        summary = f"**对话摘要**\n\n{key_info.to_summary()}"

        return {
            "role": "system",
            "content": summary
        }
