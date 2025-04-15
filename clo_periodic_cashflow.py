import pandas as pd
import numpy_financial as npf

def simulate_clo_cashflows(total_collateral,senior_size,mezz_size,equity_size,senior_rate,mezz_rate,default_rate,recovery_rate,collateral_yield,years,reinvest_toggle=False):
    months=years*12
    senior_bal=senior_size
    mezz_bal=mezz_size

    senior_cf=[-senior_size]
    mezz_cf=[-mezz_size]
    equity_cf=[-equity_size]

    df=pd.DataFrame(columns=["Month","Senior Interest","Senior Principal","Mezz Interest","Mezz Principal","Equity Cash"])
    for m in range(1,months+1):
        int_income=total_collateral*(collateral_yield/100/12)
        default_amt=total_collateral*(default_rate/100/months)
        recovery_amt=default_amt*(recovery_rate/100)
        available_cash=int_income+recovery_amt-default_amt

        sr_int_due=senior_bal*(senior_rate/100/12)
        sr_int_paid=min(sr_int_due,available_cash)
        available_cash-=sr_int_paid

        mz_int_due=mezz_bal*(mezz_rate/100/12)
        mz_int_paid=min(mz_int_due,available_cash)
        available_cash-=mz_int_paid

        if reinvest_toggle and m <= 36:
            sr_prin_paid = 0
            mz_prin_paid = 0
        else:
            sr_prin_sched = senior_size / months
            sr_prin_paid = min(sr_prin_sched, senior_bal, available_cash)
            senior_bal -= sr_prin_paid
            available_cash -= sr_prin_paid

            mz_prin_sched = mezz_size / months
            mz_prin_paid = min(mz_prin_sched, mezz_bal, available_cash)
            mezz_bal -= mz_prin_paid
            available_cash -= mz_prin_paid

        eq_paid=max(available_cash,0)

        senior_cf.append(sr_int_paid+sr_prin_paid)
        mezz_cf.append(mz_int_paid+mz_prin_paid)
        equity_cf.append(eq_paid)

        df.loc[m]=[m,sr_int_paid,sr_prin_paid,mz_int_paid,mz_prin_paid,eq_paid]

    sr_irr=npf.irr(senior_cf)*12*100
    mz_irr=npf.irr(mezz_cf)*12*100
    eq_irr=npf.irr(equity_cf)*12*100

    return df,sr_irr,mz_irr,eq_irr
