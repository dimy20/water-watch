# ETL - Water Watch

Módulos de carga de datos hacia MongoDB y PostgreSQL.

## Módulos

| Módulo | Descripción |
|---|---|
| [departamentos](departamentos/README.md) | 19 departamentos de Uruguay con sus geometrías geográficas |
| [estaciones](estaciones/README.md) | Estaciones meteorológicas de INUMET |
| [areas](areas/README.md) | Módulo utilitario compartido para persistir geometrías geográficas en MongoDB |
| [grillas](grillas/README.md) | Datos de grillas geoespaciales (IBH, PAD, ANR) |
| [inumet](inumet/README.md) | Datos meteorológicos horarios de INUMET (precipitación, humedad relativa) |
| [precipitaciones](precipitaciones/README.md) | Registros de temperatura y precipitación de 5 estaciones |
| [gems](gems/README.md) | Mediciones de calidad de agua de la base GEMStat |
| [erosion](erosion/README.md) | Datos de erosión de suelos y cuencas |
| [bacteriologia_ose](bacteriologia_ose/README.md) | Datos bacteriológicos de calidad de agua de OSE |
| [sentinal](sentinal/README.md) | Por implementar |
| [reclamos](reclamos/README.md) | Reclamos comerciales de OSE (2019–2024) por departamento |

## Orden de carga

Las dependencias entre módulos están definidas en [`etl_graph.json`](etl_graph.json).

Algunos módulos requieren que otros estén cargados primero:

- `inumet` requiere `estaciones`
- `bacteriologia_ose` requiere `departamentos`
- `precipitaciones.load_registros` requiere `precipitaciones.load_estaciones`
- `gems.load_mediciones` requiere `gems.load_estaciones`
- `reclamos` requiere `departamentos`
