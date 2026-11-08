import logging
import sys

LOG_FORMAT = "%(asctime)s - %(levelname)s - [%(name)s] - %(message)s"


def setup_app_logging():
    """
    Configures the root logger for the entire application.
    """
    logging.basicConfig(
        level=logging.INFO,
        format=LOG_FORMAT,
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,  
    )

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)


setup_app_logging()
