import streamlit as st
from clo_model import run_clo_model
from cmbs_model import run_cmbs_model

st.set_page_config(page_title="Structured Finance Dashboard", layout="wide")

model_choice = st.sidebar.radio("Select Model", ["CLO", "CMBS"])

if model_choice == "CLO":
    run_clo_model()

elif model_choice == "CMBS":
    run_cmbs_model()