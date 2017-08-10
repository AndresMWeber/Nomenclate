REGISTERED_PLATFORMS = {}


def register_class(cls):
    REGISTERED_PLATFORMS[cls.BASENAME] = cls
    return cls
