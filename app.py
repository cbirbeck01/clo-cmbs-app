import streamlit as st
from clo_model import run_clo_model
from cmbs_model import run_cmbs_model

# Must be first
st.set_page_config(page_title="Asset Backed Securities Visualizer", layout="wide")

# Custom button styling
st.markdown("""
<style>
.custom-button {
    background-color: #03893e;
    color: white;
    padding: 0.9em 2em;
    font-size: 1.1em;
    font-weight: 600;
    border-radius: 10px;
    border: none;
    cursor: pointer;
    transition: background-color 0.3s ease, transform 0.2s ease;
}
.custom-button:hover {
    background-color: #026c32;
    transform: scale(1.05);
}
</style>
""", unsafe_allow_html=True)

# Page logic
view = st.query_params.get("view", "home")

if view == "home":
    # Title and instructions
    st.markdown("<h1 style='text-align: center;'>Asset Backed Securities Visualizer</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 1.2em;'>Select a product type to begin:</p>", unsafe_allow_html=True)

    # Centered buttons using HTML + form
    st.markdown("""
    <div style='display: flex; justify-content: center; gap: 40px; margin-top: 2em;'>
        <form action='?view=clo' method='get'>
            <button class='custom-button' type='submit'>CLO Model</button>
        </form>
        <form action='?view=cmbs' method='get'>
            <button class='custom-button' type='submit'>CMBS Model</button>
        </form>
    </div>
    """, unsafe_allow_html=True)

elif view == "clo":
    run_clo_model()

elif view == "cmbs":
    run_cmbs_model()

else:
    st.error("Invalid view.")
