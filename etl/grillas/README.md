# ETL - Grillas

Carga datos de grillas geoespaciales en MongoDB (`puntos_grilla`) y PostgreSQL (`PuntoMedicion`).

## Tipos soportados

| Tipo | Directorio fuente |
|---|---|
| `IBH` | `data/grillas/ibh/` |
| `PAD` | `data/grillas/pad/` |
| `ANR` | `data/grillas/anr/` |

El loader es genérico: `load(tipo)` itera todos los CSVs del directorio correspondiente.

## Formato de los CSVs y pre-processing

Los CSVs vienen en formato **wide**: cada columna representa un período de tiempo con el formato `yyyy_mmd` (año, mes de 2 dígitos, período).

Cada mes tiene 4 columnas:
- `d=1` → días 1–10
- `d=2` → días 11–20
- `d=3` → días 21–fin de mes
- `d=0` → promedio mensual: No no interesa como cambia el promedio, no lo usamos.

El pre-processing transforma de wide a long: una fila por punto geográfico x período.

## Estrategia anti-duplicación

Estrategia de de-duplicacion igual al resto de las fuentes:

- `punto_id` = `MD5(lat | lon)` upsert idempotente en `puntos_grilla`
- `medicion_id` = `MD5(punto_id | valor | tipo | fecha_inicio | fecha_fin | granularidad)` → `ON CONFLICT DO NOTHING` en `PuntoMedicion`

## Colección en MongoDB

**`puntos_grilla`**

| Campo | Tipo | Descripción |
|---|---|---|
| `_id` | UUID | MD5 de lat + lon |
| `location` | GeoJSON Point | Coordenadas del punto |

Se crea un indice: `db.puntos_grilla.createIndex({ location: "2dsphere" })`

## Tabla en PostgreSQL

**`PuntoMedicion`**

| Campo | Tipo | Descripción |
|---|---|---|
| `medicion_id` | UUID | MD5 de punto + valor + tipo + fechas + granularidad |
| `punto_id` | UUID | FK al punto en MongoDB |
| `value` | float | Valor del parámetro |
| `type` | `tipo_medicion` (ENUM) | `IBH`, `PAD` o `ANR` |
| `fecha_inicio` | date | Inicio del período |
| `fecha_fin` | date | Fin del período |
| `granularidad` | `granularidad_tipo` (ENUM) | Siempre `PERIODO` |