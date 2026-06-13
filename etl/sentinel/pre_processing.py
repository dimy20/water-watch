import warnings
import numpy as np
import pandas as pd
import stackstac
from pystac_client import Client
from etl.sentinel.params import (
    EARTH_SEARCH_URL,
    SENTINEL_SURFACE_REFLECTION,
    AGUA,
    DATETIME_RANGE,
    MAX_CLOUD_COVER,
)
from etl.sentinel.geo import make_bounds
from etl.sentinel.logger import log

# NDCI = (rededge1 - red) / (rededge1 + red); fuera de la mascara de agua los
# pixeles son NaN y algunos pixeles de agua tienen denominador 0, lo que produce
# warnings de numpy/dask inofensivos (el resultado NaN/inf se filtra mas abajo).
warnings.filterwarnings("ignore", message="divide by zero encountered in divide")
warnings.filterwarnings("ignore", message="invalid value encountered in divide")

catalog = Client.open(EARTH_SEARCH_URL)

def compute_ndci_series(coords: list, width: float, resolution: int) -> list[tuple]:
    bounds = make_bounds(coords, dist=width)

    items = catalog.search(
        collections=[SENTINEL_SURFACE_REFLECTION],
        datetime=DATETIME_RANGE,
        query={"eo:cloud_cover": {"lt": MAX_CLOUD_COVER}},
        bbox=bounds,
    ).item_collection()

    log.info(f"  {len(items)} escenas encontradas")

    if len(items) == 0:
        return []

    stack = stackstac.stack(
        items,
        epsg=32721,
        assets=["red", "rededge1", "scl"],
        resolution=resolution,
        bounds_latlon=bounds,
    )

    stack = stack.where(stack.sel(band="scl") == AGUA)
    red = stack.sel(band="red")
    rededge1 = stack.sel(band="rededge1")
    ndci = (rededge1 - red) / (rededge1 + red)

    log.info("  calculando NDCI sobre las escenas (puede tardar varios minutos)...")
    serie = ndci.median(dim=["x", "y"], skipna=True).compute()

    result = []

    for time, value in zip(serie.time.values, serie.values):
        if np.isnan(value):
            continue
        fecha = pd.Timestamp(time).date()
        result.append((fecha, float(value)))

    log.info(f"  {len(result)} fechas con NDCI válido de {len(items)} escenas")

    return result
