# ETL - Precipitaciones

Carga registros de temperatura y precipitación de 5 estaciones en PostgreSQL.

Tiene dos loaders que deben ejecutarse en orden:

1. `load_estaciones.py` — registra las estaciones en MongoDB
2. `load_registros.py` — carga los registros. Falla con error explícito si las estaciones no están cargadas.

## Fuente de datos

`data/precipitaciones/<nombre_estacion>/` — un directorio por estación con:
- `coords.txt` — coordenadas de la estación (lon, lat)
- CSVs con formato `ppt_tmax_tmin_*.csv` — registros de temperatura y pluviometría

Estaciones: `La Estanzuela`, `Las Brujas`, `SaltoGrande`, `Tacuarembo`, `Treinta y Tres`

## Pre-processing

Cada registro viene con una fecha diaria. El pre-processing la expande a un intervalo: `fecha_inicio` = 09:00 del día, `fecha_fin` = 08:59:59 del día siguiente. La granularidad es siempre `DIA`. Se descartan filas con nulos en temperatura o pluviometro.

## Pre-requisito: colección `estaciones` en MongoDB

Las estaciones de precipitaciones se cargan en la misma colección `estaciones` que `etl/inumet`. `load_registros` busca cada estación por nombre antes de insertar — si no la encuentra, lanza `RuntimeError`.

Correr primero: `load_estaciones.py`.

## Estrategia anti-duplicación

`registro_id` = `MD5(location_id | fecha_inicio | fecha_fin | temp_max | temp_min | pluviometro | granularidad)` → `ON CONFLICT DO NOTHING`.

## Colección en MongoDB

**`estaciones`** — compartida con `etl/inumet`.

| Campo | Tipo | Descripción |
|---|---|---|
| `_id` | UUID | MD5 de nombre + lat + lon |
| `nombre` | string | Nombre de la estación |
| `location` | GeoJSON Point | Coordenadas de la estación |

## Tabla en PostgreSQL

**`RegistroTempPrec`**

| Campo | Tipo | Descripción |
|---|---|---|
| `registro_id` | UUID | MD5 de los campos del registro |
| `location_id` | UUID | FK a la estación en MongoDB |
| `fecha_inicio` | timestamp | 09:00 del día del registro |
| `fecha_fin` | timestamp | 08:59:59 del día siguiente |
| `temperatura_maxima` | float | Temperatura máxima del día |
| `temperatura_minima` | float | Temperatura mínima del día |
| `pluviometro` | float | Precipitación acumulada |
| `granularidad` | `granularidad_tipo` (ENUM) | Siempre `DIA` |
