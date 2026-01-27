#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Celery 应用配置

v3.3 新增: Redis 认证支持
"""

import os
import logging
from celery import Celery
from config.settings import load_config

logger = logging.getLogger(__name__)

# 加载配置
config = load_config()
dist_config = config.distribution

# 创建 Celery 实例
app = Celery(
    "superagent",
    broker=dist_config.broker_url,
    backend=dist_config.result_backend,
    include=["distribution.tasks"]
)

# v3.3: 配置 Celery（支持 Redis 认证）
celery_config = {
    "task_serializer": "json",
    "accept_content": ["json"],
    "result_serializer": "json",
    "timezone": "Asia/Shanghai",
    "enable_utc": True,
    "task_time_limit": dist_config.task_timeout,
    "worker_concurrency": dist_config.worker_concurrency,
    "task_track_started": True,
}

# v3.3: 如果显式配置了 redis_password，构建带认证的 broker_url
if dist_config.redis_password:
    from urllib.parse import urlparse
    parsed = urlparse(dist_config.broker_url)

    # v3.3 安全增强：验证解析结果
    if not parsed.hostname:
        logger.error("无效的 broker_url: 缺少主机名")
        raise ValueError("无效的 broker_url: 缺少主机名")

    # v3.3 安全增强：构建安全的 broker_url，密码不会出现在日志中
    safe_broker_url = (
        f"redis://:{dist_config.redis_password}@"
        f"{parsed.hostname}:{parsed.port or 6379}/"
        f"{parsed.path.lstrip('/') if parsed.path else 0}"
    )
    celery_config["broker_url"] = safe_broker_url
    # v3.3 安全增强：不记录包含密码的 URL
    logger.info("Redis 认证配置已应用 (broker_url 已隐藏)")

app.conf.update(celery_config)

if __name__ == "__main__":
    app.start()
