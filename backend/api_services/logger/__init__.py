import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s ",
    # filename="app.log",
    # filemode="a",
    datefmt="%d-%b-%y %H:%M:%S",
)

logger = logging.getLogger(__name__)
