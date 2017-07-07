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
QUIET = None

def get_module_logger(module_name, module_override_level=None):
    module_logger_level = module_override_level or PACKAGE_LOGGER_LEVEL
    return getLogger(module_name, level=module_logger_level)

# Is not a hard coded (word) and does not end with any non word characters or capitals (assuming camel)
FORMAT_STRING_REGEX = r'(?:\([\w]+\))|([A-Za-z0-9][^A-Z_\W]+)'
STATIC_TEXT_REGEX = '\([\w]+\)'
SEPARATORS = '\\._-?()'