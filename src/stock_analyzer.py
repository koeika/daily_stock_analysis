# -*- coding: utf-8 -*-
"""
===================================
趋势交易分析器 - 基于用户交易理念
===================================

交易理念核心原则：
1. 严进策略 - 不追高，追求每笔交易成功率
2. 趋势交易 - MA5>MA10>MA20 多头排列，顺势而为
3. 效率优先 - 关注筹码结构好的股票
4. 买点偏好 - 在 MA5/MA10 附近回踩买入

技术标准：
- 多头排列：MA5 > MA10 > MA20
- 乖离率：(Close - MA5) / MA5 < 5%（不追高）
- 量能形态：缩量回调优先
"""

import logging
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Tuple, Sequence
from enum import Enum

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class TrendStatus(Enum):
    """趋势状态枚举"""
    STRONG_BULL = "强势多头"      # MA5 > MA10 > MA20，且间距扩大
    BULL = "多头排列"             # MA5 > MA10 > MA20
    WEAK_BULL = "弱势多头"        # MA5 > MA10，但 MA10 < MA20
    CONSOLIDATION = "盘整"        # 均线缠绕
    WEAK_BEAR = "弱势空头"        # MA5 < MA10，但 MA10 > MA20
    BEAR = "空头排列"             # MA5 < MA10 < MA20
    STRONG_BEAR = "强势空头"      # MA5 < MA10 < MA20，且间距扩大


class VolumeStatus(Enum):
    """量能状态枚举"""
    HEAVY_VOLUME_UP = "放量上涨"       # 量价齐升
    HEAVY_VOLUME_DOWN = "放量下跌"     # 放量杀跌
    SHRINK_VOLUME_UP = "缩量上涨"      # 无量上涨
    SHRINK_VOLUME_DOWN = "缩量回调"    # 缩量回调（好）
    NORMAL = "量能正常"


class BuySignal(Enum):
    """买入信号枚举"""
    STRONG_BUY = "强烈买入"       # 多条件满足
    BUY = "买入"                  # 基本条件满足
    HOLD = "持有"                 # 已持有可继续
    WAIT = "观望"                 # 等待更好时机
    SELL = "卖出"                 # 趋势转弱
    STRONG_SELL = "强烈卖出"      # 趋势破坏


class MACDStatus(Enum):
    """MACD状态枚举"""
    GOLDEN_CROSS_ZERO = "零轴上金叉"      # DIF上穿DEA，且在零轴上方
    GOLDEN_CROSS = "金叉"                # DIF上穿DEA
    BULLISH = "多头"                    # DIF>DEA>0
    CROSSING_UP = "上穿零轴"             # DIF上穿零轴
    CROSSING_DOWN = "下穿零轴"           # DIF下穿零轴
    BEARISH = "空头"                    # DIF<DEA<0
    DEATH_CROSS = "死叉"                # DIF下穿DEA


class RSIStatus(Enum):
    """RSI状态枚举"""
    OVERBOUGHT = "超买"        # RSI > 70
    STRONG_BUY = "强势买入"    # 50 < RSI < 70
    NEUTRAL = "中性"          # 40 <= RSI <= 60
    WEAK = "弱势"             # 30 < RSI < 40
    OVERSOLD = "超卖"         # RSI < 30


class KDJStatus(Enum):
    """KDJ状态枚举 (A股核心指标)"""
    GOLDEN_CROSS = "金叉"        # K上穿D，低位金叉最佳
    DEATH_CROSS = "死叉"         # K下穿D
    OVERBOUGHT = "超买"          # J > 100 或 K/D > 80
    OVERSOLD = "超卖"            # J < 0 或 K/D < 20
    BULLISH = "多头"            # K > D，且上行
    BEARISH = "空头"            # K < D，且下行
    NEUTRAL = "中性"            # 震荡区域


class BOLLStatus(Enum):
    """布林带状态枚举"""
    UPPER_BREAK = "突破上轨"     # 价格突破上轨，强势
    LOWER_BREAK = "跌破下轨"     # 价格跌破下轨，超卖
    UPPER_NEAR = "接近上轨"      # 价格接近上轨
    LOWER_NEAR = "接近下轨"      # 价格接近下轨，关注反弹
    MID_SUPPORT = "中轨支撑"     # 价格在中轨获得支撑
    MID_RESISTANCE = "中轨压力"  # 价格受中轨压制
    NORMAL = "通道内"           # 价格在通道内正常波动


@dataclass
class TrendAnalysisResult:
    """趋势分析结果"""
    code: str
    
    # 趋势判断
    trend_status: TrendStatus = TrendStatus.CONSOLIDATION
    ma_alignment: str = ""           # 均线排列描述
    trend_strength: float = 0.0      # 趋势强度 0-100
    
    # 均线数据
    ma5: float = 0.0
    ma10: float = 0.0
    ma20: float = 0.0
    ma60: float = 0.0
    current_price: float = 0.0
    
    # 乖离率（与 MA5 的偏离度）
    bias_ma5: float = 0.0            # (Close - MA5) / MA5 * 100
    bias_ma10: float = 0.0
    bias_ma20: float = 0.0
    
    # 量能分析
    volume_status: VolumeStatus = VolumeStatus.NORMAL
    volume_ratio_5d: float = 0.0     # 当日成交量/5日均量
    volume_trend: str = ""           # 量能趋势描述
    
    # 支撑压力
    support_ma5: bool = False        # MA5 是否构成支撑
    support_ma10: bool = False       # MA10 是否构成支撑
    resistance_levels: List[float] = field(default_factory=list)
    support_levels: List[float] = field(default_factory=list)

    # MACD 指标
    macd_dif: float = 0.0          # DIF 快线
    macd_dea: float = 0.0          # DEA 慢线
    macd_bar: float = 0.0           # MACD 柱状图
    macd_status: MACDStatus = MACDStatus.BULLISH
    macd_signal: str = ""            # MACD 信号描述

    # RSI 指标
    rsi_6: float = 0.0              # RSI(6) 短期
    rsi_12: float = 0.0             # RSI(12) 中期
    rsi_24: float = 0.0             # RSI(24) 长期
    rsi_status: RSIStatus = RSIStatus.NEUTRAL
    rsi_signal: str = ""              # RSI 信号描述

    # KDJ 指标 (A股核心)
    kdj_k: float = 0.0              # K 值
    kdj_d: float = 0.0              # D 值
    kdj_j: float = 0.0              # J 值
    kdj_status: KDJStatus = KDJStatus.NEUTRAL
    kdj_signal: str = ""            # KDJ 信号描述

    # BOLL 布林带
    boll_upper: float = 0.0         # 上轨
    boll_mid: float = 0.0           # 中轨
    boll_lower: float = 0.0         # 下轨
    boll_position: float = 0.0      # 价格在通道中的相对位置 (-1到1)
    boll_status: BOLLStatus = BOLLStatus.NORMAL
    boll_signal: str = ""           # BOLL 信号描述

    # OBV 能量潮 (P2 高级指标)
    obv: float = 0.0                # 当前 OBV 值
    obv_trend: str = ""              # 趋势描述

    # 买入信号
    buy_signal: BuySignal = BuySignal.WAIT
    signal_score: int = 0            # 综合评分 0-100
    signal_reasons: List[str] = field(default_factory=list)
    risk_factors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'code': self.code,
            'trend_status': self.trend_status.value,
            'ma_alignment': self.ma_alignment,
            'trend_strength': self.trend_strength,
            'ma5': self.ma5,
            'ma10': self.ma10,
            'ma20': self.ma20,
            'ma60': self.ma60,
            'current_price': self.current_price,
            'bias_ma5': self.bias_ma5,
            'bias_ma10': self.bias_ma10,
            'bias_ma20': self.bias_ma20,
            'volume_status': self.volume_status.value,
            'volume_ratio_5d': self.volume_ratio_5d,
            'volume_trend': self.volume_trend,
            'support_ma5': self.support_ma5,
            'support_ma10': self.support_ma10,
            'buy_signal': self.buy_signal.value,
            'signal_score': self.signal_score,
            'signal_reasons': self.signal_reasons,
            'risk_factors': self.risk_factors,
            'macd_dif': self.macd_dif,
            'macd_dea': self.macd_dea,
            'macd_bar': self.macd_bar,
            'macd_status': self.macd_status.value,
            'macd_signal': self.macd_signal,
            'rsi_6': self.rsi_6,
            'rsi_12': self.rsi_12,
            'rsi_24': self.rsi_24,
            'rsi_status': self.rsi_status.value,
            'rsi_signal': self.rsi_signal,
            'kdj_k': self.kdj_k,
            'kdj_d': self.kdj_d,
            'kdj_j': self.kdj_j,
            'kdj_status': self.kdj_status.value,
            'kdj_signal': self.kdj_signal,
            'boll_upper': self.boll_upper,
            'boll_mid': self.boll_mid,
            'boll_lower': self.boll_lower,
            'boll_position': self.boll_position,
            'boll_status': self.boll_status.value,
            'boll_signal': self.boll_signal,
            'obv': self.obv,
            'obv_trend': self.obv_trend,
        }


class StockTrendAnalyzer:
    """
    股票趋势分析器

    基于用户交易理念实现：
    1. 趋势判断 - MA5>MA10>MA20 多头排列
    2. 乖离率检测 - 不追高，偏离 MA5 超过 5% 不买
    3. 量能分析 - 偏好缩量回调
    4. 买点识别 - 回踩 MA5/MA10 支撑
    5. MACD 指标 - 趋势确认和金叉死叉信号
    6. RSI 指标 - 超买超卖判断
    """
    
    # 交易参数配置
    BIAS_THRESHOLD = 5.0        # 乖离率阈值（%），超过此值不买入
    VOLUME_SHRINK_RATIO = 0.7   # 缩量判断阈值（当日量/5日均量）
    VOLUME_HEAVY_RATIO = 1.5    # 放量判断阈值
    MA_SUPPORT_TOLERANCE = 0.02  # MA 支撑判断容忍度（2%）

    # MACD 参数（标准12/26/9）
    MACD_FAST = 12              # 快线周期
    MACD_SLOW = 26             # 慢线周期
    MACD_SIGNAL = 9             # 信号线周期

    # RSI 参数
    RSI_SHORT = 6               # 短期RSI周期
    RSI_MID = 12               # 中期RSI周期
    RSI_LONG = 24              # 长期RSI周期
    RSI_OVERBOUGHT = 70        # 超买阈值
    RSI_OVERSOLD = 30          # 超卖阈值

    # KDJ 参数 (标准 9, 3, 3)
    KDJ_N = 9                  # RSV 周期
    KDJ_M1 = 3                 # K 平滑周期
    KDJ_M2 = 3                 # D 平滑周期

    # BOLL 参数 (标准 20, 2)
    BOLL_PERIOD = 20           # 中轨周期
    BOLL_STD = 2               # 标准差倍数

    # Default score weights: trend, bias, volume, support, macd, rsi, kdj, boll
    DEFAULT_WEIGHTS: List[int] = [28, 18, 12, 8, 12, 7, 8, 7]

    def __init__(self, score_weights: Optional[Sequence[int]] = None):
        """
        Initialize analyzer.

        Args:
            score_weights: Optional 8-element list for indicator weights (trend,bias,volume,
                           support,macd,rsi,kdj,boll). Must sum to 100. Falls back to
                           DEFAULT_WEIGHTS if invalid.
        """
        raw = score_weights if score_weights is not None else self.DEFAULT_WEIGHTS
        if len(raw) != 8 or sum(raw) != 100:
            self._weights = list(self.DEFAULT_WEIGHTS)
        else:
            self._weights = list(raw)
    
    def analyze(self, df: pd.DataFrame, code: str) -> TrendAnalysisResult:
        """
        分析股票趋势
        
        Args:
            df: 包含 OHLCV 数据的 DataFrame
            code: 股票代码
            
        Returns:
            TrendAnalysisResult 分析结果
        """
        result = TrendAnalysisResult(code=code)
        
        if df is None or df.empty or len(df) < 20:
            logger.warning(f"{code} 数据不足，无法进行趋势分析")
            result.risk_factors.append("数据不足，无法完成分析")
            return result
        
        # 确保数据按日期排序
        df = df.sort_values('date').reset_index(drop=True)
        
        # 计算均线
        df = self._calculate_mas(df)

        # 计算 MACD、RSI、KDJ、BOLL、OBV
        df = self._calculate_macd(df)
        df = self._calculate_rsi(df)
        df = self._calculate_kdj(df)
        df = self._calculate_boll(df)
        df = self._calculate_obv(df)

        # 获取最新数据
        latest = df.iloc[-1]
        result.current_price = float(latest['close'])
        result.ma5 = float(latest['MA5'])
        result.ma10 = float(latest['MA10'])
        result.ma20 = float(latest['MA20'])
        result.ma60 = float(latest.get('MA60', 0))

        # 1. 趋势判断
        self._analyze_trend(df, result)

        # 2. 乖离率计算
        self._calculate_bias(result)

        # 3. 量能分析
        self._analyze_volume(df, result)

        # 4. 支撑压力分析
        self._analyze_support_resistance(df, result)

        # 5. MACD 分析
        self._analyze_macd(df, result)

        # 6. RSI 分析
        self._analyze_rsi(df, result)

        # 7. KDJ 分析
        self._analyze_kdj(df, result)

        # 8. BOLL 分析
        self._analyze_boll(df, result)

        # 9. 生成买入信号
        self._generate_signal(result)

        return result
    
    def _calculate_mas(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算均线"""
        df = df.copy()
        df['MA5'] = df['close'].rolling(window=5).mean()
        df['MA10'] = df['close'].rolling(window=10).mean()
        df['MA20'] = df['close'].rolling(window=20).mean()
        if len(df) >= 60:
            df['MA60'] = df['close'].rolling(window=60).mean()
        else:
            df['MA60'] = df['MA20']  # 数据不足时使用 MA20 替代
        return df

    def _calculate_macd(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算 MACD 指标

        公式：
        - EMA(12)：12日指数移动平均
        - EMA(26)：26日指数移动平均
        - DIF = EMA(12) - EMA(26)
        - DEA = EMA(DIF, 9)
        - MACD = (DIF - DEA) * 2
        """
        df = df.copy()

        # 计算快慢线 EMA
        ema_fast = df['close'].ewm(span=self.MACD_FAST, adjust=False).mean()
        ema_slow = df['close'].ewm(span=self.MACD_SLOW, adjust=False).mean()

        # 计算快线 DIF
        df['MACD_DIF'] = ema_fast - ema_slow

        # 计算信号线 DEA
        df['MACD_DEA'] = df['MACD_DIF'].ewm(span=self.MACD_SIGNAL, adjust=False).mean()

        # 计算柱状图
        df['MACD_BAR'] = (df['MACD_DIF'] - df['MACD_DEA']) * 2

        return df

    def _calculate_rsi(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算 RSI 指标

        公式：
        - RS = 平均上涨幅度 / 平均下跌幅度
        - RSI = 100 - (100 / (1 + RS))
        """
        df = df.copy()

        for period in [self.RSI_SHORT, self.RSI_MID, self.RSI_LONG]:
            # 计算价格变化
            delta = df['close'].diff()

            # 分离上涨和下跌
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)

            # 计算平均涨跌幅
            avg_gain = gain.rolling(window=period).mean()
            avg_loss = loss.rolling(window=period).mean()

            # 计算 RS 和 RSI
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))

            # 填充 NaN 值
            rsi = rsi.fillna(50)  # 默认中性值

            # 添加到 DataFrame
            col_name = f'RSI_{period}'
            df[col_name] = rsi

        return df

    def _calculate_kdj(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算 KDJ 指标 (A股核心随机指标)

        公式：
        - RSV = (C - L9) / (H9 - L9) * 100
        - K = SMA(RSV, M1)
        - D = SMA(K, M2)
        - J = 3K - 2D
        """
        df = df.copy()
        n, m1, m2 = self.KDJ_N, self.KDJ_M1, self.KDJ_M2

        low_n = df['low'].rolling(window=n).min()
        high_n = df['high'].rolling(window=n).max()

        rsv = (df['close'] - low_n) / (high_n - low_n).replace(0, np.nan) * 100
        rsv = rsv.fillna(50)

        df['KDJ_K'] = rsv.ewm(alpha=1/m1, adjust=False).mean()
        df['KDJ_D'] = df['KDJ_K'].ewm(alpha=1/m2, adjust=False).mean()
        df['KDJ_J'] = 3 * df['KDJ_K'] - 2 * df['KDJ_D']

        return df

    def _calculate_boll(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算布林带 (BOLL)

        公式：
        - MID = MA(Close, N)
        - UPPER = MID + K * STD(Close, N)
        - LOWER = MID - K * STD(Close, N)
        """
        df = df.copy()
        period, std_mult = self.BOLL_PERIOD, self.BOLL_STD

        df['BOLL_MID'] = df['close'].rolling(window=period).mean()
        std = df['close'].rolling(window=period).std().fillna(0)
        df['BOLL_UPPER'] = df['BOLL_MID'] + std_mult * std
        df['BOLL_LOWER'] = df['BOLL_MID'] - std_mult * std

        return df

    def _calculate_obv(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算能量潮 (OBV)

        公式：当日收盘价>昨收则OBV+=成交量，反之OBV-=成交量，平则不变
        """
        df = df.copy()
        if 'volume' not in df.columns:
            df['OBV'] = 0
            return df

        delta = df['close'].diff()
        direction = np.sign(delta)
        direction.iloc[0] = 0
        obv = (direction * df['volume']).cumsum()
        df['OBV'] = obv
        return df

    def _analyze_trend(self, df: pd.DataFrame, result: TrendAnalysisResult) -> None:
        """
        分析趋势状态
        
        核心逻辑：判断均线排列和趋势强度
        """
        ma5, ma10, ma20 = result.ma5, result.ma10, result.ma20
        
        # 判断均线排列
        if ma5 > ma10 > ma20:
            # 检查间距是否在扩大（强势）
            prev = df.iloc[-5] if len(df) >= 5 else df.iloc[-1]
            prev_spread = (prev['MA5'] - prev['MA20']) / prev['MA20'] * 100 if prev['MA20'] > 0 else 0
            curr_spread = (ma5 - ma20) / ma20 * 100 if ma20 > 0 else 0
            
            if curr_spread > prev_spread and curr_spread > 5:
                result.trend_status = TrendStatus.STRONG_BULL
                result.ma_alignment = "强势多头排列，均线发散上行"
                result.trend_strength = 90
            else:
                result.trend_status = TrendStatus.BULL
                result.ma_alignment = "多头排列 MA5>MA10>MA20"
                result.trend_strength = 75
                
        elif ma5 > ma10 and ma10 <= ma20:
            result.trend_status = TrendStatus.WEAK_BULL
            result.ma_alignment = "弱势多头，MA5>MA10 但 MA10≤MA20"
            result.trend_strength = 55
            
        elif ma5 < ma10 < ma20:
            prev = df.iloc[-5] if len(df) >= 5 else df.iloc[-1]
            prev_spread = (prev['MA20'] - prev['MA5']) / prev['MA5'] * 100 if prev['MA5'] > 0 else 0
            curr_spread = (ma20 - ma5) / ma5 * 100 if ma5 > 0 else 0
            
            if curr_spread > prev_spread and curr_spread > 5:
                result.trend_status = TrendStatus.STRONG_BEAR
                result.ma_alignment = "强势空头排列，均线发散下行"
                result.trend_strength = 10
            else:
                result.trend_status = TrendStatus.BEAR
                result.ma_alignment = "空头排列 MA5<MA10<MA20"
                result.trend_strength = 25
                
        elif ma5 < ma10 and ma10 >= ma20:
            result.trend_status = TrendStatus.WEAK_BEAR
            result.ma_alignment = "弱势空头，MA5<MA10 但 MA10≥MA20"
            result.trend_strength = 40
            
        else:
            result.trend_status = TrendStatus.CONSOLIDATION
            result.ma_alignment = "均线缠绕，趋势不明"
            result.trend_strength = 50
    
    def _calculate_bias(self, result: TrendAnalysisResult) -> None:
        """
        计算乖离率
        
        乖离率 = (现价 - 均线) / 均线 * 100%
        
        严进策略：乖离率超过 5% 不追高
        """
        price = result.current_price
        
        if result.ma5 > 0:
            result.bias_ma5 = (price - result.ma5) / result.ma5 * 100
        if result.ma10 > 0:
            result.bias_ma10 = (price - result.ma10) / result.ma10 * 100
        if result.ma20 > 0:
            result.bias_ma20 = (price - result.ma20) / result.ma20 * 100
    
    def _analyze_volume(self, df: pd.DataFrame, result: TrendAnalysisResult) -> None:
        """
        分析量能
        
        偏好：缩量回调 > 放量上涨 > 缩量上涨 > 放量下跌
        """
        if len(df) < 5:
            return
        
        latest = df.iloc[-1]
        vol_5d_avg = df['volume'].iloc[-6:-1].mean()
        
        if vol_5d_avg > 0:
            result.volume_ratio_5d = float(latest['volume']) / vol_5d_avg
        
        # 判断价格变化
        prev_close = df.iloc[-2]['close']
        price_change = (latest['close'] - prev_close) / prev_close * 100
        
        # 量能状态判断
        if result.volume_ratio_5d >= self.VOLUME_HEAVY_RATIO:
            if price_change > 0:
                result.volume_status = VolumeStatus.HEAVY_VOLUME_UP
                result.volume_trend = "放量上涨，多头力量强劲"
            else:
                result.volume_status = VolumeStatus.HEAVY_VOLUME_DOWN
                result.volume_trend = "放量下跌，注意风险"
        elif result.volume_ratio_5d <= self.VOLUME_SHRINK_RATIO:
            if price_change > 0:
                result.volume_status = VolumeStatus.SHRINK_VOLUME_UP
                result.volume_trend = "缩量上涨，上攻动能不足"
            else:
                result.volume_status = VolumeStatus.SHRINK_VOLUME_DOWN
                result.volume_trend = "缩量回调，洗盘特征明显（好）"
        else:
            result.volume_status = VolumeStatus.NORMAL
            result.volume_trend = "量能正常"
    
    def _analyze_support_resistance(self, df: pd.DataFrame, result: TrendAnalysisResult) -> None:
        """
        分析支撑压力位
        
        买点偏好：回踩 MA5/MA10 获得支撑
        """
        price = result.current_price
        
        # 检查是否在 MA5 附近获得支撑
        if result.ma5 > 0:
            ma5_distance = abs(price - result.ma5) / result.ma5
            if ma5_distance <= self.MA_SUPPORT_TOLERANCE and price >= result.ma5:
                result.support_ma5 = True
                result.support_levels.append(result.ma5)
        
        # 检查是否在 MA10 附近获得支撑
        if result.ma10 > 0:
            ma10_distance = abs(price - result.ma10) / result.ma10
            if ma10_distance <= self.MA_SUPPORT_TOLERANCE and price >= result.ma10:
                result.support_ma10 = True
                if result.ma10 not in result.support_levels:
                    result.support_levels.append(result.ma10)
        
        # MA20 作为重要支撑
        if result.ma20 > 0 and price >= result.ma20:
            result.support_levels.append(result.ma20)
        
        # 近期高点作为压力
        if len(df) >= 20:
            recent_high = df['high'].iloc[-20:].max()
            if recent_high > price:
                result.resistance_levels.append(recent_high)

    def _analyze_macd(self, df: pd.DataFrame, result: TrendAnalysisResult) -> None:
        """
        分析 MACD 指标

        核心信号：
        - 零轴上金叉：最强买入信号
        - 金叉：DIF 上穿 DEA
        - 死叉：DIF 下穿 DEA
        """
        if len(df) < self.MACD_SLOW:
            result.macd_signal = "数据不足"
            return

        latest = df.iloc[-1]
        prev = df.iloc[-2]

        # 获取 MACD 数据
        result.macd_dif = float(latest['MACD_DIF'])
        result.macd_dea = float(latest['MACD_DEA'])
        result.macd_bar = float(latest['MACD_BAR'])

        # 判断金叉死叉
        prev_dif_dea = prev['MACD_DIF'] - prev['MACD_DEA']
        curr_dif_dea = result.macd_dif - result.macd_dea

        # 金叉：DIF 上穿 DEA
        is_golden_cross = prev_dif_dea <= 0 and curr_dif_dea > 0

        # 死叉：DIF 下穿 DEA
        is_death_cross = prev_dif_dea >= 0 and curr_dif_dea < 0

        # 零轴穿越
        prev_zero = prev['MACD_DIF']
        curr_zero = result.macd_dif
        is_crossing_up = prev_zero <= 0 and curr_zero > 0
        is_crossing_down = prev_zero >= 0 and curr_zero < 0

        # 判断 MACD 状态
        if is_golden_cross and curr_zero > 0:
            result.macd_status = MACDStatus.GOLDEN_CROSS_ZERO
            result.macd_signal = "⭐ 零轴上金叉，强烈买入信号！"
        elif is_crossing_up:
            result.macd_status = MACDStatus.CROSSING_UP
            result.macd_signal = "⚡ DIF上穿零轴，趋势转强"
        elif is_golden_cross:
            result.macd_status = MACDStatus.GOLDEN_CROSS
            result.macd_signal = "✅ 金叉，趋势向上"
        elif is_death_cross:
            result.macd_status = MACDStatus.DEATH_CROSS
            result.macd_signal = "❌ 死叉，趋势向下"
        elif is_crossing_down:
            result.macd_status = MACDStatus.CROSSING_DOWN
            result.macd_signal = "⚠️ DIF下穿零轴，趋势转弱"
        elif result.macd_dif > 0 and result.macd_dea > 0:
            result.macd_status = MACDStatus.BULLISH
            result.macd_signal = "✓ 多头排列，持续上涨"
        elif result.macd_dif < 0 and result.macd_dea < 0:
            result.macd_status = MACDStatus.BEARISH
            result.macd_signal = "⚠ 空头排列，持续下跌"
        else:
            result.macd_status = MACDStatus.BULLISH
            result.macd_signal = " MACD 中性区域"

    def _analyze_rsi(self, df: pd.DataFrame, result: TrendAnalysisResult) -> None:
        """
        分析 RSI 指标

        核心判断：
        - RSI > 70：超买，谨慎追高
        - RSI < 30：超卖，关注反弹
        - 40-60：中性区域
        """
        if len(df) < self.RSI_LONG:
            result.rsi_signal = "数据不足"
            return

        latest = df.iloc[-1]

        # 获取 RSI 数据
        result.rsi_6 = float(latest[f'RSI_{self.RSI_SHORT}'])
        result.rsi_12 = float(latest[f'RSI_{self.RSI_MID}'])
        result.rsi_24 = float(latest[f'RSI_{self.RSI_LONG}'])

        # 以中期 RSI(12) 为主进行判断
        rsi_mid = result.rsi_12

        # 判断 RSI 状态
        if rsi_mid > self.RSI_OVERBOUGHT:
            result.rsi_status = RSIStatus.OVERBOUGHT
            result.rsi_signal = f"⚠️ RSI超买({rsi_mid:.1f}>70)，短期回调风险高"
        elif rsi_mid > 60:
            result.rsi_status = RSIStatus.STRONG_BUY
            result.rsi_signal = f"✅ RSI强势({rsi_mid:.1f})，多头力量充足"
        elif rsi_mid >= 40:
            result.rsi_status = RSIStatus.NEUTRAL
            result.rsi_signal = f" RSI中性({rsi_mid:.1f})，震荡整理中"
        elif rsi_mid >= self.RSI_OVERSOLD:
            result.rsi_status = RSIStatus.WEAK
            result.rsi_signal = f"⚡ RSI弱势({rsi_mid:.1f})，关注反弹"
        else:
            result.rsi_status = RSIStatus.OVERSOLD
            result.rsi_signal = f"⭐ RSI超卖({rsi_mid:.1f}<30)，反弹机会大"

    def _analyze_kdj(self, df: pd.DataFrame, result: TrendAnalysisResult) -> None:
        """
        分析 KDJ 指标 (A股核心)

        核心信号：
        - 低位金叉(K上穿D)：买入信号
        - 高位死叉(K下穿D)：卖出信号
        - J>100 或 K/D>80：超买
        - J<0 或 K/D<20：超卖
        """
        if len(df) < self.KDJ_N or 'KDJ_K' not in df.columns:
            result.kdj_signal = "数据不足"
            return

        latest = df.iloc[-1]
        prev = df.iloc[-2]

        result.kdj_k = float(latest['KDJ_K'])
        result.kdj_d = float(latest['KDJ_D'])
        result.kdj_j = float(latest['KDJ_J'])

        prev_k_d = prev['KDJ_K'] - prev['KDJ_D']
        curr_k_d = result.kdj_k - result.kdj_d

        is_golden = prev_k_d <= 0 and curr_k_d > 0
        is_death = prev_k_d >= 0 and curr_k_d < 0

        if result.kdj_j > 100 or (result.kdj_k > 80 and result.kdj_d > 80):
            result.kdj_status = KDJStatus.OVERBOUGHT
            result.kdj_signal = f"⚠️ KDJ超买(K={result.kdj_k:.1f},D={result.kdj_d:.1f},J={result.kdj_j:.1f})"
        elif result.kdj_j < 0 or (result.kdj_k < 20 and result.kdj_d < 20):
            result.kdj_status = KDJStatus.OVERSOLD
            result.kdj_signal = f"⭐ KDJ超卖(K={result.kdj_k:.1f},D={result.kdj_d:.1f},J={result.kdj_j:.1f})"
        elif is_golden and result.kdj_k < 30:
            result.kdj_status = KDJStatus.GOLDEN_CROSS
            result.kdj_signal = f"✅ 低位金叉(K上穿D)，买入信号"
        elif is_golden:
            result.kdj_status = KDJStatus.GOLDEN_CROSS
            result.kdj_signal = f"✅ KDJ金叉(K上穿D)"
        elif is_death:
            result.kdj_status = KDJStatus.DEATH_CROSS
            result.kdj_signal = f"❌ KDJ死叉(K下穿D)"
        elif curr_k_d > 0:
            result.kdj_status = KDJStatus.BULLISH
            result.kdj_signal = f"✓ K>D，偏多"
        elif curr_k_d < 0:
            result.kdj_status = KDJStatus.BEARISH
            result.kdj_signal = f"⚠ K<D，偏空"
        else:
            result.kdj_status = KDJStatus.NEUTRAL
            result.kdj_signal = f" KDJ中性(K={result.kdj_k:.1f},D={result.kdj_d:.1f})"

    def _analyze_boll(self, df: pd.DataFrame, result: TrendAnalysisResult) -> None:
        """
        分析布林带 (BOLL)

        核心信号：
        - 价格突破上轨：强势，但警惕回调
        - 价格跌破下轨：超卖，关注反弹
        - 价格接近下轨：潜在买点
        - 价格在中轨获得支撑：偏多
        """
        if len(df) < self.BOLL_PERIOD or 'BOLL_MID' not in df.columns:
            result.boll_signal = "数据不足"
            return

        latest = df.iloc[-1]
        price = result.current_price
        result.boll_upper = float(latest['BOLL_UPPER'])
        result.boll_mid = float(latest['BOLL_MID'])
        result.boll_lower = float(latest['BOLL_LOWER'])

        band_width = result.boll_upper - result.boll_lower
        if band_width > 0:
            result.boll_position = (price - result.boll_mid) / (band_width / 2)
            result.boll_position = max(-1, min(1, result.boll_position))

        tol = 0.02
        if price >= result.boll_upper * (1 - tol):
            result.boll_status = BOLLStatus.UPPER_BREAK
            result.boll_signal = f"⚡ 突破上轨，强势(警惕回调)"
        elif price <= result.boll_lower * (1 + tol):
            result.boll_status = BOLLStatus.LOWER_BREAK
            result.boll_signal = f"⭐ 跌破下轨，超卖(关注反弹)"
        elif price >= result.boll_upper * (1 - tol * 2):
            result.boll_status = BOLLStatus.UPPER_NEAR
            result.boll_signal = f" 接近上轨，偏强"
        elif price <= result.boll_lower * (1 + tol * 2):
            result.boll_status = BOLLStatus.LOWER_NEAR
            result.boll_signal = f" 接近下轨，潜在买点"
        elif price >= result.boll_mid and price < result.boll_upper:
            result.boll_status = BOLLStatus.MID_SUPPORT
            result.boll_signal = f"✓ 中轨上方，获支撑"
        elif price < result.boll_mid and price > result.boll_lower:
            result.boll_status = BOLLStatus.MID_RESISTANCE
            result.boll_signal = f"⚠ 中轨下方，受压制"
        else:
            result.boll_status = BOLLStatus.NORMAL
            result.boll_signal = f" 通道内正常"

        # OBV 趋势简析 (P2)
        if 'OBV' in df.columns and len(df) >= 5:
            obv_curr = float(latest['OBV'])
            obv_5d = float(df['OBV'].iloc[-6])
            result.obv = obv_curr
            if obv_5d != 0:
                obv_chg = (obv_curr - obv_5d) / abs(obv_5d) * 100
                result.obv_trend = f"OBV 5日变化 {obv_chg:+.1f}%" if abs(obv_chg) > 1 else "OBV 平稳"

    def _generate_signal(self, result: TrendAnalysisResult) -> None:
        """
        生成买入信号

        综合评分系统 (共100分)，权重可配置 score_weights：
        趋势, 乖离率, 量能, 支撑, MACD, RSI, KDJ, BOLL
        """
        reasons = []
        risks = []
        w = self._weights
        d = self.DEFAULT_WEIGHTS

        # === 趋势评分 ===
        trend_scores = {
            TrendStatus.STRONG_BULL: 28,
            TrendStatus.BULL: 24,
            TrendStatus.WEAK_BULL: 16,
            TrendStatus.CONSOLIDATION: 10,
            TrendStatus.WEAK_BEAR: 6,
            TrendStatus.BEAR: 3,
            TrendStatus.STRONG_BEAR: 0,
        }
        trend_raw = trend_scores.get(result.trend_status, 12)
        trend_score = round(trend_raw * w[0] / d[0]) if d[0] else 0

        if result.trend_status in [TrendStatus.STRONG_BULL, TrendStatus.BULL]:
            reasons.append(f"✅ {result.trend_status.value}，顺势做多")
        elif result.trend_status in [TrendStatus.BEAR, TrendStatus.STRONG_BEAR]:
            risks.append(f"⚠️ {result.trend_status.value}，不宜做多")

        # === 乖离率评分 ===
        bias_raw = 0
        bias = result.bias_ma5
        if bias < 0:
            if bias > -3:
                bias_raw = 18
                reasons.append(f"✅ 价格略低于MA5({bias:.1f}%)，回踩买点")
            elif bias > -5:
                bias_raw = 14
                reasons.append(f"✅ 价格回踩MA5({bias:.1f}%)，观察支撑")
            else:
                bias_raw = 8
                risks.append(f"⚠️ 乖离率过大({bias:.1f}%)，可能破位")
        elif bias < 2:
            bias_raw = 16
            reasons.append(f"✅ 价格贴近MA5({bias:.1f}%)，介入好时机")
        elif bias < self.BIAS_THRESHOLD:
            bias_raw = 12
            reasons.append(f"⚡ 价格略高于MA5({bias:.1f}%)，可小仓介入")
        else:
            bias_raw = 3
            risks.append(f"❌ 乖离率过高({bias:.1f}%>5%)，严禁追高！")
        bias_score = round(bias_raw * w[1] / d[1]) if d[1] else 0

        # === 量能评分 ===
        volume_scores = {
            VolumeStatus.SHRINK_VOLUME_DOWN: 12,
            VolumeStatus.HEAVY_VOLUME_UP: 10,
            VolumeStatus.NORMAL: 8,
            VolumeStatus.SHRINK_VOLUME_UP: 5,
            VolumeStatus.HEAVY_VOLUME_DOWN: 0,
        }
        vol_raw = volume_scores.get(result.volume_status, 8)
        vol_score = round(vol_raw * w[2] / d[2]) if d[2] else 0

        if result.volume_status == VolumeStatus.SHRINK_VOLUME_DOWN:
            reasons.append("✅ 缩量回调，主力洗盘")
        elif result.volume_status == VolumeStatus.HEAVY_VOLUME_DOWN:
            risks.append("⚠️ 放量下跌，注意风险")

        # === 支撑评分 ===
        support_raw = (4 if result.support_ma5 else 0) + (4 if result.support_ma10 else 0)
        if result.support_ma5:
            reasons.append("✅ MA5支撑有效")
        if result.support_ma10:
            reasons.append("✅ MA10支撑有效")
        support_score = round(support_raw * w[3] / d[3]) if d[3] else 0

        # === MACD 评分 ===
        macd_scores = {
            MACDStatus.GOLDEN_CROSS_ZERO: 12,
            MACDStatus.GOLDEN_CROSS: 10,
            MACDStatus.CROSSING_UP: 8,
            MACDStatus.BULLISH: 6,
            MACDStatus.BEARISH: 1,
            MACDStatus.CROSSING_DOWN: 0,
            MACDStatus.DEATH_CROSS: 0,
        }
        macd_raw = macd_scores.get(result.macd_status, 5)
        macd_score = round(macd_raw * w[4] / d[4]) if d[4] else 0

        if result.macd_status in [MACDStatus.GOLDEN_CROSS_ZERO, MACDStatus.GOLDEN_CROSS]:
            reasons.append(f"✅ {result.macd_signal}")
        elif result.macd_status in [MACDStatus.DEATH_CROSS, MACDStatus.CROSSING_DOWN]:
            risks.append(f"⚠️ {result.macd_signal}")
        else:
            reasons.append(result.macd_signal)

        # === RSI 评分 ===
        rsi_scores = {
            RSIStatus.OVERSOLD: 7,
            RSIStatus.STRONG_BUY: 6,
            RSIStatus.NEUTRAL: 4,
            RSIStatus.WEAK: 2,
            RSIStatus.OVERBOUGHT: 0,
        }
        rsi_raw = rsi_scores.get(result.rsi_status, 4)
        rsi_score = round(rsi_raw * w[5] / d[5]) if d[5] else 0

        if result.rsi_status in [RSIStatus.OVERSOLD, RSIStatus.STRONG_BUY]:
            reasons.append(f"✅ {result.rsi_signal}")
        elif result.rsi_status == RSIStatus.OVERBOUGHT:
            risks.append(f"⚠️ {result.rsi_signal}")
        else:
            reasons.append(result.rsi_signal)

        # === KDJ 评分 ===
        kdj_scores = {
            KDJStatus.GOLDEN_CROSS: 8,
            KDJStatus.OVERSOLD: 7,
            KDJStatus.BULLISH: 5,
            KDJStatus.NEUTRAL: 3,
            KDJStatus.BEARISH: 1,
            KDJStatus.DEATH_CROSS: 0,
            KDJStatus.OVERBOUGHT: 0,
        }
        kdj_raw = kdj_scores.get(result.kdj_status, 3)
        kdj_score = round(kdj_raw * w[6] / d[6]) if d[6] else 0
        if result.kdj_status in [KDJStatus.GOLDEN_CROSS, KDJStatus.OVERSOLD]:
            reasons.append(f"✅ {result.kdj_signal}")
        elif result.kdj_status in [KDJStatus.DEATH_CROSS, KDJStatus.OVERBOUGHT]:
            risks.append(f"⚠️ {result.kdj_signal}")

        # === BOLL 评分 ===
        boll_scores = {
            BOLLStatus.LOWER_BREAK: 7,
            BOLLStatus.LOWER_NEAR: 6,
            BOLLStatus.MID_SUPPORT: 5,
            BOLLStatus.NORMAL: 4,
            BOLLStatus.UPPER_NEAR: 2,
            BOLLStatus.MID_RESISTANCE: 1,
            BOLLStatus.UPPER_BREAK: 1,
        }
        boll_raw = boll_scores.get(result.boll_status, 4)
        boll_score = round(boll_raw * w[7] / d[7]) if d[7] else 0
        if result.boll_status in [BOLLStatus.LOWER_BREAK, BOLLStatus.LOWER_NEAR, BOLLStatus.MID_SUPPORT]:
            reasons.append(f"✅ {result.boll_signal}")

        score = trend_score + bias_score + vol_score + support_score + macd_score + rsi_score + kdj_score + boll_score
        # === 综合判断 ===
        result.signal_score = score
        result.signal_reasons = reasons
        result.risk_factors = risks

        # 生成买入信号（调整阈值以适应新的100分制）
        if score >= 75 and result.trend_status in [TrendStatus.STRONG_BULL, TrendStatus.BULL]:
            result.buy_signal = BuySignal.STRONG_BUY
        elif score >= 60 and result.trend_status in [TrendStatus.STRONG_BULL, TrendStatus.BULL, TrendStatus.WEAK_BULL]:
            result.buy_signal = BuySignal.BUY
        elif score >= 45:
            result.buy_signal = BuySignal.HOLD
        elif score >= 30:
            result.buy_signal = BuySignal.WAIT
        elif result.trend_status in [TrendStatus.BEAR, TrendStatus.STRONG_BEAR]:
            result.buy_signal = BuySignal.STRONG_SELL
        else:
            result.buy_signal = BuySignal.SELL
    
    def format_analysis(self, result: TrendAnalysisResult) -> str:
        """
        格式化分析结果为文本

        Args:
            result: 分析结果

        Returns:
            格式化的分析文本
        """
        lines = [
            f"=== {result.code} 趋势分析 ===",
            f"",
            f"📊 趋势判断: {result.trend_status.value}",
            f"   均线排列: {result.ma_alignment}",
            f"   趋势强度: {result.trend_strength}/100",
            f"",
            f"📈 均线数据:",
            f"   现价: {result.current_price:.2f}",
            f"   MA5:  {result.ma5:.2f} (乖离 {result.bias_ma5:+.2f}%)",
            f"   MA10: {result.ma10:.2f} (乖离 {result.bias_ma10:+.2f}%)",
            f"   MA20: {result.ma20:.2f} (乖离 {result.bias_ma20:+.2f}%)",
            f"",
            f"📊 量能分析: {result.volume_status.value}",
            f"   量比(vs5日): {result.volume_ratio_5d:.2f}",
            f"   量能趋势: {result.volume_trend}",
            f"",
            f"📈 MACD指标: {result.macd_status.value}",
            f"   DIF: {result.macd_dif:.4f}",
            f"   DEA: {result.macd_dea:.4f}",
            f"   MACD: {result.macd_bar:.4f}",
            f"   信号: {result.macd_signal}",
            f"",
            f"📊 RSI指标: {result.rsi_status.value}",
            f"   RSI(6): {result.rsi_6:.1f}",
            f"   RSI(12): {result.rsi_12:.1f}",
            f"   RSI(24): {result.rsi_24:.1f}",
            f"   信号: {result.rsi_signal}",
            f"",
            f"📈 KDJ指标: {result.kdj_status.value}",
            f"   K: {result.kdj_k:.1f} D: {result.kdj_d:.1f} J: {result.kdj_j:.1f}",
            f"   信号: {result.kdj_signal}",
            f"",
            f"📊 BOLL通道: {result.boll_status.value}",
            f"   上轨: {result.boll_upper:.2f} 中轨: {result.boll_mid:.2f} 下轨: {result.boll_lower:.2f}",
            f"   信号: {result.boll_signal}",
            f"",
            f"🎯 操作建议: {result.buy_signal.value}",
            f"   综合评分: {result.signal_score}/100",
        ]

        if result.signal_reasons:
            lines.append(f"")
            lines.append(f"✅ 买入理由:")
            for reason in result.signal_reasons:
                lines.append(f"   {reason}")

        if result.risk_factors:
            lines.append(f"")
            lines.append(f"⚠️ 风险因素:")
            for risk in result.risk_factors:
                lines.append(f"   {risk}")

        return "\n".join(lines)


def analyze_stock(df: pd.DataFrame, code: str) -> TrendAnalysisResult:
    """
    便捷函数：分析单只股票
    
    Args:
        df: 包含 OHLCV 数据的 DataFrame
        code: 股票代码
        
    Returns:
        TrendAnalysisResult 分析结果
    """
    analyzer = StockTrendAnalyzer()
    return analyzer.analyze(df, code)


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)
    
    # 模拟数据测试
    import numpy as np
    
    dates = pd.date_range(start='2025-01-01', periods=60, freq='D')
    np.random.seed(42)
    
    # 模拟多头排列的数据
    base_price = 10.0
    prices = [base_price]
    for i in range(59):
        change = np.random.randn() * 0.02 + 0.003  # 轻微上涨趋势
        prices.append(prices[-1] * (1 + change))
    
    df = pd.DataFrame({
        'date': dates,
        'open': prices,
        'high': [p * (1 + np.random.uniform(0, 0.02)) for p in prices],
        'low': [p * (1 - np.random.uniform(0, 0.02)) for p in prices],
        'close': prices,
        'volume': [np.random.randint(1000000, 5000000) for _ in prices],
    })
    
    analyzer = StockTrendAnalyzer()
    result = analyzer.analyze(df, '000001')
    print(analyzer.format_analysis(result))
