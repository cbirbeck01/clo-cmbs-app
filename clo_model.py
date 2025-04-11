import streamlit as st
import plotly.graph_objects as go
import numpy_financial as npf
import pandas as pd


def run_clo_model():
    st.title("CLO Waterfall")

    if st.button("Back to Home"):
        st.query_params["view"] = "home"

    with st.sidebar:
        st.header("Tranche Inputs")
        total_collateral = st.number_input("Total Collateral ($)", value=110_000_000, step=1_000_000)
        senior_size = st.number_input("Senior Size ($)", value=70_000_000, step=1_000_000)
        mezz_size = st.number_input("Mezzanine Size ($)", value=30_000_000, step=1_000_000)

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

    senior_paid = min(senior_interest, remaining_cash)
    remaining_cash -= senior_paid

    mezz_paid = min(mezz_interest, remaining_cash)
    remaining_cash -= mezz_paid

    principal_paid = min(principal_repayment, remaining_cash)
    remaining_cash -= principal_paid

    equity_paid = max(remaining_cash, 0)

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
            width=1200,
            autosize=False,
            height=750,
            margin=dict(t=50, b=40, l=40, r=50),
            xaxis=dict(range=[0, 1], visible=False),
            yaxis=dict(range=[0, y_base + 1], visible=False),
            title="CLO Tranche Fill Funnel",
            plot_bgcolor="white",
        )

        left_spacer, center_col, right_spacer = st.columns([0.1, 0.8, 0.1])

        with center_col:
            st.plotly_chart(fig, use_container_width=False)

        # IRR Calculations
        senior_cf = [-senior_size] + [senior_paid / years] * (years - 1) + [senior_paid / years + senior_size]
        mezz_cf = [-mezz_size] + [mezz_paid / years] * (years - 1) + [mezz_paid / years + mezz_size]
        equity_cf = [-equity_size] + [equity_paid / years] * years

        senior_irr = npf.irr(senior_cf) * 100
        mezz_irr = npf.irr(mezz_cf) * 100
        equity_irr = npf.irr(equity_cf) * 100

        irr_df = pd.DataFrame({
            "Tranche": ["Senior", "Mezzanine", "Equity"],
            "Initial Investment": [senior_size, mezz_size, equity_size],
            "Total Paid": [senior_paid + senior_size, mezz_paid + mezz_size, equity_paid],
            "IRR (%)": [f"{senior_irr:.2f}", f"{mezz_irr:.2f}", f"{equity_irr:.2f}"]
        })

        st.subheader("Tranche IRR Summary Table")
        st.dataframe(irr_df, use_container_width=True)

    elif chart_view == "Waterfall View":
        senior_flag = status_flag(senior_paid, senior_interest)
        mezz_flag = status_flag(mezz_paid, mezz_interest)
        principal_flag = status_flag(principal_paid, principal_repayment)
        equity_flag = status_flag(equity_paid, 0.01)

        x_labels = [
            "Available Cash",
            "Senior Interest<br>" + senior_flag,
            "Mezzanine Interest<br>" + mezz_flag,
            "Principal<br>" + principal_flag,
            "Equity<br>" + equity_flag
        ]

        y_values = [
            available_cash,
            -senior_paid,
            -mezz_paid,
            -principal_paid,
            -equity_paid if equity_paid > 0 else -1_000_000  # force visible
        ]

        measure = ["relative", "relative", "relative", "relative", "relative"]
        show_percentage = st.checkbox("Show Percent of Expected Payout", value=False)

        def format_millions(value):
            return f"{value / 1_000_000:.1f}M"

        text_labels = [
            format_millions(available_cash),
            format_millions(senior_paid) + (
                f" ({(senior_paid / senior_interest * 100):.1f}%)" if show_percentage else ""),
            format_millions(mezz_paid) + (f" ({(mezz_paid / mezz_interest * 100):.1f}%)" if show_percentage else ""),
            format_millions(principal_paid) + (
                f" ({(principal_paid / principal_repayment * 100):.1f}%)" if show_percentage else ""),
            format_millions(equity_paid)
        ]

        hover_text = [
            f"Available Cash: ${available_cash:,.0f}",
            f"Senior Interest: ${senior_paid:,.0f} of ${senior_interest:,.0f} {senior_flag}"
            + (f" ({(senior_paid / senior_interest * 100):.1f}%)" if show_percentage else ""),
            f"Mezzanine Interest: ${mezz_paid:,.0f} of ${mezz_interest:,.0f} {mezz_flag}"
            + (f" ({(mezz_paid / mezz_interest * 100):.1f}%)" if show_percentage else ""),
            f"Principal: ${principal_paid:,.0f} of ${principal_repayment:,.0f} {principal_flag}"
            + (f" ({(principal_paid / principal_repayment * 100):.1f}%)" if show_percentage else ""),
            f"Equity Residual: ${equity_paid:,.0f} {equity_flag}"
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
                title=dict(text="Tranche", font=dict(color="black", size=14)),
                tickfont=dict(color="black")
            ),
            yaxis=dict(
                title=dict(text="Cash Flow ($)", font=dict(color="black", size=14)),
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
        irr_df = pd.DataFrame({
            "Tranche": ["Senior", "Mezzanine", "Equity"],
            "Initial Investment": [senior_size, mezz_size, equity_size],
            "Total Paid": [senior_paid + senior_size, mezz_paid + mezz_size, equity_paid],
            "IRR (%)": [f"{senior_irr:.2f}", f"{mezz_irr:.2f}", f"{equity_irr:.2f}"]
        })
        st.subheader("Tranche IRR Summary Table")
        st.dataframe(irr_df, use_container_width=True)



        import io

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            irr_df.to_excel(writer, index=False, sheet_name='IRR Summary')
            writer.close()

        st.download_button(
            label="📥 Download IRR Table as Excel",
            data=output.getvalue(),
            file_name="clo_tranche_irr_summary.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )




