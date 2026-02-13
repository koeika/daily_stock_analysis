#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
精简版报告推送脚本（独立运行，无需项目依赖）

功能：
1. 自动精简超长报告（移除详细数据表格、压缩内容）
2. 智能推送到飞书（自动分批、自动签名）
3. 支持批量推送多个报告

用法:
    python3 simple_push_feishu.py <report_file1> [report_file2] ...
    
环境变量:
    FEISHU_WEBHOOK_URL: 飞书 Webhook URL（必需）
    FEISHU_WEBHOOK_SECRET: 飞书 Webhook Secret（可选）
    AUTO_COMPACT: 是否自动精简 true/false（默认 true）
"""

import sys
import os
import logging
import time
import hmac
import hashlib
import json
import re
from datetime import datetime

import requests

# 尝试加载 .env 文件
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def read_report_file(file_path: str) -> str:
    """读取报告文件内容"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        content_bytes = len(content.encode('utf-8'))
        logger.info(f"读取报告: {file_path} ({len(content)} 字符, {content_bytes} 字节)")
        return content
    except Exception as e:
        logger.error(f"读取失败 {file_path}: {e}")
        raise


def should_compact(content: str, threshold: int = 20000) -> bool:
    """判断是否需要精简"""
    auto_compact = os.getenv('AUTO_COMPACT', 'true').lower() == 'true'
    if not auto_compact:
        return False
    
    content_bytes = len(content.encode('utf-8'))
    return content_bytes > threshold


def compact_report(content: str) -> str:
    """
    精简报告内容
    
    优化策略：
    1. 移除详细的数据透视表格（保留关键指标）
    2. 精简当日行情表格（只保留核心数据）
    3. 压缩重要信息板块（只保留风险和利好）
    4. 移除多余的空行和分隔线
    5. 精简检查清单（只显示未通过项）
    """
    lines = content.split('\n')
    result = []
    skip_mode = None
    
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # ===== 移除数据透视板块 =====
        if '### 📊 数据透视' in line:
            # 跳过整个数据透视板块
            i += 1
            while i < len(lines):
                if lines[i].strip().startswith('###') and '📊' not in lines[i]:
                    break
                i += 1
            continue
        
        # ===== 精简当日行情表格 =====
        if '### 📈 当日行情' in line:
            # 跳过标题
            i += 1
            # 查找表格并提取关键数据
            while i < len(lines):
                if lines[i].strip().startswith('|') and '收盘' in lines[i]:
                    # 找到数据行（表头后2行）
                    if i + 2 < len(lines):
                        data_row = lines[i + 2]
                        parts = [p.strip() for p in data_row.split('|')]
                        if len(parts) >= 7:
                            # 格式：收盘价 | 涨跌幅 | 最高 | 最低
                            result.append(f"📈 **当日**: {parts[1]}元 | 涨跌{parts[6]} | 高{parts[4]} 低{parts[5]}")
                            result.append("")
                    break
                if lines[i].strip().startswith('###'):
                    break
                i += 1
            # 跳过当日行情后续内容
            while i < len(lines) and not lines[i].strip().startswith('###'):
                i += 1
            continue
        
        # ===== 精简重要信息速览 =====
        if '### 📰 重要信息速览' in line:
            result.append(line)
            result.append("")
            i += 1
            # 只保留风险和利好（各最多2条）
            risk_count = 0
            catalyst_count = 0
            while i < len(lines):
                if lines[i].strip().startswith('###'):
                    break
                
                # 保留风险警报
                if '**🚨 风险警报**' in lines[i]:
                    result.append(lines[i])
                    i += 1
                    while i < len(lines) and lines[i].strip().startswith('-') and risk_count < 2:
                        result.append(lines[i])
                        risk_count += 1
                        i += 1
                    result.append("")
                    continue
                
                # 保留利好催化
                if '**✨ 利好催化**' in lines[i]:
                    result.append(lines[i])
                    i += 1
                    while i < len(lines) and lines[i].strip().startswith('-') and catalyst_count < 2:
                        result.append(lines[i])
                        catalyst_count += 1
                        i += 1
                    result.append("")
                    continue
                
                i += 1
            continue
        
        # ===== 精简检查清单（只保留未通过项）=====
        if '**✅ 检查清单**' in line:
            result.append("**检查清单**:")
            result.append("")
            i += 1
            has_failed = False
            while i < len(lines) and lines[i].strip().startswith('-'):
                # 只保留未通过的项目
                if '❌' in lines[i] or '⚠️' in lines[i]:
                    result.append(lines[i])
                    has_failed = True
                i += 1
            if not has_failed:
                result.append("- ✅ 所有检查项通过")
            result.append("")
            continue
        
        # ===== 移除连续的空行（保留单个空行）=====
        if not stripped:
            if result and result[-1].strip():
                result.append(line)
            i += 1
            continue
        
        # ===== 移除多余的分隔线 =====
        if stripped == '---' and result and result[-1].strip() == '---':
            i += 1
            continue
        
        # 保留其他内容
        result.append(line)
        i += 1
    
    compact_content = '\n'.join(result)
    
    # 统计压缩效果
    original_bytes = len(content.encode('utf-8'))
    compact_bytes = len(compact_content.encode('utf-8'))
    reduction = (1 - compact_bytes / original_bytes) * 100 if original_bytes > 0 else 0
    
    logger.info(f"精简完成: {original_bytes} -> {compact_bytes} 字节 (压缩 {reduction:.1f}%)")
    
    return compact_content


def send_feishu_message(webhook_url: str, content: str, secret: str = None) -> bool:
    """发送消息到飞书"""
    import base64
    
    payload = {
        "msg_type": "interactive",
        "card": {
            "config": {"wide_screen_mode": True},
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": "股票分析报告"
                }
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": content
                    }
                }
            ]
        }
    }
    
    # 签名
    if secret:
        timestamp = str(round(time.time()))
        key = f"{timestamp}\n{secret}".encode('utf-8')
        msg = "".encode('utf-8')
        hmac_code = hmac.new(key, msg, digestmod=hashlib.sha256).digest()
        sign = base64.b64encode(hmac_code).decode('utf-8')
        
        payload['timestamp'] = timestamp
        payload['sign'] = sign
    
    try:
        response = requests.post(webhook_url, json=payload, headers={"Content-Type": "application/json"}, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            code = result.get('code') if 'code' in result else result.get('StatusCode')
            if code == 0:
                return True
            else:
                error_msg = result.get('msg') or result.get('StatusMessage', '未知错误')
                logger.error(f"飞书返回错误 [code={code}]: {error_msg}")
                return False
        else:
            logger.error(f"请求失败: HTTP {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"发送异常: {e}")
        return False


def send_feishu_chunked(webhook_url: str, content: str, max_bytes: int = 20000, secret: str = None) -> bool:
    """分批发送长消息到飞书"""
    content_bytes = len(content.encode('utf-8'))
    
    if content_bytes <= max_bytes:
        return send_feishu_message(webhook_url, content, secret)
    
    logger.info(f"消息超长({content_bytes}字节)，将分批发送")
    
    # 按段落分割
    chunks = []
    current_chunk = ""
    current_bytes = 0
    
    paragraphs = content.split('\n\n')
    
    for para in paragraphs:
        para_bytes = len(para.encode('utf-8'))
        
        if current_bytes + para_bytes > max_bytes and current_chunk:
            chunks.append(current_chunk)
            current_chunk = para
            current_bytes = para_bytes
        else:
            if current_chunk:
                current_chunk += '\n\n' + para
            else:
                current_chunk = para
            current_bytes += para_bytes
    
    if current_chunk:
        chunks.append(current_chunk)
    
    total = len(chunks)
    logger.info(f"分 {total} 批发送")
    
    success_count = 0
    for i, chunk in enumerate(chunks):
        chunk_with_marker = f"{chunk}\n\n---\n*第 {i+1}/{total} 部分*"
        
        if send_feishu_message(webhook_url, chunk_with_marker, secret):
            success_count += 1
            logger.info(f"第 {i+1}/{total} 批发送成功")
            if i < total - 1:
                time.sleep(1)
        else:
            logger.error(f"第 {i+1}/{total} 批发送失败")
    
    return success_count == total


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python3 simple_push_feishu.py <report_file1> [report_file2] ...")
        print("\n环境变量:")
        print("  FEISHU_WEBHOOK_URL: 飞书 Webhook URL（必需）")
        print("  FEISHU_WEBHOOK_SECRET: 飞书 Webhook Secret（可选）")
        print("  AUTO_COMPACT: 自动精简 true/false（默认 true）")
        sys.exit(1)
    
    webhook_url = os.getenv('FEISHU_WEBHOOK_URL')
    webhook_secret = os.getenv('FEISHU_WEBHOOK_SECRET')
    
    if not webhook_url:
        logger.error("未配置 FEISHU_WEBHOOK_URL")
        sys.exit(1)
    
    logger.info(f"飞书 Webhook: {webhook_url[:50]}...")
    if webhook_secret:
        logger.info("已配置签名密钥")
    
    report_files = sys.argv[1:]
    success_count = 0
    
    for i, report_file in enumerate(report_files, 1):
        logger.info("=" * 60)
        logger.info(f"推送第 {i}/{len(report_files)} 个报告")
        logger.info("=" * 60)
        
        if not os.path.exists(report_file):
            logger.error(f"文件不存在: {report_file}")
            continue
        
        # 读取报告
        content = read_report_file(report_file)
        
        # 判断是否需要精简
        if should_compact(content):
            logger.info("启用自动精简模式")
            content = compact_report(content)
        
        # 发送
        content_bytes = len(content.encode('utf-8'))
        if content_bytes > 20000:
            success = send_feishu_chunked(webhook_url, content, 20000, webhook_secret)
        else:
            success = send_feishu_message(webhook_url, content, webhook_secret)
        
        if success:
            logger.info(f"✓ 第 {i} 个报告推送成功")
            success_count += 1
        else:
            logger.error(f"✗ 第 {i} 个报告推送失败")
        
        if i < len(report_files):
            time.sleep(2)
    
    logger.info("=" * 60)
    if success_count == len(report_files):
        logger.info(f"✓ 全部成功 ({success_count}/{len(report_files)})")
        sys.exit(0)
    else:
        logger.error(f"✗ 部分失败 ({success_count}/{len(report_files)})")
        sys.exit(1)


if __name__ == '__main__':
    main()
