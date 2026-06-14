import pandas as pd
import pydeck
import streamlit as st
import plotly.graph_objects as go
import pydeck as pdk
import pandas as pd
from pathlib import Path

from utils import postgres, mongo
from queries import (
    get_departamentos_con_datos,
    get_evolucion_calidad,
    transformar_para_dashboard,
    get_estaciones_por_departamento,
    get_gems_evolucion,
    get_pct_presencia_por_departamento,
    get_gems_bacterio_por_departamento,
    get_hidrico_suelo_por_departamento,
    get_departamentos_geojson,
    get_riesgo_por_departamento,
    get_reclamos_trimestral,
    get_correlacion_reclamos_calidad,
    get_locations_con_ndci,
    get_precipitacion_vs_ndci,
    get_correlacion_por_lag,
    get_punto_grilla_cercano_sentinel,
    get_punto_grilla_coords,
    TIPOS,
)
from styles import apply_styles

BACTERIO_PARAMS = {
    "Coliformes totales": {
        "ose_code":  "COLIFORMES TOTALES",
        "gems_code": "TOTCOLI",
        "unidad":    "MPN/100ml",
    },
    "E. coli": {
        "ose_code":  "ESCHERICHIA COLI",
        "gems_code": "ECOLI",
        "unidad":    "MPN/100ml",
    },
    "Coliformes fecales": {
        "ose_code":  None,
        "gems_code": "FECALCOLI",
        "unidad":    "MPN/100ml",
    },
}

GEMS_PARAMS = {
    "pH":         ("pH",                              "dimensionless"),
    "O2-Dis":     ("Oxígeno disuelto",                "mg/l"),
    "O2-Dis-Sat": ("Saturación de oxígeno",           "%"),
    "TEMP":       ("Temperatura",                     "°C"),
    "EC":         ("Conductancia eléctrica",           "µS/cm"),
    "BOD":        ("Demanda biológica de oxígeno",    "mg/l"),
    "COD":        ("Demanda química de oxígeno",      "mg/l"),
    "NH4N":       ("Amoniaco (NH4-N)",                "mg/l"),
    "TP":         ("Fósforo total",                   "mg/l"),
    "TN":         ("Nitrógeno total",                 "mg/l"),
    "TURB":       ("Turbidez",                        "NTU"),
    "TSS":        ("Sólidos suspendidos totales",     "mg/l"),
    "Chl-a":      ("Clorofila A",                     "mg/l"),
    "TRANS":      ("Transparencia",                   "m"),
}

apply_styles()


def loading_markup(text: str = "Cargando Water Watch...", subtext: str = "Preparando datos y visualizaciones") -> str:
    dots = "".join("<span></span>" for _ in range(10))
    return f"""
    <div class="ww-loader-overlay" aria-live="polite" aria-busy="true">
        <div class="ww-loader-panel">
            <div class="ww-loader-dots">{dots}</div>
            <div class="ww-loader-text">{text}</div>
            <div class="ww-loader-subtext">{subtext}</div>
        </div>
    </div>
    """


initial_loader = st.empty()
initial_loader.markdown(loading_markup(), unsafe_allow_html=True)

pg = postgres()
db = mongo()
LOGO_PATH = Path(__file__).parent / "assets" / "waterwatch-logo.svg"


@st.cache_data(ttl=3600, show_spinner="Cargando Water Watch...")
def _departamentos(_pg, _db):
    return get_departamentos_con_datos(_pg, _db)


@st.cache_data(ttl=600, show_spinner="Cargando Water Watch...")
def _calidad(_pg, departamento_id, anio_inicio, anio_fin, codigos):
    return get_evolucion_calidad(_pg, departamento_id, anio_inicio, anio_fin, codigos)


@st.cache_data(ttl=3600, show_spinner="Cargando Water Watch...")
def _estaciones_depto(_db, departamento_id):
    return get_estaciones_por_departamento(_db, departamento_id)


@st.cache_data(ttl=600, show_spinner="Cargando Water Watch...")
def _gems_calidad(_pg, location_ids, anio_inicio, anio_fin, code):
    return get_gems_evolucion(_pg, list(location_ids), anio_inicio, anio_fin, code)


@st.cache_data(ttl=3600, show_spinner="Cargando Water Watch...")
def _pct_por_depto(_pg, _db, ose_code):
    return get_pct_presencia_por_departamento(_pg, _db, ose_code)


@st.cache_data(ttl=3600, show_spinner="Cargando Water Watch...")
def _gems_bacterio_nacional(_db, _pg, gems_code):
    return get_gems_bacterio_por_departamento(_db, _pg, gems_code)


@st.cache_data(ttl=3600, show_spinner="Cargando Water Watch...")
def _geojson(_db):
    return get_departamentos_geojson(_db)


@st.cache_data(ttl=3600, show_spinner="Cargando Water Watch...")
def _geojson_detallado(_db):
    docs = list(_db["departamentos"].find({}, {"_id": 0, "nombre": 1, "geometry": 1}))
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "id": doc["nombre"],
                "properties": {"nombre": doc["nombre"]},
                "geometry": doc["geometry"],
            }
            for doc in docs
        ],
    }


@st.cache_data(ttl=3600, show_spinner="Cargando Water Watch...")
def _centroides_departamentos(_db):
    from shapely.geometry import shape

    docs = list(_db["departamentos"].find({}, {"_id": 0, "nombre": 1, "geometry": 1}))
    rows = []
    for doc in docs:
        punto = shape(doc["geometry"]).representative_point()
        rows.append({"nombre": doc["nombre"], "lon": punto.x, "lat": punto.y})
    return rows


@st.cache_data(ttl=3600, show_spinner="Cargando Water Watch...")
def _hidrico_suelo(_db, _pg, tipo, anio_inicio, anio_fin):
    return get_hidrico_suelo_por_departamento(_db, _pg, tipo, anio_inicio, anio_fin)


@st.cache_data(ttl=3600, show_spinner="Cargando Water Watch...")
def _riesgo(_db, _pg, anio_inicio, anio_fin):
    return get_riesgo_por_departamento(_db, _pg, anio_inicio, anio_fin)


@st.cache_data(ttl=3600, show_spinner="Cargando Water Watch...")
def _correlacion(_pg, _db, anio_inicio, anio_fin):
    return get_correlacion_reclamos_calidad(_pg, _db, anio_inicio, anio_fin)


@st.cache_data(ttl=600, show_spinner="Cargando Water Watch...")
def _reclamos_trimestral(_pg, departamento_id, anio_inicio, anio_fin):
    return get_reclamos_trimestral(_pg, departamento_id, anio_inicio, anio_fin)


@st.cache_data(ttl=3600)
def _estaciones_chla(_pg, _db):
    return get_estaciones_con_chla(_pg, _db)


@st.cache_data(ttl=600)
def _precip_vs_chla(_pg, _db, location_id, anio_inicio, anio_fin, lag_meses):
    return get_precipitacion_vs_chla(_pg, _db, location_id, anio_inicio, anio_fin, lag_meses)


@st.cache_data(ttl=3600, show_spinner="Cargando Water Watch...")
def _locations_ndci(_pg, _db):
    return get_locations_con_ndci(_pg, _db)


@st.cache_data(ttl=3600, show_spinner="Cargando Water Watch...")
def _punto_grilla_pad(_db, location_id):
    punto_id = get_punto_grilla_cercano_sentinel(_db, location_id)
    if punto_id is None:
        return None
    return get_punto_grilla_coords(_db, punto_id)


@st.cache_data(ttl=600, show_spinner="Cargando Water Watch...")
def _precip_vs_ndci(_pg, _db, location_id, anio_inicio, anio_fin, lag_meses):
    return get_precipitacion_vs_ndci(_pg, _db, location_id, anio_inicio, anio_fin, lag_meses)


@st.cache_data(ttl=600, show_spinner="Cargando Water Watch...")
def _correlacion_lag(_pg, _db, location_id, anio_inicio, anio_fin):
    return get_correlacion_por_lag(_pg, _db, location_id, anio_inicio, anio_fin)


def _preparar_departamentos_mapa(df, centroides, value_col, value_label, unidad=""):
    df_mapa = df.merge(pd.DataFrame(centroides), on="nombre", how="inner").copy()
    if df_mapa.empty:
        return df_mapa

    df_mapa["ranking"] = df_mapa[value_col].rank(method="first", ascending=False).astype(int)
    min_val = float(df_mapa[value_col].min())
    max_val = float(df_mapa[value_col].max())
    if max_val == min_val:
        df_mapa["radio"] = 22000
    else:
        df_mapa["radio"] = 9000 + ((df_mapa[value_col] - min_val) / (max_val - min_val)) * 36000

    sufijo = f" {unidad}" if unidad else ""
    df_mapa["tooltip"] = (
        "#" + df_mapa["ranking"].astype(str)
        + " " + df_mapa["nombre"]
        + "<br>" + value_label + ": " + df_mapa[value_col].map(lambda v: f"{v:.2f}") + sufijo
    )
    return df_mapa.sort_values("ranking")


def _mapa_departamentos_puntos(df_mapa, value_col):
    return pdk.Deck(
        map_style="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
        views=[pdk.View(type="MapView", controller=False)],
        initial_view_state=pdk.ViewState(
            latitude=-32.8,
            longitude=-56.0,
            zoom=5.7,
            pitch=0,
        ),
        layers=[
            pdk.Layer(
                "ScatterplotLayer",
                data=df_mapa,
                id=f"{value_col}_departamentos",
                get_position="[lon, lat]",
                get_radius="radio",
                get_fill_color="[229, 57, 53, 170]",
                get_line_color="[255, 255, 255, 210]",
                line_width_min_pixels=1,
                pickable=True,
                stroked=True,
                filled=True,
            )
        ],
        tooltip={
            "html": "<div style='font-size:14px;line-height:1.45'><b>{tooltip}</b></div>",
            "style": {
                "backgroundColor": "#26323f",
                "color": "#ffffff",
                "fontFamily": "Inter, sans-serif",
                "padding": "10px 12px",
            },
        },
    )


def _interpolar_color(valor, min_val, max_val):
    stops = [
        (0.0, (219, 234, 254)),
        (0.25, (147, 197, 253)),
        (0.5, (59, 130, 246)),
        (0.75, (29, 78, 216)),
        (1.0, (15, 63, 135)),
    ]
    if max_val == min_val:
        return [59, 130, 246, 215]

    t = (float(valor) - min_val) / (max_val - min_val)
    t = max(0.0, min(1.0, t))
    for idx in range(len(stops) - 1):
        left_t, left_color = stops[idx]
        right_t, right_color = stops[idx + 1]
        if left_t <= t <= right_t:
            span = right_t - left_t
            local_t = 0 if span == 0 else (t - left_t) / span
            rgb = [
                round(left_color[channel] + (right_color[channel] - left_color[channel]) * local_t)
                for channel in range(3)
            ]
            return rgb + [220]
    return [15, 63, 135, 220]


def _geojson_departamentos_calor(geojson, df_mapa, value_col, value_label):
    valores = df_mapa.set_index("nombre").to_dict("index")
    min_val = float(df_mapa[value_col].min())
    max_val = float(df_mapa[value_col].max())
    features = []

    for feature in geojson["features"]:
        nombre = feature["properties"]["nombre"]
        dato = valores.get(nombre)
        props = dict(feature["properties"])
        if dato is None:
            props.update({
                "valor": None,
                "ranking": None,
                "fill_color": [31, 41, 55, 90],
                "tooltip": f"{nombre}<br>Sin datos",
            })
        else:
            valor = float(dato[value_col])
            ranking = int(dato["ranking"])
            props.update({
                "valor": valor,
                "ranking": ranking,
                "fill_color": _interpolar_color(valor, min_val, max_val),
                "tooltip": f"#{ranking} {nombre}<br>{value_label}: {valor:.2f}",
            })

        features.append({
            "type": "Feature",
            "id": feature.get("id", nombre),
            "properties": props,
            "geometry": feature["geometry"],
        })

    return {"type": "FeatureCollection", "features": features}


def _mapa_departamentos_calor(geojson_calor):
    return pdk.Deck(
        map_style=None,
        views=[pdk.View(type="MapView", controller=False)],
        initial_view_state=pdk.ViewState(
            latitude=-32.8,
            longitude=-56.0,
            zoom=5.7,
            pitch=0,
        ),
        layers=[
            pdk.Layer(
                "GeoJsonLayer",
                data=geojson_calor,
                id="suelo_departamentos_calor",
                pickable=True,
                stroked=True,
                filled=True,
                get_fill_color="properties.fill_color",
                get_line_color=[248, 250, 252, 225],
                line_width_min_pixels=1.4,
            )
        ],
        tooltip={
            "html": "<div style='font-size:14px;line-height:1.45'><b>{tooltip}</b></div>",
            "style": {
                "backgroundColor": "#26323f",
                "color": "#ffffff",
                "fontFamily": "Inter, sans-serif",
                "padding": "10px 12px",
            },
        },
    )


def _grafico_ranking_departamentos(df_mapa, value_col, eje_titulo, unidad=""):
    df_bar = df_mapa.sort_values(value_col, ascending=True)
    hover_suffix = f" {unidad}" if unidad else ""
    fig = go.Figure(go.Bar(
        x=df_bar[value_col],
        y=df_bar["nombre"],
        orientation="h",
        marker_color="#e53935",
        hovertemplate="%{y}: %{x:.2f}" + hover_suffix + "<extra></extra>",
    ))
    fig.update_layout(
        xaxis_title=eje_titulo,
        yaxis_title=None,
        height=460,
        margin=dict(l=120, r=35, t=10, b=40),
        showlegend=False,
    )
    return fig


df_deptos = _departamentos(pg, db)
initial_loader.empty()

depto_default = st.session_state.get("departamento_mapa", df_deptos["nombre"].iloc[0])
idx = df_deptos["nombre"].tolist().index(depto_default) if depto_default in df_deptos["nombre"].values else 0

with st.sidebar:
    st.image(str(LOGO_PATH), use_container_width=True)
    st.markdown("<div class='ww-filter-kicker'>Panel de control</div>", unsafe_allow_html=True)
    st.header("Filtros")

    nombre_depto = st.selectbox(
        "Departamento",
        options=df_deptos["nombre"].tolist(),
        index=idx,
    )

    anio_inicio = st.selectbox(
        "Año de inicio",
        options=list(range(2017, 2026)),
        index=0,
    )

    anio_fin = st.selectbox(
        "Año de fin",
        options=list(range(2017, 2026)),
        index=8,
    )

if anio_inicio > anio_fin:
    st.error("El año de inicio no puede ser mayor al año de fin.")
    st.stop()

depto_row = df_deptos[df_deptos["nombre"] == nombre_depto].iloc[0]
departamento_id = depto_row["departamento_id"]

st.title("Water Watch")
st.subheader(f"{nombre_depto} · {anio_inicio}–{anio_fin}")

tab_bacterio, tab_gems, tab_resumen, tab_suelo, tab_riesgo, tab_reclamos, tab_precip_ndci = st.tabs([
    "Bacteriología",
    "Fisicoquímica (GEMS)",
    "Resumen nacional",
    "Estado hídrico del suelo",
    "Indicador de Riesgo",
    "Reclamos vs Calidad",
    "Precipitación vs NDCI",
])

# ── TAB BACTERIOLOGÍA ─────────────────────────────────────────────────────────

with tab_bacterio:
    param_nombre = st.selectbox(
        "Parámetro",
        options=list(BACTERIO_PARAMS.keys()),
    )
    param = BACTERIO_PARAMS[param_nombre]

    # ── OSE (arriba) ─────────────────────────────────────────────────────────

    st.markdown("#### Bacteriología OSE — % muestras con presencia")

    if param["ose_code"] is None:
        st.info(f"OSE no registra {param_nombre}.")
    else:
        df_crudo = _calidad(pg, departamento_id, anio_inicio, anio_fin, (param["ose_code"],))

        if df_crudo.empty:
            st.info(f"No hay datos OSE de {param_nombre} para {nombre_depto} en el período.")
        else:
            df_grafico, df_tabla = transformar_para_dashboard(df_crudo)

            total_muestras = int(df_grafico["total_muestras"].sum())
            total_presencias = (df_grafico["pct_presencia"] * df_grafico["total_muestras"] / 100).sum()
            pct_global = total_presencias / total_muestras * 100 if total_muestras > 0 else 0.0

            periodos_ordenados = df_grafico.sort_values("periodo")["periodo_str"].unique().tolist()
            n = len(periodos_ordenados)

            col1, col2, col3 = st.columns(3)
            col1.metric("Total de muestras", f"{total_muestras:,}")
            col2.metric("Muestras con contaminación", f"{pct_global:.1f}%")

            if n >= 2:
                mitad = n // 2
                primera = df_grafico[df_grafico["periodo_str"].isin(periodos_ordenados[:mitad])]
                segunda = df_grafico[df_grafico["periodo_str"].isin(periodos_ordenados[mitad:])]
                pct_p = (primera["pct_presencia"] * primera["total_muestras"]).sum() / primera["total_muestras"].sum()
                pct_s = (segunda["pct_presencia"] * segunda["total_muestras"]).sum() / segunda["total_muestras"].sum()
                delta = pct_s - pct_p
                col3.metric("Tendencia del período", "Empeora ↑" if delta > 0 else "Mejora ↓", delta=f"{delta:+.1f}%", delta_color="inverse")
            else:
                col3.metric("Tendencia del período", "Período muy corto")

            fig_ose = go.Figure()
            df_sorted = df_grafico.sort_values("periodo")
            fig_ose.add_trace(go.Scatter(
                x=df_sorted["periodo_str"],
                y=df_sorted["pct_presencia"],
                mode="lines+markers",
                name="% presencia",
                hovertemplate="%{x}: %{y:.1f}%<extra></extra>",
            ))
            fig_ose.update_layout(
                xaxis_title="Trimestre",
                yaxis_title="% Muestras con presencia",
                yaxis=dict(range=[0, max(df_grafico["pct_presencia"].max() * 1.2, 5)], ticksuffix="%"),
                hovermode="x unified",
                showlegend=False,
            )
            st.plotly_chart(fig_ose, use_container_width=True)

    st.divider()

    # ── GEMS (abajo) ──────────────────────────────────────────────────────────

    st.markdown(f"#### GEMS — {param_nombre} ({param['unidad']})")

    location_ids = _estaciones_depto(db, departamento_id)

    if not location_ids:
        st.info(f"No hay estaciones GEMS en {nombre_depto}.")
    else:
        df_gems = _gems_calidad(pg, tuple(location_ids), anio_inicio, anio_fin, param["gems_code"])

        if df_gems.empty:
            st.info(f"No hay datos GEMS de {param_nombre} para {nombre_depto} en el período.")
        else:
            col1, col2, col3 = st.columns(3)
            col1.metric(f"Promedio ({param['unidad']})", f"{df_gems['valor_medio'].mean():.2f}")
            col2.metric(f"Mínimo ({param['unidad']})", f"{df_gems['valor_min'].min():.2f}")
            col3.metric(f"Máximo ({param['unidad']})", f"{df_gems['valor_max'].max():.2f}")

            df_gems["periodo_str"] = (
                df_gems["periodo"].dt.year.astype(str)
                + "-"
                + df_gems["periodo"].dt.month.astype(str).str.zfill(2)
            )

            fig_gems_bacterio = go.Figure()
            fig_gems_bacterio.add_trace(go.Scatter(
                x=df_gems["periodo_str"], y=df_gems["valor_max"],
                mode="lines", line=dict(width=0),
                showlegend=False, hoverinfo="skip",
            ))
            fig_gems_bacterio.add_trace(go.Scatter(
                x=df_gems["periodo_str"], y=df_gems["valor_min"],
                mode="lines", line=dict(width=0),
                fill="tonexty", fillcolor="rgba(229,57,53,0.15)",
                name="Rango (min–max)", hoverinfo="skip",
            ))
            fig_gems_bacterio.add_trace(go.Scatter(
                x=df_gems["periodo_str"], y=df_gems["valor_medio"],
                mode="lines+markers", name="Promedio mensual",
                line=dict(color="#e53935"),
                hovertemplate="%{x}: %{y:.2f} " + param["unidad"] + "<extra></extra>",
            ))
            fig_gems_bacterio.update_layout(
                xaxis_title="Mes",
                yaxis_title=f"{param_nombre} ({param['unidad']})",
                hovermode="x unified",
                legend=dict(orientation="h", y=-0.2),
            )
            st.plotly_chart(fig_gems_bacterio, use_container_width=True)
            st.caption(f"Promedio mensual de {len(location_ids)} estación(es) GEMS en {nombre_depto}. La banda muestra el rango min–max.")

# ── TAB FISICOQUÍMICA (GEMS) ──────────────────────────────────────────────────

with tab_gems:
    param_code = st.selectbox(
        "Parámetro",
        options=list(GEMS_PARAMS.keys()),
        format_func=lambda k: f"{GEMS_PARAMS[k][0]}  ({GEMS_PARAMS[k][1]})",
    )

    location_ids = _estaciones_depto(db, departamento_id)

    if not location_ids:
        st.info(f"No hay estaciones de monitoreo GEMS en {nombre_depto}.")
    else:
        df_gems = _gems_calidad(pg, tuple(location_ids), anio_inicio, anio_fin, param_code)

        nombre_param, unidad = GEMS_PARAMS[param_code]

        if df_gems.empty:
            st.info(f"No hay datos de {nombre_param} para {nombre_depto} en el período seleccionado.")
        else:
            col1, col2, col3 = st.columns(3)
            col1.metric(f"Promedio del período ({unidad})", f"{df_gems['valor_medio'].mean():.2f}")
            col2.metric(f"Mínimo registrado ({unidad})", f"{df_gems['valor_min'].min():.2f}")
            col3.metric(f"Máximo registrado ({unidad})", f"{df_gems['valor_max'].max():.2f}")

            df_gems["periodo_str"] = (
                df_gems["periodo"].dt.year.astype(str)
                + "-"
                + df_gems["periodo"].dt.month.astype(str).str.zfill(2)
            )

            fig_gems = go.Figure()
            fig_gems.add_trace(go.Scatter(
                x=df_gems["periodo_str"], y=df_gems["valor_max"],
                mode="lines", line=dict(width=0),
                showlegend=False, hoverinfo="skip",
            ))
            fig_gems.add_trace(go.Scatter(
                x=df_gems["periodo_str"], y=df_gems["valor_min"],
                mode="lines", line=dict(width=0),
                fill="tonexty", fillcolor="rgba(26,115,232,0.15)",
                name="Rango (min–max)", hoverinfo="skip",
            ))
            fig_gems.add_trace(go.Scatter(
                x=df_gems["periodo_str"], y=df_gems["valor_medio"],
                mode="lines+markers", name="Promedio mensual",
                hovertemplate="%{x}: %{y:.2f} " + unidad + "<extra></extra>",
            ))
            fig_gems.update_layout(
                title=f"{nombre_param} — {nombre_depto}",
                xaxis_title="Mes",
                yaxis_title=f"{nombre_param} ({unidad})",
                hovermode="x unified",
                legend=dict(orientation="h", y=-0.2),
            )
            st.plotly_chart(fig_gems, use_container_width=True)
            st.caption(f"Promedio mensual de {len(location_ids)} estación(es) GEMS en {nombre_depto}. La banda azul muestra el rango entre el mínimo y máximo registrado en el mes.")

# ── TAB RESUMEN NACIONAL ──────────────────────────────────────────────────────

with tab_resumen:
    param_resumen = st.selectbox(
        "Parámetro bacteriológico",
        options=list(BACTERIO_PARAMS.keys()),
        key="resumen_param",
    )
    ose_code_resumen = BACTERIO_PARAMS[param_resumen]["ose_code"]
    gems_code_resumen = BACTERIO_PARAMS[param_resumen]["gems_code"]
    unidad_resumen = BACTERIO_PARAMS[param_resumen]["unidad"]
    centroides = _centroides_departamentos(db)

    # ── OSE (arriba) ─────────────────────────────────────────────────────────

    st.markdown("#### Bacteriología OSE — % muestras con presencia por departamento")

    if ose_code_resumen is None:
        st.info(f"OSE no registra {param_resumen}.")
    else:
        df_resumen = _pct_por_depto(pg, db, ose_code_resumen)
        df_resumen = df_resumen.sort_values("pct_presencia", ascending=True)

        if df_resumen.empty:
            st.info(f"No hay datos OSE de {param_resumen}.")
        else:
            df_ose_mapa = _preparar_departamentos_mapa(
                df_resumen,
                centroides,
                "pct_presencia",
                "% muestras con presencia",
                "%",
            )
            col_mapa, col_ranking = st.columns([1.2, 1])
            with col_mapa:
                st.pydeck_chart(
                    _mapa_departamentos_puntos(df_ose_mapa, "pct_presencia"),
                    height=460,
                )
            with col_ranking:
                st.plotly_chart(
                    _grafico_ranking_departamentos(
                        df_ose_mapa,
                        "pct_presencia",
                        "% muestras con presencia",
                        "%",
                    ),
                    use_container_width=True,
                )
            st.caption(f"OSE · {param_resumen}. El tamaño del punto representa el porcentaje de muestras con presencia.")

    st.divider()

    # ── GEMS (abajo) ──────────────────────────────────────────────────────────

    st.markdown(f"#### GEMS — {param_resumen} promedio por departamento ({unidad_resumen})")

    df_gems_nac = _gems_bacterio_nacional(db, pg, gems_code_resumen)

    if df_gems_nac.empty:
        st.info(f"No hay datos GEMS de {param_resumen} para ningún departamento.")
    else:
        df_gems_nac = df_gems_nac.sort_values("valor_medio", ascending=True)
        df_gems_mapa = _preparar_departamentos_mapa(
            df_gems_nac,
            centroides,
            "valor_medio",
            "Promedio",
            unidad_resumen,
        )
        col_mapa, col_ranking = st.columns([1.2, 1])
        with col_mapa:
            st.pydeck_chart(
                _mapa_departamentos_puntos(df_gems_mapa, "valor_medio"),
                height=460,
            )
        with col_ranking:
            st.plotly_chart(
                _grafico_ranking_departamentos(
                    df_gems_mapa,
                    "valor_medio",
                    f"Promedio {param_resumen} ({unidad_resumen})",
                    unidad_resumen,
                ),
                use_container_width=True,
            )
        st.caption(f"GEMS · Promedio histórico por departamento según estaciones. {len(df_gems_nac)} departamentos con datos.")

# ── TAB ESTADO HÍDRICO DEL SUELO ─────────────────────────────────────────────

with tab_suelo:
    tipo_suelo = st.selectbox(
        "Indicador",
        options=list(TIPOS.keys()),
        format_func=lambda k: f"{k} — {TIPOS[k]}",
    )

    df_suelo = _hidrico_suelo(db, pg, tipo_suelo, anio_inicio, anio_fin)

    if df_suelo.empty:
        st.info(f"No hay datos de {tipo_suelo} para el período {anio_inicio}–{anio_fin}.")
    else:
        df_suelo = df_suelo.copy()
        df_suelo["ranking"] = df_suelo["valor_medio"].rank(method="first", ascending=False).astype(int)

        col1, col2, col3 = st.columns(3)
        col1.metric("Promedio nacional", f"{df_suelo['valor_medio'].mean():.2f}")
        col2.metric("Departamento mínimo", f"{df_suelo['valor_medio'].min():.2f}")
        col3.metric("Departamento máximo", f"{df_suelo['valor_medio'].max():.2f}")

        geojson = _geojson_detallado(db)
        df_suelo_map = df_suelo.sort_values("valor_medio", ascending=False)
        geojson_suelo = _geojson_departamentos_calor(geojson, df_suelo_map, "valor_medio", tipo_suelo)

        df_bar = df_suelo.sort_values("valor_medio", ascending=True)
        fig_bar = go.Figure(go.Bar(
            x=df_bar["valor_medio"],
            y=df_bar["nombre"],
            orientation="h",
            marker=dict(
                color=df_bar["valor_medio"],
                colorscale=[
                    [0.0, "#bfdbfe"],
                    [0.5, "#3b82f6"],
                    [1.0, "#0f3f87"],
                ],
                line=dict(color="rgba(255,255,255,0.85)", width=1),
            ),
            hovertemplate="<b>%{y}</b><br>" + tipo_suelo + ": %{x:.2f}<extra></extra>",
        ))
        fig_bar.update_layout(
            xaxis_title=f"Promedio {tipo_suelo}",
            yaxis_title=None,
            height=560,
            margin=dict(l=125, r=36, t=54, b=40),
            title=dict(
                text="Ranking departamental",
                x=0.02,
                xanchor="left",
                font=dict(size=18, color="#17192f"),
            ),
            showlegend=False,
            paper_bgcolor="#ffffff",
            plot_bgcolor="#ffffff",
            xaxis=dict(showgrid=True, gridcolor="rgba(15, 63, 135, 0.08)"),
        )

        col_mapa, col_ranking = st.columns([1.28, 1])
        with col_mapa:
            st.markdown(f"#### {tipo_suelo} — {TIPOS[tipo_suelo]} · {anio_inicio}–{anio_fin}")
            st.pydeck_chart(
                _mapa_departamentos_calor(geojson_suelo),
                use_container_width=True,
                height=560,
            )
        with col_ranking:
            st.plotly_chart(
                fig_bar,
                use_container_width=True,
                config={
                    "displayModeBar": False,
                    "scrollZoom": False,
                    "doubleClick": False,
                    "responsive": True,
                },
            )

        st.caption(f"Promedio de puntos de grilla por departamento. {len(df_suelo)} departamentos con datos.")

# ── TAB INDICADOR DE RIESGO ───────────────────────────────────────────────────

with tab_riesgo:
    st.markdown("#### Indicador de Riesgo")
    st.caption(
        "Resume tres señales del período seleccionado: contaminación bacteriológica, "
        "precipitación elevada y menor humedad del suelo. El score indica cuántas señales "
        "están activas en cada departamento."
    )

    df_riesgo = _riesgo(db, pg, anio_inicio, anio_fin)

    if df_riesgo.empty:
        st.info("No hay datos suficientes para calcular el indicador de riesgo en el período seleccionado.")
    else:
        riesgo_labels = {
            0: "Sin señales",
            1: "Bajo",
            2: "Medio",
            3: "Alto",
        }
        riesgo_colors = {
            0: "#dbeafe",
            1: "#93c5fd",
            2: "#f59e0b",
            3: "#dc2626",
        }

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Sin señales", int((df_riesgo["score"] == 0).sum()))
        col2.metric("Riesgo bajo", int((df_riesgo["score"] == 1).sum()))
        col3.metric("Riesgo medio", int((df_riesgo["score"] == 2).sum()))
        col4.metric("Riesgo alto", int((df_riesgo["score"] == 3).sum()))

        geojson = _geojson(db)

        def _fmt(val, fmt, suffix=""):
            return f"{val:{fmt}}{suffix}" if val == val else "—"  # nan check

        def _senales(row):
            activas = []
            if row["condicion_contam"]:
                activas.append("contaminación")
            if row["condicion_precip"]:
                activas.append("precipitación")
            if row["condicion_suelo"]:
                activas.append("suelo")
            return ", ".join(activas) if activas else "sin señales activas"

        df_riesgo["_tip_ose"] = df_riesgo["pct_ose"].apply(lambda x: _fmt(x, ".1f", "%"))
        df_riesgo["_tip_gems"] = df_riesgo["val_gems"].apply(lambda x: _fmt(x, ".2f", " MPN/100ml"))
        df_riesgo["_tip_precip"] = df_riesgo["val_precip"].apply(
            lambda x: _fmt(x, ".1f", " mm/día") if x == x else "sin datos"
        )
        df_riesgo["_tip_ibh"] = df_riesgo["val_suelo"].apply(lambda x: _fmt(x, ".2f"))
        df_riesgo["_nivel"] = df_riesgo["score"].map(riesgo_labels)
        df_riesgo["_senales"] = df_riesgo.apply(_senales, axis=1)

        customdata = df_riesgo[[
            "_nivel", "_senales", "_tip_ose", "_tip_gems", "_tip_precip", "_tip_ibh",
        ]].values

        fig_riesgo = go.Figure(go.Choropleth(
            geojson=geojson,
            locations=df_riesgo["nombre"].tolist(),
            z=df_riesgo["score"].tolist(),
            featureidkey="properties.nombre",
            colorscale=[
                [0.0, riesgo_colors[0]],
                [0.33, riesgo_colors[1]],
                [0.67, riesgo_colors[2]],
                [1.0, riesgo_colors[3]],
            ],
            zmin=0,
            zmax=3,
            marker_line_color="white",
            marker_line_width=1.5,
            colorbar=dict(
                title="Riesgo",
                tickvals=[0, 1, 2, 3],
                ticktext=["0", "1", "2", "3"],
                thickness=14,
                outlinewidth=0,
            ),
            customdata=customdata,
            hovertemplate=(
                "<b>%{location}</b><br>"
                "Nivel: <b>%{customdata[0]}</b> (%{z}/3)<br>"
                "Señales: %{customdata[1]}<br>"
                "OSE: %{customdata[2]}<br>"
                "GEMS: %{customdata[3]}<br>"
                "Precipitación: %{customdata[4]}<br>"
                "IBH: %{customdata[5]}"
                "<extra></extra>"
            ),
        ))
        fig_riesgo.update_geos(fitbounds="locations", visible=False)
        fig_riesgo.update_layout(
            title=dict(
                text=f"Riesgo departamental · {anio_inicio}–{anio_fin}",
                x=0.02,
                xanchor="left",
                font=dict(size=18, color="#17192f"),
            ),
            margin={"r": 0, "t": 52, "l": 0, "b": 0},
            height=550,
            paper_bgcolor="#ffffff",
            plot_bgcolor="#ffffff",
        )
        st.plotly_chart(fig_riesgo, use_container_width=True)

        with st.expander("Detalle por departamento"):
            df_tabla_riesgo = df_riesgo[[
                "nombre", "_nivel", "score", "_senales", "pct_ose", "val_gems", "val_precip", "val_suelo",
            ]].copy()
            df_tabla_riesgo.columns = [
                "Departamento", "Nivel", "Score", "Señales activas",
                "OSE (%)", "GEMS (MPN/100ml)", "Precipitación (mm/día)", "IBH",
            ]
            for col in ["OSE (%)", "GEMS (MPN/100ml)", "Precipitación (mm/día)", "IBH"]:
                df_tabla_riesgo[col] = df_tabla_riesgo[col].apply(
                    lambda x: round(x, 2) if x == x else None
                )
            st.dataframe(
                df_tabla_riesgo.sort_values("Score", ascending=False).reset_index(drop=True),
                use_container_width=True,
                hide_index=True,
            )

        with st.expander("Criterio de cálculo"):
            st.markdown(
                "Cada señal suma 1 punto. La contaminación combina OSE y GEMS y se activa por encima "
                "del percentil 66 del período; la precipitación se activa por encima del percentil 66; "
                "la señal de suelo se activa cuando el IBH queda por debajo del percentil 33. "
                "La precipitación solo cubre departamentos con estación INIA, por lo que en los demás "
                "el score máximo observable puede ser menor."
            )

# ── TAB RECLAMOS VS CALIDAD ───────────────────────────────────────────────────

with tab_reclamos:
    st.markdown("#### Reclamos OSE vs Calidad Bacteriológica")
    st.caption(
        "Los reclamos son de tipo comercial (facturación, lectura de medidor, tarifas). "
        "La relación con la calidad bacteriológica es exploratoria."
    )

    # ── Scatter nacional ─────────────────────────────────────────────────────

    st.markdown("##### Correlación por departamento")

    df_corr = _correlacion(pg, db, anio_inicio, anio_fin)

    if df_corr.empty:
        st.info("No hay datos suficientes para el período seleccionado.")
    else:
        fig_scatter = go.Figure(go.Scatter(
            x=df_corr["pct_presencia"],
            y=df_corr["total_reclamos"],
            mode="markers+text",
            text=df_corr["nombre"],
            textposition="top center",
            marker=dict(size=10, color="#e53935"),
            hovertemplate="<b>%{text}</b><br>Contaminación: %{x:.1f}%<br>Reclamos: %{y:,}<extra></extra>",
        ))
        fig_scatter.update_layout(
            xaxis_title="% muestras con contaminación (Coliformes Totales)",
            yaxis_title="Total reclamos comerciales",
            xaxis=dict(ticksuffix="%"),
            hovermode="closest",
            height=500,
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

    st.divider()

    # ── Evolución temporal del departamento seleccionado ─────────────────────

    st.markdown(f"##### Evolución trimestral — {nombre_depto}")

    df_rec_trim = _reclamos_trimestral(pg, departamento_id, anio_inicio, anio_fin)
    df_cal_crudo = _calidad(pg, departamento_id, anio_inicio, anio_fin, ("COLIFORMES TOTALES",))

    if df_rec_trim.empty and df_cal_crudo.empty:
        st.info(f"No hay datos para {nombre_depto} en el período seleccionado.")
    else:
        fig_dual = go.Figure()

        if not df_rec_trim.empty:
            fig_dual.add_trace(go.Bar(
                x=df_rec_trim["periodo"],
                y=df_rec_trim["n_reclamos"],
                name="Reclamos",
                marker_color="rgba(66,133,244,0.7)",
                yaxis="y1",
                hovertemplate="%{x|%Y-%m}: %{y:,} reclamos<extra></extra>",
            ))

        if not df_cal_crudo.empty:
            df_cal_grafico, _ = transformar_para_dashboard(df_cal_crudo)
            df_cal_grafico = df_cal_grafico.sort_values("periodo")
            fig_dual.add_trace(go.Scatter(
                x=df_cal_grafico["periodo"],
                y=df_cal_grafico["pct_presencia"],
                name="% contaminación",
                mode="lines+markers",
                line=dict(color="#e53935", width=2),
                yaxis="y2",
                hovertemplate="%{x|%Y-%m}: %{y:.1f}% contaminación<extra></extra>",
            ))

        fig_dual.update_layout(
            xaxis=dict(title="Trimestre", type="date"),
            yaxis=dict(title="Reclamos", side="left", rangemode="tozero"),
            yaxis2=dict(
                title="% contaminación",
                side="right",
                overlaying="y",
                ticksuffix="%",
                showgrid=False,
                rangemode="tozero",
            ),
            hovermode="x unified",
            legend=dict(orientation="h", y=-0.2),
            height=450,
        )
        st.plotly_chart(fig_dual, use_container_width=True)

    st.divider()

    # ── Tabla resumen por departamento ────────────────────────────────────────

    st.markdown("##### Resumen por departamento")

    if not df_corr.empty:
        df_tabla_rec = df_corr[["nombre", "total_reclamos", "pct_presencia"]].copy()
        df_tabla_rec.columns = ["Departamento", "Reclamos totales", "% Contaminación"]
        df_tabla_rec["% Contaminación"] = df_tabla_rec["% Contaminación"].round(1)
        st.dataframe(
            df_tabla_rec.sort_values("Reclamos totales", ascending=False).reset_index(drop=True),
            use_container_width=True,
            hide_index=True,
        )

# ── TAB PRECIPITACIÓN VS CHL-A ────────────────────────────────────────────────

with tab_precip_ndci:
    st.markdown("#### Precipitación (PAD) vs NDCI")
    st.caption(
        "Compara la precipitación acumulada decádica (PAD) del punto de grilla más cercano "
        "a un punto de monitoreo Sentinel-2 con el NDCI (índice, proxy de clorofila) de ese "
        "punto, desplazando la precipitación un número de meses (lag) para evaluar su efecto "
        "posterior."
    )

    df_locations_ndci = _locations_ndci(pg, db)

    if df_locations_ndci.empty:
        st.info("No hay puntos de monitoreo con mediciones de NDCI.")
    else:
        st.session_state.setdefault("ndci_location_id", df_locations_ndci["location_id"].iloc[0])

        df_mapa = df_locations_ndci.copy()
        seleccionado = df_mapa["location_id"] == st.session_state["ndci_location_id"]
        df_mapa["color"] = [
            [230, 80, 40, 200] if sel else [66, 133, 244, 140] for sel in seleccionado
        ]
        df_mapa["radio"] = [12000 if sel else 7000 for sel in seleccionado]

        capa_puntos = pydeck.Layer(
            "ScatterplotLayer",
            data=df_mapa,
            id="sentinel-points",
            get_position=["lon", "lat"],
            get_fill_color="color",
            get_radius="radio",
            pickable=True,
            auto_highlight=True,
        )
        capas = []

        coords_grilla = _punto_grilla_pad(db, st.session_state["ndci_location_id"])
        if coords_grilla is not None:
            fila_actual = df_locations_ndci.loc[
                df_locations_ndci["location_id"] == st.session_state["ndci_location_id"]
            ].iloc[0]
            lat_grilla, lon_grilla = coords_grilla

            df_linea = pd.DataFrame([{
                "lat_origen": fila_actual["lat"],
                "lon_origen": fila_actual["lon"],
                "lat_destino": lat_grilla,
                "lon_destino": lon_grilla,
            }])
            capa_linea = pydeck.Layer(
                "LineLayer",
                data=df_linea,
                id="pad-grid-line",
                get_source_position=["lon_origen", "lat_origen"],
                get_target_position=["lon_destino", "lat_destino"],
                get_color=[120, 120, 120, 160],
                get_width=2,
            )

            df_grilla = pd.DataFrame([{
                "lat": lat_grilla,
                "lon": lon_grilla,
                "nombre": "Punto de grilla PAD",
            }])
            capa_grilla = pydeck.Layer(
                "ScatterplotLayer",
                data=df_grilla,
                id="pad-grid-point",
                get_position=["lon", "lat"],
                get_fill_color=[46, 125, 50, 220],
                get_radius=9000,
                stroked=True,
                get_line_color=[255, 255, 255],
                line_width_min_pixels=2,
                pickable=False,
            )

            capas = [capa_linea, capa_grilla]

        vista_mapa = pydeck.ViewState(
            latitude=df_mapa["lat"].mean(),
            longitude=df_mapa["lon"].mean(),
            zoom=6,
            controller=True,
        )
        mapa_puntos = pydeck.Deck(
            layers=[*capas, capa_puntos],
            initial_view_state=vista_mapa,
            tooltip={"html": "<b>{nombre}</b>"},
        )

        evento_mapa = st.pydeck_chart(
            mapa_puntos,
            on_select="rerun",
            selection_mode="single-object",
            use_container_width=True,
            height=550,
        )

        opciones = df_locations_ndci["nombre"].tolist()
        ids = df_locations_ndci["location_id"].tolist()
        ids_str = [str(i) for i in ids]

        objetos_seleccionados = evento_mapa.selection.get("objects", {}).get("sentinel-points", [])
        if objetos_seleccionados:
            nuevo_location_id_str = str(objetos_seleccionados[0]["location_id"])
            if nuevo_location_id_str != str(st.session_state["ndci_location_id"]):
                idx_nuevo = ids_str.index(nuevo_location_id_str)
                st.session_state["ndci_location_id"] = ids[idx_nuevo]
                st.session_state["ndci_punto_selectbox"] = opciones[idx_nuevo]
                st.rerun()

        col_est, col_lag = st.columns([3, 1])
        with col_est:
            try:
                indice_actual = ids_str.index(str(st.session_state["ndci_location_id"]))
            except ValueError:
                indice_actual = 0
            nombre_punto = st.selectbox(
                "Punto de monitoreo (Sentinel-2)",
                options=opciones,
                index=indice_actual,
                key="ndci_punto_selectbox",
            )
        with col_lag:
            lag_meses = st.selectbox("Lag (meses)", options=list(range(0, 7)), index=1)

        location_id = df_locations_ndci.loc[
            df_locations_ndci["nombre"] == nombre_punto, "location_id"
        ].iloc[0]
        st.session_state["ndci_location_id"] = location_id

        df_precip_ndci = _precip_vs_ndci(pg, db, location_id, anio_inicio, anio_fin, lag_meses)

        if df_precip_ndci.empty:
            st.info(f"No hay datos para {nombre_punto} en el período seleccionado.")
        else:
            fig_precip_ndci = go.Figure()

            if df_precip_ndci["pad"].notna().any():
                fig_precip_ndci.add_trace(go.Bar(
                    x=df_precip_ndci["periodo"],
                    y=df_precip_ndci["pad"],
                    name=f"PAD (t-{lag_meses})",
                    marker_color="rgba(66,133,244,0.7)",
                    yaxis="y1",
                    customdata=df_precip_ndci["pad_periodo"].dt.strftime("%Y-%m"),
                    hovertemplate="PAD de %{customdata}: %{y:.1f} mm<extra></extra>",
                ))
            else:
                st.info("No se encontró un punto de grilla PAD cercano a este punto.")

            if df_precip_ndci["ndci"].notna().any():
                fig_precip_ndci.add_trace(go.Scatter(
                    x=df_precip_ndci["periodo"],
                    y=df_precip_ndci["ndci"],
                    name="NDCI",
                    mode="lines+markers",
                    connectgaps=False,
                    line=dict(color="#2e7d32", width=2),
                    yaxis="y2",
                    hovertemplate="%{x|%Y-%m}: %{y:.3f}<extra></extra>",
                ))

            fig_precip_ndci.update_layout(
                xaxis=dict(title="Mes", type="date"),
                yaxis=dict(title="PAD (mm)", side="left", rangemode="tozero"),
                yaxis2=dict(
                    title="NDCI (índice)",
                    side="right",
                    overlaying="y",
                    showgrid=False,
                ),
                hovermode="x unified",
                legend=dict(orientation="h", y=-0.2),
                height=450,
            )
            st.plotly_chart(fig_precip_ndci, use_container_width=True)

            st.divider()
            st.markdown("##### Correlación PAD vs NDCI por lag")

            df_corr_lag = _correlacion_lag(pg, db, location_id, anio_inicio, anio_fin)

            if df_corr_lag.empty or df_corr_lag["correlacion"].isna().all():
                st.info("No hay suficientes datos para calcular la correlación por lag.")
            else:
                colores = [
                    "#f9a825" if lag == lag_meses else "rgba(66,133,244,0.7)"
                    for lag in df_corr_lag["lag"]
                ]

                fig_corr_lag = go.Figure()
                fig_corr_lag.add_trace(go.Bar(
                    x=df_corr_lag["lag"],
                    y=df_corr_lag["correlacion"],
                    marker_color=colores,
                    customdata=df_corr_lag["n"],
                    hovertemplate="lag=%{x} meses: r=%{y:.2f} (n=%{customdata})<extra></extra>",
                ))
                fig_corr_lag.update_layout(
                    xaxis=dict(title="Lag (meses)", dtick=1),
                    yaxis=dict(title="Correlación (Pearson)", range=[-1, 1]),
                    height=350,
                )
                st.plotly_chart(fig_corr_lag, use_container_width=True)
                st.caption(
                    f"La barra resaltada corresponde al lag seleccionado arriba (t-{lag_meses})."
                )
