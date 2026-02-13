#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
推送报告到飞书 Webhook

用法:
    python3 push_reports_to_feishu.py <report_file1> <report_file2>
    
环境变量:
    FEISHU_WEBHOOK_URL: 飞书 Webhook URL（必需）
    FEISHU_WEBHOOK_SECRET: 飞书 Webhook Secret（可选，用于签名验证）
"""

import sys
import os
import logging
import time
import hmac
import hashlib
import json
from pathlib import Path
from datetime import datetime

import requests

# 尝试加载 .env 文件
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv 不可用时跳过

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def read_report_file(file_path: str) -> str:
    """读取报告文件内容"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        logger.info(f"成功读取报告文件: {file_path} ({len(content)} 字符)")
        return content
    except Exception as e:
        logger.error(f"读取报告文件失败 {file_path}: {e}")
        raise


def format_feishu_markdown(content: str) -> str:
    """
    格式化 Markdown 内容为飞书支持的格式
    
    飞书 lark_md 格式支持基本的 Markdown，但有一些限制
    """
    # 飞书支持基本的 Markdown，但表格可能需要特殊处理
    # 这里先简单返回原内容，飞书会自动处理
    return content


def send_feishu_message(webhook_url: str, content: str, secret: str = None) -> bool:
    """
    发送消息到飞书 Webhook
    
    Args:
        webhook_url: 飞书 Webhook URL
        content: 消息内容（Markdown 格式）
        secret: Webhook Secret（可选，用于签名验证）
    
    Returns:
        是否发送成功
    """
    import base64
    
    # 格式化内容
    formatted_content = format_feishu_markdown(content)
    
    # 1) 优先使用交互卡片（支持 Markdown 渲染）
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
                        "content": formatted_content
                    }
                }
            ]
        }
    }
    
    # 如果有 Secret，需要添加签名（签名放在 payload 中）
    if secret:
        timestamp = str(round(time.time()))
        # 飞书签名算法：HMAC-SHA256(key=timestamp+"\n"+secret, msg="")
        key = f"{timestamp}\n{secret}".encode('utf-8')
        msg = "".encode('utf-8')
        hmac_code = hmac.new(key, msg, digestmod=hashlib.sha256).digest()
        sign = base64.b64encode(hmac_code).decode('utf-8')
        
        payload['timestamp'] = timestamp
        payload['sign'] = sign
        
        logger.debug(f"飞书签名: timestamp={timestamp}, sign={sign[:20]}...")
    
    try:
        response = requests.post(
            webhook_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        logger.debug(f"飞书响应状态码: {response.status_code}")
        logger.debug(f"飞书响应内容: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            code = result.get('code') if 'code' in result else result.get('StatusCode')
            if code == 0:
                logger.info("飞书消息发送成功")
                return True
            else:
                error_msg = result.get('msg') or result.get('StatusMessage', '未知错误')
                error_code = result.get('code') or result.get('StatusCode', 'N/A')
                logger.error(f"飞书返回错误 [code={error_code}]: {error_msg}")
                logger.error(f"完整响应: {result}")
                return False
        else:
            logger.error(f"飞书请求失败: HTTP {response.status_code}")
            logger.error(f"响应内容: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"发送飞书消息异常: {e}")
        return False


def send_feishu_chunked(webhook_url: str, content: str, max_bytes: int = 20000, secret: str = None) -> bool:
    """
    分批发送长消息到飞书
    
    Args:
        webhook_url: 飞书 Webhook URL
        content: 消息内容
        max_bytes: 每批最大字节数（默认 20000）
        secret: Webhook Secret
    
    Returns:
        是否全部发送成功
    """
    content_bytes = len(content.encode('utf-8'))
    
    if content_bytes <= max_bytes:
        # 单次发送
        return send_feishu_message(webhook_url, content, secret)
    
    logger.info(f"消息内容超长({content_bytes}字节)，将分批发送")
    
    # 按段落分割（以 \n\n 或 --- 分隔）
    chunks = []
    current_chunk = ""
    current_bytes = 0
    
    # 按双换行符分割
    paragraphs = content.split('\n\n')
    
    for para in paragraphs:
        para_bytes = len(para.encode('utf-8'))
        
        if current_bytes + para_bytes > max_bytes and current_chunk:
            # 当前块已满，保存并开始新块
            chunks.append(current_chunk)
            current_chunk = para
            current_bytes = para_bytes
        else:
            # 添加到当前块
            if current_chunk:
                current_chunk += '\n\n' + para
            else:
                current_chunk = para
            current_bytes += para_bytes
    
    # 添加最后一个块
    if current_chunk:
        chunks.append(current_chunk)
    
    total_chunks = len(chunks)
    logger.info(f"飞书分批发送：共 {total_chunks} 批")
    
    success_count = 0
    for i, chunk in enumerate(chunks):
        # 添加分页标记
        chunk_with_marker = f"{chunk}\n\n---\n*第 {i+1}/{total_chunks} 部分*"
        
        if send_feishu_message(webhook_url, chunk_with_marker, secret):
            success_count += 1
            logger.info(f"飞书第 {i+1}/{total_chunks} 批发送成功")
            # 等待一下，避免请求过快
            if i < total_chunks - 1:
                time.sleep(1)
        else:
            logger.error(f"飞书第 {i+1}/{total_chunks} 批发送失败")
    
    return success_count == total_chunks


def push_reports_to_feishu(report_file1: str, report_file2: str):
    """推送两个报告到飞书"""
    # 读取报告内容
    report1_content = read_report_file(report_file1)
    report2_content = read_report_file(report_file2)
    
    # 获取配置
    webhook_url = os.getenv('FEISHU_WEBHOOK_URL')
    webhook_secret = os.getenv('FEISHU_WEBHOOK_SECRET')
    
    if not webhook_url:
        logger.error("飞书 Webhook URL 未配置，请设置环境变量 FEISHU_WEBHOOK_URL")
        return False
    
    logger.info(f"飞书 Webhook URL: {webhook_url[:50]}...")
    if webhook_secret:
        logger.info("飞书 Webhook Secret 已配置（将使用签名验证）")
    
    # 推送第一个报告
    logger.info("=" * 60)
    logger.info("推送第一个报告...")
    logger.info("=" * 60)
    
    content1_bytes = len(report1_content.encode('utf-8'))
    if content1_bytes > 20000:
        success1 = send_feishu_chunked(webhook_url, report1_content, max_bytes=20000, secret=webhook_secret)
    else:
        success1 = send_feishu_message(webhook_url, report1_content, webhook_secret)
    
    if success1:
        logger.info("✓ 第一个报告推送成功")
    else:
        logger.error("✗ 第一个报告推送失败")
    
    # 等待一下，避免消息过快
    time.sleep(2)
    
    # 推送第二个报告
    logger.info("=" * 60)
    logger.info("推送第二个报告...")
    logger.info("=" * 60)
    
    content2_bytes = len(report2_content.encode('utf-8'))
    if content2_bytes > 20000:
        success2 = send_feishu_chunked(webhook_url, report2_content, max_bytes=20000, secret=webhook_secret)
    else:
        success2 = send_feishu_message(webhook_url, report2_content, webhook_secret)
    
    if success2:
        logger.info("✓ 第二个报告推送成功")
    else:
        logger.error("✗ 第二个报告推送失败")
    
    # 返回总体结果
    return success1 and success2


def main():
    """主函数"""
    if len(sys.argv) != 3:
        print("用法: python3 push_reports_to_feishu.py <report_file1> <report_file2>")
        print("\n环境变量:")
        print("  FEISHU_WEBHOOK_URL: 飞书 Webhook URL（必需）")
        print("  FEISHU_WEBHOOK_SECRET: 飞书 Webhook Secret（可选）")
        sys.exit(1)
    
    report_file1 = sys.argv[1]
    report_file2 = sys.argv[2]
    
    # 检查文件是否存在
    if not os.path.exists(report_file1):
        logger.error(f"报告文件不存在: {report_file1}")
        sys.exit(1)
    
    if not os.path.exists(report_file2):
        logger.error(f"报告文件不存在: {report_file2}")
        sys.exit(1)
    
    # 推送报告
    success = push_reports_to_feishu(report_file1, report_file2)
    
    if success:
        logger.info("=" * 60)
        logger.info("✓ 所有报告推送成功！")
        logger.info("=" * 60)
        sys.exit(0)
    else:
        logger.error("=" * 60)
        logger.error("✗ 部分报告推送失败")
        logger.error("=" * 60)
        sys.exit(1)


if __name__ == '__main__':
    main()
