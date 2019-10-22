# Mimicking these exception styles found here:
# https://github.com/frictionlessdata/tabulator-py/blob/master/tabulator/exceptions.py

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

class BalanceError(ValidationError):
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


class OverlapError(NomenclateException):
    """Overlap error.
    """
    pass
