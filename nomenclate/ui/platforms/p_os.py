import os
from . import default as default
from . import platform_registry as registry


@registry.register_class
class OSPlatform(default.DefaultPlatform):
    BASENAME = 'python'

    @classmethod
    def rename(cls, node_path, new_name, keep_extension=True):
        old_extension = '' if keep_extension else os.path.extsep(node_path)[1]
        os.rename(node_path, os.path.join(os.path.dirname(node_path), new_name) + old_extension)
