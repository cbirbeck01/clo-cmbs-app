import streamlit as st
from clo_model import run_clo_model
from cmbs_model import run_cmbs_model

st.set_page_config(page_title="Asset Backed Securities Dashboard", layout="centered")

st.title("Asset Backed Securities Dashboard")

st.markdown("### Choose security to begin:")

app_choice: st.selectbox("Select Application:", ["-", "CLO", "CMBS"])
if app_choice == "CLO":
    run_clo_model()

elif app_choice == "CMBS":
    run_cmbs_model()
