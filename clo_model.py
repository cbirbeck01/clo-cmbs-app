import streamlit as st
import plotly.graph_objects as go
import numpy_financial as npf
import pandas as pd


def create_clo_annual_cashflow_summary(df, years):
    df["Year"]=(df["Month"]-1)//12+1
    summary=df.groupby("Year")[["Senior Interest","Senior Principal","Mezz Interest","Mezz Principal","Equity Cash"]].sum().reset_index()
    summary["Senior Cash Flow"]=summary["Senior Interest"]+summary["Senior Principal"]
    summary["Mezzanine Cash Flow"]=summary["Mezz Interest"]+summary["Mezz Principal"]
    summary["Equity Cash Flow"]=summary["Equity Cash"]
    summary["Year Label"]=summary["Year"].apply(lambda x:f"Year {x}")
    return summary[["Year Label","Senior Cash Flow","Mezzanine Cash Flow","Equity Cash Flow"]]


def run_clo_model():

    st.title("CLO Waterfall")

    if st.button("Back to Home"):
        st.query_params["view"] = "home"
        st.rerun()

    with st.sidebar:
        st.header("Deal Inputs")
        total_collateral = st.number_input("Total Collateral ($)", value=110_000_000, step=1_000_000)
        senior_size = st.number_input("Senior Size ($)", value=70_000_000, step=1_000_000)
        mezz_size = st.number_input("Mezzanine Size ($)", value=40_000_000, step=1_000_000)

        equity_size = total_collateral - senior_size - mezz_size

        scenario = st.selectbox("Stress Scenario", ["Custom", "Mild", "Moderate", "Severe"])

        st.header("Assumptions")
        st.markdown("Scenarios account for default rates, recovery rates, and collateral yield according to severity. Use 'Custom' for manual input.")
        if scenario == "Custom":
            default_rate = st.slider("Default Rate (%)", 0.0, 40.0, 10.0)
            recovery_rate = st.slider("Recovery Rate (%)", 0.0, 100.0, 30.0)
            collateral_yield = st.slider("Collateral Yield (%)", 5.0, 20.0, 10.0)
        elif scenario == "Mild":
            default_rate = 5.0
            recovery_rate = 40.0
            collateral_yield = 10.0
        elif scenario == "Moderate":
            default_rate = 15.0
            recovery_rate = 30.0
            collateral_yield = 9.0
        elif scenario == "Severe":
            default_rate = 30.0
            recovery_rate = 20.0
            collateral_yield = 7.0

        st.markdown(f"""
        **Scenario Settings**  
        - Default Rate: `{default_rate}%`  
        - Recovery Rate: `{recovery_rate}%`  
        - Collateral Yield: `{collateral_yield}%`
        """)
        senior_rate = st.number_input("Senior Coupon (%)", 1.0, 10.0, 4.0, step=0.5)
        mezz_rate = st.number_input("Mezz Coupon (%)", 1.0, 15.0, 8.0, step=0.5)
        years = st.number_input("Years", 1, 10, 5)

        show_advanced = st.checkbox("Advanced Options")

        if show_advanced:
            st.markdown("### Loan Pool Characteristics")
            st.markdown("**Senior Loan Characteristics**")
            senior_coupon = st.slider("Senior Avg Coupon (%)", 2.0, 10.0, 4.5, step=0.5)
            senior_default = st.slider("Senior Default Rate (%)", 0.0, 20.0, 5.0, step=0.1)
            senior_yield = st.slider("Senior Recovery Rate (%)", 0.0, 100.0, 45.0, step=0.5)

            st.markdown("**Mezzanine Loan Characteristics**")
            mezz_coupon = st.slider("Mezzanine Avg Coupon (%)", 5.0, 12.0, 7.5, step=0.5)
            mezz_default = st.slider("Mezzanine Default Rate (%)", 0.0, 40.0, 15.0, step=0.1)
            mezz_recovery = st.slider("Mezzanine Recovery Rate (%)", 0.0, 100.0, 30.0, step=0.5)

            st.markdown("**Equity Assumptions (Residual)**")
            equity_yield = st.slider("Equity Target Yield (%)", 0.0, 25.0, 12.0, step=0.1)

        st.markdown("---")
        show_stats = st.checkbox("Add Collateral Pool Characteristics (Optional)")

        if show_stats:
            st.markdown("### Collateral Quality Metrics")
            was = st.slider("Weighted Avg Spread (bps)", 250, 600, 375)
            avg_ltv = st.slider("Avg LTV (%)", 50, 100, 70)
            avg_dscr = st.slider("Avg DSCR", 0.5, 3.0, 1.5)

            if avg_ltv <= 60:
                default_rate = max(default_rate - 2, 0)
            elif avg_ltv > 80:
                default_rate += 3

            if avg_dscr >= 1.5:
                recovery_rate = min(recovery_rate + 3, 100)
            elif avg_dscr < 1.2:
                recovery_rate = max(recovery_rate - 4, 0)

            collateral_yield = round(5 + was / 10000, 2)

    int_income = total_collateral * (collateral_yield / 100) * years
    default_loss = total_collateral * (default_rate / 100)
    recoveries = default_loss * (recovery_rate / 100)
    available_cash = int_income + recoveries - default_loss

    senior_interest = senior_size * (senior_rate / 100) * years
    mezz_interest = mezz_size * (mezz_rate / 100) * years
    principal_repayment = senior_size + mezz_size

    remaining_cash = available_cash

    from clo_periodic_cashflow import simulate_clo_cashflows

    df, sr_irr, mz_irr, eq_irr = simulate_clo_cashflows(
        total_collateral,
        senior_size,
        mezz_size,
        equity_size,
        senior_rate,
        mezz_rate,
        default_rate,
        recovery_rate,
        collateral_yield,
        years
    )

    # Use cumulative results for visuals
    senior_paid = df["Senior Interest"].sum() + df["Senior Principal"].sum()
    mezz_paid = df["Mezz Interest"].sum() + df["Mezz Principal"].sum()
    principal_paid = df["Senior Principal"].sum() + df["Mezz Principal"].sum()
    equity_paid = df["Equity Cash"].sum()
    expected_loss = total_collateral * (default_rate / 100) * (1 - recovery_rate / 100)
    net_cash = senior_paid + mezz_paid + principal_paid + equity_paid

    chart_view = st.selectbox("Select Chart View", ["Tranche View", "Waterfall View"], index=0)

    def status_flag(actual, expected):
        if actual >= expected:
            return "✅"
        elif actual > 0:
            return "⚠️"
        else:
            return "❌"

    if chart_view == "Tranche View":
        tranches = list(reversed([
            {"label": "Senior", "expected": senior_interest, "paid": senior_paid, "color": "rgba(1,31,75,0.7)"},
            {"label": "Mezzanine", "expected": mezz_interest, "paid": mezz_paid, "color": "rgba(0,91,150,0.6)"},
            {"label": "Principal", "expected": principal_repayment, "paid": principal_paid, "color": "rgba(100,151,177, 0.5)"},
            {"label": "Equity", "expected": equity_paid + 1e-6, "paid": equity_paid, "color": "rgba(179,205,224, 0.4)"}
        ]))

        fig = go.Figure()
        y_base = 0
        bar_gap = 0.3
        bar_height = 0.9

        for i, tranche in enumerate(tranches):
            pct_paid = min(tranche["paid"] / tranche["expected"], 1.0)
            filled_height = bar_height * pct_paid
            empty_height = bar_height - filled_height
            color = tranche["color"]
            label = tranche["label"]
            flag = status_flag(tranche["paid"], tranche["expected"])

            fig.add_shape(type="rect", x0=0.3, x1=0.7, y0=y_base, y1=y_base + filled_height, fillcolor=color, line=dict(color="black", width=1), layer="below")

            if empty_height > 0:
                fig.add_shape(type="rect", x0=0.3, x1=0.7, y0=y_base + filled_height, y1=y_base + bar_height, fillcolor="rgba(230,230,230,0.3)", line=dict(color="gray", width=0.5), layer="below")

            fig.add_annotation(x=0.75, y=y_base + bar_height / 2, text=f"<b>{label}</b> {flag}<br>${tranche['paid']:,.0f}", showarrow=False, font=dict(size=14, color="black", family="Helvetica"), align="left", xanchor="left")

            fig.add_annotation(
                x=0.3, y=y_base + bar_height / 2,
                ax=0.15, ay=y_base + bar_height / 2,
                xref="x", yref="y",
                axref="x", ayref="y",
                showarrow=True,
                arrowhead=2,
                arrowsize=1,
                arrowwidth=2,
                arrowcolor="gray"
            )

            y_base += bar_height + bar_gap

        fig.add_shape(type="rect", x0=0.0, x1=0.15, y0=0, y1=y_base - bar_gap, fillcolor="rgba(180,220,255,0.6)", line=dict(color="black", width=1), layer="below")
        fig.add_annotation(x=0.075, y=(y_base - bar_gap) / 2, text=f"<b>Loan Pool</b><br>${total_collateral:,.0f}", showarrow=False, font=dict(size=13, color="black"), align="center")

        fig.update_layout(
                autosize=True,
                height=750,
                margin=dict(t=50, l=40, r=40, b=50),
                xaxis=dict(range=[0, 1], visible=False),
                yaxis=dict(range=[0, y_base + 1], visible=False),
                title="CLO Tranche Fill Funnel",
                plot_bgcolor="rgba(0,0,0,0)"
            )


        left_spacer, center_col, right_spacer = st.columns([0.1, 0.8, 0.1])

        with st.container():
            st.markdown(
                """
                <style>
                .full-width-chart .js-plotly-plot {
                    width: 100% !important;
                    max-width: 1400px;
                    margin: auto;
                }
                </style>
                """,
                unsafe_allow_html=True,
            )

            chart_html_id = "full-width-chart"

            # Start custom wrapper
            st.markdown(f'<div class="{chart_html_id}">', unsafe_allow_html=True)

            # Render the chart using container width
            st.plotly_chart(fig, use_container_width=True)

        # Tranche Summary Breakdown
        senior_interest_paid=df["Senior Interest"].sum()
        senior_principal_paid=df["Senior Principal"].sum()
        mezz_interest_paid=df["Mezzanine Interest"].sum() if "Mezzanine Interest" in df.columns else df["Mezz Interest"].sum()
        mezz_principal_paid=df["Mezz Principal"].sum()
        equity_paid=df["Equity Cash"].sum()

        expected_loss=total_collateral*(default_rate/100)*(1-recovery_rate/100)
        net_cash=senior_interest_paid+senior_principal_paid+mezz_interest_paid+mezz_principal_paid+equity_paid

        st.subheader("Tranche Summary")
        col1,col2,col3=st.columns(3)
        with col1:
            st.metric("Senior Interest",f"${senior_interest_paid/1_000_000:.2f}M")
            st.metric("Senior Principal",f"${senior_principal_paid/1_000_000:.2f}M")
        with col2:
            st.metric("Mezzanine Interest",f"${mezz_interest_paid/1_000_000:.2f}M")
            st.metric("Mezzanine Principal",f"${mezz_principal_paid/1_000_000:.2f}M")
        with col3:
            st.metric("Equity Residual",f"${equity_paid/1_000_000:.2f}M")
            st.metric("Expected Loss",f"${expected_loss/1_000_000:.2f}M")
            st.metric("Net Cash Distributed",f"${net_cash/1_000_000:.2f}M")


            # Close the wrapper
            st.markdown("</div>", unsafe_allow_html=True)

        # IRR Calculations
        senior_cf = [-senior_size] + [senior_paid / years] * (years - 1) + [senior_paid / years + senior_size]
        mezz_cf = [-mezz_size] + [mezz_paid / years] * (years - 1) + [mezz_paid / years + mezz_size]
        equity_cf = [-equity_size] + [equity_paid / years] * years

        senior_irr = npf.irr(senior_cf) * 100
        mezz_irr = npf.irr(mezz_cf) * 100
        equity_irr = npf.irr(equity_cf) * 100

        st.subheader("Tranche IRRs")
        col1, col2, col3 = st.columns(3)
        col1.metric("Senior IRR", f"{sr_irr:.2f}%")
        col2.metric("Mezzanine IRR", f"{mz_irr:.2f}%")
        col3.metric("Equity IRR", f"{eq_irr:.2f}%")

        st.subheader("Annual Cash Flow Summary")
        annual_df = create_clo_annual_cashflow_summary(df, years)
        for col in ["Senior Cash Flow", "Mezzanine Cash Flow", "Equity Cash Flow"]:
            annual_df[col] = annual_df[col].apply(lambda x: f"${x / 1_000_000:.2f}M")
        st.dataframe(annual_df, use_container_width=True)

        # Monthly Cashflows
        df.rename(columns={"Mezz Interest":"Mezzanine Interest"},inplace=True)
        df.rename(columns={"Mezz Principal":"Mezzanine Principal"},inplace=True)
        st.subheader("Monthly Cashflows")
        st.dataframe(df,use_container_width=True)

#WATERFALL VIEW:

    elif chart_view == "Waterfall View":
        senior_flag = status_flag(senior_paid, senior_interest)
        mezz_flag = status_flag(mezz_paid, mezz_interest)
        principal_flag = status_flag(principal_paid, principal_repayment)
        equity_flag = status_flag(equity_paid, 0.01)
        expected_senior_total=senior_interest+principal_repayment*(senior_size/(senior_size+mezz_size))
        expected_mezz_total=mezz_interest+principal_repayment*(mezz_size/(senior_size+mezz_size))


        x_labels = [
        "Available Cash",
        "Senior",
        "Mezzanine",
        "Equity"
        ]


        y_values = [
        available_cash,
        -senior_paid,
        -mezz_paid,
        equity_paid if equity_paid > 0 else -1_000_000
        ]


        measure = ["relative","relative","relative","relative"]
        show_percentage = st.checkbox("Show Percent of Expected Payout", value=False)

        def format_millions(value):
            return f"{value / 1_000_000:.1f}M"

        text_labels=[
        format_millions(available_cash),
        format_millions(senior_paid)+(f" ({(senior_paid/expected_senior_total*100):.1f}%)" if show_percentage else ""),
        format_millions(mezz_paid)+(f" ({(mezz_paid/expected_mezz_total*100):.1f}%)" if show_percentage else ""),
        format_millions(equity_paid)
        ]




        

        fig = go.Figure(go.Waterfall(
            name="CLO Waterfall",
            orientation="v",
            measure=measure,
            x=x_labels,
            y=y_values,
            text=text_labels,
            textposition="inside",
            texttemplate="%{text}",
            insidetextfont=dict(color="white", size=14, family="Helvetica"),
            hovertext=hover_text,
            hoverinfo="text",
            connector={"line": {"color": "#666", "width": 1.5}},
            decreasing={"marker": {"color": "#003366"}},
            increasing={"marker": {"color": "#cc0000"}},
            totals={"marker": {"color": "#27a119"}},
            opacity=0.85
        ))

        fig.update_layout(
            title="CLO Tranche Waterfall Distribution",
            showlegend=False,
            xaxis=dict(
                title=dict(text="Cash Flow Step", font=dict(color="black", size=14)),
                tickfont=dict(color="black")
            ),
            yaxis=dict(
                title=dict(text="Amount ($)", font=dict(color="black", size=14)),
                tickfont=dict(color="black"),
                range=[-available_cash * 1.05, available_cash * 1.05]
            ),
            margin=dict(t=50, l=80, r=80, b=120),
            autosize=True,
            height=750,
            transition_duration=500
        )
        # Recreate IRR table for CSV download
        senior_cf = [-senior_size] + [senior_paid / years] * (years - 1) + [senior_paid / years + senior_size]
        mezz_cf = [-mezz_size] + [mezz_paid / years] * (years - 1) + [mezz_paid / years + mezz_size]
        equity_cf = [-equity_size] + [equity_paid / years] * years

        senior_irr = npf.irr(senior_cf) * 100
        mezz_irr = npf.irr(mezz_cf) * 100
        equity_irr = npf.irr(equity_cf) * 100
        st.plotly_chart(fig)
        # IRR Summary
        st.subheader("Tranche IRRs")
        col1,col2,col3=st.columns(3)
        col1.metric("Senior IRR",f"{senior_irr:.2f}%")
        col2.metric("Mezzanine IRR",f"{mezz_irr:.2f}%")
        col3.metric("Equity IRR",f"{equity_irr:.2f}%")



        # Tranche Summary Breakdown
        senior_interest_paid=df["Senior Interest"].sum()
        senior_principal_paid=df["Senior Principal"].sum()
        mezz_interest_paid=df["Mezzanine Interest"].sum() if "Mezzanine Interest" in df.columns else df["Mezz Interest"].sum()
        mezz_principal_paid=df["Mezz Principal"].sum()
        equity_paid=df["Equity Cash"].sum()

        expected_loss=total_collateral*(default_rate/100)*(1-recovery_rate/100)
        net_cash=senior_interest_paid+senior_principal_paid+mezz_interest_paid+mezz_principal_paid+equity_paid

        st.subheader("Tranche Summary")
        col1,col2,col3=st.columns(3)
        with col1:
            st.metric("Senior Interest",f"${senior_interest_paid/1_000_000:.2f}M")
            st.metric("Senior Principal",f"${senior_principal_paid/1_000_000:.2f}M")
        with col2:
            st.metric("Mezzanine Interest",f"${mezz_interest_paid/1_000_000:.2f}M")
            st.metric("Mezzanine Principal",f"${mezz_principal_paid/1_000_000:.2f}M")
        with col3:
            st.metric("Equity Residual",f"${equity_paid/1_000_000:.2f}M")
            st.metric("Expected Loss",f"${expected_loss/1_000_000:.2f}M")
            st.metric("Net Cash Distributed",f"${net_cash/1_000_000:.2f}M")


        # Annual Summary
        st.subheader("Annual Cash Flow Summary")
        annual_df=create_clo_annual_cashflow_summary(df,years)
        for col in ["Senior Cash Flow","Mezzanine Cash Flow","Equity Cash Flow"]:
            annual_df[col]=annual_df[col].apply(lambda x:f"${x/1_000_000:.2f}M")
        st.dataframe(annual_df,use_container_width=True)

        # Monthly Cashflows
        df.rename(columns={"Mezz Interest":"Mezzanine Interest"},inplace=True)
        df.rename(columns={"Mezz Principal":"Mezzanine Principal"},inplace=True)
        st.subheader("Monthly Cashflows")
        st.dataframe(df,use_container_width=True)






