# ✅ GitHub Actions 配置清单

## 📋 5分钟完成配置

按照这个清单，逐步完成 GitHub Actions 配置。

---

## Step 1: Fork 仓库 (1分钟)

- [ ] 访问 https://github.com/ZhuLinsen/daily_stock_analysis
- [ ] 点击右上角 **Fork** 按钮
- [ ] 选择你的 GitHub 账号
- [ ] 等待 Fork 完成

---

## Step 2: 配置 Secrets (3分钟)

### 进入配置页面

- [ ] 进入你 Fork 的仓库
- [ ] 点击 **Settings** (设置)
- [ ] 左侧菜单点击 **Secrets and variables**
- [ ] 点击 **Actions**
- [ ] 点击 **New repository secret**

### 添加 6 个必填 Secrets

打开你本地的 `.env` 文件，复制对应的值：

#### 1. AI 配置 (3个)

- [ ] **Name**: `OPENAI_API_KEY`
  - **Secret**: 从 .env 复制 `OPENAI_API_KEY=` 后面的值
  - 示例: `sk-bf0c1ee9fb4c46cc8c9ea62a14d03a21`
  - 点击 **Add secret**

- [ ] **Name**: `OPENAI_BASE_URL`
  - **Secret**: 从 .env 复制 `OPENAI_BASE_URL=` 后面的值
  - 示例: `https://api.deepseek.com/v1`
  - 点击 **Add secret**

- [ ] **Name**: `OPENAI_MODEL`
  - **Secret**: 从 .env 复制 `OPENAI_MODEL=` 后面的值
  - 示例: `deepseek-chat`
  - 点击 **Add secret**

#### 2. 飞书配置 (2个)

- [ ] **Name**: `FEISHU_WEBHOOK_URL`
  - **Secret**: 从 .env 复制 `FEISHU_WEBHOOK_URL=` 后面的值
  - 示例: `https://open.feishu.cn/open-apis/bot/v2/hook/79791f9f-d027-46e5-98fe-b6bc8a3b3c51`
  - ⚠️ 注意：完整复制，包括 `https://`
  - 点击 **Add secret**

- [ ] **Name**: `FEISHU_WEBHOOK_SECRET`
  - **Secret**: 从 .env 复制 `FEISHU_WEBHOOK_SECRET=` 后面的值
  - 示例: `Gf55G2oRdxXqMtULRAGBY`
  - 点击 **Add secret**

#### 3. 股票列表 (1个)

- [ ] **Name**: `STOCK_LIST`
  - **Secret**: 从 .env 复制 `STOCK_LIST=` 后面的值
  - 示例: `159636,159740,159928,588920,516270,159525,512980`
  - 点击 **Add secret**

### 验证配置

- [ ] 确认看到 6 个 Secrets:
  - ✅ OPENAI_API_KEY
  - ✅ OPENAI_BASE_URL
  - ✅ OPENAI_MODEL
  - ✅ FEISHU_WEBHOOK_URL
  - ✅ FEISHU_WEBHOOK_SECRET
  - ✅ STOCK_LIST

---

## Step 3: 启用 Actions (30秒)

- [ ] 点击仓库顶部的 **Actions** 标签
- [ ] 如果看到提示，点击 **"I understand my workflows, go ahead and enable them"**
- [ ] 确认看到 "每日股票分析" workflow

---

## Step 4: 测试运行 (30秒 + 等待3-5分钟)

- [ ] 在 **Actions** 页面
- [ ] 左侧选择 **"每日股票分析"**
- [ ] 右侧点击 **"Run workflow"** 下拉按钮
- [ ] 运行模式选择 **full**
- [ ] 点击绿色的 **"Run workflow"** 按钮
- [ ] 刷新页面，看到新的运行任务

### 等待执行

- [ ] 点击新出现的运行任务
- [ ] 查看执行日志
- [ ] 等待 3-5 分钟
- [ ] 执行完成后，查看飞书群消息

---

## ✅ 配置完成！

如果一切正常：
- ✅ Actions 执行成功（绿色✓）
- ✅ 飞书收到分析报告
- ✅ 每周一到五 18:00 自动执行

---

## ⚠️ 常见问题排查

### 问题1: Actions 执行失败

**检查步骤**：
1. [ ] 点击失败的任务，查看日志
2. [ ] 搜索 "error" 关键词
3. [ ] 常见错误：
   - `OPENAI_API_KEY not found` → 检查 Secret 名称是否正确
   - `Invalid API key` → 检查 Secret 值是否正确
   - `Failed to send message` → 检查 Webhook URL

### 问题2: 飞书没收到消息

**检查步骤**：
1. [ ] 确认 Actions 执行成功
2. [ ] 查看日志中的 "飞书" 相关信息
3. [ ] 确认 `FEISHU_WEBHOOK_URL` 配置正确
4. [ ] 确认机器人已添加到飞书群

### 问题3: 分析结果不符合预期

**检查步骤**：
1. [ ] 确认 `STOCK_LIST` 配置正确
2. [ ] 检查是否有逗号分隔
3. [ ] 确认股票代码格式正确

---

## 📊 可选配置（提升体验）

### 配置报告类型

- [ ] **Name**: `REPORT_TYPE`
  - **Secret**: `full`
  - 说明: 完整报告格式，推荐飞书使用

### 配置搜索 API（强烈推荐）

- [ ] **Name**: `TAVILY_API_KEYS`
  - **Secret**: 你的 Tavily API Key
  - 说明: 获取最新新闻和舆情
  - 申请: https://tavily.com/

---

## 🎯 下一步

### 修改执行时间

如果想修改定时执行时间（默认 18:00）：

1. [ ] 编辑 `.github/workflows/daily_analysis.yml`
2. [ ] 修改这一行：
   ```yaml
   - cron: '0 10 * * 1-5'  # UTC 10:00 = 北京 18:00
   ```
3. [ ] 常用时间对照：
   - 09:30 → `'30 1 * * 1-5'`
   - 15:00 → `'0 7 * * 1-5'`
   - 18:00 → `'0 10 * * 1-5'`
   - 21:00 → `'0 13 * * 1-5'`

### 添加更多通知渠道

支持同时推送到多个渠道：

- [ ] 企业微信: `WECHAT_WEBHOOK_URL`
- [ ] Telegram: `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID`
- [ ] 邮件: `EMAIL_SENDER` + `EMAIL_PASSWORD`

---

## 📚 相关文档

- [ ] [GitHub-Secrets配置指南.md](./GitHub-Secrets配置指南.md) - 详细说明
- [ ] [Secrets工作原理图解.md](./Secrets工作原理图解.md) - 原理图解
- [ ] [快速开始.md](./快速开始.md) - 快速上手

---

## 🎉 完成状态

### 必做项
- [ ] Fork 仓库
- [ ] 配置 6 个 Secrets
- [ ] 启用 Actions
- [ ] 测试运行成功
- [ ] 飞书收到消息

### 可选项
- [ ] 配置 REPORT_TYPE
- [ ] 配置搜索 API
- [ ] 修改执行时间
- [ ] 添加其他通知渠道

---

**全部完成后，你的股票分析系统就能自动运行了！** 🎉

每周一到五 18:00，自动分析并推送到飞书，完全不需要本地运行。

有问题查看日志，或参考详细文档。
