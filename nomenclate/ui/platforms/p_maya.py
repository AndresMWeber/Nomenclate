import os
from . import default as default
from . import platform_registry as registry
import maya.cmds as cmds
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin


@registry.register_class
class MayaPlatform(default.DefaultPlatform):
    BASENAME = 'maya'
    DOCKABLE = True
    RUN_KWARGS = {'dockable': 1, 'floating': 1, 'area': 'left'}
    PLATFORM_MIXIN = MayaQWidgetDockableMixin

    @classmethod
    def rename(cls, node_path, new_name, keep_extension=True):
        old_extension = '' if keep_extension else os.path.extsep(node_path)[1]
        cmds.rename(node_path, os.path.join(os.path.dirname(node_path), new_name) + old_extension)
