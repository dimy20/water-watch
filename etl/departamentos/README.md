# ETL - Departamentos de Uruguay

Carga 19 deparatamentos de Uruguay en MongoDb, con
sus geometrias geograficas.

Origen: <>

Es necesario para poder hacer consultas como:
Como evoluciona X parametro ente 2020 y 2025 en Maldonado?


## Fuente de datos

`data/departamentos.geojson` — GeoJSON con los límites administrativos de Uruguay.

## Problema con las geometrías originales

Para que todo sea compatible con mongo, necesitamos que cualquier geometria este en `Polygon`, `MultiPolygon` o 
`Point`.

El script `scripts/test_departamentos_geometry.py` es un script
de diagnostico que utilizamos para detectar que geometrias
originales tienen algun problema.

El dataset original de departamentos esta en `MultiLineString`.

Esto es un problema porque MongoDB requiere polígonos cerrados para hacer consultas espaciales con `$geoWithin`.

En el pre proccessing se utiliza `_fix_geometry()` para convertir a un tipo compatible de geometria.



1. Intenta reconstruir polígonos a partir de los segmentos con `polygonize`
2. Si hay pequeñas brechas entre segmentos (algunos departamentos las tienen), aplica `snap` con tolerancias progresivas para cerrarlas y reintenta

3. Si lo anterior falla, se encuentra un convex hull para
esa geometria, un convex hull es el polygono convexo
mas chico que se ajusta al polygono original, se pierde un poco
de precision.


## Cómo ejecutar

[COMPLETAR]

## Colección en MongoDB

**`departamentos`**

| Campo      | Tipo            | Descripción                        |
|------------|-----------------|------------------------------------|
| `_id`      | UUID            | ID único generado del nombre+código |
| `nombre`   | string          | Nombre del departamento            |
| `codigo`   | string          | Código administrativo              |
| `geometry` | GeoJSON Polygon | Límite geográfico del departamento |