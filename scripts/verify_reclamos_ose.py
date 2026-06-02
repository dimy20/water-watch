"""
Verifica la totalidad de registros en los CSVs originales de reclamos OSE,
mostrando cuántos quedan y cuántos se descartan con el filtro >= 2015.

Uso:
    python scripts/verify_reclamos_ose.py
"""

import glob
from pathlib import Path
import sys
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from etl.reclamos.pre_processing import RECLAMOS_MAP

DATA_GLOB = str(Path(__file__).parent.parent / "data" / "reclamos" / "solicitudes_y_reclamos-comerciales_*.csv")

COLS_KEEP = ["fecha_ingreso", "tipo_reclamo_comercial", "departamento"]


def verify():
    files = sorted(glob.glob(DATA_GLOB))
    print(f"Archivos encontrados: {len(files)}")
    for f in files:
        print(f"  {Path(f).name}")
    print()

    dfs = [pd.read_csv(f, sep=";", encoding="latin1", low_memory=False) for f in files]
    df = pd.concat(dfs, ignore_index=True)
    print(f"Total registros en CSVs: {len(df):,}\n")

    # Filtro SIN DATOS
    sin_datos = (df["departamento"] == "SIN DATOS").sum()
    df = df[df["departamento"] != "SIN DATOS"]
    print(f"Descartados por departamento == SIN DATOS: {sin_datos:,}")
    print(f"Restantes: {len(df):,}\n")

    # Parsear fecha
    df["fecha_inicio"] = pd.to_datetime(df["fecha_ingreso"], errors="coerce")
    fecha_nula = df["fecha_inicio"].isna().sum()
    if fecha_nula:
        print(f"Descartados por fecha_ingreso no parseable: {fecha_nula:,}")
        df = df.dropna(subset=["fecha_inicio"])
        print(f"Restantes: {len(df):,}\n")

    # Distribución por año (todos los registros)
    df["anio"] = df["fecha_inicio"].dt.year
    print("Distribución por año (dataset completo):")
    por_anio = df["anio"].value_counts().sort_index()
    for anio, cnt in por_anio.items():
        marca = "  " if anio >= 2015 else "✗ "
        print(f"  {marca}{int(anio)}: {cnt:>10,}")
    print()

    # Filtro >= 2015
    pre2015 = (df["anio"] < 2015).sum()
    df_filtrado = df[df["anio"] >= 2015]
    print(f"Descartados por fecha_inicio < 2015: {pre2015:,}")
    print(f"Restantes tras filtro 2015: {len(df_filtrado):,}\n")

    # Tipos no mapeables
    df_filtrado = df_filtrado.copy()
    df_filtrado["tipo_mapeado"] = df_filtrado["tipo_reclamo_comercial"].map(RECLAMOS_MAP)
    no_mapeados = df_filtrado["tipo_mapeado"].isna()
    print(f"Descartados por tipo no reconocido: {no_mapeados.sum():,}")
    if no_mapeados.sum() > 0:
        print("  Tipos sin mapeo:")
        for tipo, cnt in df_filtrado[no_mapeados]["tipo_reclamo_comercial"].value_counts().items():
            print(f"    '{tipo}': {cnt:,}")
    print(f"Restantes tras normalización de tipo: {(~no_mapeados).sum():,}\n")

    # Resumen final
    total_original = len(pd.concat(dfs, ignore_index=True))
    total_final = (~no_mapeados).sum()
    print(f"--- Resumen ---")
    print(f"  Total original:  {total_original:>10,}")
    print(f"  Total a cargar:  {total_final:>10,}")
    print(f"  Descartados:     {total_original - total_final:>10,} ({(total_original - total_final) / total_original * 100:.1f}%)")


if __name__ == "__main__":
    verify()
