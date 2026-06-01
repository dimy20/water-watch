# ETL - GEMS

Carga mediciones de calidad de agua de la base GEMStat (GEMS/Water) en PostgreSQL. Solo se cargan estaciones y mediciones de Uruguay, desde 2015 en adelante.

Tiene dos loaders que deben ejecutarse en orden:

1. `load_estaciones.py` — registra las estaciones uruguayas en MongoDB
2. `load_mediciones.py` — carga las mediciones. Omite filas cuya estación no esté en Mongo.

## Fuente de datos

`data/GFQA_v3/` — dataset GEMStat con:
- `GEMStat_station_metadata.csv` — metadata de estaciones (coordenadas, país)
- CSVs de mediciones separados por tipo de parámetro (`Optical.csv`, `Water.csv`, `Pigment.csv`, etc.)

## Tipos de medición

| Tipo | Descripción |
|---|---|
| `in_situ` | Parámetros definidos en `scripts/search_result.json` |
| `remote_sensing` | TURB, TSS, Chl-a, TRANS — definidos en `params.py` |

## Pre-processing

`fecha_inicio` se construye combinando `Sample Date` + `Sample Time`. Si no hay hora disponible, se usa solo la fecha. `fecha_fin` = `fecha_inicio + 1 día`. Granularidad siempre `DIA`.

El campo `unit` de pH viene como `---` en el dataset original — se reemplaza por `dimensionless` para no confundirlo con un error o nulo.

## Pre-requisito: colección `estaciones` en MongoDB

Las estaciones de GEMS se cargan en la misma colección `estaciones` que `etl/inumet` y `etl/precipitaciones`. `load_mediciones` resuelve el nombre de estación (`GEMS Station Number`, prefijo `URY`) a UUID antes de insertar.

Correr primero: `load_estaciones.py`.

## Estrategia anti-duplicación

`gems_param_id` = `MD5(location_id | code | fecha_inicio | fecha_fin | value | unit | data_quality | depth | granularidad)` → `ON CONFLICT DO NOTHING`.

## Colección en MongoDB

**`estaciones`** — compartida con `etl/inumet` y `etl/precipitaciones`.

| Campo | Tipo | Descripción |
|---|---|---|
| `_id` | UUID | MD5 de nombre + lat + lon |
| `nombre` | string | GEMS Station Number (ej: `URY000001`) |
| `location` | GeoJSON Point | Coordenadas de la estación |

## Tabla en PostgreSQL

**`GemsParams`**

| Campo | Tipo | Descripción |
|---|---|---|
| `gems_param_id` | UUID | MD5 de los campos de la medición |
| `location_id` | UUID | FK a la estación en MongoDB |
| `code` | varchar(50) | Código del parámetro medido |
| `fecha_inicio` | timestamp | Inicio del período |
| `fecha_fin` | timestamp | `fecha_inicio + 1 día` |
| `value` | float | Valor medido (puede ser nulo) |
| `value_cat` | varchar(50) | Categoría del valor (nullable) |
| `unit` | varchar(30) | Unidad de medida |
| `data_quality` | varchar(30) | Calidad del dato |
| `depth` | float | Profundidad de la muestra (nullable) |
| `granularidad` | `granularidad_tipo` (ENUM) | Siempre `DIA` |
