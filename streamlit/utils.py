import sys
import os
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from db import get_streamlit_postgres_conn, get_streamlit_mongo_conn

@st.cache_resource
def postgres():
    return get_streamlit_postgres_conn()

@st.cache_resource
def mongo():
    return get_streamlit_mongo_conn()
