import pandas as pd


def get_evolucion_calidad(
    pg_conn,
    departamento_id,
    anio_inicio: int,
    anio_fin: int,
    codigos: tuple,
) -> pd.DataFrame:
    sql = """--sql
        SELECT
            DATE_TRUNC('quarter', fecha_inicio) AS periodo,
            code,
            value_cat,
            COUNT(*) AS total
        FROM oseparam
        WHERE departamento_id = %s
          AND EXTRACT(YEAR FROM fecha_inicio) >= %s
          AND EXTRACT(YEAR FROM fecha_inicio) <= %s
          AND code = ANY(%s)
          AND value_cat IN ('Presencia', 'Ausencia')
        GROUP BY periodo, code, value_cat
        ORDER BY periodo, code, value_cat
    """
    cur = pg_conn.cursor()
    cur.execute(sql, (departamento_id, anio_inicio, anio_fin, list(codigos)))
    rows = cur.fetchall()
    return pd.DataFrame(rows, columns=["periodo", "code", "value_cat", "total"])


def transformar_para_dashboard(df_crudo: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    totales = (
        df_crudo.groupby(["periodo", "code"])["total"]
        .sum()
        .reset_index()
        .rename(columns={"total": "total_muestras"})
    )

    presencias = (
        df_crudo[df_crudo["value_cat"] == "Presencia"][["periodo", "code", "total"]]
        .rename(columns={"total": "presencias"})
    )

    merged = totales.merge(presencias, on=["periodo", "code"], how="left")
    merged["presencias"] = merged["presencias"].fillna(0)
    merged["pct_presencia"] = merged["presencias"] / merged["total_muestras"] * 100

    mes_a_trimestre = {1: 1, 4: 2, 7: 3, 10: 4}
    merged["q"] = merged["periodo"].dt.month.map(mes_a_trimestre)
    merged["periodo_str"] = (
        merged["periodo"].dt.year.astype(str) + " Q" + merged["q"].astype(str)
    )
    merged["anio"] = merged["periodo"].dt.year

    df_grafico = merged[["periodo_str", "periodo", "code", "pct_presencia", "total_muestras"]]

    df_tabla = merged.pivot_table(
        index="anio",
        columns="code",
        values="pct_presencia",
        aggfunc="mean",
    ).round(1)
    df_tabla.columns.name = "Parámetro"
    df_tabla.index.name = "Año"

    return df_grafico, df_tabla
