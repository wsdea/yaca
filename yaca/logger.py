import logging

LOGGER_NAME = "yaca"

_CONFIGURED = False


def get_logger(name: str) -> logging.Logger:
    """Get a configured logger.

    Configures the `yaca` base logger once. Descendant loggers rely on propagation.
    """
    global _CONFIGURED

    base_logger = logging.getLogger(LOGGER_NAME)

    if not _CONFIGURED:
        base_logger.setLevel(logging.DEBUG)
        base_logger.propagate = False
        _CONFIGURED = True

    if name == LOGGER_NAME:
        return base_logger

    if name.startswith(LOGGER_NAME + "."):
        return logging.getLogger(name)

    return logging.getLogger(f"{LOGGER_NAME}.{name}")
