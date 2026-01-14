#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试用户登录模块 - 包含一些常见的代码质量问题
"""

import hashlib
import json


class User:
    """用户类"""

    def __init__(self, username, password):
        self.username = username
        self.password = password  # 硬编码密码 - 安全问题
        self.is_active = True

    def check_password(self, password):
        # 没有密码哈希 - 安全问题
        return self.password == password

    def to_dict(self):
        return {
            "username": self.username,
            "password": self.password,  # 暴露密码 - 安全问题
            "is_active": self.is_active
        }


class UserAuth:
    """用户认证类"""

    SECRET_KEY = "my-secret-key-123"  # 硬编码密钥 - 安全问题

    def login(self, username, password):
        # 没有输入验证 - 安全问题
        user = self.get_user(username)

        if user:
            if user.check_password(password):
                # 没有错误处理 - 最佳实践问题
                token = self.generate_token(user)
                return {"token": token}

        return {"error": "登录失败"}

    def get_user(self, username):
        # 没有数据库连接管理 - 资源泄漏风险
        import sqlite3
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM users WHERE username = '{username}'")  # SQL注入风险
        result = cursor.fetchone()
        # 没有关闭连接 - 资源泄漏
        return result

    def generate_token(self, user):
        # 使用弱哈希算法 - 安全问题
        data = json.dumps(user.to_dict())
        return hashlib.md5(data.encode()).hexdigest()  # MD5不安全

    def validate_token(self, token):
        # 没有验证token格式 - 安全问题
        return len(token) == 32


# 全局变量 - 最佳实践问题
current_user = None
login_attempts = 0


def process_login(username, password):
    # 没有类型注解 - 最佳实践问题
    global current_user, login_attempts
    login_attempts += 1

    auth = UserAuth()
    result = auth.login(username, password)

    # 没有日志记录 - 最佳实践问题
    if "token" in result:
        current_user = username
        return {"success": True, "token": result["token"]}

    return {"success": False, "message": "登录失败"}


if __name__ == "__main__":
    # 简单的测试代码 - 没有异常处理
    result = process_login("admin", "password123")
    print(result)
