# ETL - Sentinel

Calcula la serie temporal del índice NDCI (Normalized Difference Chlorophyll Index)
para un conjunto de puntos de interés (lagos, lagunas, embalses y arroyos), a partir
de imágenes Sentinel-2 L2A vía STAC (Earth Search by Element 84) + `stackstac`.

## Datos de entrada

`data/sentinel/puntos_v1.csv` — columnas `Nombre, Latitud, Longitud, Link_Google_Maps,
Width, Resolution`. `Width` y `Resolution` fueron ajustados manualmente por punto
(ver `ndci.ipynb`) para maximizar la cantidad de píxeles de agua capturados según el
tamaño del cuerpo de agua.

## Módulos

- `geo.py` — `make_bounds` / `make_bbox_polygon`: bbox `[lon_min, lat_min, lon_max,
  lat_max]` a partir de `coords` + `Width`.
- `pre_processing.py` — `compute_ndci_series(coords, width, resolution)`: busca
  escenas Sentinel-2 (`DATETIME_RANGE`, `MAX_CLOUD_COVER`), apila bandas `red`,
  `rededge1`, `scl` con `stackstac`, enmascara píxeles que no son agua (`SCL == AGUA`)
  y calcula la mediana de NDCI por escena. Devuelve `[(fecha, valor), ...]`,
  descartando escenas sin píxeles de agua válidos.
- `load_locations.py` — crea un documento por punto en la colección MongoDB
  `sentinel_locations` (geometría = bbox del punto), vía `bulk_write`/upsert.
- `load_mediciones.py` — para cada punto, busca su `location_id` en
  `sentinel_locations`, calcula la serie NDCI y la inserta en PostgreSQL
  (`sentinel_params`), una fila por escena (`granularidad = 'DIA'`,
  `fecha_inicio = fecha_fin = fecha de la escena`).

## Storage

| Dato | Destino |
|---|---|
| Ubicación / bbox por punto | MongoDB, colección `sentinel_locations` |
| Serie NDCI | PostgreSQL, tabla `sentinel_params` |

Deduplicación determinística vía `create_id` (MD5) sobre todos los campos de cada fila.
