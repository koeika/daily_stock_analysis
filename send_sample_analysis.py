#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
发送股票分析样例消息到飞书
"""
import os
import time
import hmac
import hashlib
import base64
from datetime import datetime

try:
    import requests
    from dotenv import load_dotenv
    load_dotenv()
except ImportError as e:
    print(f"❌ 缺少依赖: {e}")
    exit(1)


def send_stock_analysis_sample():
    """发送股票分析样例消息"""
    webhook_url = os.getenv('FEISHU_WEBHOOK_URL')
    secret = os.getenv('FEISHU_WEBHOOK_SECRET', '')
    
    if not webhook_url:
        print("❌ 未配置 FEISHU_WEBHOOK_URL")
        return False
    
    # 构建股票分析样例消息
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    message = f"""# 🎯 2026-02-13 决策仪表盘

共分析 **7只ETF** | 🟢买入:2 🟡观望:4 🔴卖出:1

---

## 📊 分析结果摘要

⚪ **港科技30 (159636)**: 观望 | 评分 68 | 看多
⚪ **恒生科技 (159740)**: 观望 | 评分 65 | 震荡  
🟢 **消费ETF (159928)**: 买入 | 评分 75 | 看多
⚪ **KC芯片 (588920)**: 观望 | 评分 62 | 震荡
🟢 **新能源50 (516270)**: 买入 | 评分 72 | 看多
⚪ **红利低波 (159525)**: 观望 | 评分 70 | 看多
🔴 **传媒ETF (512980)**: 卖出 | 评分 45 | 看空

---

## 📈 重点关注

### 🟢 消费ETF (159928)
**建议**: 买入 | **评分**: 75分

**📰 重要信息**
- 💭 舆情情绪: 市场对消费板块预期改善
- 📊 业绩预期: 基本面逐步回暖

**🎯 操作建议**
- 买入价: ¥2.850
- 止损价: ¥2.750
- 目标价: ¥3.050

**✨ 利好催化**
1. 政策支持消费复苏
2. 估值处于历史低位
3. 成交量温和放大

---

### 🟢 新能源50 (516270)  
**建议**: 买入 | **评分**: 72分

**📰 重要信息**
- 💭 舆情情绪: 新能源板块持续活跃
- 📊 业绩预期: 行业景气度上升

**🎯 操作建议**
- 买入价: ¥0.685
- 止损价: ¥0.660
- 目标价: ¥0.730

**✨ 利好催化**
1. 行业政策利好不断
2. 技术创新加速
3. 出口数据向好

---

## ⚠️ 风险提示

### 🔴 传媒ETF (512980)
**建议**: 卖出 | **评分**: 45分

**🚨 风险警报**
1. 技术面破位,跌破关键支撑
2. 成交量萎缩,多头动能不足
3. 板块整体表现疲软

**建议操作**: 逢高减仓,等待企稳信号

---

## 📊 市场概况

**主要指数**
- 上证指数: 3250.12 (🟢+0.85%)
- 深证成指: 10521.36 (🟢+1.02%)  
- 创业板指: 2156.78 (🟢+1.35%)

**板块表现**
- 🔥 领涨: 消费、新能源、科技
- 📉 领跌: 传媒、地产、金融

---

**生成时间**: {current_time}
**系统**: A股自选股智能分析系统 v1.0
**免责声明**: 本分析仅供参考,不构成投资建议,股市有风险,投资需谨慎。
"""

    # 构建飞书卡片
    payload = {
        "msg_type": "interactive",
        "card": {
            "config": {"wide_screen_mode": True},
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": "📊 A股智能分析 - 每日决策仪表盘"
                },
                "template": "blue"
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": message
                    }
                }
            ]
        }
    }
    
    # 添加签名
    if secret:
        timestamp = str(round(time.time()))
        key = f"{timestamp}\n{secret}".encode('utf-8')
        msg = "".encode('utf-8')
        hmac_code = hmac.new(key, msg, digestmod=hashlib.sha256).digest()
        sign = base64.b64encode(hmac_code).decode('utf-8')
        
        payload['timestamp'] = timestamp
        payload['sign'] = sign
    
    # 发送消息
    try:
        print("正在发送股票分析样例消息到飞书...")
        response = requests.post(webhook_url, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            code = result.get('code', result.get('StatusCode'))
            
            if code == 0:
                print("✅ 股票分析样例消息发送成功!")
                print("\n请到飞书群查看完整的分析报告展示效果")
                return True
            else:
                error_msg = result.get('msg', result.get('StatusMessage', '未知错误'))
                print(f"❌ 发送失败: {error_msg}")
                return False
        else:
            print(f"❌ HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 发送异常: {e}")
        return False


if __name__ == "__main__":
    print("=" * 70)
    print("发送股票分析样例消息到飞书")
    print("=" * 70)
    print()
    
    success = send_stock_analysis_sample()
    
    if success:
        print("\n" + "=" * 70)
        print("✅ 样例消息发送成功!")
        print("=" * 70)
        print("\n这就是每天股票分析完成后,推送到飞书的消息格式")
        print("包含:")
        print("  - 决策仪表盘总览")
        print("  - 每只股票的详细分析")
        print("  - 买卖建议和具体点位")
        print("  - 风险提示")
        print("  - 市场概况")
        print("\n现在你可以运行完整分析: python3 main.py")
