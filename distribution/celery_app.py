#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Celery 应用配置
"""

import os
from celery import Celery
from config.settings import load_config

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

# 配置 Celery
app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_time_limit=dist_config.task_timeout,
    worker_concurrency=dist_config.worker_concurrency,
    task_track_started=True
)

if __name__ == "__main__":
    app.start()
