from .nlog import (
    getLogger,
    DEBUG,
    INFO,
    CRITICAL,
    WARNING,
    ERROR,
    FATAL
)

PACKAGE_LOGGER_LEVEL = CRITICAL

CRITICAL = CRITICAL
INFO = INFO
DEBUG = DEBUG
WARNING = WARNING
ERROR = ERROR
FATAL = FATAL


def get_module_logger(module_name, module_override_level=None):
    module_logger_level = module_override_level or PACKAGE_LOGGER_LEVEL
    return getLogger(module_name, level=module_logger_level)