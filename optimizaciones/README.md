# Optimizaciones de consultas PostgreSQL

Este documento identifica criterios de optimizacion para las consultas usadas por el dashboard en `streamlit/queries`.

El foco esta en PostgreSQL. Las consultas revisadas filtran principalmente por departamento, estacion, punto de grilla, codigo/tipo de medicion y `fecha_inicio`. Por eso los indices propuestos son compuestos: combinan las columnas que reducen primero el conjunto de datos y luego la columna temporal usada para acotar el periodo.

## Criterios detectados

| Criterio filtrado | Tabla(s) | Donde se usa | Indice propuesto |
| --- | --- | --- | --- |
| `departamento_id` + `fecha_inicio` | `reclamosose` | `streamlit/queries/reclamos.py`: reclamos por departamento y serie trimestral | `idx_reclamosose_depto_fecha` |
| `departamento_id` + `code` + `fecha_inicio` + `value_cat` | `oseparam` | `streamlit/queries/ose.py`: evolucion de calidad por departamento, parametro y periodo | `idx_oseparam_depto_code_fecha_valuecat` |
| `code` + `fecha_inicio` + `departamento_id` + `value_cat` | `oseparam` | `streamlit/queries/reclamos.py` y `streamlit/queries/riesgo.py`: calculos nacionales de contaminacion por `COLIFORMES TOTALES` | `idx_oseparam_code_fecha_depto_valuecat` |
| `location_id` + `code` + `fecha_inicio` | `gemsparams` | `streamlit/queries/gems.py`, `streamlit/queries/riesgo.py`: mediciones GEMS por estacion, parametro y periodo | `idx_gemsparams_location_code_fecha` |
| `code` + `location_id` | `gemsparams` | Sin uso actual desde que `precipitacion_chla.py` fue reemplazado por `precipitacion_ndci.py` (sentinel_params) | `idx_gemsparams_code_location` |
| `punto_id` + `type` + `fecha_inicio` | `puntomedicion` | `streamlit/queries/grillas.py` y `streamlit/queries/precipitacion_ndci.py`: mediciones de grilla por punto, tipo y periodo | `idx_puntomedicion_punto_type_fecha` |
| `location_id` + `fecha_inicio` | `registrotempprec` | `streamlit/queries/riesgo.py`: precipitacion por estacion y periodo | `idx_registrotempprec_location_fecha` |
| `location_id` + `fecha_inicio` | `paraminumet` | Datos meteorologicos por estacion y periodo, si se consultan desde el dashboard o analisis posteriores | `idx_paraminumet_location_fecha` |
| `code` + `location_id` + `fecha_inicio` | `sentinel_params` | `streamlit/queries/precipitacion_ndci.py`: puntos con NDCI (`code = 'NDCI'`) y promedio mensual por punto y periodo | `idx_sentinelparams_code_location_fecha` |

## SQL propuesto

```sql
CREATE INDEX IF NOT EXISTS idx_reclamosose_depto_fecha
ON reclamosose (departamento_id, fecha_inicio);

CREATE INDEX IF NOT EXISTS idx_oseparam_depto_code_fecha_valuecat
ON oseparam (departamento_id, code, fecha_inicio, value_cat);

CREATE INDEX IF NOT EXISTS idx_oseparam_code_fecha_depto_valuecat
ON oseparam (code, fecha_inicio, departamento_id, value_cat);

CREATE INDEX IF NOT EXISTS idx_gemsparams_location_code_fecha
ON gemsparams (location_id, code, fecha_inicio);

CREATE INDEX IF NOT EXISTS idx_gemsparams_code_location
ON gemsparams (code, location_id);

CREATE INDEX IF NOT EXISTS idx_puntomedicion_punto_type_fecha
ON puntomedicion (punto_id, type, fecha_inicio);

CREATE INDEX IF NOT EXISTS idx_registrotempprec_location_fecha
ON registrotempprec (location_id, fecha_inicio);

CREATE INDEX IF NOT EXISTS idx_paraminumet_location_fecha
ON paraminumet (location_id, fecha_inicio);

CREATE INDEX IF NOT EXISTS idx_sentinelparams_code_location_fecha
ON sentinel_params (code, location_id, fecha_inicio);
```

## Por que estos indices

### `reclamosose`

Las consultas de reclamos filtran por periodo y, en la vista trimestral, tambien por `departamento_id`.

```sql
WHERE departamento_id = %s
  AND EXTRACT(YEAR FROM fecha_inicio) BETWEEN %s AND %s
```

El indice `(departamento_id, fecha_inicio)` permite ubicar rapidamente los reclamos de un departamento y luego recorrer solo el rango temporal relevante.

### `oseparam`

`oseparam` se consulta de dos formas principales:

1. Por departamento, codigo de parametro y periodo.
2. A nivel nacional, por codigo (`COLIFORMES TOTALES`) y periodo, agrupando luego por departamento.

Por eso se proponen dos indices con distinto orden:

```sql
ON oseparam (departamento_id, code, fecha_inicio, value_cat);
ON oseparam (code, fecha_inicio, departamento_id, value_cat);
```

El primero favorece consultas de evolucion por departamento. El segundo favorece calculos nacionales donde no hay filtro inicial por departamento.

### `gemsparams`

Las consultas GEMS filtran por estaciones (`location_id`), parametro (`code`) y periodo.

```sql
WHERE location_id = ANY(%s)
  AND code = %s
  AND EXTRACT(YEAR FROM fecha_inicio) BETWEEN %s AND %s
```

El indice `(location_id, code, fecha_inicio)` reduce primero por estacion, despues por parametro y finalmente por fecha.

### `puntomedicion`

Las consultas de grilla filtran por punto, tipo de medicion (`IBH`, `PAD`, `ANR`) y periodo.

```sql
WHERE punto_id = ANY(%s)
  AND type = %s
  AND EXTRACT(YEAR FROM fecha_inicio) BETWEEN %s AND %s
```

El indice `(punto_id, type, fecha_inicio)` acompana directamente ese patron.

### `registrotempprec`

La precipitacion se consulta por estacion y periodo:

```sql
WHERE location_id = ANY(%s)
  AND EXTRACT(YEAR FROM fecha_inicio) BETWEEN %s AND %s
```

El indice `(location_id, fecha_inicio)` evita recorrer toda la tabla para calcular promedios por estacion.

### `paraminumet`

Aunque no aparece con tanta fuerza en las consultas actuales del dashboard, `paraminumet` sigue el mismo criterio de datos meteorologicos por estacion y fecha. Si se usa para analisis por estacion/periodo, el indice `(location_id, fecha_inicio)` es el mas natural.

### `sentinel_params`

`precipitacion_ndci.py` consulta `sentinel_params` de dos formas:

```sql
SELECT DISTINCT location_id
FROM sentinel_params
WHERE code = 'NDCI'
```

```sql
WHERE code = 'NDCI'
  AND location_id = %s
  AND EXTRACT(YEAR FROM fecha_inicio) BETWEEN %s AND %s
```

El indice `(code, location_id, fecha_inicio)` cubre ambos patrones: primero filtra por `code`, y de ahi resuelve tanto el conjunto de `location_id` distintos como el promedio mensual por punto y periodo.

## Nota sobre `fecha_inicio`

Las consultas actuales usan `fecha_inicio` para filtrar el periodo. Por eso estos indices no incluyen `fecha_fin`.

Para que PostgreSQL aproveche mejor los indices de fecha, conviene reemplazar condiciones con `EXTRACT(YEAR FROM fecha_inicio)` por rangos directos:

```sql
WHERE fecha_inicio >= %s
  AND fecha_inicio < %s
```

Por ejemplo, para consultar 2020 a 2024:

```sql
WHERE fecha_inicio >= '2020-01-01'
  AND fecha_inicio < '2025-01-01'
```

Esto permite usar el orden del indice sobre `fecha_inicio` de forma mas eficiente.
