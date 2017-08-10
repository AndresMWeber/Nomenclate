import os
import glob
import json
import tempfile
import nomenclate.ui.utils as utils
import nomenclate.settings as settings

MODULE_LOGGER_LEVEL_OVERRIDE = settings.QUIET

LOG = settings.get_module_logger(__name__, module_override_level=MODULE_LOGGER_LEVEL_OVERRIDE)

preset_header = 'nomenclate_preset'
preset_info = 'This is a nomenclate preset file.'
preset_metadata = {'nomenclate_preset': preset_info}


class NomenclateFileContext(object):
    TEMP_PATH = tempfile.gettempdir()
    HOME_PATH = os.path.expanduser("~")

    BASE_DIR = '.nomenclate'
    UI_DIR = 'ui'
    PRESETS_DIR = 'presets'

    DEFAULT_PATH = os.path.join(HOME_PATH, BASE_DIR)
    DEFAULT_UI_PATH = os.path.join(DEFAULT_PATH, UI_DIR)
    DEFAULT_PRESETS_PATH = os.path.join(DEFAULT_UI_PATH, PRESETS_DIR)

    FILE_HISTORY = []

    def __init__(self, filename):
        self.filename = filename
        self.data_cache = {}
        self.modes = {0: 'HOME_PATH',
                      1: 'TEMP_PATH'}
        self.mode = None
        self.set_root_dir_mode(0)

    def presets_dir(self):
        return os.path.join(self.get_root_dir_from_mode(), self.BASE_DIR, self.UI_DIR, self.PRESETS_DIR)

    def get_valid_presets_dirs(self):
        return [os.path.join(path, self.BASE_DIR, self.UI_DIR, self.PRESETS_DIR) for path in self.valid_root_dirs]

    @property
    def valid_history_dirs(self):
        return [os.path.dirname(path) for path in self.FILE_HISTORY if os.path.exists(os.path.dirname(path))]

    @property
    def valid_root_dirs(self):
        return [path for path in [getattr(self, self.modes[mode]) for mode in list(self.modes)] if
                os.path.exists(path) and os.path.isdir(path)]

    def get_valid_dirs(self):
        return self.valid_history_dirs + self.valid_root_dirs

    def set_root_dir_mode(self, mode_int):
        self.mode = getattr(self, self.modes.get(mode_int))

    def get_root_dir_from_mode(self):
        return self.mode

    def save(self, data=None, temp_dir=None, filename=None, full_path_override=None):
        LOG.info('Saving file from filename %s and full path %s' % (filename, full_path_override))
        data = self.data_cache if data is None else data
        temp_dir = self.get_root_dir_from_mode() if temp_dir is None else temp_dir
        filename = self.filename if filename is None else filename
        save_file_path = os.path.join(temp_dir, self.BASE_DIR, filename)

        if full_path_override:
            save_file_path = full_path_override

        if not os.path.exists(os.path.dirname(save_file_path)):
            os.makedirs(os.path.dirname(save_file_path))

        with open(save_file_path, 'w') as f:
            json.dump(data, f, indent=4, separators=(',', ': '))
            self.data_cache = data

        self.FILE_HISTORY.append(save_file_path)
        LOG.info('Successfully wrote state to file %s' % self.FILE_HISTORY[-1])

    def load(self, filename=None, full_path_override=None):
        if full_path_override is None:
            filename = self.filename if filename is None else filename
            matches = []
            for settings_file in [os.path.join(dir, self.BASE_DIR, filename) for dir in self.valid_root_dirs]:
                if os.path.exists(settings_file) and os.path.isfile(settings_file):
                    matches.append(settings_file)
        else:
            matches = [full_path_override]

        for settings_file in matches:
            with open(settings_file, 'r') as f:
                data = json.load(f)
                self.FILE_HISTORY.append(settings_file)
                self.data_cache = data
                return data
        return {}

    def save_preset_file(self, data=None, filename=None, full_path_override=None):
        if full_path_override is None:
            file = self.filename if filename is None else filename
            full_path_override = os.path.join(self.presets_dir(), file)
        default_data = preset_metadata.copy()
        default_data.update(data or {})
        self.save(data=default_data, filename=filename, full_path_override=full_path_override)

    def valid_preset_file(self, json_file_path):
        if not os.path.exists(json_file_path):
            return False

        with open(json_file_path, 'r') as f:
            data = json.load(f)
            if data.get(preset_header) == preset_info:
                return True
        return False

    def load_preset_file(self, filename=None, full_path_override=None):
        for settings_folder in self.get_valid_presets_dirs():
            filename = filename if filename else self.filename
            if filename is None and full_path_override is None:
                files = glob.glob(settings_folder, '*.json')
            else:
                files = [full_path_override] if full_path_override else [os.path.join(settings_folder, filename)]

            for json_file in files:
                if self.valid_preset_file(json_file):
                    return self.load(full_path_override=json_file)
        return None

    def find_preset_files(self):
        preset_files = []
        for settings_folder in self.get_valid_presets_dirs():
            for json_file in glob.glob(os.path.join(settings_folder, '*.json')):
                if self.valid_preset_file(json_file):
                    preset_files.append(json_file)
        return preset_files


class WidgetState(object):
    WIDGETS = utils.INPUT_WIDGETS.copy()
    FILE_CONTEXT = NomenclateFileContext('last_ui_settings.json')
    STORE_WITH_HASH = True

    @classmethod
    def list_presets(cls):
        return cls.FILE_CONTEXT.find_preset_files()

    @classmethod
    def generate_state(cls, ui, filename=None, fullpath_override=None):
        """ save "ui" controls and values to registry "setting"
        """
        settings = {}
        unhandled_types = []
        for widget in cls.get_ui_members(ui):
            try:
                if widget != ui:
                    widget_path = cls.get_widget_path(widget, top_level=ui)

                    if cls.is_unique_widget_path(widget_path, settings):
                        value = cls.serialize_widget_settings(widget)
                        if value != '':
                            settings[widget_path] = value
                    else:
                        parent = widget.parent()
                        LOG.warning(
                            '{0} needs an objectName, siblings of same class exist under parent {1}'.format(widget,
                                                                                                            parent))
            except AttributeError:
                LOG.warning('Cannot handle widget %s of type %s' % (widget, type(widget)))
                unhandled_types.append(type(widget))

        LOG.info('Generated state...now saving to preset file')

        cls.FILE_CONTEXT.save_preset_file(data=settings, filename=filename, full_path_override=fullpath_override)
        return settings

    @classmethod
    def restore_state(cls, ui, filename=None, fullpath_override=None, defaults=False):
        """ restore "ui" controls with values stored in registry "settings"
        """
        settings = cls.FILE_CONTEXT.load_preset_file(filename=filename, full_path_override=fullpath_override)

        failed_load = []
        if settings:
            for widget in cls.get_ui_members(ui):
                for supported_widget_type in list(cls.WIDGETS):
                    if issubclass(type(widget), supported_widget_type):
                        widget_path = cls.get_widget_path(widget, top_level=ui)

                        if defaults:
                            setting = getattr(widget, 'default_value', None)
                        else:
                            setting = settings.get(widget_path, None)

                        if setting is not None:
                            setter = cls.WIDGETS[supported_widget_type][utils.SETTER]
                            setter(widget, setting)
                        else:
                            failed_load.append(widget_path)
                        break

            LOG.info('Successfully loaded state from file %s' % cls.FILE_CONTEXT.FILE_HISTORY[-1])
        else:
            LOG.warning('No data was found from dirs %s for filename %s and fullpath_override %s' %
                        (cls.FILE_CONTEXT.valid_root_dirs, filename, fullpath_override))
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

    @classmethod
    def get_widget_path(cls, qwidget, top_level=None):
        LOG.debug('Starting widget path for widget %s until %s' % (qwidget, top_level))
        widget_path = cls.get_widget_name(qwidget)
        while qwidget.parent() and qwidget != top_level:
            widget_path = cls.get_widget_name(qwidget.parent()) + utils.OBJECT_PATH_SEPARATOR + widget_path
            qwidget = qwidget.parent()
        widget_path = widget_path if not cls.STORE_WITH_HASH else utils.persistent_hash(widget_path)
        LOG.debug('Attained widget path %s' % (widget_path))
        return str(widget_path)

    @classmethod
    def get_widget_name(cls, widget):
        object_name = '#' + widget.objectName() if widget.objectName() else ''
        return cls.strip_instance_formatting(widget) + object_name

    @staticmethod
    def strip_instance_formatting(widget):
        return str(type(widget)).replace("<class \'", '').replace("\'>", "").split('.')[-1]
