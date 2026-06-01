# ETL - Estaciones INUMET

Carga las estaciones meteorológicas de INUMET en MongoDB. Es prerequisito de `etl/inumet`.

## Fuente de datos

`data/estaciones_inumet.json` — lista de estaciones con nombre, latitud y longitud.

## Estrategia anti-duplicación

`_id` = `MD5(nombre | lat | lon)` — upsert idempotente, correr dos veces no duplica estaciones.

## Colección en MongoDB

**`estaciones`**

| Campo | Tipo | Descripción |
|---|---|---|
| `_id` | UUID | MD5 de nombre + lat + lon |
| `nombre` | string | Nombre de la estación |
| `location` | GeoJSON Point | Coordenadas de la estación |

Se crea un indice 2dsphere para búsquedas geoespaciales (ej: estaciones dentro de un departamento):

`db.estaciones.createIndex({ location: "2dsphere" })`
