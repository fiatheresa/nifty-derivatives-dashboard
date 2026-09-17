import numpy as np
import pandas as pd
from pricing_engine import bsm_price_vec, greeks


def portfolio_value(portfolio_df):
    return (portfolio_df['ltp'] * portfolio_df['position_size']).sum()


def portfolio_delta_exposure(portfolio_df, spot, r):
    deltas = portfolio_df.apply(
        lambda row: greeks(spot, row['strike'], row['T'], r, row['iv'], row['option_type'])['delta'],
        axis=1
    )
    exposure = deltas * portfolio_df['position_size'] * spot
    return exposure.sum()


def parametric_var(net_delta_exposure, daily_vol, confidence=0.95):
    z_scores = {0.95: 1.645, 0.99: 2.326}
    z = z_scores.get(confidence)
    if z is None:
        raise ValueError("confidence must be 0.95 or 0.99")
    return abs(net_delta_exposure) * daily_vol * z


def historical_simulation_var(portfolio_df, current_spot, current_value, r, historical_returns, confidence=0.95):
    simulated_pnl = []
    for ret in historical_returns:
        shocked_spot = current_spot * (1 + ret)
        shocked_value = 0
        for _, leg in portfolio_df.iterrows():
            shocked_price = bsm_price_vec(
                shocked_spot, leg['strike'], leg['T'], r, leg['iv'], leg['option_type']
            )
            shocked_value += shocked_price * leg['position_size']
        simulated_pnl.append(shocked_value - current_value)

    simulated_pnl = np.array(simulated_pnl)
    percentile = (1 - confidence) * 100
    return -np.percentile(simulated_pnl, percentile)