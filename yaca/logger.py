import logging

LOGGER_NAME = "yaca"

_CONFIGURED = False


def get_logger(name: str) -> logging.Logger:
    """Get a configured logger.

    Configures a single shared console handler+formatter once (no duplicates)
    on the `yaca` base logger. Descendant loggers rely on propagation.
    """
    global _CONFIGURED

    base_logger = logging.getLogger(LOGGER_NAME)

    if not _CONFIGURED:
        base_logger.setLevel(logging.DEBUG)

        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.DEBUG)
        stream_handler.setFormatter(formatter)

        if not any(isinstance(h, logging.StreamHandler) for h in base_logger.handlers):
            base_logger.addHandler(stream_handler)

        base_logger.propagate = False
        _CONFIGURED = True

    if name == LOGGER_NAME:
        return base_logger

    if name.startswith(LOGGER_NAME + "."):
        return logging.getLogger(name)

    return logging.getLogger(f"{LOGGER_NAME}.{name}")
