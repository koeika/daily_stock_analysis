# 🔐 GitHub Actions 配置指南

## 💡 核心概念：GitHub Secrets

### ❓ 为什么 .env 不能提交到 GitHub？

**.env 文件包含敏感信息**：
- ❌ API Keys（DeepSeek、Gemini 等）
- ❌ Webhook URLs（飞书、企业微信）
- ❌ 密钥（FEISHU_WEBHOOK_SECRET）

**如果提交到 GitHub**：
- 🚨 任何人都能看到你的密钥
- 🚨 可能被滥用，产生费用
- 🚨 安全风险

---

## ✅ 解决方案：GitHub Secrets

GitHub Secrets 是 GitHub 提供的**加密存储**功能：
- ✅ 安全存储敏感信息
- ✅ 只有你和 GitHub Actions 能访问
- ✅ 在日志中自动脱敏显示
- ✅ 支持加密传输

### 工作原理

```
┌──────────────────────────────────────────────────────────────┐
│                      GitHub Secrets                           │
│  (存储在 GitHub，加密保存)                                      │
│                                                               │
│  OPENAI_API_KEY = sk-bf0c1ee9fb4c46cc...                     │
│  FEISHU_WEBHOOK_URL = https://open.feishu.cn/...            │
│  STOCK_LIST = 159636,159740,159928,...                       │
│  ...                                                          │
└────────────────────────┬──────────────────────────────────────┘
                        │
                        │ GitHub Actions 运行时注入
                        ↓
┌──────────────────────────────────────────────────────────────┐
│                   GitHub Actions 环境                         │
│                                                               │
│  env:                                                         │
│    OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}            │
│    FEISHU_WEBHOOK_URL: ${{ secrets.FEISHU_WEBHOOK_URL }}    │
│    STOCK_LIST: ${{ vars.STOCK_LIST || secrets.STOCK_LIST }} │
│                                                               │
│  运行: python main.py                                         │
│  (程序读取环境变量，就像本地的 .env 一样)                       │
└──────────────────────────────────────────────────────────────┘
```

---

## 🚀 配置步骤

### 第1步：Fork 仓库

1. 访问原仓库：https://github.com/ZhuLinsen/daily_stock_analysis
2. 点击右上角 **Fork** 按钮
3. 选择你的账号，创建副本

---

### 第2步：配置 GitHub Secrets

#### 进入 Secrets 设置页面

```
你的仓库 → Settings → Secrets and variables → Actions → New repository secret
```

或直接访问：
```
https://github.com/你的用户名/daily_stock_analysis/settings/secrets/actions
```

#### 需要配置的 Secrets（根据你的 .env）

点击 **"New repository secret"**，逐个添加以下配置：

---

### 📋 必填 Secrets 清单

#### 1. AI 模型配置

| Secret 名称 | 值（从你的 .env 复制） | 说明 |
|------------|---------------------|------|
| `OPENAI_API_KEY` | `sk-bf0c1ee9fb4c46cc8c9ea62a14d03a21` | DeepSeek API Key |
| `OPENAI_BASE_URL` | `https://api.deepseek.com/v1` | DeepSeek API 地址 |
| `OPENAI_MODEL` | `deepseek-chat` | 模型名称 |

**添加方式**：
1. Name: `OPENAI_API_KEY`
2. Secret: `sk-bf0c1ee9fb4c46cc8c9ea62a14d03a21`
3. 点击 "Add secret"

---

#### 2. 飞书推送配置

| Secret 名称 | 值（从你的 .env 复制） | 说明 |
|------------|---------------------|------|
| `FEISHU_WEBHOOK_URL` | `https://open.feishu.cn/open-apis/bot/v2/hook/79791f9f-d027-46e5-98fe-b6bc8a3b3c51` | 飞书 Webhook |
| `FEISHU_WEBHOOK_SECRET` | `Gf55G2oRdxXqMtULRAGBY` | 飞书签名密钥 |

**注意**：URL 要完整复制，包括 `https://`

---

#### 3. 股票列表配置

| Secret 名称 | 值（从你的 .env 复制） | 说明 |
|------------|---------------------|------|
| `STOCK_LIST` | `159636,159740,159928,588920,516270,159525,512980` | 自选股代码 |

---

#### 4. 可选配置（如需要）

| Secret 名称 | 值 | 说明 |
|------------|---|------|
| `REPORT_TYPE` | `full` | 报告类型 |
| `ANALYSIS_DELAY` | `10` | 分析间隔 |
| `TAVILY_API_KEYS` | 你的 Key | 搜索 API（推荐） |
| `GEMINI_API_KEY` | 你的 Key | Gemini 备用 |

---

### 第3步：验证 Secrets 配置

配置完成后，你会看到类似这样的列表：

```
Repository secrets
├─ OPENAI_API_KEY          Updated 2 minutes ago
├─ OPENAI_BASE_URL         Updated 2 minutes ago
├─ OPENAI_MODEL            Updated 2 minutes ago
├─ FEISHU_WEBHOOK_URL      Updated 2 minutes ago
├─ FEISHU_WEBHOOK_SECRET   Updated 2 minutes ago
└─ STOCK_LIST              Updated 2 minutes ago
```

**注意**：
- ✅ Secret 的值永远不会显示（安全）
- ✅ 只能更新或删除
- ✅ 在 Actions 日志中自动脱敏（显示为 `***`）

---

### 第4步：启用 GitHub Actions

1. 进入你的仓库
2. 点击顶部 **Actions** 标签
3. 如果看到提示，点击 **"I understand my workflows, go ahead and enable them"**

---

### 第5步：手动测试运行

1. 进入 **Actions** 标签
2. 左侧选择 **"每日股票分析"**
3. 右侧点击 **"Run workflow"** 下拉按钮
4. 选择运行模式（推荐 `full`）
5. 点击绿色的 **"Run workflow"** 确认

等待 3-5 分钟，查看：
- ✅ Actions 执行日志
- ✅ 飞书群消息

---

## 🔍 查看 Secrets 在 Actions 中的使用

打开 `.github/workflows/daily_analysis.yml` 文件，你会看到：

```yaml
- name: 执行股票分析
  env:
    # AI 配置 - 从 Secrets 读取
    OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
    OPENAI_BASE_URL: ${{ vars.OPENAI_BASE_URL || secrets.OPENAI_BASE_URL }}
    OPENAI_MODEL: ${{ vars.OPENAI_MODEL || secrets.OPENAI_MODEL }}
    
    # 飞书配置 - 从 Secrets 读取
    FEISHU_WEBHOOK_URL: ${{ secrets.FEISHU_WEBHOOK_URL }}
    
    # 股票列表 - 从 Secrets 读取
    STOCK_LIST: ${{ vars.STOCK_LIST || secrets.STOCK_LIST || '600519' }}
    
  run: |
    python main.py
```

**语法说明**：
- `${{ secrets.OPENAI_API_KEY }}` - 读取 Secret
- `${{ vars.STOCK_LIST || secrets.STOCK_LIST }}` - 优先读取 Variables，没有则读取 Secrets

---

## 📊 Secrets vs Variables 对比

| 类型 | 用途 | 可见性 | 示例 |
|-----|------|-------|------|
| **Secrets** | 敏感信息 | 完全隐藏 | API Key, Webhook URL |
| **Variables** | 公开配置 | 可查看 | 模型名称, 报告类型 |

**推荐做法**：
- 🔐 敏感信息 → Secrets（API Key、Webhook）
- 📝 普通配置 → Variables 或直接硬编码（模型名称）

---

## 🎯 完整配置检查清单

### 必填项（6个）
- [ ] `OPENAI_API_KEY` - DeepSeek API Key
- [ ] `OPENAI_BASE_URL` - DeepSeek API 地址
- [ ] `OPENAI_MODEL` - 模型名称
- [ ] `FEISHU_WEBHOOK_URL` - 飞书 Webhook
- [ ] `FEISHU_WEBHOOK_SECRET` - 飞书签名密钥
- [ ] `STOCK_LIST` - 股票代码列表

### 可选项
- [ ] `REPORT_TYPE` - 报告类型（推荐 `full`）
- [ ] `ANALYSIS_DELAY` - 分析间隔
- [ ] `TAVILY_API_KEYS` - 搜索 API（强烈推荐）
- [ ] `GEMINI_API_KEY` - Gemini 备用

---

## 🔧 常见问题

### Q1: 配置 Secret 后，Actions 还是失败？
**A**: 检查几点：
1. Secret 名称是否完全一致（区分大小写）
2. Secret 值是否完整（没有多余空格）
3. 查看 Actions 日志确认错误原因

### Q2: 如何更新 Secret？
**A**: 
```
Settings → Secrets and variables → Actions → 点击 Secret 名称 → Update secret
```

### Q3: Secret 值显示为 `***`，是正常的吗？
**A**: ✅ 是的！这是 GitHub 的安全保护机制。

### Q4: 忘记配置了哪些 Secret 怎么办？
**A**: 查看 `.github/workflows/daily_analysis.yml` 文件的 `env:` 部分。

### Q5: 本地 .env 和 GitHub Secrets 要同步吗？
**A**: 
- 本地 .env：本地测试用
- GitHub Secrets：云端运行用
- 两者内容相同，但存储位置不同

---

## 🎉 配置完成后

### 自动执行
- ⏰ 每周一到周五 18:00（北京时间）
- 🤖 GitHub Actions 自动运行
- 📱 分析完成后推送到飞书

### 手动执行
- 进入 Actions 页面
- 点击 "Run workflow"
- 随时触发分析

---

## 📚 相关文档

- [GitHub Secrets 官方文档](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [项目配置指南](./docs/full-guide.md)
- [快速开始](./快速开始.md)

---

## 🎯 快速配置命令（复制粘贴版）

打开你的 .env 文件，复制以下值到 GitHub Secrets：

```bash
# 从 .env 提取的值（替换成你的实际值）

# 1. OPENAI_API_KEY
sk-bf0c1ee9fb4c46cc8c9ea62a14d03a21

# 2. OPENAI_BASE_URL
https://api.deepseek.com/v1

# 3. OPENAI_MODEL
deepseek-chat

# 4. FEISHU_WEBHOOK_URL
https://open.feishu.cn/open-apis/bot/v2/hook/79791f9f-d027-46e5-98fe-b6bc8a3b3c51

# 5. FEISHU_WEBHOOK_SECRET
Gf55G2oRdxXqMtULRAGBY

# 6. STOCK_LIST
159636,159740,159928,588920,516270,159525,512980
```

---

**配置完成后，GitHub Actions 就能读取这些配置，定时推送分析报告了！** 🎉

有任何问题，查看 Actions 运行日志就能找到原因。
