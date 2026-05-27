from __future__ import annotations

import logging
import time
from contextlib import contextmanager


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
    )


@contextmanager
def stage_timer(name: str):
    start = time.time()
    logging.info('stage started: %s', name)
    try:
        yield
    finally:
        elapsed = time.time() - start
        logging.info('stage finished: %s (%.2fs)', name, elapsed)
