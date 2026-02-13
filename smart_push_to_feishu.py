#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能推送分析报告到飞书

功能：
1. 自动读取报告文件
2. 根据配置或长度智能选择报告格式（完整版/精简版）
3. 支持多个报告批量推送

用法:
    python3 smart_push_to_feishu.py <report_files...>
    
环境变量:
    FEISHU_WEBHOOK_URL: 飞书 Webhook URL（必需）
    FEISHU_WEBHOOK_SECRET: 飞书 Webhook Secret（可选）
    REPORT_DETAIL_LEVEL: 报告详细程度 full/compact（默认 full）
    FEISHU_AUTO_COMPACT: 是否自动精简 true/false（默认 true）
"""

import sys
import os
import logging
import time
import re
from pathlib import Path
from datetime import datetime

# 尝试加载 .env 文件
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.notification import NotificationService
from src.config import get_config
from src.analyzer import AnalysisResult

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
        logger.info(f"成功读取报告文件: {file_path} ({len(content)} 字符, {len(content.encode('utf-8'))} 字节)")
        return content
    except Exception as e:
        logger.error(f"读取报告文件失败 {file_path}: {e}")
        raise


def should_use_compact_format(content: str, config) -> bool:
    """
    判断是否应该使用精简格式
    
    规则：
    1. 如果配置强制使用 compact，则使用
    2. 如果启用自动精简且内容超长，则使用
    3. 否则使用完整格式
    """
    # 强制使用精简模式
    if config.report_detail_level == 'compact':
        logger.info("配置强制使用精简格式")
        return True
    
    # 自动精简模式
    if config.feishu_auto_compact:
        content_bytes = len(content.encode('utf-8'))
        threshold = config.feishu_max_bytes  # 20KB
        
        if content_bytes > threshold:
            logger.info(f"内容超长 ({content_bytes} > {threshold} 字节)，自动使用精简格式")
            return True
    
    logger.info("使用完整格式")
    return False


def convert_to_compact_format(content: str) -> str:
    """
    将完整报告转换为精简格式
    
    优化策略：
    1. 移除详细的数据透视表格
    2. 精简重要信息速览（只保留风险和利好）
    3. 压缩行情数据表格
    4. 移除冗余的分隔线和空行
    """
    lines = content.split('\n')
    result_lines = []
    skip_until_marker = None
    in_data_perspective = False
    in_market_snapshot = False
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # 跳过数据透视板块
        if '### 📊 数据透视' in line:
            in_data_perspective = True
            i += 1
            continue
        
        # 跳过当日行情详细表格，只保留关键数据
        if '### 📈 当日行情' in line:
            in_market_snapshot = True
            # 查找后面的表格，提取关键数据
            j = i + 1
            while j < len(lines) and j < i + 10:
                if lines[j].strip().startswith('|') and '收盘' in lines[j]:
                    # 找到数据行
                    data_row = lines[j+2] if j+2 < len(lines) else ""
                    parts = [p.strip() for p in data_row.split('|')]
                    if len(parts) >= 7:
                        # 提取：收盘、涨跌幅、最高、最低
                        result_lines.append(f"📈 **当日**: 收盘 {parts[1]} | 涨跌幅 {parts[6]} | 高 {parts[4]} | 低 {parts[5]}")
                        result_lines.append("")
                    break
                j += 1
            # 跳过整个当日行情板块
            while i < len(lines) and not lines[i].strip().startswith('###'):
                i += 1
            continue
        
        # 结束数据透视板块
        if in_data_perspective and line.startswith('###'):
            in_data_perspective = False
        
        # 跳过数据透视内容
        if in_data_perspective:
            i += 1
            continue
        
        # 精简重要信息速览
        if '### 📰 重要信息速览' in line:
            result_lines.append(line)
            result_lines.append("")
            # 只保留风险和利好
            j = i + 1
            while j < len(lines):
                if lines[j].strip().startswith('###'):
                    break
                if '**🚨 风险警报**:' in lines[j] or '**✨ 利好催化**:' in lines[j]:
                    # 保留标题和最多2条
                    result_lines.append(lines[j])
                    count = 0
                    j += 1
                    while j < len(lines) and lines[j].strip().startswith('-') and count < 2:
                        result_lines.append(lines[j])
                        count += 1
                        j += 1
                    result_lines.append("")
                j += 1
            # 跳过已处理的行
            while i < j:
                i += 1
            continue
        
        # 移除多余的空行（连续超过1个空行）
        if not line and i > 0 and not result_lines[-1].strip() if result_lines else False:
            i += 1
            continue
        
        # 保留其他内容
        result_lines.append(lines[i])
        i += 1
    
    compact_content = '\n'.join(result_lines)
    
    # 统计压缩效果
    original_bytes = len(content.encode('utf-8'))
    compact_bytes = len(compact_content.encode('utf-8'))
    reduction = (1 - compact_bytes / original_bytes) * 100 if original_bytes > 0 else 0
    
    logger.info(f"精简完成: {original_bytes} -> {compact_bytes} 字节 (减少 {reduction:.1f}%)")
    
    return compact_content


def push_reports_to_feishu(*report_files):
    """推送多个报告到飞书"""
    # 获取配置
    config = get_config()
    
    if not config.feishu_webhook_url:
        logger.error("飞书 Webhook URL 未配置，请设置环境变量 FEISHU_WEBHOOK_URL")
        return False
    
    logger.info(f"飞书 Webhook URL: {config.feishu_webhook_url[:50]}...")
    if hasattr(config, 'feishu_webhook_secret') and config.feishu_webhook_secret:
        logger.info("飞书 Webhook Secret 已配置")
    
    logger.info(f"报告详细程度配置: {config.report_detail_level}")
    logger.info(f"自动精简配置: {config.feishu_auto_compact}")
    
    # 创建通知服务
    notifier = NotificationService()
    
    success_count = 0
    total_count = len(report_files)
    
    for i, report_file in enumerate(report_files, 1):
        logger.info("=" * 60)
        logger.info(f"推送第 {i}/{total_count} 个报告...")
        logger.info("=" * 60)
        
        # 读取报告内容
        content = read_report_file(report_file)
        
        # 判断是否使用精简格式
        use_compact = should_use_compact_format(content, config)
        
        # 如果需要精简，进行转换
        if use_compact:
            content = convert_to_compact_format(content)
        
        # 推送
        success = notifier.send_to_feishu(content)
        
        if success:
            logger.info(f"✓ 第 {i} 个报告推送成功")
            success_count += 1
        else:
            logger.error(f"✗ 第 {i} 个报告推送失败")
        
        # 等待一下，避免请求过快
        if i < total_count:
            time.sleep(2)
    
    return success_count == total_count


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python3 smart_push_to_feishu.py <report_file1> [report_file2] ...")
        print("\n环境变量:")
        print("  FEISHU_WEBHOOK_URL: 飞书 Webhook URL（必需）")
        print("  FEISHU_WEBHOOK_SECRET: 飞书 Webhook Secret（可选）")
        print("  REPORT_DETAIL_LEVEL: 报告详细程度 full/compact（默认 full）")
        print("  FEISHU_AUTO_COMPACT: 是否自动精简 true/false（默认 true）")
        sys.exit(1)
    
    report_files = sys.argv[1:]
    
    # 检查文件是否存在
    for report_file in report_files:
        if not os.path.exists(report_file):
            logger.error(f"报告文件不存在: {report_file}")
            sys.exit(1)
    
    # 推送报告
    success = push_reports_to_feishu(*report_files)
    
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
