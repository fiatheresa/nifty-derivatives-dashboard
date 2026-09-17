from scipy.stats import norm
import numpy as np
import pandas as pd

def bsm_price(S, K, T, r, sigma, option_type='call'):
    d1 = (np.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*np.sqrt(T))
    d2 = d1 - sigma*np.sqrt(T)
    if option_type == 'call':
        return S*norm.cdf(d1) - K*np.exp(-r*T)*norm.cdf(d2)
    else:
        return K*np.exp(-r*T)*norm.cdf(-d2) - S*norm.cdf(-d1)


def bsm_price_vec(S, K, T, r, sigma, option_type='call'):
    d1 = (np.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*np.sqrt(T))
    d2 = d1 - sigma*np.sqrt(T)
    call = S*norm.cdf(d1) - K*np.exp(-r*T)*norm.cdf(d2)
    put  = K*np.exp(-r*T)*norm.cdf(-d2) - S*norm.cdf(-d1)
    return np.where(option_type == 'call', call, put)


def greeks(S, K, T, r, sigma, option_type='call'):
    d1 = (np.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*np.sqrt(T))
    d2 = d1 - sigma*np.sqrt(T)
    delta = norm.cdf(d1) if option_type == 'call' else norm.cdf(d1) - 1
    gamma = norm.pdf(d1) / (S*sigma*np.sqrt(T))
    vega  = S*norm.pdf(d1)*np.sqrt(T) / 100
    theta = ( -(S*norm.pdf(d1)*sigma)/(2*np.sqrt(T))
              - r*K*np.exp(-r*T)*norm.cdf(d2 if option_type=='call' else -d2) ) / 365
    rho   = (K*T*np.exp(-r*T)*norm.cdf(d2 if option_type=='call' else -d2)) / 100
    return {'delta': delta, 'gamma': gamma, 'vega': vega, 'theta': theta, 'rho': rho}

def greeks_vec(S, K, T, r, sigma, option_type='call'):
    d1 = (np.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*np.sqrt(T))
    d2 = d1 - sigma*np.sqrt(T)

    is_call = (option_type == 'call')

    delta = np.where(is_call, norm.cdf(d1), norm.cdf(d1) - 1)
    gamma = norm.pdf(d1) / (S*sigma*np.sqrt(T))
    vega  = S*norm.pdf(d1)*np.sqrt(T) / 100
    theta = ( -(S*norm.pdf(d1)*sigma)/(2*np.sqrt(T))
              - r*K*np.exp(-r*T)*np.where(is_call, norm.cdf(d2), norm.cdf(-d2)) ) / 365
    rho   = (K*T*np.exp(-r*T)*np.where(is_call, norm.cdf(d2), norm.cdf(-d2))) / 100

    return pd.DataFrame({'delta': delta, 'gamma': gamma, 'vega': vega, 'theta': theta, 'rho': rho})

def noarb_lower_bound(spot, strike, T, r, option_type='call'):
    if option_type == 'call':
        return spot - strike * np.exp(-r*T)
    else:
        return np.maximum(0, strike * np.exp(-r*T) - spot)