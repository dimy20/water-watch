# ETL - Erosion

Dos sub-módulos independientes que cargan datos de erosión en MongoDB (`areas`) y PostgreSQL.

Ambos usan `etl/areas` para persistir geometrías geográficas antes de insertar los datos de erosión.

## cuencas

Fuente: `data/erosion_de_99_cuencas_WGS84.geojsonl.json`

El dataset tiene cuencas con nombres nulos o duplicados. Los nulos se reemplazan por `AREA_A`, `AREA_B`, etc. y los duplicados se les agrega sufijo `_1`, `_2`, etc. Esto es necesario porque el `_id` del área se genera a partir del nombre — nombres duplicados o nulos colisionarían en MongoDB.

Colección MongoDB: `areas` (con nombre)

Tabla PostgreSQL: `erosion_cuenca`

| Campo | Tipo | Descripción |
|---|---|---|
| `erosion_id` | UUID | MD5 de area_id + ponderacion + cluster |
| `area_id` | UUID | FK al área en MongoDB |
| `ponderacion_erosion` | float | Ponderación de erosión de la cuenca |
| `cluster` | int | Cluster al que pertenece la cuenca |

## suelos

Fuente: `data/Erodabilidad_de_suelos_(geojson_wgs84).geojson`

Se descartan filas con `Factor_K` nulo. Las áreas de suelos no tienen nombre y se guardan como `SIN_NOMBRE` en MongoDB.

Colección MongoDB: `areas` (sin nombre)

Tabla PostgreSQL: `erosion_suelos`

| Campo | Tipo | Descripción |
|---|---|---|
| `erosion_id` | UUID | MD5 de area_id + grupo_coneat + perfil_modal + factor_k + taxonomia |
| `area_id` | UUID | FK al área en MongoDB |
| `grupo_coneat` | string | Grupo CONEAT del suelo |
| `perfil_modal` | string | Perfil modal del suelo |
| `factor_k` | float | Factor K de erodabilidad |
| `taxonomia` | string | Taxonomía del suelo |

## Estrategia anti-duplicación

`erosion_id` = MD5 determinístico de los campos clave, upsert con `ON CONFLICT DO NOTHING`.
