import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("water_watch.log", mode="a", encoding="utf-8"),
    ],
    force=True,
)

# CPLE_NotSupported "warp options does not support option SHARING": warning inofensivo
# de GDAL al leer tiles de Sentinel-2 vía stackstac, se repite por cada banda/tile.
logging.getLogger("rasterio._env").setLevel(logging.ERROR)

# "Found credentials in environment variables": botocore lo loguea por cada
# request S3 que hace stackstac al leer tiles de Sentinel-2.
logging.getLogger("botocore.credentials").setLevel(logging.WARNING)