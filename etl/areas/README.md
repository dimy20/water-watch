# ETL - Areas

Módulo utilitario compartido. expone `crear_area_doc()`, normaliza geometrías geográficas para persistirlas en MongoDB.

## Por que ?

Varios ETLs necesitan guardar un área geográfica en Mongo antes de insertar sus datos en PostgreSQL. 


**Modulos que utilizan esto actualmente :**
- `etl/erosion/suelos` — áreas sin nombre
- `etl/erosion/cuencas` — áreas con nombre

## Estrategia anti-duplicación

El `_id` se genera como hash `MD5(geometry | nombre)`, un UUID determinístico. Esto permite hacer upsert idempotente: si el mismo área llega dos veces (desde distintos ETLs o reruns), no se duplica en la colección.

## Colección en MongoDB

**`areas`**

| Campo      | Tipo            | Descripción                              |
|------------|-----------------|------------------------------------------|
| `_id`      | UUID            | MD5 de la geometría y el nombre          |
| `nombre`   | string          | Nombre del área, o `SIN_NOMBRE` si no tiene |
| `geometry` | GeoJSON         | Geometría del área                       |
