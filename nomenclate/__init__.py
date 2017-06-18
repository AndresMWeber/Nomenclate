""" Overall module nomenclate
    It contains a convenience variable Nom which you can instantiate a
    nomenclate.core.nomenclature.Nomenclate object from.
    It also imports the version as __version__ from nomenclate.version for convenience

"""
from . import core
from . import version
from . import settings

__version__ = version.__version__
Nom = core.nomenclature.Nomenclate
