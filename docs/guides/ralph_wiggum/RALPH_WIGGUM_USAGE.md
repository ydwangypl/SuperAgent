# Ralph Wiggum 自然语言调用指南

**在 Claude Code 中用自然语言单独调用 Ralph Wiggum 进行代码改进**

---

## 🎯 功能说明

### 场景

当 SuperAgent 的自动审查结束后,如果代码质量未达标,您可以用自然语言单独调用 Ralph Wiggum 继续改进。

### 优势

- ✅ 灵活控制迭代次数
- ✅ 针对特定文件
- ✅ 不需要重新运行整个 SuperAgent
- ✅ 可以多次调用,逐步改进

---

## 💬 自然语言命令

### 基础用法

#### 命令 1: 改进单个文件 (默认3次)

```
使用 Ralph Wiggum 改进 user.py
```

**我会执行**:
```python
from pathlib import Path
from ralph_wiggum_cli import RalphWiggumStandalone

rw = RalphWiggumStandalone(Path("."), min_score=70.0, max_iterations=3)
result = await rw.improve_file("user.py")

# 显示结果
# - 第1次审查: 评分 65/100
# - 第2次改进后: 评分 72/100 ✅ 达标
```

---

#### 命令 2: 指定迭代次数

```
使用 Ralph Wiggum 改进 user.py,最多5次迭代
```

**我会执行**:
```python
result = await rw.improve_file("user.py", max_iterations=5)
```

---

#### 命令 3: 指定目标评分

```
使用 Ralph Wiggum 改进 user.py,目标85分
```

**我会执行**:
```python
rw = RalphWiggumStandalone(Path("."), min_score=85.0)
result = await rw.improve_file("user.py")
```

---

#### 命令 4: 完全自定义

```
使用 Ralph Wiggum 改进 auth.py,最多5次迭代,目标90分
```

**我会执行**:
```python
rw = RalphWiggumStandalone(
    Path("."),
    min_score=90.0,
    max_iterations=5
)
result = await rw.improve_file("auth.py")
```

---

#### 命令 5: 改进多个文件

```
使用 Ralph Wiggum 改进所有 Python 文件
```

**我会执行**:
```python
results = await rw.improve_files(["**/*.py"])
```

---

#### 命令 6: 改进指定目录

```
使用 Ralph Wiggum 改进 src/api/ 目录下的所有文件
```

**我会执行**:
```python
results = await rw.improve_files(["src/api/*.py"])
```

---

### 高级用法

#### 命令 7: 只审查不改进

```
使用 Ralph Wiggum 审查 user.py,不要改进
```

**我会执行**:
```python
config = ReviewConfig(
    enable_ralph_wiggum=False,  # 关闭循环
    min_overall_score=70.0
)
result = await code_reviewer.review_code(...)
```

---

#### 命令 8: 先审查再决定

```
使用 Ralph Wiggum 审查 user.py,告诉我评分和主要问题
```

**我会执行**:
```python
result = await code_reviewer.review_code(...)
print(f"评分: {result.metrics.overall_score}/100")
print(f"主要问题: {result.issues[:3]}")
```

---

## 📊 实际对话示例

### 示例 1: 三次未达标后继续改进

```
您: 使用 SuperAgent 开发用户登录功能

[SuperAgent 执行...]

我:
✅ 计划执行完成
❌ 代码审查未达标 (65/100, 需要70分)
提示: 达到最大迭代次数 (3次)

您: 使用 Ralph Wiggum 继续改进 auth.py,再试3次

我:
[执行 Ralph Wiggum 改进...]

第1次审查: 65/100
第2次改进后: 68/100
第3次改进后: 71/100 ✅ 达标!

最终评分: 71/100
改进成功!
```

---

### 示例 2: 针对特定文件

```
您: 使用 Ralph Wiggum 改进 user.py,最多5次

我:
正在改进 user.py...
目标评分: 70.0
最大迭代: 5次

迭代 1/5:
  评分: 55/100
  主要问题: 8个
  改进中...

迭代 2/5:
  评分: 62/100
  主要问题: 5个
  改进中...

迭代 3/5:
  评分: 68/100
  主要问题: 3个
  改进中...

迭代 4/5:
  评分: 73/100 ✅ 达标!
  主要问题: 1个

[SUCCESS] 经过4次迭代,代码已达标!

最终评分: 73/100
迭代次数: 4
```

---

### 示例 3: 提高要求

```
您: 代码质量还不够,使用 Ralph Wiggum 改进到90分

我:
[执行改进...]

第1次: 75/100
第2次: 82/100
第3次: 87/100
第4次: 89/100
第5次: 91/100 ✅ 达标!

最终评分: 91/100
[SUCCESS] 经过5次迭代,达到90分目标!
```

---

## 🎛️ 参数说明

### 迭代次数 (max_iterations)

| 值 | 适用场景 |
|----|---------|
| 1 | 快速检查 |
| 3 | 默认推荐 ⭐ |
| 5 | 质量要求高 |
| 7-10 | 严格模式 |

### 目标评分 (min_score)

| 分数 | 难度 | 适用场景 |
|------|------|---------|
| 60 | 容易 | 原型开发 |
| 70 | 中等 | 默认推荐 ⭐ |
| 80 | 较难 | 生产代码 |
| 85+ | 很难 | 关键模块 |

---

## 💡 最佳实践

### 1. 分步达标

```
# 第1步: 先达到70分
您: 使用 Ralph Wiggum 改进 user.py
→ 评分: 72/100 ✅

# 第2步: 提高到85分
您: 使用 Ralph Wiggum 改进 user.py,目标85分
→ 评分: 86/100 ✅

# 第3步: 严格模式
您: 使用 Ralph Wiggum 改进 user.py,目标90分,最多5次
→ 评分: 91/100 ✅
```

### 2. 先审查后改进

```
# 先看看问题
您: 使用 Ralph Wiggum 审查 user.py,只显示评分和问题

我:
评分: 65/100
主要问题:
  1. 缺少错误处理
  2. 未验证输入
  3. 硬编码密钥

# 再决定是否改进
您: 问题很多,使用 Ralph Wiggum 改进 user.py,最多5次

[执行改进...]
```

### 3. 批量改进

```
您: 使用 Ralph Wiggum 改进所有 API 文件,目标75分

我:
正在改进: src/api/*.py

[1/5] user.py: 68/100 → 76/100 ✅
[2/5] auth.py: 62/100 → 73/100 ✅
[3/5] post.py: 70/100 → 72/100 ✅
[4/5] comment.py: 75/100 → 77/100 ✅
[5/5] admin.py: 65/100 → 74/100 ✅

全部达标!
```

---

## 🔧 命令格式总结

### 基础格式

```
使用 Ralph Wiggum 改进 <文件>
```

### 完整格式

```
使用 Ralph Wiggum 改进 <文件>,最多<N>次迭代,目标<M>分
```

### 变体

| 命令 | 说明 |
|------|------|
| 使用 Ralph Wiggum 改进 user.py | 默认3次,70分 |
| 使用 Ralph Wiggum 改进 user.py,最多5次 | 指定迭代次数 |
| 使用 Ralph Wiggum 改进 user.py,目标85分 | 指定目标评分 |
| 使用 Ralph Wiggum 改进 user.py,5次,90分 | 完全自定义 |
| 使用 Ralph Wiggum 审查 user.py | 只审查,不改进 |
| 使用 Ralph Wiggum 改进所有py文件 | 批量改进 |

---

## 🚨 注意事项

### ⚠️ 重要提示

1. **需要配置环境变量**
   ```powershell
   $env:SUPERAGENT_ROOT = "E:\SuperAgent"
   ```

2. **实际改进需要 Claude Code 配合**
   - Ralph Wiggum 会生成改进建议
   - 但实际修改代码需要 Claude Code 执行
   - 我会协调这个过程

3. **文件必须存在**
   - 确保文件路径正确
   - 支持相对路径和绝对路径

4. **迭代次数不宜过多**
   - 3-5次通常足够
   - 过多迭代可能陷入循环
   - 建议分步达标

---

## 📝 与 SuperAgent 的关系

### 自动调用 (SuperAgent)

```
使用 SuperAgent 开发用户登录
→ 自动触发 Ralph Wiggum (如果配置了)
→ 默认3次迭代
→ 未达标会警告,但继续执行
```

### 手动调用 (独立使用)

```
[SuperAgent 完成后]
使用 Ralph Wiggum 继续改进 user.py,5次
→ 单独触发 Ralph Wiggum
→ 灵活指定参数
→ 可以多次调用
```

---

## 🎯 使用流程

### 完整工作流

```
1. 使用 SuperAgent 开发功能
   ↓
2. 查看审查结果
   ↓
3a. 如果达标 → 完成 ✅
   ↓
3b. 如果未达标
   ↓
4. 使用 Ralph Wiggum 继续改进 <文件>,5次
   ↓
5. 查看改进结果
   ↓
6a. 如果达标 → 完成 ✅
   ↓
6b. 如果仍未达标
   ↓
7. 调整策略:
   - 增加迭代次数
   - 降低目标评分
   - 或手动改进
```

---

## 💬 自然语言示例

### 场景 1: 继续改进

```
您: 使用 SuperAgent 开发博客系统

[执行完成,评分68/100]

您: 代码质量不够,使用 Ralph Wiggum 改进 main.py,再试5次

我: [执行5次迭代,最终75/100 ✅]
```

### 场景 2: 严格模式

```
您: 使用 Ralph Wiggum 改进 payment.py,目标90分,最多7次

我:
迭代1: 70/100
迭代2: 78/100
迭代3: 83/100
迭代4: 87/100
迭代5: 89/100
迭代6: 90/100 ✅ 达标!
```

### 场景 3: 批量改进

```
您: 使用 Ralph Wiggum 改进 src/models/ 下所有文件,目标80分

我:
[1/3] user.py: 75/100 → 82/100 ✅
[2/3] post.py: 72/100 → 78/100 ✅
[3/3] comment.py: 70/100 → 76/100 ✅
```

---

## 🎉 总结

### ✅ 现在您可以

1. **单独调用 Ralph Wiggum**
   ```
   使用 Ralph Wiggum 改进 user.py
   ```

2. **灵活控制参数**
   ```
   使用 Ralph Wiggum 改进 user.py,5次,85分
   ```

3. **多次调用,逐步改进**
   ```
   第1次: 使用 Ralph Wiggum 改进 user.py (目标70)
   第2次: 使用 Ralph Wiggum 改进 user.py,目标85
   第3次: 使用 Ralph Wiggum 改进 user.py,目标90
   ```

4. **针对特定文件**
   ```
   使用 Ralph Wiggum 改进 auth.py 和 user.py
   ```

---

**立即开始**:

```
使用 Ralph Wiggum 改进 <您的文件>
```

就这么简单! 🚀
