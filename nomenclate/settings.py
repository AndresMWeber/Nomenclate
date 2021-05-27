# Is not a hard coded (word) and does not end with any non word characters or capitals (assuming camel)

TEMPLATE_YML_CONFIG_FILE_PATH = "template/env.yml"
DEFAULT_YML_CONFIG_FILE = ".nomenclate.yml"

SEPARATORS = r"\(\)\{\}\[\]<>.()_\-"
REGEX_SINGLE_PARENTHESIS = r"(\()|(\))"
REGEX_PARENTHESIS = r"([\(\)]+)"
REGEX_BRACKETS = r"([\{\}]+)"
REGEX_STATIC_TOKEN = r"(\(\w+\))"
REGEX_BRACKET_TOKEN = r"(\{\w+\})"
REGEX_TOKEN_SEARCH = (
    r"(?P<token>((?<![a-z\(\)]){TOKEN}(?![0-9]))|((?<=[a-z_\(\)]){TOKEN_CAPITALIZED}(?![0-9])))"
)
REGEX_ADJACENT_UNDERSCORE = r"(^[\W_]+)|([\W_]+$)"
REGEX_SINGLE_LETTER = r"[a-zA-Z]"
REGEX_TOKEN = r"[A-Za-z0-9][^A-Z\W{SEP}]+".format(SEP=SEPARATORS)

FORMAT_STRING_REGEX = r"(?:{STATIC})|({TOKEN})|{CHAR}".format(
    STATIC=REGEX_STATIC_TOKEN, TOKEN=REGEX_TOKEN, CHAR=REGEX_SINGLE_LETTER
)
