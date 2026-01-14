#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SuperAgent v3.2 单元测试配置
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
SUPERAGENT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(SUPERAGENT_ROOT))
