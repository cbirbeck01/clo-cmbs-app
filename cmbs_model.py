import streamlit as st
import plotly.graph_objects as go
import numpy_financial as npf

def run_cmbs_model():
    with st.container():
        st.title("CMBS Cash Flow Model")

        if st.button("Back to Home"):
        st.experimental_set_query_params(view="home")
        
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

        #cash flow calcs
        senior_interest = senior_size * (senior_coupon / 100) * years
        mezz_interest = mezz_size * (mezz_coupon / 100) * years
        principal_repayment = senior_size + mezz_size
        noi = total_loan_pool * (noi_yield / 100) * years
        expected_loss = total_loan_pool * (default_rate / 100) * (loss_severity / 100)
        net_cash = noi - expected_loss
        remaining_cash = net_cash
        senior_paid = min(senior_interest, remaining_cash)
        remaining_cash -= senior_paid
        mezz_paid = min(mezz_interest, remaining_cash)
        remaining_cash -= mezz_paid
        principal_paid = min(principal_repayment, remaining_cash)
        remaining_cash -= principal_paid
        equity_paid = max(remaining_cash, 0)

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
                net_cash,
                -senior_paid,
                -mezz_paid,
                -principal_paid,
                equity_paid
            ],
            text=[
                to_millions(net_cash),
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
            plot_bgcolor="white"
        )

        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Tranche Cash Flow Summary")
        st.write(f"Senior Paid: {to_millions(senior_paid)}")
        st.write(f"Mezzanine Paid: {to_millions(mezz_paid)}")
        st.write(f"Principal Paid: {to_millions(principal_paid)}")
        st.write(f"Equity Residual: {to_millions(equity_paid)}")

        st.subheader("Cash Flow Summary")
        st.write(f"**Total NOI** over {years} years: {to_millions(noi)}")
        st.write(f"**Expected Loss:** {to_millions(expected_loss)}")
        st.write(f"**Net Cash:** {to_millions(net_cash)}")

        import pandas as pd

        #Annual cash flow
        years_list = [f"Year {i}" for i in range(1, years + 1)]

        senior_annual = [to_millions(senior_paid / years)] * years
        mezz_annual = [to_millions(mezz_paid / years)] * years
        equity_annual = [to_millions(equity_paid / years)] * years

        cf_table = pd.DataFrame({
            "Year": years_list,
            "Senior Cash Flow": senior_annual,
            "Mezzanine Cash Flow": mezz_annual,
            "Equity Cash Flow": equity_annual
        })

        st.subheader("Investor Payment Schedule")
        st.dataframe(cf_table, use_container_width=True)

        #IRR calcs
        senior_cf = [-senior_size] + [senior_paid / years] * (years - 1) + [senior_paid / years + senior_size]
        mezz_cf = [-mezz_size] + [mezz_paid / years] * (years - 1) + [mezz_paid / years + mezz_size]
        equity_cf = [-equity_size] + [equity_paid / years] * years

        senior_irr = npf.irr(senior_cf) * 100
        mezz_irr = npf.irr(mezz_cf) * 100
        equity_irr = npf.irr(equity_cf) * 100

        st.subheader("Estimated IRRs")
        st.write(f"Senior IRR: {senior_irr:.2f}%")
        st.write(f"Mezzanine IRR: {mezz_irr:.2f}%")
        st.write(f"Equity IRR: {equity_irr:.2f}%")

        if show_advanced:
            st.subheader("Mortgage Characteristics")
            st.write(f"**Avg DSCR:** {avg_dscr}")
            st.write(f"**Avg LTV:** {avg_ltv}%")
            st.write(f"**Retail Exposure:** {retail_pct}%")
            st.write(f"**Office Exposure:** {office_pct}%")
            st.write(f"**Multi-Family Exposure:** {multifamily_pct}%")
