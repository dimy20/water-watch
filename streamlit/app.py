from pathlib import Path
#from dotenv import load_dotenv
#load_dotenv(override=True, dotenv_path=Path(__file__).parent.parent / ".env.local")

import sys, os
import importlib
import streamlit as st

if os.getenv("ENTORNO", "utec") == "utec":
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".vendor"))

MOSTRAR_BOTON=True

with st.sidebar:
    if MOSTRAR_BOTON:
        if st.button("Recargar codigo (post git pull)"):
            for nombre in ["db", "utils"]:
                if nombre in sys.modules:
                    importlib.reload(sys.modules[nombre])
            st.cache_resource.clear()
            st.cache_data.clear()
            st.rerun()

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
