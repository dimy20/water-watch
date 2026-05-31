"""
Testea que todos los departamentos en el GeoJSON fuente tienen geometrias validas
para usar con $geoWithin (Polygon o MultiPolygon).

Para los que no lo son, intenta convertirlos con polygonize y reporta el resultado.

Uso:
    python scripts/test_departamentos_geometry.py
"""

import json
from pathlib import Path
from shapely.geometry import shape
from shapely.ops import polygonize, unary_union

GEOJSON_PATH = Path(__file__).parent.parent / "data" / "departamentos.geojson"
TIPOS_VALIDOS = {"Polygon", "MultiPolygon"}


def test_departamentos():
    with open(GEOJSON_PATH, encoding="utf-8") as f:
        geojson = json.load(f)

    features = geojson["features"]
    print(f"Total departamentos: {len(features)}\n")

    ok = []
    convertibles = []
    fallidos = []

    for feat in features:
        props = feat.get("properties", {})
        nombre = props.get("nombre") or props.get("NOMBRE") or props.get("name") or str(props)
        geom_type = feat["geometry"]["type"]

        if geom_type in TIPOS_VALIDOS:
            ok.append((nombre, geom_type))
            continue

        try:
            geom = shape(feat["geometry"])
            polygons = list(polygonize(geom))

            if not polygons:
                fallidos.append((nombre, geom_type, "polygonize devolvio 0 poligonos — lineas no forman anillos cerrados"))
                continue

            fixed = polygons[0] if len(polygons) == 1 else unary_union(polygons)

            if not fixed.is_valid:
                fallidos.append((nombre, geom_type, f"geometria resultante invalida"))
                continue

            convertibles.append((nombre, geom_type, fixed.geom_type, len(polygons)))

        except Exception as e:
            fallidos.append((nombre, geom_type, str(e)))

    print(f"OK - Ya validos ({len(ok)}):")
    for nombre, tipo in ok:
        print(f"   {nombre}: {tipo}")

    print(f"\n~ Convertibles con polygonize ({len(convertibles)}):")
    for nombre, tipo_orig, tipo_nuevo, n_polys in convertibles:
        print(f"   {nombre}: {tipo_orig} -> {tipo_nuevo} ({n_polys} poligono(s))")

    print(f"\nX Fallidos ({len(fallidos)}):")
    for nombre, tipo_orig, razon in fallidos:
        print(f"   {nombre} ({tipo_orig}): {razon}")

    print(f"\nResumen: {len(ok)} OK | {len(convertibles)} convertibles | {len(fallidos)} fallidos")

    if not fallidos:
        print("\n-> Todos los departamentos pueden usarse con $geoWithin tras la conversion.")
    else:
        print("\n-> Los fallidos necesitan correccion en el dato fuente.")

    # Mostrar las propiedades del primer feature para saber el nombre del campo
    print(f"\nPropiedades del primer feature: {list(features[0]['properties'].keys())}")


if __name__ == "__main__":
    test_departamentos()
