import streamlit as st
import plotly.graph_objects as go

from utils import postgres, mongo
from queries import (
    get_departamentos_con_datos,
    get_evolucion_calidad,
    transformar_para_dashboard,
    get_estaciones_por_departamento,
    get_gems_evolucion,
)
from styles import apply_styles

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
    "FECALCOLI":  ("Coliformes fecales",              "MPN/100ml"),
    "ECOLI":      ("E. coli",                         "MPN/100ml"),
    "TOTCOLI":    ("Coliformes totales",              "MPN/100ml"),
    "TURB":       ("Turbidez",                        "NTU"),
    "TSS":        ("Sólidos suspendidos totales",     "mg/l"),
    "Chl-a":      ("Clorofila A",                     "mg/l"),
    "TRANS":      ("Transparencia",                   "m"),
}

apply_styles()

pg = postgres()
db = mongo()


@st.cache_data(ttl=3600)
def _departamentos(_pg, _db):
    return get_departamentos_con_datos(_pg, _db)


@st.cache_data(ttl=600)
def _calidad(_pg, departamento_id, anio_inicio, anio_fin, codigos):
    return get_evolucion_calidad(_pg, departamento_id, anio_inicio, anio_fin, codigos)


@st.cache_data(ttl=3600)
def _estaciones_depto(_db, departamento_id):
    return get_estaciones_por_departamento(_db, departamento_id)


@st.cache_data(ttl=600)
def _gems_calidad(_pg, location_ids, anio_inicio, anio_fin, code):
    return get_gems_evolucion(_pg, list(location_ids), anio_inicio, anio_fin, code)


df_deptos = _departamentos(pg, db)

depto_default = st.session_state.get("departamento_mapa", df_deptos["nombre"].iloc[0])
idx = df_deptos["nombre"].tolist().index(depto_default) if depto_default in df_deptos["nombre"].values else 0

with st.sidebar:
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

st.title("Calidad del Agua — Uruguay")
st.subheader(f"{nombre_depto} · {anio_inicio}–{anio_fin}")

tab_ose, tab_gems = st.tabs(["🦠 Bacteriología (OSE)", "🔬 Fisicoquímica (GEMS)"])

# ── TAB OSE ──────────────────────────────────────────────────────────────────

with tab_ose:
    parametros_ose = st.multiselect(
        "Parámetros",
        options=["COLIFORMES TOTALES", "ESCHERICHIA COLI"],
        default=["COLIFORMES TOTALES", "ESCHERICHIA COLI"],
    )

    if not parametros_ose:
        st.warning("Seleccioná al menos un parámetro bacteriológico en el panel lateral.")
    else:
        df_crudo = _calidad(pg, departamento_id, anio_inicio, anio_fin, tuple(parametros_ose))

        if df_crudo.empty:
            st.info(f"No hay datos bacteriológicos para {nombre_depto} entre {anio_inicio} y {anio_fin}.")
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

            fig = go.Figure()
            df_sorted = df_grafico.sort_values("periodo")
            for code in df_sorted["code"].unique():
                df_code = df_sorted[df_sorted["code"] == code]
                fig.add_trace(go.Scatter(
                    x=df_code["periodo_str"],
                    y=df_code["pct_presencia"],
                    mode="lines+markers",
                    name=code.title(),
                    hovertemplate="%{x}: %{y:.1f}%<extra></extra>",
                ))

            fig.update_layout(
                title=f"Evolución de contaminación bacteriana — {nombre_depto}",
                xaxis_title="Trimestre",
                yaxis_title="% Muestras con presencia",
                yaxis=dict(range=[0, max(df_grafico["pct_presencia"].max() * 1.2, 5)], ticksuffix="%"),
                legend_title="Parámetro",
                hovermode="x unified",
            )
            st.plotly_chart(fig, use_container_width=True)

            st.subheader("% promedio de muestras con contaminación por año")
            st.dataframe(df_tabla, use_container_width=True)

# ── TAB GEMS ─────────────────────────────────────────────────────────────────

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

            # Banda de variabilidad (min-max)
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

            # Línea de promedio mensual
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
