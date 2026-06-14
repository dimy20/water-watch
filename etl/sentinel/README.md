# ETL - Sentinel

Calcula series temporales de índices espectrales (NDCI y NDTI) para un conjunto de
puntos de interés (lagos, lagunas, embalses y arroyos), a partir de imágenes
Sentinel-2 L2A vía STAC (Earth Search by Element 84) + `stackstac`.

- **NDCI** (Normalized Difference Chlorophyll Index): `(rededge1 - red) / (rededge1 + red)`.
- **NDTI** (Normalized Difference Turbidity Index): `(red - green) / (red + green)`.

Ambos índices se calculan sobre píxeles de agua (`SCL == AGUA`) y se cargan por
separado, cada uno como su propia tarea del pipeline.

## Datos de entrada

`data/sentinel/puntos_v1.csv` — columnas `Nombre, Latitud, Longitud, Link_Google_Maps,
Width, Resolution`. `Width` y `Resolution` fueron ajustados manualmente por punto
(ver `ndci.ipynb`) para maximizar la cantidad de píxeles de agua capturados según el
tamaño del cuerpo de agua.

## Módulos

- `geo.py` — `make_bounds` / `make_bbox_polygon`: bbox `[lon_min, lat_min, lon_max,
  lat_max]` a partir de `coords` + `Width`.
- `params.py` — define `INDICES`, un diccionario con la configuración de cada
  índice soportado (`CODE_NDCI`, `CODE_NDTI`): las bandas Sentinel-2 que requiere
  y la fórmula para calcularlo a partir de ellas.
- `pre_processing.py` — `compute_index_series(coords, width, resolution, code)`:
  busca escenas Sentinel-2 (`DATETIME_RANGE`, `MAX_CLOUD_COVER`), apila las bandas
  requeridas por `code` (según `INDICES`) más `scl` con `stackstac`, enmascara
  píxeles que no son agua (`SCL == AGUA`) y calcula la mediana del índice por
  escena. Devuelve `[(fecha, valor), ...]`, descartando escenas sin píxeles de
  agua válidos.
- `load_locations.py` — crea un documento por punto en la colección MongoDB
  `sentinel_locations` (geometría = bbox del punto), vía `bulk_write`/upsert.
- `load_mediciones.py` — `load(code)`: para cada punto, busca su `location_id`
  en `sentinel_locations`, calcula la serie del índice `code` y la inserta en
  PostgreSQL (`sentinel_params`), una fila por escena (`granularidad = 'DIA'`,
  `fecha_inicio = fecha_fin = fecha de la escena`).

## Tareas del pipeline

- `sentinel.load_locations` — carga `sentinel_locations`.
- `sentinel.load_mediciones_ndci` — carga NDCI (`code = "NDCI"`).
- `sentinel.load_mediciones_turbidez` — carga NDTI (`code = "NDTI"`).

## Storage

| Dato | Destino |
|---|---|
| Ubicación / bbox por punto | MongoDB, colección `sentinel_locations` |
| Series NDCI / NDTI | PostgreSQL, tabla `sentinel_params` (columna `code`) |

Deduplicación determinística vía `create_id` (MD5) sobre todos los campos de cada fila.
