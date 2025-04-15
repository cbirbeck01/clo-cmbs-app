import pandas as pd
import numpy_financial as npf

def simulate_cmbs_cashflows(total_loan_pool,senior_size,mezz_size,equity_size,senior_rate,mezz_rate,default_rate,loss_severity,noi_yield,years,reinvest_toggle=False):
    months=years*12
    senior_bal=senior_size
    mezz_bal=mezz_size

    senior_cf=[-senior_size]
    mezz_cf=[-mezz_size]
    equity_cf=[-equity_size]

    df=pd.DataFrame(columns=["Month","Senior Interest","Senior Principal","Mezz Interest","Mezz Principal","Equity Cash"])
    for m in range(1,months+1):
        noi=total_loan_pool*(noi_yield/100/12)
        default_amt=total_loan_pool*(default_rate/100/months)
        loss_amt=default_amt*(loss_severity/100)
        net_cash=noi-loss_amt

        sr_int_due=senior_bal*(senior_rate/100/12)
        sr_int_paid=min(sr_int_due,net_cash)
        net_cash-=sr_int_paid

        mz_int_due=mezz_bal*(mezz_rate/100/12)
        mz_int_paid=min(mz_int_due,net_cash)
        net_cash-=mz_int_paid

        if reinvest_toggle and m <= 36:
            sr_prin_paid = 0
            mz_prin_paid = 0
        else:
            sr_prin_sched = senior_size / months
            sr_prin_paid = min(sr_prin_sched, senior_bal, net_cash)
            senior_bal -= sr_prin_paid
            net_cash -= sr_prin_paid

            mz_prin_sched = mezz_size / months
            mz_prin_paid = min(mz_prin_sched, mezz_bal, net_cash)
            mezz_bal -= mz_prin_paid
            net_cash -= mz_prin_paid

        eq_paid=max(net_cash,0)

        senior_cf.append(sr_int_paid+sr_prin_paid)
        mezz_cf.append(mz_int_paid+mz_prin_paid)
        equity_cf.append(eq_paid)

        df.loc[m]=[m,sr_int_paid,sr_prin_paid,mz_int_paid,mz_prin_paid,eq_paid]

    sr_irr=npf.irr(senior_cf)*12*100
    mz_irr=npf.irr(mezz_cf)*12*100
    eq_irr=npf.irr(equity_cf)*12*100

    return df,sr_irr,mz_irr,eq_irr
