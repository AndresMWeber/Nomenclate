
# Module API

class NomenclateException(Exception):
    """Base Tabulator exception.
    """
    pass


class SourceError(NomenclateException):
    """Stream error.
    """
    pass


class SchemeError(NomenclateException):
    """Scheme error.
    """
    pass


class FormatError(NomenclateException):
    """Format error.
    """
    pass


class OptionsError(NomenclateException):
    """Options error.
    """
    pass


class ValidationError(NomenclateException):
    """IO error.
    """
    pass


class ResourceNotFoundError(NomenclateException):
    """HTTP error.
    """
    pass


class ResetError(NomenclateException):
    """Reset error.
    """
    pass