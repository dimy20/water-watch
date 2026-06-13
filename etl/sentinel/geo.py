from shapely.geometry import box

# dada un coordenada y una distancia, se creat una boundind box
def make_bounds(coords: list, dist: float) -> list:
    lat, lon = coords
    return [
        lon - dist,  # lon_min
        lat - dist,  # lat_min
        lon + dist,  # lon_max
        lat + dist,  # lat_max
    ]

def make_bbox_polygon(coords: list, dist: float):
    return box(*make_bounds(coords, dist))
