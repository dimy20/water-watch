from pathlib import Path
from dotenv import load_dotenv
load_dotenv(override=True, dotenv_path=Path(__file__).parent.parent / ".env.local")

import streamlit as st

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
