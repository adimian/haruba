from haruba.api import app
from .conf import configure
import logging
import sys

logging.basicConfig(stream=sys.stdout,
                    format="%(asctime)s [%(levelname)s] %(message)s")

logger = logging.getLogger(__name__)
logger.level = logging.INFO


def init_plugin():
    logger.info("Plug-in chmod activated.")
    configure(app.config)
    from . import events
