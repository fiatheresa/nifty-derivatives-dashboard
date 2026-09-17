from scipy.optimize import brentq
from pricing_engine import bsm_price


def implied_vol(market_price, S, K, T, r, option_type='call'):
    objective = lambda sigma: bsm_price(S, K, T, r, sigma, option_type) - market_price
    try:
        return brentq(objective, 1e-4, 5.0)
    except ValueError:
        return None   # solver failed — flag instead of crashing