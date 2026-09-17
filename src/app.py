import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from pricing_engine import bsm_price, greeks
from implied_vol import implied_vol
from var_module import parametric_var, historical_simulation_var, portfolio_value, portfolio_delta_exposure

RISK_FREE_RATE = 0.05278  # RBI 91-day T-Bill, as of 2026-08-05

st.set_page_config(page_title="Live Derivatives Analytics Dashboard", layout="wide")
st.title("NIFTY Derivatives Analytics Dashboard")

MODULES = [
    "Live Market Data",
    "Option Pricing Calculator",
    "Greeks Calculator",
    "Implied Volatility Estimator",
    "Payoff Diagram Visualisation",
    "Value at Risk (VaR) Analysis",
    "Portfolio Risk Summary",
]

selected_module = st.sidebar.selectbox("Select Module", MODULES)

if selected_module == "Live Market Data":
    st.header("Live Market Data")
    st.caption("Fetches current NIFTY 50 price and recent trend directly from Yahoo Finance.")
    import yfinance as yf

    if st.button("Refresh Live Data"):
        with st.spinner("Fetching live NIFTY data..."):
            nifty_live = yf.download("^NSEI", period="5d", interval="1d", auto_adjust=False)
            if isinstance(nifty_live.columns, pd.MultiIndex):
                nifty_live.columns = nifty_live.columns.get_level_values(0)

        if nifty_live.empty:
            st.error("Could not fetch live data. Check your internet connection or try again shortly.")
        else:
            nifty_live = nifty_live.reset_index()
            latest_row = nifty_live.iloc[-1]

            if latest_row["Volume"] == 0 and len(nifty_live) > 1:
                st.warning("Latest session shows zero volume (market likely still settling or closed) — showing prior session's close instead.")
                latest_row = nifty_live.iloc[-2]

            live_spot = float(latest_row["Close"])
            live_date = latest_row["Date"]

            c1, c2 = st.columns(2)
            c1.metric("NIFTY 50 Spot", f"₹{live_spot:,.2f}")
            c2.metric("As of", live_date.strftime("%d-%b-%Y"))

            st.subheader("Last 5 Sessions")
            chart_df = nifty_live[["Date", "Close"]].copy()
            chart_df["Date"] = chart_df["Date"].dt.strftime("%d-%b")
            fig_live = go.Figure()
            fig_live.add_trace(go.Scatter(x=chart_df["Date"], y=chart_df["Close"], mode="lines+markers"))
            fig_live.update_layout(title="NIFTY 50 — Recent Trend", template="plotly_white", yaxis_title="Close")
            st.plotly_chart(fig_live, use_container_width=True)

            st.session_state["live_spot"] = live_spot
    else:
        st.info("Click 'Refresh Live Data' to fetch the current NIFTY price.")
        
elif selected_module == "Option Pricing Calculator":
    st.header("Option Pricing Calculator")
    st.caption("Estimate a theoretical option price using the Black-Scholes-Merton model.")

    col1, col2 = st.columns(2)

    with col1:
        spot = st.number_input("Spot Price (S)", min_value=0.01, value=24150.0, step=1.0)
        strike = st.number_input("Strike Price (K)", min_value=0.01, value=24150.0, step=1.0)
        option_type = st.selectbox("Option Type", ["call", "put"])

    with col2:
        days_to_expiry = st.number_input("Days to Expiry", min_value=1, value=7, step=1)
        r = st.number_input("Risk-Free Rate (r, as decimal)", min_value=0.0, value=RISK_FREE_RATE, step=0.001, format="%.5f")
        sigma = st.number_input("Volatility (σ, as decimal)", min_value=0.0001, value=0.15, step=0.01, format="%.4f")

    T = days_to_expiry / 365.0

    if st.button("Calculate Price"):
        price = bsm_price(spot, strike, T, r, sigma, option_type)
        st.metric(label=f"Theoretical {option_type.capitalize()} Price", value=f"₹{price:,.2f}")

        intrinsic = max(0, spot - strike) if option_type == "call" else max(0, strike - spot)
        extrinsic = price - intrinsic
        c1, c2 = st.columns(2)
        c1.metric("Intrinsic Value", f"₹{intrinsic:,.2f}")
        c2.metric("Extrinsic (Time) Value", f"₹{extrinsic:,.2f}")

elif selected_module == "Greeks Calculator":
    st.header("Greeks Calculator")
    st.caption("Calculate option Greeks: Delta, Gamma, Theta, Vega, Rho.")

    col1, col2 = st.columns(2)

    with col1:
        spot_g = st.number_input("Spot Price (S)", min_value=0.01, value=24150.0, step=1.0, key="greeks_spot")
        strike_g = st.number_input("Strike Price (K)", min_value=0.01, value=24150.0, step=1.0, key="greeks_strike")
        option_type_g = st.selectbox("Option Type", ["call", "put"], key="greeks_type")

    with col2:
        days_g = st.number_input("Days to Expiry", min_value=1, value=7, step=1, key="greeks_days")
        r_g = st.number_input("Risk-Free Rate (r)", min_value=0.0, value=RISK_FREE_RATE, step=0.001, format="%.5f", key="greeks_r")
        sigma_g = st.number_input("Volatility (σ)", min_value=0.0001, value=0.15, step=0.01, format="%.4f", key="greeks_sigma")

    T_g = days_g / 365.0

    if st.button("Calculate Greeks"):
        g = greeks(spot_g, strike_g, T_g, r_g, sigma_g, option_type_g)

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Delta", f"{g['delta']:.4f}")
        c2.metric("Gamma", f"{g['gamma']:.6f}")
        c3.metric("Vega", f"{g['vega']:.4f}")
        c4.metric("Theta", f"{g['theta']:.4f}")
        c5.metric("Rho", f"{g['rho']:.4f}")

elif selected_module == "Implied Volatility Estimator":
    st.header("Implied Volatility Estimator")
    st.caption("Recovers implied volatility from market prices and compares it against NSE's reported IV.")

    try:
        df_iv = pd.read_csv(os.path.join(DATA_PROCESSED, "final_nifty_option_chain.csv"))
    except FileNotFoundError:
        st.error("final_nifty_option_chain.csv not found in data/processed/. Run the Phase 1-3 pipeline first.")
        st.stop()

    spot_iv = df_iv["spot_price"].iloc[0]

    with st.spinner("Recovering implied volatility from market prices..."):
        df_iv["call_recovered_iv"] = df_iv.apply(
            lambda r: implied_vol(r["call_ltp"], r["spot_price"], r["strike"], r["T"], RISK_FREE_RATE, "call")
            if r["call_data_available"] else None, axis=1
        )
        df_iv["put_recovered_iv"] = df_iv.apply(
            lambda r: implied_vol(r["put_ltp"], r["spot_price"], r["strike"], r["T"], RISK_FREE_RATE, "put")
            if r["put_data_available"] else None, axis=1
        )

    fig_iv = go.Figure()
    fig_iv.add_trace(go.Scatter(
        x=df_iv["strike"], y=df_iv["call_iv"], mode="lines", name="NSE reported call IV",
        line=dict(dash="dash", color="orange")
    ))
    fig_iv.add_trace(go.Scatter(
        x=df_iv["strike"], y=df_iv["call_recovered_iv"] * 100, mode="lines", name="Recovered call IV",
        line=dict(color="steelblue")
    ))
    fig_iv.add_trace(go.Scatter(
        x=df_iv["strike"], y=df_iv["put_iv"], mode="lines", name="NSE reported put IV",
        line=dict(dash="dash", color="mediumpurple")
    ))
    fig_iv.add_trace(go.Scatter(
        x=df_iv["strike"], y=df_iv["put_recovered_iv"] * 100, mode="lines", name="Recovered put IV",
        line=dict(color="seagreen")
    ))
    fig_iv.add_vline(x=spot_iv, line_dash="dot", line_color="red", annotation_text="Spot")
    fig_iv.update_layout(
        title="NIFTY Volatility Smile",
        xaxis_title="Strike", yaxis_title="Implied Volatility (%)",
        template="plotly_white",
    )
    st.plotly_chart(fig_iv,use_container_width=True)

    n_call_failed = df_iv["call_recovered_iv"].isna().sum() - (~df_iv["call_data_available"]).sum()
    n_put_failed = df_iv["put_recovered_iv"].isna().sum() - (~df_iv["put_data_available"]).sum()
    st.caption(
        f"Note: {n_call_failed} call and {n_put_failed} put strikes could not be recovered — "
        f"their last-traded price fell below the no-arbitrage floor, typically due to stale quotes "
        f"or timing differences between the option chain and spot data."
    )
    st.subheader("Implied vs. Historical Volatility")
    st.caption("Compares what the market is currently pricing in (IV) against how much NIFTY has actually moved recently (realized volatility).")

    nifty_hist_iv = pd.read_csv("../data/raw/nifty50_20260819_232859.csv", skiprows=[1, 2])
    nifty_hist_iv = nifty_hist_iv.rename(columns={"Price": "Date"})
    nifty_hist_iv["Close"] = pd.to_numeric(nifty_hist_iv["Close"], errors="coerce")
    nifty_hist_iv["daily_return"] = nifty_hist_iv["Close"].pct_change()

    lookback = st.selectbox("Historical lookback period", ["30 days", "90 days", "1 year (252 days)"], index=1)
    lookback_days = {"30 days": 30, "90 days": 90, "1 year (252 days)": 252}[lookback]

    recent_returns = nifty_hist_iv["daily_return"].dropna().tail(lookback_days)
    realized_vol = recent_returns.std() * np.sqrt(252) * 100  # annualized, as a percentage

    near_atm_iv = df_iv[
        (df_iv["strike"] >= spot_iv * 0.98) & (df_iv["strike"] <= spot_iv * 1.02)
    ]
    avg_market_iv = pd.concat([near_atm_iv["call_iv"], near_atm_iv["put_iv"]]).mean()

    c1, c2, c3 = st.columns(3)
    c1.metric("Near-ATM Market IV (avg)", f"{avg_market_iv:.2f}%")
    c2.metric(f"Realized Volatility ({lookback})", f"{realized_vol:.2f}%")
    iv_premium = avg_market_iv - realized_vol
    c3.metric("IV Premium", f"{iv_premium:+.2f} pts")

    if iv_premium > 3:
        st.info("Market IV is running well above realized volatility — options are pricing in more movement than NIFTY has recently shown. This is common ahead of events (results, policy announcements) or simply reflects a volatility risk premium.")
    elif iv_premium < -3:
        st.info("Market IV is running below realized volatility — options may be relatively cheap compared to how much NIFTY has actually been moving.")
    else:
        st.info("Market IV is roughly in line with realized volatility — no strong signal either way.")

elif selected_module == "Payoff Diagram Visualisation":
    st.header("Payoff Diagram Visualisation")
    st.caption("Build a multi-leg option strategy and see its payoff at expiry.")

    st.subheader("Strategy Legs")
    num_legs = st.number_input("Number of legs", min_value=1, max_value=4, value=1, step=1, key="payoff_num_legs")

    legs = []
    for i in range(int(num_legs)):
        st.markdown(f"**Leg {i+1}**")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            leg_type = st.selectbox("Type", ["call", "put"], key=f"payoff_type_{i}")
        with c2:
            leg_position = st.selectbox("Position", ["Buy (Long)", "Sell (Short)"], key=f"payoff_pos_{i}")
        with c3:
            leg_strike = st.number_input("Strike", min_value=0.01, value=24150.0, step=50.0, key=f"payoff_strike_{i}")
        with c4:
            leg_premium = st.number_input("Premium", min_value=0.0, value=100.0, step=1.0, key=f"payoff_premium_{i}")

        sign = 1 if leg_position == "Buy (Long)" else -1
        legs.append({"type": leg_type, "sign": sign, "strike": leg_strike, "premium": leg_premium})

    if st.button("Plot Payoff"):
        center = np.mean([leg["strike"] for leg in legs])
        spot_range = np.linspace(center * 0.85, center * 1.15, 200)

        total_payoff = np.zeros_like(spot_range)
        for leg in legs:
            if leg["type"] == "call":
                intrinsic = np.maximum(spot_range - leg["strike"], 0)
            else:
                intrinsic = np.maximum(leg["strike"] - spot_range, 0)
            leg_pnl = leg["sign"] * (intrinsic - leg["premium"])
            total_payoff += leg_pnl

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=spot_range, y=total_payoff, mode="lines", name="Strategy P&L", line=dict(width=3)))
        fig.add_hline(y=0, line_dash="dash", line_color="red")
        fig.update_layout(
            title="Strategy Payoff at Expiry",
            xaxis_title="Underlying Price at Expiry",
            yaxis_title="Profit / Loss (₹)",
            template="plotly_white",
        )
        st.plotly_chart(fig, use_container_width=True)

        breakeven_indices = np.where(np.diff(np.sign(total_payoff)))[0]
        if len(breakeven_indices) > 0:
            breakevens = [round(spot_range[i], 2) for i in breakeven_indices]
            st.info(f"Approximate breakeven price(s): {', '.join(str(b) for b in breakevens)}")
        max_profit = total_payoff.max()
        max_loss = total_payoff.min()
        c1, c2 = st.columns(2)
        c1.metric("Max Profit (in shown range)", f"₹{max_profit:,.2f}")
        c2.metric("Max Loss (in shown range)", f"₹{max_loss:,.2f}")
        st.subheader("Strategy Notes")

        leg_summary = [(leg["type"], leg["sign"], leg["strike"]) for leg in legs]

        if len(legs) == 1:
            single_type, single_sign, _ = leg_summary[0]
            if single_sign == 1:
                note = f"**Long {single_type}.** Loss is capped at the premium paid; profit is theoretically unlimited (calls) or capped at the strike (puts). Used to express a directional view with defined, limited risk."
            else:
                note = f"**Short {single_type}.** Profit is capped at the premium received; loss is theoretically unlimited (calls) or very large (puts). Carries significant risk — typically used to collect premium when expecting the market to stay range-bound or move against the option."

        elif len(legs) == 2:
            types = set(l[0] for l in leg_summary)
            signs = set(l[1] for l in leg_summary)
            strikes = [l[2] for l in leg_summary]

            if types == {"call", "put"} and len(signs) == 1 and strikes[0] != strikes[1]:
                position = "Short" if list(signs)[0] == -1 else "Long"
                note = f"**{position} Strangle.** Combines a call and put at different strikes. {'Profits from low realized volatility (the market staying between the two strikes) but carries risk on large moves in either direction.' if position == 'Short' else 'Profits from a large move in either direction, but both premiums must be recovered before turning profitable — needs significant volatility to pay off.'}"
            elif types == {"call", "put"} and len(signs) == 1 and strikes[0] == strikes[1]:
                position = "Short" if list(signs)[0] == -1 else "Long"
                note = f"**{position} Straddle.** Same strike, both call and put. {'Profits if the market stays very close to the strike; a big move in either direction causes losses.' if position == 'Short' else 'Profits from a large move in either direction, but needs a bigger move than a strangle since both options are struck at-the-money (more expensive to buy).'}"
            elif len(types) == 1:
                note = f"**{list(types)[0].capitalize()} Spread.** Combines two of the same option type at different strikes. This caps both maximum profit and maximum loss — a defined-risk way to express a directional view more cheaply than a single option, at the cost of limited upside."
            else:
                note = "**Custom two-leg strategy.** Review the payoff shape above to understand its risk profile — check whether losses are capped on both sides or open-ended."
        else:
            note = "**Multi-leg strategy.** With 3+ legs, review the chart directly — look for whether the payoff flattens out (capped risk) or keeps sloping at the edges (open-ended risk) on either side."

        st.markdown(note)
        st.caption("This note describes the general characteristics of this strategy shape — it is not a recommendation for any specific position.")

elif selected_module == "Value at Risk (VaR) Analysis":
    st.header("Value at Risk (VaR) Analysis")
    st.caption("Estimate portfolio VaR using Parametric (Delta-Normal) and Historical Simulation methods.")

    try:
        df_var = pd.read_csv(os.path.join(DATA_PROCESSED, "final_nifty_option_chain.csv"))
nifty_hist_var = pd.read_csv(os.path.join(DATA_RAW, "nifty50_20260819_232859.csv"), skiprows=[1, 2])
        nifty_hist_var = nifty_hist_var.rename(columns={"Price": "Date"})
        nifty_hist_var["Date"] = pd.to_datetime(nifty_hist_var["Date"])
        for c in ["Close", "High", "Low", "Open", "Volume"]:
            nifty_hist_var[c] = pd.to_numeric(nifty_hist_var[c], errors="coerce")
        nifty_hist_var = nifty_hist_var.sort_values("Date").reset_index(drop=True)
        nifty_hist_var["daily_return"] = nifty_hist_var["Close"].pct_change()
        nifty_hist_var = nifty_hist_var.dropna(subset=["daily_return"])
    except FileNotFoundError:
        st.error("Required data files not found.")
        st.stop()

    spot_var = df_var["spot_price"].iloc[0]
    daily_vol_var = nifty_hist_var["daily_return"].std()

    st.subheader("Portfolio Legs")
    num_var_legs = st.number_input("Number of legs", min_value=1, max_value=4, value=2, step=1, key="var_num_legs")

    var_legs = []
    for i in range(int(num_var_legs)):
        st.markdown(f"**Leg {i+1}**")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            vtype = st.selectbox("Type", ["call", "put"], key=f"var_type_{i}")
        with c2:
            vstrike = st.number_input("Strike", min_value=0.01, value=24200.0, step=50.0, key=f"var_strike_{i}")
        with c3:
            vsize = st.number_input("Position Size (+long/-short)", value=-75, step=75, key=f"var_size_{i}")
        with c4:
            viv = st.number_input("IV (as decimal)", min_value=0.0001, value=0.10, step=0.01, format="%.4f", key=f"var_iv_{i}")
        var_legs.append({"strike": vstrike, "option_type": vtype, "position_size": vsize, "iv": viv})

    confidence_level = st.selectbox("Confidence Level", ["95%", "99%"], key="var_confidence")
    conf_value = 0.95 if confidence_level == "95%" else 0.99

    if st.button("Calculate VaR"):
        var_portfolio = pd.DataFrame(var_legs)
        var_portfolio["T"] = df_var["T"].iloc[0]
        var_portfolio["ltp"] = var_portfolio.apply(
            lambda r: bsm_price(spot_var, r["strike"], r["T"], RISK_FREE_RATE, r["iv"], r["option_type"]), axis=1
        )

        current_val = portfolio_value(var_portfolio)
        net_delta_exp = portfolio_delta_exposure(var_portfolio, spot_var, RISK_FREE_RATE)

        param_var = parametric_var(net_delta_exp, daily_vol_var, confidence=conf_value)
        hist_var = historical_simulation_var(
            var_portfolio, spot_var, current_val, RISK_FREE_RATE,
            nifty_hist_var["daily_return"].values, confidence=conf_value
        )

        c1, c2, c3 = st.columns(3)
        c1.metric("Current Portfolio Value", f"₹{current_val:,.2f}")
        c2.metric(f"Parametric VaR ({confidence_level})", f"₹{param_var:,.2f}")
        c3.metric(f"Historical Sim. VaR ({confidence_level})", f"₹{hist_var:,.2f}")

        if hist_var < 0:
            st.info("Historical Simulation VaR is negative — no losses occurred across the historical sample; this figure reflects retained minimum gain rather than tail risk.")

elif selected_module == "Portfolio Risk Summary":
    st.header("Portfolio Risk Summary")
    st.caption("Aggregate Greeks across multiple positions to see net portfolio exposure.")

    st.subheader("Portfolio Legs")
    num_summary_legs = st.number_input("Number of legs", min_value=1, max_value=6, value=2, step=1, key="summary_num_legs")

    summary_legs = []
    for i in range(int(num_summary_legs)):
        st.markdown(f"**Leg {i+1}**")
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            stype = st.selectbox("Type", ["call", "put"], key=f"summary_type_{i}")
        with c2:
            sspot = st.number_input("Spot", min_value=0.01, value=24150.0, step=1.0, key=f"summary_spot_{i}")
        with c3:
            sstrike = st.number_input("Strike", min_value=0.01, value=24150.0, step=50.0, key=f"summary_strike_{i}")
        with c4:
            ssize = st.number_input("Position Size", value=75, step=75, key=f"summary_size_{i}")
        with c5:
            siv = st.number_input("IV", min_value=0.0001, value=0.15, step=0.01, format="%.4f", key=f"summary_iv_{i}")
        summary_legs.append({"type": stype, "spot": sspot, "strike": sstrike, "size": ssize, "iv": siv})

    days_summary = st.number_input("Days to Expiry", min_value=1, value=7, step=1, key="summary_days")
    T_summary = days_summary / 365.0

    if st.button("Calculate Portfolio Greeks"):
        rows = []
        totals = {"delta": 0, "gamma": 0, "vega": 0, "theta": 0, "rho": 0}
        for leg in summary_legs:
            g = greeks(leg["spot"], leg["strike"], T_summary, RISK_FREE_RATE, leg["iv"], leg["type"])
            weighted = {k: v * leg["size"] for k, v in g.items()}
            for k in totals:
                totals[k] += weighted[k]
            rows.append({"Strike": leg["strike"], "Type": leg["type"], "Size": leg["size"], **weighted})

        st.subheader("Per-Leg Weighted Greeks")
        st.dataframe(pd.DataFrame(rows))

        st.subheader("Net Portfolio Exposure")
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Net Delta", f"{totals['delta']:.2f}")
        c2.metric("Net Gamma", f"{totals['gamma']:.4f}")
        c3.metric("Net Vega", f"{totals['vega']:.2f}")
        c4.metric("Net Theta", f"{totals['theta']:.2f}")
        c5.metric("Net Rho", f"{totals['rho']:.2f}")