# ETL - Bacteriología OSE

Carga datos bacteriológicos de calidad de agua de OSE en PostgreSQL, agrupados por departamento y trimestre.

## Fuente de datos

`data/calidad_de_agua_bacteriologia_2017t1_2025t2 (1).csv` — registros bacteriológicos de OSE desde 2017 T1 hasta 2025 T2.

## Pre-processing

Los datos vienen con granularidad trimestral. El pre-processing convierte año + trimestre en `fecha_inicio` y `fecha_fin` (ej: T2 → 2024-04-01 / 2024-06-30).

Los valores son categóricos — no hay valor numérico. `value` se guarda como `None` y el resultado real queda en `value_cat`. Se descartan filas con `valor == "<1"` (por debajo del límite de detección).

## Pre-requisito: colección `departamentos` en MongoDB

El loader resuelve el nombre del departamento a UUID consultando la colección `departamentos`. Los nombres se normalizan (minúsculas, sin tildes) para evitar problemas de encoding entre el CSV y Mongo.

Correr primero: `etl/departamentos`.

## Estrategia anti-duplicación

`ose_param_id` = `MD5(departamento_id | code | fecha_inicio | fecha_fin | value_cat | granularidad | id_muestra_m)` → `ON CONFLICT DO NOTHING`.

El campo `id_muestra_m` se usa solo para la deduplicación, no se persiste en la tabla.

## Tabla en PostgreSQL

**`OSEParam`**

| Campo | Tipo | Descripción |
|---|---|---|
| `ose_param_id` | UUID | MD5 de los campos del registro |
| `departamento_id` | UUID | FK al departamento en MongoDB |
| `code` | varchar(50) | Código del parámetro bacteriológico |
| `fecha_inicio` | timestamp | Inicio del trimestre |
| `fecha_fin` | timestamp | Fin del trimestre |
| `value` | float | Siempre nulo — los datos son categóricos |
| `value_cat` | varchar(50) | Resultado del análisis (ej: "Satisfactorio") |
| `granularidad` | `granularidad_tipo` (ENUM) | Siempre `TRIMESTRE` |
