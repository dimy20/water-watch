import geopandas as pd
from typing import List

def get_repetidos(df: pd.GeoDataFrame):
    nombres_count = {}
    for n in df["NOMBRE"]:
        if n == "SIN_NOMBRE":
            continue
        nombres_count[n] = nombres_count.get(n, 0) + 1
    nombres_repetidos = set([kv[0] for kv in nombres_count.items() if kv[1] > 1])
    return nombres_repetidos

def fix_nombres(df: pd.GeoDataFrame) -> str:
    df["NOMBRE"] = df["NOMBRE"].fillna("SIN_NOMBRE")

    nuevos_nombres = []
    areas_disponibles = set(["AREA_A", "AREA_B", "AREA_C", "AREA_D"])
    counts = {}
    nombres_repetidos = get_repetidos(df)

    for nombre in nombres_repetidos:
        counts[nombre] = 0

    def fix_repetido(n):
        i = counts[n]
        res = f"{n}_{i+1}"
        counts[n] += 1
        return res
        
    for n in df["NOMBRE"]:
        if n in nombres_repetidos:
            nuevo = fix_repetido(n)
            nuevos_nombres.append(nuevo)
        elif n == "SIN_NOMBRE":
            nuevo = areas_disponibles.pop()
            nuevos_nombres.append(nuevo)
        else:
            nuevos_nombres.append(n)

    return nuevos_nombres

def cambiar_nombres(gdf: pd.GeoDataFrame, nombres_nuevos: List[str]):
    if len(gdf) != len(nombres_nuevos):
        raise ValueError("La cantidad de nombres nuevos no coincide con la cantidad de filas del GeoDataFrame")

    gdf = gdf.copy()
    gdf["NOMBRE"] = nombres_nuevos

    return gdf