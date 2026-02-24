#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试修复效果验证脚本
验证MACD和RSI是否正确传递到AI Prompt
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.analyzer import GeminiAnalyzer
from src.stock_analyzer import StockTrendAnalyzer
import pandas as pd
import numpy as np

def test_macd_rsi_in_prompt():
    """测试MACD和RSI是否包含在prompt中"""
    
    print("=" * 60)
    print("🔍 MACD/RSI 修复验证测试")
    print("=" * 60)
    
    # 1. 创建模拟数据
    dates = pd.date_range(start='2025-01-01', periods=60, freq='D')
    np.random.seed(42)
    
    base_price = 10.0
    prices = [base_price]
    volumes = []
    
    for i in range(59):
        change = np.random.randn() * 0.02 + 0.003
        prices.append(prices[-1] * (1 + change))
        volumes.append(np.random.randint(1000000, 5000000))
    
    df = pd.DataFrame({
        'date': dates,
        'open': prices,
        'high': [p * (1 + np.random.uniform(0, 0.02)) for p in prices],
        'low': [p * (1 - np.random.uniform(0, 0.02)) for p in prices],
        'close': prices,
        'volume': volumes + [np.random.randint(1000000, 5000000)],
    })
    
    # 2. 执行趋势分析
    print("\n📊 步骤1: 执行趋势分析...")
    analyzer = StockTrendAnalyzer()
    trend_result = analyzer.analyze(df, '000001')
    
    # 3. 验证MACD和RSI是否计算
    print(f"✅ MACD DIF: {trend_result.macd_dif:.4f}")
    print(f"✅ MACD DEA: {trend_result.macd_dea:.4f}")
    print(f"✅ MACD BAR: {trend_result.macd_bar:.4f}")
    print(f"✅ MACD信号: {trend_result.macd_signal}")
    print(f"✅ MACD状态: {trend_result.macd_status.value}")
    
    print(f"\n✅ RSI(6): {trend_result.rsi_6:.1f}")
    print(f"✅ RSI(12): {trend_result.rsi_12:.1f}")
    print(f"✅ RSI(24): {trend_result.rsi_24:.1f}")
    print(f"✅ RSI信号: {trend_result.rsi_signal}")
    print(f"✅ RSI状态: {trend_result.rsi_status.value}")
    
    # 4. 构建上下文
    print("\n📝 步骤2: 构建AI分析上下文...")
    context = {
        'code': '000001',
        'stock_name': '测试股票',
        'date': '2026-02-24',
        'today': {
            'close': prices[-1],
            'open': prices[-1],
            'high': prices[-1] * 1.01,
            'low': prices[-1] * 0.99,
            'volume': volumes[-1],
            'amount': volumes[-1] * prices[-1],
            'pct_chg': 1.5,
            'ma5': trend_result.ma5,
            'ma10': trend_result.ma10,
            'ma20': trend_result.ma20,
        },
        'trend_analysis': trend_result.to_dict(),
        'ma_status': '多头排列 📈',
    }
    
    # 5. 生成prompt并检查
    print("\n🔍 步骤3: 检查Prompt内容...")
    ai_analyzer = GeminiAnalyzer()
    prompt = ai_analyzer._format_prompt(context, '测试股票', None)
    
    # 验证关键字是否存在
    checks = {
        'MACD指标': 'MACD' in prompt,
        'RSI指标': 'RSI' in prompt or 'rsi' in prompt.lower(),
        'DIF快线': 'DIF' in prompt,
        'DEA慢线': 'DEA' in prompt,
        'MACD柱': 'MACD柱' in prompt,
        'RSI(6)': 'RSI(6)' in prompt or 'rsi_6' in prompt,
        'RSI(12)': 'RSI(12)' in prompt or 'rsi_12' in prompt,
        'RSI(24)': 'RSI(24)' in prompt or 'rsi_24' in prompt,
        'MACD信号解读': 'MACD状态' in prompt or '金叉' in prompt,
        'RSI信号解读': 'RSI状态' in prompt or '超买' in prompt or '超卖' in prompt,
    }
    
    print("\n✅ Prompt内容检查:")
    all_pass = True
    for check_name, result in checks.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {status} - {check_name}")
        if not result:
            all_pass = False
    
    # 6. 显示prompt片段
    if 'MACD' in prompt:
        macd_start = prompt.find('### MACD')
        macd_end = prompt.find('###', macd_start + 10)
        if macd_start != -1:
            print("\n📄 MACD部分预览:")
            print("-" * 60)
            print(prompt[macd_start:macd_end if macd_end != -1 else macd_start+500])
            print("-" * 60)
    
    if 'RSI' in prompt:
        rsi_start = prompt.find('### RSI')
        rsi_end = prompt.find('###', rsi_start + 10)
        if rsi_start != -1:
            print("\n📄 RSI部分预览:")
            print("-" * 60)
            print(prompt[rsi_start:rsi_end if rsi_end != -1 else rsi_start+500])
            print("-" * 60)
    
    # 7. 总结
    print("\n" + "=" * 60)
    if all_pass:
        print("✅ 修复验证通过! MACD和RSI已成功传递到AI Prompt")
    else:
        print("❌ 修复验证失败! 部分指标未传递")
    print("=" * 60)
    
    return all_pass

def test_volume_zero_warning():
    """测试成交量为0的警告"""
    print("\n" + "=" * 60)
    print("🔍 成交量为0警告测试")
    print("=" * 60)
    
    ai_analyzer = GeminiAnalyzer()
    
    # 测试1: 成交量为0
    context1 = {
        'code': '159928',
        'stock_name': '消费ETF',
        'date': '2026-02-24',
        'today': {
            'close': 0.77,
            'open': 0.77,
            'high': 0.77,
            'low': 0.77,
            'volume': 0,
            'amount': 0,
            'pct_chg': -0.3,
            'ma5': 0.79,
            'ma10': 0.79,
            'ma20': 0.78,
        },
        'ma_status': '震荡',
    }
    
    prompt1 = ai_analyzer._format_prompt(context1, '消费ETF', None)
    
    has_warning = '今日成交量为零' in prompt1 or '数据异常' in prompt1 or '无法判断真实量能' in prompt1
    
    if has_warning:
        print("✅ 成交量为0警告已添加")
        # 找到警告位置并显示
        warning_start = max(prompt1.find('今日成交量'), prompt1.find('数据异常'))
        if warning_start != -1:
            print("\n📄 警告内容:")
            print("-" * 60)
            print(prompt1[warning_start:warning_start+200])
            print("-" * 60)
    else:
        print("❌ 未找到成交量为0的警告")
    
    print("\n" + "=" * 60)
    return has_warning

if __name__ == '__main__':
    result1 = test_macd_rsi_in_prompt()
    result2 = test_volume_zero_warning()
    
    print("\n" + "=" * 60)
    print("📊 最终测试结果")
    print("=" * 60)
    print(f"MACD/RSI传递: {'✅ 通过' if result1 else '❌ 失败'}")
    print(f"成交量警告: {'✅ 通过' if result2 else '❌ 失败'}")
    
    if result1 and result2:
        print("\n🎉 所有测试通过! 修复成功!")
        sys.exit(0)
    else:
        print("\n⚠️ 部分测试失败,请检查代码")
        sys.exit(1)
