import os
from . import default as default
from . import platform_registry as registry
import nuke
import nukescripts
from nukescripts import panels


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
        nuke.Node(node_path)['name'].setValue(os.path.join(os.path.dirname(node_path), new_name) + old_extension)

    def show(self, window_instance):
        super(NukePlatform, self).show(window_instance)
        nukescripts.registerWidgetAsPanel(str(type(window_instance)), 'Nomenclate', 'nomenclate.ui.MainDialog')
