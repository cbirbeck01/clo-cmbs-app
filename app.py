import streamlit as st
from clo_model import run_clo_model
from cmbs_model import run_cmbs_model

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

if view=="home":
    st.title("Asset Backed Securities Visualizer")


    st.markdown("<div style='height:25vh;'></div>", unsafe_allow_html=True)

    #horizontal spacing
    spacer1, center_col, spacer2 = st.columns([1, 2, 1])
    with center_col:
        st.markdown("### Select a product type to begin:")
        col1, col2 = st.columns(2)

        with col1:
            if st.button("🚀 CLO Waterfall"):
                st.query_params["view"]="clo"
                st.rerun()

        with col2:
            if st.button("🏢 CMBS Model"):
                st.query_params["view"]="cmbs"
                st.rerun()

elif view=="clo":
    run_clo_model()

elif view=="cmbs":
    run_cmbs_model()

else:
    st.error("Invalid view.")
