# ETL - Reclamos OSE

Carga reclamos comerciales de OSE en PostgreSQL, agrupados por departamento.

## Fuente de datos

`data/reclamos/solicitudes_y_reclamos-comerciales_<año>.csv` — un CSV por año (2019–2024), separador `;`, encoding latin1.

## Columnas descartadas

`via_comunicacion`, `fecha_resuelto`, `estado_resuelto`, `fecha_foto` y las variantes rotas de `año` no se usan. `id_reclamo_comercial_m` se usa solo para la deduplicación (no se persiste).

## Pre-processing

**Selección de columnas:** Se retienen explícitamente solo las 5 columnas necesarias para descartar variantes rotas de `año` y columnas irrelevantes.

**Filtro de año:** Se descartan registros con `fecha_inicio < 2015-01-01`.

**Filtro de departamento:** Se descartan filas con `departamento == 'SIN DATOS'` (854 filas del total).

**Normalización de tipo:** `tipo_reclamo_comercial` se mapea al ENUM `reclamo_ose_tipo` mediante `RECLAMOS_MAP` en `pre_processing.py`. El mapa cubre variantes de encoding (texto correcto y variante mal decodificada) y agrupa subtipos en la categoría correspondiente (ej. `Alto Consumo (Social)` → `ALTO_CONSUMO`). Filas cuyo tipo no esté en el mapa se descartan.

**Fechas:** `fecha_inicio` = `fecha_ingreso` parseado. `fecha_fin` = `fecha_inicio + 1 día`.

## Pre-requisito: colección `departamentos` en MongoDB

El loader resuelve el nombre del departamento a UUID consultando la colección `departamentos`. Los nombres se normalizan (minúsculas, sin tildes) antes del lookup.

Correr primero: `etl/departamentos`.

## Estrategia anti-duplicación

`reclamo_id` = `MD5(departamento_id | tipo_reclamo | region | fecha_inicio | fecha_fin | id_reclamo_comercial_m)` → `ON CONFLICT DO NOTHING`.

## Tabla en PostgreSQL

**`ReclamosOSE`**

| Campo | Tipo | Descripción |
|---|---|---|
| `reclamo_id` | UUID | MD5 de los campos del registro |
| `departamento_id` | UUID | FK al departamento en MongoDB |
| `tipo_reclamo` | `reclamo_ose_tipo` (ENUM) | Tipo de reclamo normalizado |
| `region` | varchar(100) | Región de Uruguay |
| `fecha_inicio` | timestamp | Fecha en que se ingresó el reclamo |
| `fecha_fin` | timestamp | `fecha_inicio + 1 día` |

### Valores del ENUM `reclamo_ose_tipo`

`ALTO_CONSUMO`, `DATOS_ERRONEOS_CONTRATO`, `DENUNCIA_NOTIFICACION_FACTURAS`, `DENUNCIA_NOTIFICACION_FACTURA_MAIL`, `ERROR_LECTURA`, `ERROR_TARIFA`, `ERROR_ESTIMACION`, `OTROS_AJUSTES_FACTURACION`, `RETRASO_CONEXION_NUEVA`, `QUEJAS_SUGERENCIAS`, `VARIOS`, `WS_GENERACION_AVISOS`
