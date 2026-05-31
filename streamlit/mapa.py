import streamlit as st
import plotly.graph_objects as go

from utils import postgres, mongo
from queries import get_departamentos_geojson, get_pct_presencia_por_departamento
from styles import apply_styles

apply_styles()

pg = postgres()
db = mongo()


@st.cache_data(ttl=3600)
def _mapa_data(_pg, _db):
    geojson = get_departamentos_geojson(_db)
    df = get_pct_presencia_por_departamento(_pg, _db)
    return geojson, df


geojson, df_pct = _mapa_data(pg, db)

st.title("Calidad del Agua — Uruguay")
st.markdown("Hacé click en un departamento para ver cómo evolucionó la calidad del agua.")

fig = go.Figure(go.Choropleth(
    geojson=geojson,
    locations=df_pct["nombre"].tolist(),
    z=df_pct["pct_presencia"].round(2).tolist(),
    featureidkey="properties.nombre",
    colorscale="Reds",
    zmin=0,
    zmax=round(df_pct["pct_presencia"].max(), 2),
    marker_line_color="white",
    marker_line_width=1.5,
    colorbar_title="% contaminación",
    hovertemplate="<b>%{location}</b><br>%{z:.1f}% con contaminación<extra></extra>",
))

fig.update_geos(
    fitbounds="locations",
    visible=False,
)

fig.update_layout(
    margin={"r": 0, "t": 0, "l": 0, "b": 0},
    height=600,
)

event = st.plotly_chart(fig, on_select="rerun", use_container_width=True)

if event and event.selection and event.selection.get("points"):
    nombre_depto = event.selection["points"][0].get("location")
    if nombre_depto:
        st.session_state["departamento_mapa"] = nombre_depto
        st.switch_page("evolucion.py")
