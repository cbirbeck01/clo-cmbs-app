import streamlit as st
import plotly.graph_objects as go
import numpy_financial as npf
from cmbs_periodic_cashflow import simulate_cmbs_cashflows

def create_cmbs_annual_cashflow_summary(df, years):
    df["Year"]=(df["Month"]-1)//12+1
    summary=df.groupby("Year")[["Senior Interest","Senior Principal","Mezz Interest","Mezz Principal","Equity Cash"]].sum().reset_index()
    summary["Senior Cash Flow"]=summary["Senior Interest"]+summary["Senior Principal"]
    summary["Mezzanine Cash Flow"]=summary["Mezz Interest"]+summary["Mezz Principal"]
    summary["Equity Cash Flow"]=summary["Equity Cash"]
    summary["Year Label"]=summary["Year"].apply(lambda x:f"Year {x}")
    return summary[["Year Label","Senior Cash Flow","Mezzanine Cash Flow","Equity Cash Flow"]]

def run_cmbs_model():

    with st.container():
        st.title("CMBS Cash Flow Model")

        if st.button("Back to Home"):
            st.query_params["view"] = "home"
            st.rerun()

        with st.sidebar:
            st.header("CMBS Deal Inputs")

            total_loan_pool = st.number_input("Total Loan Pool ($)", value=100_000_000, step=1_000_000, key="cmbs_total_pool")
            years = st.number_input("Investment Horizon (Years)", 1, 10, 5, key="cmbs_years")
            st.markdown("### Tranche Structure")
            senior_size = st.number_input("Senior Tranche ($)", value=65_000_000, step=1_000_000, key="cmbs_senior_size")
            mezz_size = st.number_input("Mezzanine Tranche ($)", value=25_000_000, step=1_000_000, key="cmbs_mezz_size")
            equity_size = total_loan_pool - senior_size - mezz_size
            senior_coupon = st.slider("Senior Interest Rate (%)", 2.0, 6.0, 4.0, key="cmbs_senior_coupon")
            mezz_coupon = st.slider("Mezzanine Interest Rate (%)", 5.0, 12.0, 8.0, key="cmbs_mezz_coupon")
            scenario = st.selectbox("Stress Scenario", ["Custom", "Mild", "Moderate", "Severe"], key="cmbs_scenario")

            st.header("Assumptions")
            if scenario == "Custom":
                noi_yield = st.slider("NOI Yield (%)", 4.0, 10.0, 6.0, key="cmbs_noi_yield")
                default_rate = st.slider("Default Rate (%)", 0.0, 20.0, 5.0, key="cmbs_default_rate")
                loss_severity = st.slider("Loss Severity (%)", 10.0, 70.0, 40.0, key="cmbs_loss_severity")
            elif scenario =="Mild":
                noi_yield =6.5
                default_rate = 2.0
                loss_severity= 30.0
            elif scenario== "Moderate":
                noi_yield=6.0
                default_rate=5.0
                loss_severity = 40.0
            elif scenario=="Severe":
                noi_yield=5.0
                default_rate= 12.0
                loss_severity=55.0

            st.markdown("---")
            show_advanced = st.checkbox("Advanced Options", key="cmbs_advanced_toggle")

            if show_advanced:
                st.markdown("### Mortgage Characteristics")
                avg_dscr = st.slider("Avg DSCR", 0.5, 3.0, 1.5, step=0.1, key="cmbs_dscr")
                avg_ltv = st.slider("Avg LTV (%)", 50, 100, 70, step=1,key="cmbs_ltv")
                st.markdown("#### Property Type Mix (Must Sum to 100%)")
                retail_pct = st.number_input("Retail Exposure (%)", value=25,step=5,key="cmbs_retail")
                office_pct = st.number_input("Office Exposure (%)",value=35,step=5, key="cmbs_office")
                multifamily_pct = st.number_input("Multi-Family Exposure (%)",value=40,step=5, key="cmbs_multifamily")
                total_exposure = retail_pct + office_pct + multifamily_pct
                if total_exposure > 100:
                    st.warning(f"Total property exposure is {total_exposure}%. Please reduce one or more categories.")
                if avg_ltv>80:
                    default_rate += 2
                if avg_dscr<1.2:
                    loss_severity+=5
                if retail_pct >40:
                    loss_severity += 5
                if office_pct>40:
                    default_rate += 2
                if multifamily_pct> 50:
                    loss_severity=max(loss_severity - 3, 0)


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

        senior_paid = df["Senior Interest"].sum() + df["Senior Principal"].sum()
        mezz_paid = df["Mezz Interest"].sum() + df["Mezz Principal"].sum()
        principal_paid = df["Senior Principal"].sum() + df["Mezz Principal"].sum()
        equity_paid = df["Equity Cash"].sum()

        def to_millions(value):
            return f"${value / 1_000_000:.2f}M"

        fig = go.Figure(go.Waterfall(
            name="CMBS Waterfall",
            orientation="v",
            measure=["absolute", "relative", "relative", "relative", "relative"],
            x=[
                "Net Available Cash",
                "Senior Interest",
                "Mezzanine Interest",
                "Principal",
                "Equity Residual"
            ],
            y=[
                senior_paid + mezz_paid + principal_paid + equity_paid,
                -senior_paid,
                -mezz_paid,
                -principal_paid,
                equity_paid
            ],
            text = [
            to_millions(senior_paid + mezz_paid + principal_paid + equity_paid),
            to_millions(senior_paid),
            to_millions(mezz_paid),
            to_millions(principal_paid),
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

        expected_loss = total_loan_pool * (default_rate / 100) * (loss_severity / 100)
        net_cash = senior_paid + mezz_paid + principal_paid + equity_paid

        st.subheader("Tranche Summary")

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Senior Paid", to_millions(senior_paid))
            st.metric("Mezzanine Paid", to_millions(mezz_paid))
            st.metric("Principal Paid", to_millions(principal_paid))
        with col2:
            st.metric("Equity Residual", to_millions(equity_paid))
            st.metric("Expected Loss", to_millions(expected_loss))
            st.metric("Net Cash Distributed", to_millions(net_cash))

        import pandas as pd

        cf_table = create_cmbs_annual_cashflow_summary(df, years)
        cf_table["Senior Cash Flow"] = cf_table["Senior Cash Flow"].apply(to_millions)
        cf_table["Mezzanine Cash Flow"] = cf_table["Mezzanine Cash Flow"].apply(to_millions)
        cf_table["Equity Cash Flow"] = cf_table["Equity Cash Flow"].apply(to_millions)

        st.subheader("Annual Cash Flow Summary")
        st.dataframe(cf_table, use_container_width=True)

        st.subheader("Tranche IRRs")
        col1, col2, col3 = st.columns(3)
        col1.metric("Senior IRR", f"{sr_irr:.2f}%")
        col2.metric("Mezzanine IRR", f"{mz_irr:.2f}%")
        col3.metric("Equity IRR", f"{eq_irr:.2f}%" if not pd.isna(eq_irr) else "n/a")

        st.subheader("Monthly Cashflows")
        df.rename(columns={"Mezz Interest": "Mezzanine Interest"}, inplace=True)
        st.dataframe(df, use_container_width=True)

        if show_advanced:
            st.subheader("Mortgage Characteristics")
            st.write(f"**Avg DSCR:** {avg_dscr}")
            st.write(f"**Avg LTV:** {avg_ltv}%")
            st.write(f"**Retail Exposure:** {retail_pct}%")
            st.write(f"**Office Exposure:** {office_pct}%")
            st.write(f"**Multi-Family Exposure:** {multifamily_pct}%")
