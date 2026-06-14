EARTH_SEARCH_URL = "https://earth-search.aws.element84.com/v1"
SENTINEL_SURFACE_REFLECTION = "sentinel-2-l2a"
# En SCL (Scene Classification Layer) 
# pixels con valor 6 significa agua, esto se usa para aplicar una mascara a la imagen
# y filtran solo pixels que tienen agua.
AGUA = 6
CODE_NDCI = "NDCI"
CODE_NDTI = "NDTI"
DATA_FILE = "./data/sentinel/puntos_v1.csv"
DATETIME_RANGE = "2016-01-01/2026-01-01"
MAX_CLOUD_COVER = 20

# Por cada indice, las bandas necesarias (sin "scl", que se agrega siempre
# para la mascara de agua) y la formula para calcularlo a partir de ellas.
INDICES = {
    CODE_NDCI: {
        "bands": ("rededge1", "red"),
        "formula": lambda b: (b["rededge1"] - b["red"]) / (b["rededge1"] + b["red"]),
    },
    CODE_NDTI: {
        "bands": ("red", "green"),
        "formula": lambda b: (b["red"] - b["green"]) / (b["red"] + b["green"]),
    },
}
