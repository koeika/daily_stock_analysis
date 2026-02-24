#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ETF 成分股获取模块

功能：
1. 维护 ETF 成分股映射表（港股科技类 ETF）
2. 支持获取 ETF 的核心重仓股
3. 提供成分股权重信息
"""

import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Holding:
    """成分股持仓信息"""
    code: str          # 股票代码（带市场前缀，如 hk00700）
    name: str          # 股票名称
    weight: float      # 权重（%）
    sector: str = ""   # 所属行业


class ETFHoldingsManager:
    """
    ETF 成分股管理器

    维护常见 ETF（特别是港股科技类）的成分股映射表。
    支持自动扩展 ETF 到其核心成分股。
    """

    # 港股科技类 ETF 成分股映射（手动维护，定期更新）
    # 数据来源：天天基金网、Wind、各 ETF 官网
    ETF_HOLDINGS_MAP: Dict[str, List[Holding]] = {
        # 港科技30 (159636) - 跟踪恒生科技指数前30只
        '159636': [
            Holding('hk00700', '腾讯控股', 30.5, '互联网'),
            Holding('hk03690', '美团', 15.2, '互联网'),
            Holding('hk09988', '阿里巴巴', 12.8, '互联网'),
            Holding('hk01810', '小米集团', 8.3, '消费电子'),
            Holding('hk00981', '中芯国际', 6.1, '半导体'),
            Holding('hk01024', '快手', 5.4, '互联网'),
            Holding('hk02015', '理想汽车', 4.2, '新能源车'),
            Holding('hk09961', '携程', 3.8, '互联网'),
            Holding('hk09618', '京东集团', 3.5, '互联网'),
            Holding('hk01833', '平安好医生', 2.1, '医疗'),
        ],

        # 恒生科技 ETF (513180) - 华泰柏瑞南方东英
        '513180': [
            Holding('hk00700', '腾讯控股', 28.7, '互联网'),
            Holding('hk09988', '阿里巴巴', 14.5, '互联网'),
            Holding('hk03690', '美团', 13.8, '互联网'),
            Holding('hk01024', '快手', 6.2, '互联网'),
            Holding('hk02015', '理想汽车', 5.1, '新能源车'),
            Holding('hk01810', '小米集团', 4.9, '消费电子'),
            Holding('hk00981', '中芯国际', 4.6, '半导体'),
            Holding('hk09618', '京东集团', 4.3, '互联网'),
            Holding('hk09961', '携程', 3.2, '互联网'),
            Holding('hk02359', '药明生物', 2.8, '生物医药'),
        ],

        # 易方达中证香港科技 (513050)
        '513050': [
            Holding('hk00700', '腾讯控股', 32.1, '互联网'),
            Holding('hk03690', '美团', 16.3, '互联网'),
            Holding('hk09988', '阿里巴巴', 11.2, '互联网'),
            Holding('hk01810', '小米集团', 9.1, '消费电子'),
            Holding('hk09618', '京东集团', 6.4, '互联网'),
            Holding('hk00981', '中芯国际', 5.8, '半导体'),
            Holding('hk01024', '快手', 4.7, '互联网'),
            Holding('hk02015', '理想汽车', 3.9, '新能源车'),
            Holding('hk09961', '携程', 3.2, '互联网'),
            Holding('hk02382', '舜宇光学', 2.5, '光学器件'),
        ],

        # 恒生科技指数 ETF (159742) - 华安恒生科技
        '159742': [
            Holding('hk00700', '腾讯控股', 29.3, '互联网'),
            Holding('hk09988', '阿里巴巴', 13.9, '互联网'),
            Holding('hk03690', '美团', 14.2, '互联网'),
            Holding('hk01024', '快手', 5.8, '互联网'),
            Holding('hk01810', '小米集团', 5.2, '消费电子'),
            Holding('hk00981', '中芯国际', 4.9, '半导体'),
            Holding('hk09618', '京东集团', 4.5, '互联网'),
            Holding('hk02015', '理想汽车', 4.1, '新能源车'),
            Holding('hk09961', '携程', 3.4, '互联网'),
            Holding('hk02359', '药明生物', 2.6, '生物医药'),
        ],

        # 恒生科技 ETF (513130) - 易方达恒生科技
        '513130': [
            Holding('hk00700', '腾讯控股', 28.5, '互联网'),
            Holding('hk09988', '阿里巴巴', 14.1, '互联网'),
            Holding('hk03690', '美团', 13.6, '互联网'),
            Holding('hk01024', '快手', 6.0, '互联网'),
            Holding('hk02015', '理想汽车', 5.3, '新能源车'),
            Holding('hk01810', '小米集团', 4.8, '消费电子'),
            Holding('hk00981', '中芯国际', 4.7, '半导体'),
            Holding('hk09618', '京东集团', 4.2, '互联网'),
            Holding('hk09961', '携程', 3.3, '互联网'),
            Holding('hk02359', '药明生物', 2.9, '生物医药'),
        ],
    }

    # ETF 基本信息
    ETF_INFO: Dict[str, Dict[str, str]] = {
        '159636': {
            'name': '港科技30',
            'index': '恒生科技指数',
            'type': '港股科技',
            'description': '跟踪恒生科技指数前30只成份股',
        },
        '513180': {
            'name': '恒生科技ETF',
            'index': '恒生科技指数',
            'type': '港股科技',
            'description': '华泰柏瑞南方东英恒生科技ETF',
        },
        '513050': {
            'name': '易方达中证香港科技',
            'index': '中证香港科技指数',
            'type': '港股科技',
            'description': '跟踪中证香港科技指数',
        },
        '513130': {
            'name': '易方达恒生科技',
            'index': '恒生科技指数',
            'type': '港股科技',
            'description': '易方达恒生科技ETF',
        },
        '159742': {
            'name': '华安恒生科技',
            'index': '恒生科技指数',
            'type': '港股科技',
            'description': '华安恒生科技ETF',
        },
    }

    @classmethod
    def is_supported_etf(cls, etf_code: str) -> bool:
        """
        判断是否为已支持的 ETF

        Args:
            etf_code: ETF 代码

        Returns:
            是否支持
        """
        return etf_code in cls.ETF_HOLDINGS_MAP

    @classmethod
    def get_holdings(cls, etf_code: str, top_n: Optional[int] = None) -> List[Holding]:
        """
        获取 ETF 成分股列表

        Args:
            etf_code: ETF 代码
            top_n: 返回前 N 只重仓股，None 表示返回全部

        Returns:
            成分股列表
        """
        holdings = cls.ETF_HOLDINGS_MAP.get(etf_code, [])
        if top_n is not None:
            holdings = holdings[:top_n]
        return holdings

    @classmethod
    def get_holding_codes(cls, etf_code: str, top_n: Optional[int] = None) -> List[str]:
        """
        获取 ETF 成分股代码列表

        Args:
            etf_code: ETF 代码
            top_n: 返回前 N 只重仓股

        Returns:
            成分股代码列表
        """
        holdings = cls.get_holdings(etf_code, top_n)
        return [h.code for h in holdings]

    @classmethod
    def get_etf_info(cls, etf_code: str) -> Optional[Dict[str, str]]:
        """
        获取 ETF 基本信息

        Args:
            etf_code: ETF 代码

        Returns:
            ETF 信息字典
        """
        return cls.ETF_INFO.get(etf_code)

    @classmethod
    def format_holdings_summary(cls, etf_code: str, top_n: int = 5) -> str:
        """
        格式化成分股摘要（用于日志或报告）

        Args:
            etf_code: ETF 代码
            top_n: 显示前 N 只

        Returns:
            格式化的成分股摘要
        """
        holdings = cls.get_holdings(etf_code, top_n)
        if not holdings:
            return f"{etf_code}: 无成分股数据"

        info = cls.get_etf_info(etf_code)
        etf_name = info['name'] if info else etf_code

        lines = [f"{etf_name} 前{top_n}大重仓股:"]
        for i, h in enumerate(holdings, 1):
            lines.append(f"  {i}. {h.name}({h.code}) {h.weight:.1f}%")

        return "\n".join(lines)

    @classmethod
    def get_search_keywords(cls, etf_code: str) -> List[str]:
        """
        获取 ETF 相关的搜索关键词（用于新闻搜索）

        包括：
        1. ETF 名称
        2. 跟踪指数
        3. 核心成分股名称
        4. 行业关键词

        Args:
            etf_code: ETF 代码

        Returns:
            搜索关键词列表
        """
        keywords = []

        # 1. ETF 基本信息
        info = cls.get_etf_info(etf_code)
        if info:
            keywords.append(info['name'])
            keywords.append(info['index'])
            if 'description' in info:
                keywords.append(info['description'])

        # 2. 前5大成分股名称
        holdings = cls.get_holdings(etf_code, top_n=5)
        for h in holdings:
            keywords.append(h.name)

        # 3. 行业关键词
        sectors = set(h.sector for h in holdings if h.sector)
        keywords.extend(sectors)

        # 4. 通用关键词
        if info and info.get('type') == '港股科技':
            keywords.extend([
                '港股科技股',
                '恒生科技',
                '香港科技股',
                'HK Tech',
            ])

        return keywords


def expand_etf_to_holdings(
    stock_codes: List[str],
    top_n: int = 5,
    include_etf: bool = True
) -> Tuple[List[str], Dict[str, List[str]]]:
    """
    将 ETF 代码扩展为成分股代码

    Args:
        stock_codes: 原始股票代码列表（可能包含 ETF）
        top_n: 每个 ETF 扩展前 N 只重仓股
        include_etf: 是否保留 ETF 本身

    Returns:
        (扩展后的代码列表, ETF->成分股映射)
    """
    expanded_codes = []
    etf_mapping = {}

    for code in stock_codes:
        # 非 ETF，直接添加
        if not ETFHoldingsManager.is_supported_etf(code):
            expanded_codes.append(code)
            continue

        # ETF：添加本身 + 成分股
        if include_etf:
            expanded_codes.append(code)

        holdings = ETFHoldingsManager.get_holding_codes(code, top_n)
        expanded_codes.extend(holdings)
        etf_mapping[code] = holdings

        logger.info(f"[ETF扩展] {code} -> {len(holdings)} 只成分股: {', '.join(holdings[:3])}...")

    # 去重但保持顺序
    seen = set()
    unique_codes = []
    for code in expanded_codes:
        if code not in seen:
            seen.add(code)
            unique_codes.append(code)

    return unique_codes, etf_mapping


if __name__ == '__main__':
    # 测试代码
    logging.basicConfig(level=logging.INFO)

    print("=== ETF 成分股管理器测试 ===\n")

    # 测试1：获取成分股
    etf_code = '159636'
    holdings = ETFHoldingsManager.get_holdings(etf_code, top_n=5)
    print(f"1. {etf_code} 前5大重仓股:")
    for i, h in enumerate(holdings, 1):
        print(f"   {i}. {h.name}({h.code}) - {h.weight:.1f}% - {h.sector}")

    # 测试2：格式化摘要
    print(f"\n2. 格式化摘要:")
    print(ETFHoldingsManager.format_holdings_summary(etf_code, 5))

    # 测试3：搜索关键词
    print(f"\n3. 搜索关键词:")
    keywords = ETFHoldingsManager.get_search_keywords(etf_code)
    print(f"   {', '.join(keywords[:10])}")

    # 测试4：扩展功能
    print(f"\n4. 自动扩展测试:")
    original = ['600519', '159636', '513180']
    expanded, mapping = expand_etf_to_holdings(original, top_n=3)
    print(f"   原始: {original}")
    print(f"   扩展后: {expanded}")
    print(f"   映射: {mapping}")
