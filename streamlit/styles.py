import streamlit as st


def apply_styles():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"], [class*="st-"] {
        font-family: 'Inter', sans-serif !important;
    }
    h1, h2, h3 { font-weight: 600; }
    .stMetric label { font-size: 0.85rem; color: #555; }
    </style>
    """, unsafe_allow_html=True)
