import streamlit as st
from clo_model import run_clo_model



st.set_page_config(page_title="Asset Backed Securities Visualizer", layout="wide")


st.markdown("""
<style>
div.stButton > button {
    background-color:#03893e;
    color:white;
    padding:0.75em 2em;
    font-size:1.1em;
    font-weight:600;
    border-radius:10px;
    border:none;
    transition:background-color 0.3s ease;
}
div.stButton > button:hover {
    background-color:#026c32;
}
</style>
""", unsafe_allow_html=True)


view = st.query_params.get("view", "home")

if view == "home":
    st.title("Asset Backed Securities Visualizer")
    st.markdown("### Select a product type to begin:")

    col1= st.columns(1)

    with col1:
        if st.button("CLO Model"):
            st.query_params["view"] = "clo"
            st.rerun()


elif view == "clo":
    run_clo_model()


else:
    st.error("Invalid view.")
