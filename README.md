# \# NIFTY 50 Derivatives Analytics Dashboard

# 

# A live, open-source derivatives analytics platform for NIFTY 50 index options — built as a course project for \*\*Financial Derivatives and Risk Management\*\* at IIFM Bhopal.

# 

# Combines option pricing (Black-Scholes-Merton), the full set of Greeks, implied volatility estimation, payoff diagram visualisation, and Value at Risk (VaR) into a single interactive Streamlit dashboard — an affordable, transparent alternative to expensive commercial platforms like Bloomberg or Refinitiv.

# 

# 🔗 \*\*Live demo:\*\* https://nifty-derivatives-dashboard-iwixg6pcqbsggmzty83tnx.streamlit.app/

# 

# \---

# 

# \## Features

# 

# | Module | What it does |

# |---|---|

# | \*\*Live Market Data\*\* | Fetches current NIFTY 50 spot price and recent trend via Yahoo Finance, with automatic fallback when markets are closed |

# | \*\*Option Pricing Calculator\*\* | Theoretical call/put pricing using the Black-Scholes-Merton model |

# | \*\*Greeks Calculator\*\* | Delta, Gamma, Vega, Theta, and Rho for any option |

# | \*\*Payoff Diagram Visualisation\*\* | Multi-leg strategy builder (spreads, straddles, strangles) with breakeven analysis |

# | \*\*Implied Volatility Estimator\*\* | Recovers IV from market prices via numerical root-finding; plots the volatility smile against NSE's own reported IV |

# | \*\*Value at Risk (VaR) Analysis\*\* | Parametric (Delta-Normal) and Historical Simulation methods, side by side |

# | \*\*Portfolio Risk Summary\*\* | Aggregates Greeks across multiple positions into net portfolio exposure |

# 

# \## Key Findings

# 

# This project goes beyond simply implementing the formulas — the pricing engine was validated against real NSE market data, which surfaced a genuine data-quality issue:

# 

# \- \*\*Spot-price timing mismatch\*\*: pricing options using the previous session's closing spot produced a \*\*57.65% median pricing error\*\* on near-the-money contracts.

# \- \*\*Root cause\*\*: the option chain and spot price were captured at different moments. Diagnosed using a \*\*no-arbitrage check\*\* (48 of 231 contracts priced below their theoretical floor).

# \- \*\*Fix\*\*: derived spot directly from the option chain via \*\*put-call parity\*\* (S = C − P + Ke⁻ʳᵀ), reducing near-ATM error to \*\*14.42%\*\* — a 4× accuracy improvement from a 0.27% input correction.

# \- \*\*VaR method comparison\*\*: on a short-strangle portfolio, Historical Simulation VaR exceeded Parametric VaR by \*\*2.5×–4.2×\*\*, demonstrating Parametric VaR's known blind spot for Gamma risk.

# 

# \## Tech Stack

# 

# \- \*\*Python\*\* — core language

# \- \*\*Streamlit\*\* — interactive dashboard framework

# \- \*\*Plotly\*\* — interactive charts

# \- \*\*NumPy / SciPy\*\* — numerical computation (BSM formula, Greeks, Brent's-method IV solver)

# \- \*\*Pandas\*\* — data cleaning and manipulation

# \- \*\*yfinance\*\* — live and historical market data

# 

# \## Project Structure

# 

# ```

# derivatives\_dashboard/

# ├── data/

# │   ├── raw/              # unprocessed NSE option chain + Yahoo Finance history

# │   └── processed/        # cleaned dataset, validation tables, saved charts

# ├── src/

# │   ├── app.py                # Streamlit entry point

# │   ├── data\_fetch.py         # market data collection

# │   ├── data\_clean.py         # cleaning, no-arbitrage flags, spot/T calculation

# │   ├── pricing\_engine.py     # BSM pricing, Greeks, no-arbitrage bounds

# │   ├── implied\_vol.py        # implied volatility solver

# │   └── var\_module.py         # Parametric and Historical Simulation VaR

# ├── requirements.txt

# └── README.md

# ```

# 

# \## Setup \& Running Locally

# 

# ```bash

# git clone https://github.com/fiatheresa/nifty-derivatives-dashboard.git

# cd nifty-derivatives-dashboard

# pip install -r requirements.txt

# cd src

# streamlit run app.py

# ```

# 

# The app will open at `http://localhost:8501`.

# 

# \## Data Sources

# 

# | Source | Purpose |

# |---|---|

# | NSE Option Chain | Strike prices, premiums, IV, open interest, volume |

# | Yahoo Finance | Historical and near-live NIFTY 50 prices |

# | RBI 91-Day T-Bill | Risk-free interest rate |

# 

# \## Limitations

# 

# \- Analysis is based on a single option chain snapshot and a single 7-day expiry; results may not generalise to longer-dated contracts.

# \- VaR is demonstrated on illustrative portfolios, not real client data.

# \- Live data depends on Yahoo Finance and NSE's public feeds, which can be rate-limited or intermittently unavailable.

# \- Volatility is treated as constant per the Black-Scholes-Merton assumptions, though the dashboard's own volatility smile shows this does not fully hold in practice.

# 

# \## Future Scope

# 

# \- Extend across multiple expiries and underlyings

# \- Add a GARCH-based volatility forecast

# \- Test VaR against real or simulated multi-asset portfolios, with Monte Carlo as a third method

# \- Host a persistent live deployment

# 

# \## Authors

# \- Fia Theresa Sabu

# \- Aditya Pratap Singh 

# 

# 

# Submitted to Professor Santanu Das, IIFM Bhopal.

# 

# \## References

# 

# \- Black, F., \& Scholes, M. (1973). \*The pricing of options and corporate liabilities.\* Journal of Political Economy.

# \- Hull, J. C. (2022). \*Options, futures, and other derivatives\* (11th ed.). Pearson.

# \- Jorion, P. (2007). \*Value at Risk: The new benchmark for managing financial risk\* (3rd ed.). McGraw-Hill.

# \- Natenberg, S. (2015). \*Option volatility and pricing\* (2nd ed.). McGraw-Hill.

# 

# \_Full reference list in the project report.\_

