import os
from . import default as default
from . import platform_registry as registry
import nuke
import nukescripts


@registry.register_class
class NukePlatform(default.DefaultPlatform):
    BASENAME = 'nuke'
    DOCKABLE = True
    RUN_KWARGS = {'dockable': 1, 'floating': 1, 'area': 'left'}

    def __init__(self):
        super(NukePlatform).__init__()

    @classmethod
    def rename(cls, node_path, new_name, keep_extension=True):
        old_extension = '' if keep_extension else os.path.extsep(node_path)[1]
        new_name = os.path.join(os.path.dirname(node_path), new_name) + old_extension
        nuke.Node(node_path)['name'].setValue()
        return new_name

    def show(self, window_instance):
        super(NukePlatform, self).show(window_instance)
        nukescripts.registerWidgetAsPanel(str(type(window_instance)), 'Nomenclate', 'nomenclate.ui.MainDialog')

    @classmethod
    def exists(cls, node_path):
        return nuke.exists(node_path)

    @classmethod
    def short_name(cls, node_path):
        return cls.long_name(node_path)

    @classmethod
    def long_name(cls, node_path):
        return nuke.Node(node_path)['name']