# ETL - INUMET

Carga datos meteorológicos horarios de estaciones de INUMET en PostgreSQL.

## Parámetros soportados

| Tipo | Archivo fuente | Code |
|---|---|---|
| `precipitacion` | `inumet_precipitacion_acumulada_horaria.csv` | `PRECIP_HORARIA` |
| `humedad_relativa` | `inumet_humedad_relativa.csv` | `HUM_RELATIVA` |

El loader es genérico: `load(tipo)` maneja ambos parámetros a través de `CONFIG_BY_TIPO`.

## Pre-requisito: colección `estaciones` en MongoDB

**Este ETL no funciona si `estaciones` no está cargada.** Antes de insertar, el loader resuelve nombre de estación a  UUID consultando esa colección. Si una estación no existe, la fila se omite.

Correr primero: `etl/estaciones`.

## Estrategia anti-duplicación

El `param_id` se genera como hash `MD5(location_id | fecha | code | granularidad)`. Esto permite reinsertar el mismo CSV sin duplicar filas (`ON CONFLICT DO NOTHING`).

## Tabla en PostgreSQL

**`ParamInumet`**

| Campo | Tipo | Descripción |
|---|---|---|
| `param_id` | UUID | MD5 de location_id + fecha + code + granularidad |
| `location_id` | UUID | FK a la estación en MongoDB |
| `fecha_inicio` | timestamp | Inicio del intervalo horario |
| `fecha_fin` | timestamp | `fecha_inicio + 1 hora` |
| `value` | float | Valor del parámetro |
| `code` | `codigo_inumet` (ENUM) | `PRECIP_HORARIA` o `HUM_RELATIVA` |
| `granularidad` | `granularidad_tipo` (ENUM) | Siempre `HORA` para INUMET |
