import streamlit as st
import plotly.graph_objects as go

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


@st.cache_data(ttl=3600)
def _pct_por_depto(_pg, _db):
    return get_pct_presencia_por_departamento(_pg, _db)


@st.cache_data(ttl=3600)
def _gems_bacterio_nacional(_db, _pg, gems_code):
    return get_gems_bacterio_por_departamento(_db, _pg, gems_code)


@st.cache_data(ttl=3600)
def _geojson(_db):
    return get_departamentos_geojson(_db)


@st.cache_data(ttl=3600)
def _hidrico_suelo(_db, _pg, tipo, anio_inicio, anio_fin):
    return get_hidrico_suelo_por_departamento(_db, _pg, tipo, anio_inicio, anio_fin)


@st.cache_data(ttl=3600)
def _riesgo(_db, _pg, anio_inicio, anio_fin):
    return get_riesgo_por_departamento(_db, _pg, anio_inicio, anio_fin)


@st.cache_data(ttl=3600)
def _correlacion(_pg, _db, anio_inicio, anio_fin):
    return get_correlacion_reclamos_calidad(_pg, _db, anio_inicio, anio_fin)


@st.cache_data(ttl=600)
def _reclamos_trimestral(_pg, departamento_id, anio_inicio, anio_fin):
    return get_reclamos_trimestral(_pg, departamento_id, anio_inicio, anio_fin)


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

st.title("Water Watch")
st.subheader(f"{nombre_depto} · {anio_inicio}–{anio_fin}")

tab_bacterio, tab_gems, tab_resumen, tab_suelo, tab_riesgo, tab_reclamos = st.tabs([
    "Bacteriología",
    "Fisicoquímica (GEMS)",
    "Resumen nacional",
    "Estado hídrico del suelo",
    "Indicador de Riesgo",
    "Reclamos vs Calidad",
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
    gems_code_resumen = BACTERIO_PARAMS[param_resumen]["gems_code"]
    unidad_resumen = BACTERIO_PARAMS[param_resumen]["unidad"]

    # ── OSE (arriba) ─────────────────────────────────────────────────────────

    st.markdown("#### Bacteriología OSE — % muestras con presencia por departamento")

    df_resumen = _pct_por_depto(pg, db)
    df_resumen = df_resumen.sort_values("pct_presencia", ascending=True)

    fig_resumen = go.Figure(go.Bar(
        x=df_resumen["pct_presencia"],
        y=df_resumen["nombre"],
        orientation="h",
        marker_color="#e53935",
        hovertemplate="%{y}: %{x:.1f}%<extra></extra>",
    ))
    fig_resumen.update_layout(
        xaxis_title="% muestras con contaminación",
        xaxis=dict(ticksuffix="%"),
        yaxis_title=None,
        height=550,
        margin=dict(l=140),
    )
    st.plotly_chart(fig_resumen, use_container_width=True)
    st.caption("Datos OSE 2017–2025. Incluye Coliformes Totales y E. coli.")

    st.divider()

    # ── GEMS (abajo) ──────────────────────────────────────────────────────────

    st.markdown(f"#### GEMS — {param_resumen} promedio por departamento ({unidad_resumen})")

    df_gems_nac = _gems_bacterio_nacional(db, pg, gems_code_resumen)

    if df_gems_nac.empty:
        st.info(f"No hay datos GEMS de {param_resumen} para ningún departamento.")
    else:
        df_gems_nac = df_gems_nac.sort_values("valor_medio", ascending=True)

        fig_gems_nac = go.Figure(go.Bar(
            x=df_gems_nac["valor_medio"],
            y=df_gems_nac["nombre"],
            orientation="h",
            marker_color="#e53935",
            hovertemplate="%{y}: %{x:.2f} " + unidad_resumen + "<extra></extra>",
        ))
        fig_gems_nac.update_layout(
            xaxis_title=f"Promedio {param_resumen} ({unidad_resumen})",
            yaxis_title=None,
            height=550,
            margin=dict(l=140),
        )
        st.plotly_chart(fig_gems_nac, use_container_width=True)
        st.caption(f"Promedio histórico por departamento según estaciones GEMS. {len(df_gems_nac)} departamentos con datos.")

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
        col1, col2, col3 = st.columns(3)
        col1.metric("Promedio nacional", f"{df_suelo['valor_medio'].mean():.2f}")
        col2.metric("Departamento mínimo", f"{df_suelo['valor_medio'].min():.2f}")
        col3.metric("Departamento máximo", f"{df_suelo['valor_medio'].max():.2f}")

        geojson = _geojson(db)

        fig_suelo = go.Figure(go.Choropleth(
            geojson=geojson,
            locations=df_suelo["nombre"].tolist(),
            z=df_suelo["valor_medio"].round(3).tolist(),
            featureidkey="properties.nombre",
            colorscale="Blues",
            zmin=df_suelo["valor_medio"].min(),
            zmax=df_suelo["valor_medio"].max(),
            marker_line_color="white",
            marker_line_width=1.5,
            colorbar_title=tipo_suelo,
            hovertemplate="<b>%{location}</b><br>%{z:.2f}<extra></extra>",
        ))
        fig_suelo.update_geos(fitbounds="locations", visible=False)
        fig_suelo.update_layout(
            title=f"{tipo_suelo} — {TIPOS[tipo_suelo]} · {anio_inicio}–{anio_fin}",
            margin={"r": 0, "t": 40, "l": 0, "b": 0},
            height=550,
        )
        st.plotly_chart(fig_suelo, use_container_width=True)

        df_bar = df_suelo.sort_values("valor_medio", ascending=True)
        fig_bar = go.Figure(go.Bar(
            x=df_bar["valor_medio"],
            y=df_bar["nombre"],
            orientation="h",
            marker_color="#1a73e8",
            hovertemplate="%{y}: %{x:.2f}<extra></extra>",
        ))
        fig_bar.update_layout(
            xaxis_title=f"Promedio {tipo_suelo}",
            yaxis_title=None,
            height=500,
            margin=dict(l=140),
        )
        st.plotly_chart(fig_bar, use_container_width=True)
        st.caption(f"Promedio de puntos de grilla por departamento. {len(df_suelo)} departamentos con datos.")

# ── TAB INDICADOR DE RIESGO ───────────────────────────────────────────────────

with tab_riesgo:
    st.markdown("#### Indicador de Riesgo Combinado")

    with st.expander("Metodología", expanded=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(
                "**Contaminación bacteriológica**  \n"
                "OSE (% presencia coliformes totales) + GEMS (TOTCOLI, MPN/100ml).  \n"
                "Activa si supera el percentil 66 del período."
            )
        with c2:
            st.markdown(
                "**Precipitación**  \n"
                "Pluviometría media diaria (mm/día) — estaciones INIA.  \n"
                "Activa si supera el percentil 66 del período."
            )
        with c3:
            st.markdown(
                "**Índice de Humedad del Balance (IBH)**  \n"
                "Grillas INIA-GRAS, cobertura nacional.  \n"
                "Activa si está por debajo del percentil 33 del período."
            )

        st.divider()
        st.markdown(
            "| Score | Interpretación |\n"
            "|---|---|\n"
            "| 0 | Sin condiciones adversas |\n"
            "| 1 | Una condición supera el umbral |\n"
            "| 2 | Dos condiciones coinciden |\n"
            "| 3 | Las tres condiciones coinciden — riesgo elevado |"
        )

    st.caption(
        "La precipitación cubre solo los 5 departamentos con estación INIA (score máximo 2 en los demás). "
        "Los umbrales son relativos al período seleccionado."
    )

    df_riesgo = _riesgo(db, pg, anio_inicio, anio_fin)

    if df_riesgo.empty:
        st.info("No hay datos suficientes para calcular el indicador de riesgo en el período seleccionado.")
    else:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Score 0 (sin riesgo)", int((df_riesgo["score"] == 0).sum()))
        col2.metric("Score 1", int((df_riesgo["score"] == 1).sum()))
        col3.metric("Score 2", int((df_riesgo["score"] == 2).sum()))
        col4.metric("Score 3 (riesgo total)", int((df_riesgo["score"] == 3).sum()))

        geojson = _geojson(db)

        def _fmt(val, fmt, suffix=""):
            return f"{val:{fmt}}{suffix}" if val == val else "—"  # nan check

        df_riesgo["_tip_ose"] = df_riesgo["pct_ose"].apply(lambda x: _fmt(x, ".1f", "%"))
        df_riesgo["_tip_gems"] = df_riesgo["val_gems"].apply(lambda x: _fmt(x, ".2f", " MPN/100ml"))
        df_riesgo["_tip_precip"] = df_riesgo["val_precip"].apply(
            lambda x: _fmt(x, ".1f", " mm/día") if x == x else "sin datos"
        )
        df_riesgo["_tip_ibh"] = df_riesgo["val_suelo"].apply(lambda x: _fmt(x, ".2f"))
        df_riesgo["_tip_c"] = df_riesgo["condicion_contam"].map({True: "⚠", False: ""})
        df_riesgo["_tip_p"] = df_riesgo["condicion_precip"].map({True: "⚠", False: ""})
        df_riesgo["_tip_s"] = df_riesgo["condicion_suelo"].map({True: "⚠", False: ""})

        customdata = df_riesgo[[
            "_tip_ose", "_tip_gems", "_tip_precip", "_tip_ibh",
            "_tip_c", "_tip_p", "_tip_s",
        ]].values

        fig_riesgo = go.Figure(go.Choropleth(
            geojson=geojson,
            locations=df_riesgo["nombre"].tolist(),
            z=df_riesgo["score"].tolist(),
            featureidkey="properties.nombre",
            colorscale=[
                [0.0,  "#2ca02c"],
                [0.33, "#ffdd57"],
                [0.67, "#ff7f0e"],
                [1.0,  "#d62728"],
            ],
            zmin=0,
            zmax=3,
            marker_line_color="white",
            marker_line_width=1.5,
            colorbar=dict(
                title="Score",
                tickvals=[0, 1, 2, 3],
                ticktext=["0 — Sin riesgo", "1 — Bajo", "2 — Medio", "3 — Alto"],
            ),
            customdata=customdata,
            hovertemplate=(
                "<b>%{location}</b><br>"
                "Score: <b>%{z}/3</b><br>"
                "Contam. OSE: %{customdata[0]} %{customdata[4]}<br>"
                "Contam. GEMS: %{customdata[1]} %{customdata[5]}<br>"
                "Precipitación: %{customdata[2]} %{customdata[6]}<br>"
                "IBH: %{customdata[3]}"
                "<extra></extra>"
            ),
        ))
        fig_riesgo.update_geos(fitbounds="locations", visible=False)
        fig_riesgo.update_layout(
            title=f"Indicador de Riesgo · {anio_inicio}–{anio_fin}",
            margin={"r": 0, "t": 40, "l": 0, "b": 0},
            height=550,
        )
        st.plotly_chart(fig_riesgo, use_container_width=True)

        with st.expander("Ver datos por departamento"):
            df_tabla_riesgo = df_riesgo[[
                "nombre", "score", "pct_ose", "val_gems", "val_precip", "val_suelo",
                "condicion_contam", "condicion_precip", "condicion_suelo",
            ]].copy()
            df_tabla_riesgo.columns = [
                "Departamento", "Score",
                "Contam. OSE (%)", "Contam. GEMS (MPN/100ml)",
                "Precipitación (mm/día)", "IBH",
                "⚠ Contam.", "⚠ Precip.", "⚠ Suelo",
            ]
            df_tabla_riesgo["⚠ Contam."] = df_tabla_riesgo["⚠ Contam."].map({True: "✓", False: "✗"})
            df_tabla_riesgo["⚠ Precip."] = df_tabla_riesgo["⚠ Precip."].map({True: "✓", False: "✗"})
            df_tabla_riesgo["⚠ Suelo"] = df_tabla_riesgo["⚠ Suelo"].map({True: "✓", False: "✗"})
            for col in ["Contam. OSE (%)", "Contam. GEMS (MPN/100ml)", "Precipitación (mm/día)", "IBH"]:
                df_tabla_riesgo[col] = df_tabla_riesgo[col].apply(
                    lambda x: round(x, 2) if x == x else None
                )
            st.dataframe(
                df_tabla_riesgo.sort_values("Score", ascending=False).reset_index(drop=True),
                use_container_width=True,
                hide_index=True,
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
