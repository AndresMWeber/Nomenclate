import nomenclate.ui.utils as utils
import tempfile
import json
import os
import nomenclate.settings as settings

MODULE_LOGGER_LEVEL_OVERRIDE = settings.QUIET

LOG = settings.get_module_logger(__name__, module_override_level=MODULE_LOGGER_LEVEL_OVERRIDE)


class NomenclateFileContext(object):
    BASE_DIR = '.nomenclate'
    TEMP_DIR = tempfile.gettempdir()
    HOME_DIR = os.path.expanduser("~")
    DEFAULT_DIR = os.path.join(HOME_DIR, BASE_DIR)

    FILE_HISTORY = []

    def __init__(self, filename):
        self.filename = filename
        self.data_cache = {}

        self.modes = {0: 'HOME_DIR',
                      1: 'TEMP_DIR'}
        self.mode = self.modes[0]

    @property
    def valid_write_dirs(self):
        return [os.path.dirname(path) for path in self.FILE_HISTORY if os.path.exists(os.path.dirname(path))]

    @property
    def valid_temp_dirs(self):
        return [path for path in [getattr(self, self.modes[mode]) for mode in self.modes] if
                os.path.exists(path) and os.path.isdir(path)]

    def get_valid_dirs(self):
        return self.valid_write_dirs + self.valid_temp_dirs

    def swap_mode(self, mode_int):
        self.mode = self.modes.get(mode_int, 0)

    def get_mode_dir(self):
        return getattr(self, self.mode)

    def save(self, data=None, temp_dir=None, filename=None, fullpath_override=None):
        data = self.data_cache if data is None else data
        temp_dir = self.get_mode_dir() if temp_dir is None else temp_dir
        filename = self.filename if filename is None else filename
        save_file_path = os.path.join(temp_dir, self.BASE_DIR, filename)

        if fullpath_override:
            save_file_path = fullpath_override

        if not os.path.exists(os.path.dirname(save_file_path)):
            os.makedirs(os.path.dirname(save_file_path))

        with open(save_file_path, 'w') as f:
            json.dump(data, f, indent=4, separators=(',', ': '))
            self.data_cache = data

        self.FILE_HISTORY.append(save_file_path)
        LOG.info('Successfully wrote state to file %s' % self.FILE_HISTORY[-1])

    def load(self, filename=None, fullpath_override=None):
        if fullpath_override is None:
            filename = self.filename if filename is None else filename
            matches = []
            for settings_file in [os.path.join(dir, self.BASE_DIR, filename) for dir in self.get_valid_dirs()]:
                if os.path.exists(settings_file) and os.path.isfile(settings_file):
                    matches.append(settings_file)
        else:
            matches = [fullpath_override]

        for settings_file in matches:
            with open(settings_file, 'r') as f:
                data = json.load(f)
                self.FILE_HISTORY.append(settings_file)
                self.data_cache = data
                return data

        if fullpath_override:
            save_file_path = fullpath_override
        return {}


class WidgetState(object):
    WIDGETS = utils.INPUT_WIDGETS.copy()
    FILE_CONTEXT = NomenclateFileContext('ui_state.json')
    STORE_WITH_HASH = True

    @classmethod
    def generate_state(cls, ui, filename=None, fullpath_override=None):
        """ save "ui" controls and values to registry "setting"
        """
        settings = {}
        unhandled_types = []
        for widget in cls.get_ui_members(ui):
            try:
                widget_path = cls.get_widget_path(widget)
                widget_path = widget_path if not cls.STORE_WITH_HASH else hash(widget_path)

                if cls.is_unique_widget_path(widget_path, settings):
                    settings[widget_path] = cls.serialize_widget_settings(widget)
                else:
                    parent = widget.parent()
                    LOG.warning('{0} needs an objectName, siblings of same class exist under parent {1}'.format(widget,
                                                                                                                parent))
            except AttributeError:
                unhandled_types.append(type(widget))

        cls.FILE_CONTEXT.save(data=settings, filename=filename, fullpath_override=fullpath_override)
        return settings

    @classmethod
    def restore_state(cls, ui, filename=None, fullpath_override=None, defaults=False):
        """ restore "ui" controls with values stored in registry "settings"
        """
        settings = cls.FILE_CONTEXT.load(filename=filename, fullpath_override=fullpath_override)

        failed_load = []
        if settings:
            for widget in cls.get_ui_members(ui):
                for supported_widget_type in list(cls.WIDGETS):
                    if issubclass(type(widget), supported_widget_type):
                        widget_path = cls.get_widget_path(widget)
                        widget_path = widget_path if not cls.STORE_WITH_HASH else hash(widget_path)

                        if defaults:
                            setting = getattr(widget, 'default_value', None)
                        else:
                            setting = settings.get(str(hash(widget_path)), None)

                        if setting is not None:
                            setter = cls.WIDGETS[supported_widget_type][utils.SETTER]
                            setter(widget, setting)
                        else:
                            failed_load.append(widget_path)
                        break

            LOG.info('Successfully Loaded state from file %s' % cls.FILE_CONTEXT.FILE_HISTORY[-1])
        else:
            LOG.warning('No data was found from dirs %s' % cls.FILE_CONTEXT.get_valid_dirs())
        return settings

    @property
    def supported_widget_types(self):
        return list(self.WIDGETS)

    @staticmethod
    def get_ui_members(ui):
        return utils.get_all_widget_children(ui)

    @classmethod
    def serialize_widget_settings(cls, widget):
        return cls.get_widget_method(type(widget), utils.GETTER)(widget)

    @classmethod
    def get_widget_method(cls, widget_type, type):
        if not widget_type in list(cls.WIDGETS):
            for supported_widget_type in list(cls.WIDGETS):
                if issubclass(widget_type, supported_widget_type):
                    widget_type = supported_widget_type
        return cls.WIDGETS.get(widget_type).get(type)

    @classmethod
    def deserialize_widget_settings(cls, widget, settings):
        return cls.get_widget_method(widget, utils.SETTER)(widget, settings[widget.objectName()])

    @classmethod
    def is_unique_widget_path(self, widget_path, settings):
        if settings.get(widget_path, None) is None:
            return True
        else:
            return False

    def get_ui_custom_attributes(self):
        pass
        # import inspect
        # inspect.getmembers(MyClass, lambda a: not (inspect.isroutine(a)))

    @classmethod
    def get_widget_path(cls, qwidget):
        widget_path = cls.get_widget_name(qwidget)
        while qwidget.parent():
            widget_path = cls.get_widget_name(qwidget.parent()) + utils.OBJECT_PATH_SEPARATOR + widget_path
            qwidget = qwidget.parent()
        return str(widget_path)

    @classmethod
    def get_widget_name(cls, widget):
        object_name = '#' + widget.objectName() if widget.objectName() else ''
        return cls.strip_instance_formatting(widget) + object_name

    @staticmethod
    def strip_instance_formatting(widget):
        return str(type(widget)).replace("<class \'", '').replace("\'>", "").split('.')[-1]
