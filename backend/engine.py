# backend/engine.py
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

def run_backtest(
    data: pd.DataFrame, 
    initial_investment: float, 
    monthly_investment: float
):
    """
    执行定投策略回测
    :param data: 包含股价数据的 DataFrame，必须包含 'Close' 列
    :param initial_investment: 初始投资金额
    :param monthly_investment: 每月定投金额
    :return: 包含性能指标和每日资产净值的字典
    """
    
    # 检查数据有效性
    if data.empty:
        raise ValueError("数据为空")
    
    if 'Close' not in data.columns:
        raise ValueError("数据必须包含 'Close' 列")
    
    if len(data) < 30:  # 至少需要30天数据
        raise ValueError(f"数据长度不足，至少需要30个数据点")
    
    # 1. 准备数据
    df = data.copy()
    
    # 处理多层索引列的情况
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    # 确保索引是日期类型
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)
    
    # 2. 计算定投日期（每月第一个交易日）
    investment_dates = []
    current_date = df.index[0]
    
    # 首先加入初始投资日期
    investment_dates.append(current_date)
    
    # 计算后续每月投资日期
    while current_date < df.index[-1]:
        # 计算下个月的同一天
        next_month = current_date + relativedelta(months=1)
        
        # 找到该月最接近的交易日
        available_dates = df.index[df.index >= next_month]
        if len(available_dates) > 0:
            next_investment_date = available_dates[0]
            if next_investment_date not in investment_dates:
                investment_dates.append(next_investment_date)
            current_date = next_investment_date
        else:
            break
    
    # 3. 模拟定投过程
    portfolio = pd.DataFrame(index=df.index)
    portfolio['cash'] = 0.0
    portfolio['shares'] = 0.0
    portfolio['total_invested'] = 0.0  # 累计投入金额
    portfolio['holdings'] = 0.0
    portfolio['total'] = 0.0
    
    # 初始化
    current_shares = 0.0
    total_invested = 0.0
    
    # 遍历每一天
    for i, date in enumerate(df.index):
        current_price = df.loc[date, 'Close']
        
        # 检查是否为投资日
        if date in investment_dates:
            if date == investment_dates[0]:
                # 初始投资
                investment_amount = initial_investment
            else:
                # 定期投资
                investment_amount = monthly_investment
            
            # 计算可购买的股数
            shares_to_buy = investment_amount / current_price
            current_shares += shares_to_buy
            total_invested += investment_amount
        
        # 更新每日资产状态
        portfolio.loc[date, 'shares'] = current_shares
        portfolio.loc[date, 'total_invested'] = total_invested
        portfolio.loc[date, 'holdings'] = current_shares * current_price
        portfolio.loc[date, 'total'] = portfolio.loc[date, 'holdings']
        portfolio.loc[date, 'cash'] = 0.0  # 定投策略不持有现金
    
    # 4. 计算性能指标
    final_total = portfolio['total'].iloc[-1]
    total_invested_final = portfolio['total_invested'].iloc[-1]
    
    # 计算收益率（相对于总投入）
    total_return = (final_total / total_invested_final - 1) * 100 if total_invested_final > 0 else 0
    
    # 计算最大回撤（相对于当时累计投入）
    portfolio['return_pct'] = (portfolio['total'] / portfolio['total_invested'] - 1) * 100
    portfolio['return_pct'].fillna(0, inplace=True)
    
    # 计算回撤（相对于历史最高收益率）
    running_max_return = portfolio['return_pct'].cummax()
    drawdown = portfolio['return_pct'] - running_max_return
    max_drawdown = drawdown.min()
    
    # 计算基准收益（投入本金，无任何投资收益）
    # 基准就是累计投入的本金总额，没有任何收益
    benchmark_return = 0  # 本金基准收益率为0%
    
    # 统计投资次数
    total_investments = len(investment_dates)
    
    # 构建基准曲线（纯本金累计，无投资收益）
    benchmark_curve = {}
    for date in df.index:
        # 计算到该日期为止应该投入的总金额（纯本金）
        investments_up_to_date = [d for d in investment_dates if d <= date]
        if not investments_up_to_date:
            invested_so_far = 0
        else:
            invested_so_far = initial_investment + (len(investments_up_to_date) - 1) * monthly_investment
        
        # 基准线就是投入的本金总额，不产生任何收益
        benchmark_curve[date.strftime('%Y-%m-%d')] = invested_so_far
    
    # 转换日期格式用于JSON序列化
    portfolio_dict = portfolio.copy()
    portfolio_dict.index = portfolio_dict.index.strftime('%Y-%m-%d')
    
    return {
        "initial_investment": initial_investment,
        "monthly_investment": monthly_investment,
        "total_invested": float(total_invested_final),
        "final_total": float(final_total),
        "total_return_pct": float(total_return),
        "max_drawdown_pct": float(max_drawdown),
        "benchmark_return_pct": float(benchmark_return),  # 本金基准收益率固定为0%
        "absolute_profit": float(final_total - total_invested_final),  # 绝对收益金额
        "total_investments": int(total_investments),
        "equity_curve": portfolio_dict['total'].to_dict(),
        "benchmark_curve": benchmark_curve,
        "strategy_stats": {
            "investment_dates": [d.strftime('%Y-%m-%d') for d in investment_dates],
            "trading_days": len(df),
            "investment_period_months": len(investment_dates) - 1
        }
    }