import streamlit as st
from clo_model import run_clo_model
from cmbs_model import run_cmbs_model

st.set_page_config(page_title="Structured Products Explorer", layout="centered")
query_params = st.query_params
view = query_params.get("view", "home")
if view == "home":
    st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
    st.title("📊 Structured Products Explorer")
    st.markdown("### Select a product type to begin:")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("CLO"):
            st.experimental_set_query_params(view="clo")
    with col2:
        if st.button("CMBS"):
            st.experimental_set_query_params(view="cmbs")
elif view=="clo":
    run_clo_model()

elif view=="cmbs":
    run_cmbs_model()

else:
    st.error("Invalid view.")
