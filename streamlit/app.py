from pathlib import Path
#from dotenv import load_dotenv
#load_dotenv(override=True, dotenv_path=Path(__file__).parent.parent / ".env.local")

import sys, os
import streamlit as st

if os.getenv("ENTORNO", "local") == "utec":
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".vendor"))

st.set_page_config(
    page_title="Water Watch",
    page_icon=None,
    layout="wide",
)

pg = st.navigation(
    [st.Page("evolucion.py", title="Dashboard", default=True)],
    position="hidden",
)
pg.run()
