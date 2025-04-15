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



    with st.container():
        st.markdown("<div style='height:25vh;'></div>", unsafe_allow_html=True)
        # Centered heading
        st.markdown("<h1 style='text-align: center;'>Asset Backed Securities Visualizer</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-size: 1.2em;'>Select a product type to begin:</p>", unsafe_allow_html=True)

        # Centered buttons using inline-block layout
        st.markdown("""
        <div style="text-align: center; margin-top: 2em;">
            <form action="?view=clo" style="display: inline-block; margin: 10px;">
                <button class="custom-button">🚀 CLO Waterfall</button>
            </form>
            <form action="?view=cmbs" style="display: inline-block; margin: 10px;">
                <button class="custom-button">🏢 CMBS Model</button>
            </form>
        </div>
        """, unsafe_allow_html=True)



elif view=="clo":
    run_clo_model()

elif view=="cmbs":
    run_cmbs_model()

else:
    st.error("Invalid view.")
