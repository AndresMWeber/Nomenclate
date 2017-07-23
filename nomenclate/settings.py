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

SEPARATORS = r'\(\)\{\}\[\]<>.()_\-'
REGEX_SINGLE_PARENTHESIS = r'(\()|(\))'
REGEX_PARENTHESIS = r'([\(\)]+)'
REGEX_BRACKETS = r'([\{\}]+)'
REGEX_STATIC_TOKEN = '(\(\w+\))'
REGEX_BRACKET_TOKEN = r'(\{\w+\})'
REGEX_TOKEN_SEARCH = r'(?P<token>((?<![a-z\(\)]){TOKEN}(?![0-9]))|((?<=[a-z_\(\)]){TOKEN_CAPITALIZED}(?![0-9])))'
REGEX_ADJACENT_UNDERSCORE = r'(^[\W_]+)|([\W_]+$)'
REGEX_SINGLE_LETTER = r'[a-zA-Z]'
REGEX_TOKEN = r'[A-Za-z0-9][^A-Z\W{SEP}]+'.format(SEP=SEPARATORS)

FORMAT_STRING_REGEX = r'(?:{STATIC})|({TOKEN})|{CHAR}'.format(STATIC=REGEX_STATIC_TOKEN,
                                                              TOKEN=REGEX_TOKEN,
                                                              CHAR=REGEX_SINGLE_LETTER)
