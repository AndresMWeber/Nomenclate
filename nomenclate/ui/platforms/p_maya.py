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
        new_name = os.path.join(os.path.dirname(node_path), new_name) + old_extension
        cmds.rename(node_path, new_name)
        return new_name

    @classmethod
    def exists(cls, node_path):
        return cmds.objExists(node_path)

    @classmethod
    def short_name(cls, node_path):
        return cls.long_name(node_path).split('|')[-1]

    @classmethod
    def long_name(cls, node_path):
        return cmds.ls(node_path, long=True)[0]

    @classmethod
    def close(cls, ui):
        # 2017 bug where it only checks for the PARENT as a workspace control for some reason instead of the UI itself.
        # {MAYA_INSTALL}/Python/Lib/site-packages/maya/app/general/mayaMixin.py
        if cmds.about(v=True) == '2017':
            mayaWorkspaceControlName = ui.objectName() + 'WorkspaceControl'
            if cmds.workspaceControl(mayaWorkspaceControlName, q=True, exists=True):
                print('Detected UI registered as control, closing...')
                cmds.workspaceControl(mayaWorkspaceControlName, e=True, close=True)

        super(MayaPlatform, cls).close(ui)
