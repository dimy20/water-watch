import logging

LOG_FILENAME = "water_watch.log"

logging.basicConfig(
    filename=LOG_FILENAME,
    filemode="a",
    level=logging.WARNING, 
    format="%(levelname)s %(name)s: %(message)s", 
    force=True
)