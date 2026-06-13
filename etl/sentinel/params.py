EARTH_SEARCH_URL = "https://earth-search.aws.element84.com/v1"
SENTINEL_SURFACE_REFLECTION = "sentinel-2-l2a"
# En SCL (Scene Classification Layer) 
# pixels con valor 6 significa agua, esto se usa para aplicar una mascara a la imagen
# y filtran solo pixels que tienen agua.
AGUA = 6
CODE_NDCI = "NDCI"
DATA_FILE = "./data/sentinel/puntos_v1.csv"
DATETIME_RANGE = "2016-01-01/2026-01-01"
MAX_CLOUD_COVER = 20
