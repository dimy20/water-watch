# Water Watch

Sistema de monitoreo de calidad y recursos hídricos de Uruguay. Integra datos de múltiples fuentes (INUMET, OSE, GEMS, grillas geoespaciales) en una base dual MongoDB + PostgreSQL, y los expone en un dashboard Streamlit.

## Arquitectura

```
fuentes de datos
      │
      ▼
   etl/          ← pipeline de carga (Python)
      │
      ├── MongoDB     ← geometrías y ubicaciones (departamentos, estaciones, áreas, puntos de grilla)
      └── PostgreSQL  ← series temporales y mediciones
                            │
                            ▼
                      streamlit/    ← dashboard de visualización
```

## Stack

| Componente | Tecnología |
|---|---|
| ETL | Python, pandas, geopandas |
| Base geoespacial | MongoDB (colecciones con índice 2dsphere) |
| Base de series temporales | PostgreSQL |
| Migraciones | yoyo-migrations |
| Dashboard | Streamlit + Plotly |

## Estructura del repositorio

```
etl/              pipeline de carga por módulo/fuente
migrations/       migraciones de esquema PostgreSQL (yoyo)
streamlit/        aplicación Streamlit
scripts/          scripts de diagnóstico y exploración
data/             datos fuente (no versionados)
local/            cluster MongoDB sharded para desarrollo local (Docker Compose)
users/            usuarios y permisos de PostgreSQL y MongoDB
db.py             conexiones a MongoDB y PostgreSQL
main.py           entry point del ETL
```

## Configuración

Las credenciales se leen de `.env.local`. Variables necesarias:

```
ENTORNO=                  # "utec" u otro entorno
ETL_DATABASE_URL=         # PostgreSQL para el ETL
ETL_MONGO_URL=            # MongoDB para el ETL (entorno utec)
ETL_MONGO_SERVER_URL=     # MongoDB para el ETL (otros entornos)
STREAMLIT_DATABASE_URL=   # PostgreSQL para el dashboard
STREAMLIT_MONGO_URL=      # MongoDB para el dashboard
S3_BUCKET=                # Bucket S3 para backups
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_DEFAULT_REGION=
```

## Migraciones

```bash
bash init_migrations.sh
```

Las migraciones están en `migrations/` y se aplican con yoyo (`yoyo.ini`).

## ETL

Ver [etl/README.md](etl/README.md) para la lista de módulos y el orden de carga.

El orden de ejecución respeta dependencias definidas en [`etl/etl_graph.json`](etl/etl_graph.json). Ejemplo básico:

```python
# main.py
from etl.estaciones.loading import load as load_estaciones
from etl.inumet.loading import load as load_inumet

load_estaciones()
load_inumet("precipitacion")
```

#### Logging

El pipeline usa el módulo estándar `logging`. `init_logger.py` configura el root logger con dos handlers: consola y archivo `water_watch.log` (nivel INFO, formato con timestamp). Cada módulo ETL tiene su propio child logger (`etl/<modulo>/logger.py`) y loggea al final de cada etapa de pre-processing cuántos registros entraron, cuántos se descartaron y por qué.

## Dashboard

```bash
streamlit run streamlit/app.py
```

---

## Estado por etapa

Esta sección registra el avance del proyecto por etapa. Se actualiza con cada cambio relevante.

### DDL

Esquema PostgreSQL gestionado con yoyo-migrations (`migrations/`).

##### ENUMs

| Tipo | Valores |
|---|---|
| `codigo_inumet` | `HUM_RELATIVA`, `PRECIP_HORARIA` |
| `granularidad_tipo` | `HORA`, `DIA`, `SEMANA`, `MES`, `TRIMESTRE`, `ANIO`, `PERIODO` |
| `tipo_medicion` | `IBH`, `PAD`, `ANR` |
| `reclamo_ose_tipo` | `ALTO_CONSUMO`, `DATOS_ERRONEOS_CONTRATO`, `DENUNCIA_NOTIFICACION_FACTURAS`, `DENUNCIA_NOTIFICACION_FACTURA_MAIL`, `ERROR_LECTURA`, `ERROR_TARIFA`, `ERROR_ESTIMACION`, `OTROS_AJUSTES_FACTURACION`, `RETRASO_CONEXION_NUEVA`, `QUEJAS_SUGERENCIAS`, `VARIOS`, `WS_GENERACION_AVISOS` |

##### Tablas

**`erosion_cuenca`**

| Columna | Tipo | Notas |
|---|---|---|
| `erosion_id` | UUID | PK |
| `area_id` | UUID | NOT NULL, UNIQUE |
| `ponderacion_erosion` | DOUBLE PRECISION | NOT NULL |
| `cluster` | INTEGER | NOT NULL |

**`erosion_suelos`**

| Columna | Tipo | Notas |
|---|---|---|
| `erosion_id` | UUID | PK |
| `area_id` | UUID | NOT NULL |
| `grupo_coneat` | VARCHAR | NOT NULL |
| `perfil_modal` | VARCHAR | NOT NULL |
| `factor_k` | FLOAT | NOT NULL |
| `taxonomia` | VARCHAR | NOT NULL |

**`paraminumet`**

| Columna | Tipo | Notas |
|---|---|---|
| `param_id` | UUID | PK |
| `location_id` | UUID | NOT NULL |
| `fecha_inicio` | TIMESTAMP | NOT NULL |
| `fecha_fin` | TIMESTAMP | NOT NULL |
| `value` | DOUBLE PRECISION | NOT NULL |
| `code` | `codigo_inumet` | NOT NULL |
| `granularidad` | `granularidad_tipo` | NOT NULL |

**`puntomedicion`**

| Columna | Tipo | Notas |
|---|---|---|
| `medicion_id` | UUID | PK |
| `punto_id` | UUID | NOT NULL |
| `value` | FLOAT | NOT NULL |
| `type` | `tipo_medicion` | NOT NULL |
| `fecha_inicio` | DATE | NOT NULL |
| `fecha_fin` | DATE | NOT NULL |
| `granularidad` | `granularidad_tipo` | NOT NULL |

**`gemsparams`**

| Columna | Tipo | Notas |
|---|---|---|
| `gems_param_id` | UUID | PK |
| `location_id` | UUID | NOT NULL |
| `code` | VARCHAR(50) | NOT NULL |
| `fecha_inicio` | TIMESTAMP | NOT NULL |
| `fecha_fin` | TIMESTAMP | NOT NULL, CHECK `fecha_inicio <= fecha_fin` |
| `value` | FLOAT | NULL |
| `value_cat` | VARCHAR(50) | NULL |
| `unit` | VARCHAR(30) | NULL |
| `data_quality` | VARCHAR(30) | NULL |
| `depth` | FLOAT | NULL |
| `granularidad` | `granularidad_tipo` | NOT NULL |

**`oseparam`**

| Columna | Tipo | Notas |
|---|---|---|
| `ose_param_id` | UUID | PK |
| `departamento_id` | UUID | NOT NULL |
| `code` | VARCHAR(50) | NOT NULL |
| `fecha_inicio` | TIMESTAMP | NOT NULL |
| `fecha_fin` | TIMESTAMP | NOT NULL |
| `value` | FLOAT | NULL |
| `value_cat` | VARCHAR(50) | NULL |
| `granularidad` | `granularidad_tipo` | NOT NULL |

**`registrotempprec`**

| Columna | Tipo | Notas |
|---|---|---|
| `registro_id` | UUID | PK |
| `location_id` | UUID | NOT NULL |
| `fecha_inicio` | TIMESTAMP | NOT NULL |
| `fecha_fin` | TIMESTAMP | NOT NULL, CHECK `fecha_inicio <= fecha_fin` |
| `temperatura_maxima` | FLOAT | NOT NULL |
| `temperatura_minima` | FLOAT | NOT NULL |
| `pluviometro` | FLOAT | NOT NULL |
| `granularidad` | `granularidad_tipo` | NOT NULL |

**`reclamosose`**

| Columna | Tipo | Notas |
|---|---|---|
| `reclamo_id` | UUID | PK |
| `departamento_id` | UUID | NOT NULL |
| `tipo_reclamo` | `reclamo_ose_tipo` | NOT NULL |
| `region` | VARCHAR(100) | NOT NULL |
| `fecha_inicio` | TIMESTAMP | NOT NULL |
| `fecha_fin` | TIMESTAMP | NOT NULL, CHECK `fecha_fin >= fecha_inicio` |

**`sentinel_params`**

| Columna | Tipo | Notas |
|---|---|---|
| `sentinel_param_id` | UUID | PK |
| `location_id` | UUID | NOT NULL — referencia a `sentinel_locations` (MongoDB) |
| `code` | VARCHAR(50) | NOT NULL — `'NDCI'` |
| `fecha_inicio` | DATE | NOT NULL |
| `fecha_fin` | DATE | NOT NULL, CHECK `fecha_inicio <= fecha_fin` |
| `value` | FLOAT | NOT NULL |
| `granularidad` | `granularidad_tipo` | NOT NULL |

**`etl_file_state`**

| Columna | Tipo | Notas |
|---|---|---|
| `resource_id` | VARCHAR | PK — id del resource en CKAN |
| `package` | VARCHAR | NOT NULL — dataset CKAN (ej. `inia-pad-por-grilla`) |
| `modulo` | VARCHAR | NOT NULL — módulo ETL afectado, según `etl/etl_graph.json` |
| `hash` | VARCHAR | NOT NULL — hash MD5 reportado por CKAN para el resource |
| `archivo_local` | VARCHAR | NOT NULL — ruta relativa a `data/` |
| `last_synced` | TIMESTAMP | NOT NULL |

---

### ETL modular

Pipeline de carga por fuente. Cada módulo es independiente y tiene dedup determinístico por MD5.

| Módulo | Destino | Estado |
|---|---|---|
| `departamentos` | MongoDB | Completo |
| `estaciones` (INUMET) | MongoDB | Completo |
| `areas` | MongoDB | Completo |
| `grillas` (IBH, PAD, ANR) | MongoDB + PostgreSQL | Completo |
| `inumet` (precipitación, humedad) | PostgreSQL | Completo |
| `precipitaciones` (5 estaciones) | MongoDB + PostgreSQL | Completo |
| `gems` (GEMStat, Uruguay 2015+) | MongoDB + PostgreSQL | Completo |
| `erosion` (cuencas, suelos) | MongoDB + PostgreSQL | Completo |
| `bacteriologia_ose` | PostgreSQL | Completo |
| `reclamos` | PostgreSQL | Completo |
| `sentinel` (NDCI Sentinel-2) | MongoDB + PostgreSQL | Completo |

### Scripts de diagnóstico

| Script | Descripción |
|---|---|
| `scripts/count_records.py` | Cuenta registros en todas las tablas PostgreSQL y colecciones MongoDB, e imprime el total por base. |
| `scripts/backup.py` | Backups de PostgreSQL, MongoDB y `data/` hacia S3. Ver sección Seguridad → Backups. |

```bash
python scripts/count_records.py
```

### CDC

Sincronización de archivos fuente desde el catálogo de datos abiertos (`catalogodatos.gub.uy`, API CKAN). La carga inicial (2015–2025) ya está en `data/`; el CDC solo trackea recursos de `MIN_YEAR` (2026) en adelante, que son los que se siguen actualizando.

| Componente | Descripción |
|---|---|
| `etl/ckan_client.py` | Wrapper de la API CKAN: `package_search(package)` y `download_resource(resource)`. |
| `etl/ckan_sources.py` | `SOURCES`: mapeo de cada dataset CKAN al módulo ETL afectado y a un resolver que deriva la ruta destino en `data/` a partir del resource (filtrando por formato CSV y `MIN_YEAR`). |
| `etl_file_state` | Tabla PostgreSQL con el último hash sincronizado por resource (ver DDL). |
| `scripts/sync_data.py` | Recorre `SOURCES`, compara el hash de cada resource contra `etl_file_state` y descarga a `data/` solo los archivos nuevos o modificados. |

```bash
python scripts/sync_data.py
```

El script **no** corre el pipeline ETL — solo actualiza `data/` y `etl_file_state`. Correr `python main.py` después es seguro e idempotente gracias al dedup determinístico (`ON CONFLICT DO NOTHING`) de cada loader.

Esto es independiente del backup de `data/` a S3 (`scripts/backup.py data` / `pull-data`): CKAN → `data/` es la sincronización con la fuente; `data/` ↔ S3 es la distribución entre entornos del equipo.

### Seguridad

#### Usuarios

Cinco usuarios con permisos mínimos según su función: `streamlit_user` (read only), `etl_user` (read + write), `mig_user` (solo DDL), `enzo_admin` y `belen_admin` (administradores). Ver comandos de creación en [`users/README.md`](users/README.md).

#### Backups

Script `scripts/backup.py`. Genera dumps de ambas bases y empaqueta los datos fuente; todo se sube a S3.

Tres tipos: `postgres` (pg_dump), `mongo` (mongodump), `data` (zip de `data/`). Se pueden correr individualmente o los tres juntos.

```bash
python scripts/backup.py              # los tres
python scripts/backup.py postgres
python scripts/backup.py mongo
python scripts/backup.py data
python scripts/backup.py pull-data    # descarga y extrae el zip más reciente de data/
```

`pull-data` descarga el zip más reciente del prefijo `data/` en S3 y lo extrae en el directorio `data/` local.

Requiere `S3_BUCKET`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` y `AWS_DEFAULT_REGION` en `.env.local`.

### Streamlit

```bash
streamlit run streamlit/app.py
```

#### Páginas

| Archivo | Descripción |
|---|---|
| `app.py` | Entry point. Configura la app y registra las páginas. |
| `evolucion.py` | Dashboard principal — 7 tabs por departamento y rango de años. |
| `mapa.py` | Mapa coroplético nacional de contaminación OSE. Click en un departamento navega a `evolucion.py`. Actualmente no está en la navegación de `app.py`. |

#### Filtros globales (sidebar)

Departamento · Año de inicio · Año de fin (rango 2017–2025).

#### Tabs del dashboard (`evolucion.py`)

| Tab | Fuentes | Visualización |
|---|---|---|
| **Bacteriología** | OSE + GEMS | Evolución trimestral de % presencia (coliformes totales, E. coli, coliformes fecales). Métricas de total de muestras y tendencia del período. |
| **Fisicoquímica (GEMS)** | GEMS | Evolución mensual con banda min–max para 14 parámetros (pH, O₂, conductancia, BOD, COD, nutrientes, turbidez, etc.). |
| **Resumen nacional** | OSE + GEMS | Barras horizontales con % contaminación y valor promedio por parámetro bacteriológico para todos los departamentos. |
| **Estado hídrico del suelo** | Grillas (IBH, PAD, ANR) | Mapa coroplético + barras por departamento. Promedio de puntos de grilla dentro de cada departamento. |
| **Indicador de Riesgo** | OSE + GEMS + Precipitaciones + IBH | Score 0–3 por departamento. Combina tres condiciones: contaminación bacteriológica (OSE + GEMS), precipitación y estado hídrico del suelo. Mapa coroplético con tooltip por condición. |
| **Reclamos vs Calidad** | ReclamosOSE + OSEParam | Scatter por departamento (reclamos comerciales vs % contaminación), evolución trimestral dual-eje (barras de reclamos + línea de % contaminación), tabla resumen. |
| **Precipitación vs NDCI** | SentinelParams (NDCI) + Grillas (PAD) | Selector de punto de monitoreo Sentinel-2 con mediciones de NDCI y de lag (1–3 meses). Para cada punto se busca el punto de grilla PAD más cercano al centroide de su geometría (`$nearSphere`) y se compara su precipitación mensual (desplazada por el lag) contra el NDCI mensual, en gráfico dual-eje y tabla. |

#### Metodología del indicador de riesgo

Tres condiciones binarias, cada una activa si supera/cae bajo el percentil 66/33 del período seleccionado:

- **Contaminación**: promedio normalizado de OSE (% presencia coliformes) + GEMS (TOTCOLI). Activa si > p66.
- **Precipitación**: pluviometría media diaria (estaciones INIA, 5 departamentos). Activa si > p66.
- **Humedad del suelo (IBH)**: grillas INIA-GRAS, cobertura nacional. Activa si < p33.

Score = suma de condiciones activas (0 = sin riesgo, 3 = riesgo elevado).

#### Capa de queries (`streamlit/queries/`)

| Archivo | Responsabilidad |
|---|---|
| `departamentos.py` | GeoJSON simplificado, lista de deptos con datos, % presencia OSE por depto |
| `ose.py` | Evolución trimestral de calidad bacteriológica OSE |
| `gems.py` | Estaciones por departamento (`$geoWithin`), evolución mensual GEMS, promedio por depto |
| `grillas.py` | Estado hídrico por departamento (puntos de grilla `$geoWithin`) |
| `riesgo.py` | Indicador de riesgo combinado |
| `reclamos.py` | Reclamos por departamento, serie trimestral, correlación reclamos–calidad |
| `precipitacion_ndci.py` | Puntos Sentinel con NDCI, punto de grilla PAD más cercano al centroide (`$nearSphere`), cruce mensual PAD vs NDCI con lag |

#### Caché

| Dato | TTL |
|---|---|
| Conexiones a BD (`cache_resource`) | Toda la sesión |
| Departamentos, GeoJSON, estaciones por depto | 3600 s |
| Series temporales (calidad, grillas, riesgo) | 600 s |

### Testing

Estructura de tests con `pytest`, espejando la estructura de `etl/` dentro de `tests/`.

```bash
pytest
```

### Docker

#### Cluster MongoDB local

Para desarrollo local, `local/docker-compose-cluster.yml` levanta un cluster MongoDB sharded:
- 3 config servers (`configReplSet`)
- 2 shards con replica set de 3 nodos cada uno
- 1 router `mongos` expuesto en el puerto `32888`

Ver instrucciones de inicialización en [`local/README.md`](local/README.md).

```bash
docker compose -f local/docker-compose-cluster.yml up -d
```

