import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy_financial as npf
from cmbs_periodic_cashflow import simulate_cmbs_cashflows

def run_cmbs_model():
    st.title("CMBS Cash Flow Model")

    if st.button("Back to Home"):
        st.query_params["view"] = "home"
        st.rerun()

    with st.sidebar:
        st.header("CMBS Deal Inputs")

        total_loan_pool = st.number_input("Total Loan Pool ($)", value=100_000_000, step=1_000_000)
        years = st.number_input("Investment Horizon (Years)", 1, 10, 5)
        st.markdown("### Tranche Structure")
        senior_size = st.number_input("Senior Tranche ($)", value=65_000_000, step=1_000_000)
        mezz_size = st.number_input("Mezzanine Tranche ($)", value=25_000_000, step=1_000_000)
        equity_size = total_loan_pool - senior_size - mezz_size
        senior_coupon = st.slider("Senior Interest Rate (%)", 2.0, 6.0, 4.0)
        mezz_coupon = st.slider("Mezzanine Interest Rate (%)", 5.0, 12.0, 8.0)
        scenario = st.selectbox("Stress Scenario", ["Custom", "Mild", "Moderate", "Severe"])

        st.header("Assumptions")
        if scenario == "Custom":
            noi_yield = st.slider("NOI Yield (%)", 4.0, 10.0, 6.0)
            default_rate = st.slider("Default Rate (%)", 0.0, 20.0, 5.0)
            loss_severity = st.slider("Loss Severity (%)", 10.0, 70.0, 40.0)
        elif scenario == "Mild":
            noi_yield = 6.5
            default_rate = 2.0
            loss_severity = 30.0
        elif scenario == "Moderate":
            noi_yield = 6.0
            default_rate = 5.0
            loss_severity = 40.0
        elif scenario == "Severe":
            noi_yield = 5.0
            default_rate = 12.0
            loss_severity = 55.0

    df, sr_irr, mz_irr, eq_irr = simulate_cmbs_cashflows(
        total_loan_pool,
        senior_size,
        mezz_size,
        equity_size,
        senior_coupon,
        mezz_coupon,
        default_rate,
        loss_severity,
        noi_yield,
        years
    )

    senior_interest_paid = df["Senior Interest"].sum()
    senior_principal = df["Senior Principal"].sum()
    mezz_interest_paid = df["Mezz Interest"].sum()
    mezz_principal = df["Mezz Principal"].sum()
    equity_paid = df["Equity Cash"].sum()

    senior_paid = senior_interest_paid + senior_principal
    mezz_paid = mezz_interest_paid + mezz_principal
    principal_paid = senior_principal + mezz_principal
    net_cash = senior_paid + mezz_paid + equity_paid
    expected_loss = total_loan_pool * (default_rate / 100) * (loss_severity / 100)

    def to_millions(value):
        return f"${value / 1_000_000:.2f}M"

    fig = go.Figure(go.Waterfall(
        name="CMBS Waterfall",
        orientation="v",
        measure=["relative", "relative", "relative", "relative"],
        x=["Available Cash", "Senior Tranche", "Mezzanine Tranche", "Equity Tranche"],
        y=[net_cash, -senior_paid, -mezz_paid, equity_paid if equity_paid > 0 else -1_000_000],
        text=[
            to_millions(net_cash),
            to_millions(senior_paid),
            to_millions(mezz_paid),
            to_millions(equity_paid)
        ],
        textposition="inside",
        insidetextanchor="middle",
        hoverinfo="x+text",
        connector={"line": {"color": "#2d6cd2", "width": 1.5}},
        decreasing={"marker": {"color": "#2d6cd2"}},
        increasing={"marker": {"color": "#2d6cd2"}},
        totals={"marker": {"color": "#27a119"}},
        opacity=0.75
    ))

    fig.update_layout(
        title="CMBS Tranche Waterfall Distribution",
        title_font_size=22,
        xaxis_title="Cash Flow Step",
        yaxis_title="Amount ($)",
        font=dict(family="Helvetica", size=14, color="black"),
        height=500,
        plot_bgcolor="rgba(0,0,0,0)"
    )

    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Tranche IRRs")
    col1, col2, col3 = st.columns(3)
    col1.metric("Senior IRR", f"{sr_irr:.2f}%")
    col2.metric("Mezzanine IRR", f"{mz_irr:.2f}%")
    col3.metric("Equity IRR", f"{eq_irr:.2f}%")

    st.subheader("Tranche Summary")
    col4, col5 = st.columns(2)
    with col4:
        st.metric("Senior Paid", to_millions(senior_paid))
        st.metric("Mezzanine Paid", to_millions(mezz_paid))
        st.metric("Principal Paid", to_millions(principal_paid))
    with col5:
        st.metric("Equity Residual", to_millions(equity_paid))
        st.metric("Expected Loss", to_millions(expected_loss))
        st.metric("Net Cash Distributed", to_millions(net_cash))

    st.subheader("Monthly Cashflows")
    df.rename(columns={"Mezz Interest": "Mezzanine Interest"}, inplace=True)
    st.dataframe(df, use_container_width=True)
