# 🔐 GitHub Secrets 工作原理图解

## 📋 问题：.env 在 gitignore 中，GitHub 怎么获取配置？

---

## ✅ 答案：使用 GitHub Secrets

```
┌─────────────────────────────────────────────────────────────────────┐
│                      本地开发环境                                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  📁 项目文件                                                          │
│  ├── main.py                                                         │
│  ├── src/                                                            │
│  ├── .env  ← 包含敏感信息（API Key、Webhook等）                       │
│  └── .gitignore  ← 忽略 .env，不提交到 Git                           │
│                                                                      │
│  🚫 .env 文件不会被提交到 GitHub！                                    │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
                    git push（不包含 .env）
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      GitHub 仓库                                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  📁 代码仓库（公开或私有）                                             │
│  ├── main.py           ✅                                            │
│  ├── src/              ✅                                            │
│  ├── .env              ❌ 不在仓库中                                  │
│  └── .gitignore        ✅                                            │
│                                                                      │
│  ⚠️  如果 .env 被提交，任何人都能看到你的密钥！                        │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
                              +
┌─────────────────────────────────────────────────────────────────────┐
│                   GitHub Secrets（加密存储）                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  🔐 Settings → Secrets and variables → Actions                      │
│                                                                      │
│  ┌────────────────────────────────────────────────────┐             │
│  │ OPENAI_API_KEY          sk-bf0c1ee...  [Update]  │             │
│  │ OPENAI_BASE_URL         https://api... [Update]  │             │
│  │ FEISHU_WEBHOOK_URL      https://ope... [Update]  │             │
│  │ STOCK_LIST              159636,1597...  [Update]  │             │
│  └────────────────────────────────────────────────────┘             │
│                                                                      │
│  ✅ 加密存储，只有你和 Actions 能访问                                  │
│  ✅ 在日志中显示为 ***                                                │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
                    定时触发或手动触发
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    GitHub Actions 运行时                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  🤖 Ubuntu 虚拟机（临时创建）                                          │
│                                                                      │
│  1️⃣ 检出代码（git clone）                                            │
│     ├── main.py                                                      │
│     ├── src/                                                         │
│     └── .github/workflows/daily_analysis.yml                        │
│                                                                      │
│  2️⃣ 注入环境变量（从 Secrets 读取）                                   │
│     env:                                                             │
│       OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}                │
│       FEISHU_WEBHOOK_URL: ${{ secrets.FEISHU_WEBHOOK_URL }}        │
│       STOCK_LIST: ${{ secrets.STOCK_LIST }}                         │
│       ↓                                                              │
│     实际注入为：                                                       │
│       OPENAI_API_KEY=sk-bf0c1ee...                                  │
│       FEISHU_WEBHOOK_URL=https://open.feishu...                     │
│       STOCK_LIST=159636,159740,...                                  │
│                                                                      │
│  3️⃣ 运行程序                                                          │
│     python main.py                                                   │
│     ↓                                                                │
│     程序读取环境变量（就像读取本地 .env 一样）                          │
│     ├── 使用 OPENAI_API_KEY 调用 AI                                  │
│     ├── 分析 STOCK_LIST 中的股票                                      │
│     └── 推送到 FEISHU_WEBHOOK_URL                                    │
│                                                                      │
│  4️⃣ 推送结果                                                          │
│     HTTP POST → 飞书 Webhook                                         │
│     ↓                                                                │
│     📱 你在飞书收到消息                                                │
│                                                                      │
│  5️⃣ 清理环境                                                          │
│     虚拟机销毁，所有数据清除                                            │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 完整流程图

```
你的本地电脑                 GitHub 仓库              GitHub Actions
─────────────────────────────────────────────────────────────────────

    .env 文件                                        
    (敏感信息)               
         │                   
         │ 不提交             
         ↓                   
    .gitignore              
         │                   
         │ git push          
         ↓                   
                           ┌─────────────┐
                           │  代码仓库    │
                           │  (无 .env)  │
                           └─────────────┘
                                  │
    手动配置                       │
         │                        │
         ↓                        │
    ┌──────────────┐             │
    │GitHub Secrets│             │
    │  (加密存储)   │             │
    └──────────────┘             │
         │                        │
         │                        │
         └────────┬───────────────┘
                  │ 定时触发 18:00
                  ↓
           ┌──────────────┐
           │GitHub Actions│
           │  虚拟机创建   │
           └──────────────┘
                  │
                  ↓
           ┌──────────────┐
           │ 1.检出代码    │
           └──────────────┘
                  │
                  ↓
           ┌──────────────┐
           │ 2.注入Secrets │  ← 从 Secrets 读取配置
           │   作为环境变量 │
           └──────────────┘
                  │
                  ↓
           ┌──────────────┐
           │ 3.运行程序    │
           │ python main.py│
           └──────────────┘
                  │
                  ↓
           ┌──────────────┐
           │ 4.推送到飞书  │  → 📱 你收到消息
           └──────────────┘
                  │
                  ↓
           ┌──────────────┐
           │ 5.清理环境    │
           └──────────────┘
```

---

## 🔍 详细对比：本地 vs GitHub

### 本地运行

```bash
# 1. 读取 .env 文件
# 程序启动时，python-dotenv 加载 .env

# 2. 环境变量可用
OPENAI_API_KEY=sk-bf0c1ee...
FEISHU_WEBHOOK_URL=https://...
STOCK_LIST=159636,159740,...

# 3. 程序使用这些变量
python main.py
```

### GitHub Actions 运行

```yaml
# 1. 在 workflow 中声明环境变量
env:
  OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
  FEISHU_WEBHOOK_URL: ${{ secrets.FEISHU_WEBHOOK_URL }}
  STOCK_LIST: ${{ secrets.STOCK_LIST }}

# 2. Actions 注入这些变量
# （运行时替换 ${{ secrets.XXX }} 为实际值）

# 3. 程序使用这些变量（完全相同）
python main.py
```

**结论**：对程序来说，两种方式完全一样！

---

## 🛡️ 安全对比

### ❌ 如果 .env 被提交到 GitHub

```
你的仓库（公开）
├── main.py
├── .env  ← 所有人都能看到！
│   ├── OPENAI_API_KEY=sk-bf0c1ee...  🚨 泄露！
│   ├── FEISHU_WEBHOOK_URL=https://... 🚨 泄露！
│   └── STOCK_LIST=159636...           ⚠️ 无所谓

危险：
🚨 API Key 被滥用，产生费用
🚨 Webhook 被刷屏
🚨 个人信息泄露
```

### ✅ 使用 GitHub Secrets

```
你的仓库（公开）
├── main.py
├── .gitignore  ← 忽略 .env
└── （没有 .env）

GitHub Secrets（私密）
├── OPENAI_API_KEY     🔒 加密存储
├── FEISHU_WEBHOOK_URL 🔒 加密存储
└── STOCK_LIST         🔒 加密存储

安全：
✅ 只有你能看到
✅ Actions 运行时注入
✅ 日志中显示为 ***
```

---

## 📋 配置步骤速查

### Step 1: Fork 仓库
```
https://github.com/ZhuLinsen/daily_stock_analysis
↓ 点击 Fork
https://github.com/你的用户名/daily_stock_analysis
```

### Step 2: 添加 Secrets
```
你的仓库 → Settings → Secrets and variables → Actions
↓
点击 "New repository secret"
↓
Name: OPENAI_API_KEY
Secret: sk-bf0c1ee9fb4c46cc...
↓
点击 "Add secret"
↓
重复添加其他 Secrets
```

### Step 3: 启用 Actions
```
Actions → Enable workflows
```

### Step 4: 测试运行
```
Actions → 每日股票分析 → Run workflow
```

---

## 🎯 需要配置的 Secrets（从你的 .env 复制）

```
┌─────────────────────┬──────────────────────────────────────┐
│ Secret 名称          │ 值（从 .env 复制）                    │
├─────────────────────┼──────────────────────────────────────┤
│ OPENAI_API_KEY      │ sk-bf0c1ee9fb4c46cc8c9ea62a14d03a21  │
│ OPENAI_BASE_URL     │ https://api.deepseek.com/v1          │
│ OPENAI_MODEL        │ deepseek-chat                        │
│ FEISHU_WEBHOOK_URL  │ https://open.feishu.cn/open-apis/... │
│ FEISHU_WEBHOOK_...  │ Gf55G2oRdxXqMtULRAGBY                │
│ STOCK_LIST          │ 159636,159740,159928,588920,...      │
└─────────────────────┴──────────────────────────────────────┘
```

---

## ❓ 常见疑问

### Q: 为什么不直接在代码里写死？
```python
# ❌ 不要这样做
OPENAI_API_KEY = "sk-bf0c1ee..."  # 提交到 GitHub，泄露！
```

### Q: Secrets 和 .env 有什么区别？
```
.env            → 本地文件，用于本地开发
GitHub Secrets  → GitHub 加密存储，用于 Actions
```

### Q: 如何验证 Secrets 配置正确？
```
Actions → 查看运行日志
如果配置错误，会显示 "OPENAI_API_KEY not found"
```

### Q: 可以只配置部分 Secrets 吗？
```
✅ 可以！未配置的会使用默认值
但 API Key 和 Webhook 必须配置
```

---

## 🎉 配置完成效果

```
每周一到周五 18:00
    ↓
GitHub Actions 自动触发
    ↓
读取 Secrets 配置
    ↓
分析股票（使用你的 STOCK_LIST）
    ↓
推送到飞书（使用你的 WEBHOOK）
    ↓
📱 你收到分析报告！
```

---

**总结**：GitHub Secrets 是 .env 的云端替代品，专为 CI/CD 设计，既安全又方便！

查看详细配置步骤：[GitHub-Secrets配置指南.md](./GitHub-Secrets配置指南.md)
