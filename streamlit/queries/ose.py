import pandas as pd


TRIMESTRE_LABEL = {
    1: "Q1 (Ene–Mar)",
    2: "Q2 (Abr–Jun)",
    3: "Q3 (Jul–Sep)",
    4: "Q4 (Oct–Dic)",
}


def get_patron_estacional(pg_conn, ose_code: str, anio_inicio: int, anio_fin: int) -> pd.DataFrame:
    sql = """
        SELECT
            EXTRACT(QUARTER FROM fecha_inicio)::int AS trimestre,
            COUNT(*) AS total,
            SUM(CASE WHEN value_cat = 'Presencia' THEN 1 ELSE 0 END) AS presencias,
            ROUND(SUM(CASE WHEN value_cat = 'Presencia' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS pct_presencia
        FROM oseparam
        WHERE code = %s
          AND EXTRACT(YEAR FROM fecha_inicio) BETWEEN %s AND %s
          AND value_cat IN ('Presencia', 'Ausencia')
        GROUP BY trimestre
        ORDER BY trimestre
    """
    cur = pg_conn.cursor()
    cur.execute(sql, (ose_code, anio_inicio, anio_fin))
    rows = cur.fetchall()
    df = pd.DataFrame(rows, columns=["trimestre", "total", "presencias", "pct_presencia"])
    df["trimestre_label"] = df["trimestre"].map(TRIMESTRE_LABEL)
    df["pct_presencia"] = df["pct_presencia"].astype(float)
    return df


def get_pct_presencia_por_departamento_periodo(
    pg_conn, mongo_db, ose_code: str, anio_inicio: int, anio_fin: int
) -> pd.DataFrame:
    sql = """
        SELECT departamento_id,
            SUM(CASE WHEN value_cat = 'Presencia' THEN total ELSE 0 END) * 100.0 / SUM(total) AS pct_presencia
        FROM (
            SELECT departamento_id, value_cat, COUNT(*) AS total
            FROM oseparam
            WHERE code = %s
              AND EXTRACT(YEAR FROM fecha_inicio) BETWEEN %s AND %s
              AND value_cat IN ('Presencia', 'Ausencia')
            GROUP BY departamento_id, value_cat
        ) sub
        GROUP BY departamento_id
    """
    cur = pg_conn.cursor()
    cur.execute(sql, (ose_code, anio_inicio, anio_fin))
    rows = cur.fetchall()
    if not rows:
        return pd.DataFrame(columns=["nombre", "pct_presencia"])
    df = pd.DataFrame(rows, columns=["departamento_id", "pct_presencia"])
    uuids = df["departamento_id"].tolist()
    docs = mongo_db["departamentos"].find({"_id": {"$in": uuids}}, {"_id": 1, "nombre": 1})
    nombres = {d["_id"]: d["nombre"] for d in docs}
    df["nombre"] = df["departamento_id"].map(nombres)
    df["pct_presencia"] = df["pct_presencia"].astype(float)
    return df[["nombre", "pct_presencia"]].dropna(subset=["nombre"])


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
