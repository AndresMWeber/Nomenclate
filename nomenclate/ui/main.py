import os
from glob import glob
from functools import partial
import PyQt5.QtWidgets as QtWidgets
import PyQt5.QtCore as QtCore
import PyQt5.QtGui as QtGui
import nomenclate.ui.utils as utils
import nomenclate.settings as settings
import nomenclate.ui.instance_handler as instance_handler
import nomenclate.ui.object_list as object_list
import nomenclate.ui.default as default
import nomenclate.ui.components.gui_save as gui_save

try:
    UNICODE_EXISTS = bool(type(unicode))
except NameError:
    unicode = lambda s: str(s)

MODULE_LOGGER_LEVEL_OVERRIDE = settings.QUIET


class UISetting(object):
    def __init__(self, default_value=None):
        self.default_value = default_value
        self.value = default_value

    @property
    def is_default(self):
        return self.default == self.value

    @property
    def default(self):
        return self.default

    def get(self):
        return self.value

    def set_default(self):
        self.value = self.default

    def set(self, value):
        self.value = value


class MainDialog(default.DefaultWidget, utils.Cacheable, object):
    file_saved = QtCore.pyqtSignal()
    dropped_files = QtCore.pyqtSignal(list)
    update_stylesheet = QtCore.pyqtSignal()
    update_color_coded = QtCore.pyqtSignal(str, list, bool)

    NAME = 'Nomenclate'
    LOG = settings.get_module_logger(__name__, module_override_level=MODULE_LOGGER_LEVEL_OVERRIDE)
    WIDTH = 800
    HEIGHT = 600

    DEFAULT_QSS = 'default.qss'
    DARK_TEXT_QSS = 'text-on-light.qss'
    LIGHT_TEXT_QSS = 'text-on-dark.qss'
    MAIN_QSS = 'dark-too-cool.qss'
    QSS_GLOB = '*.qss'

    default_css_cache = None

    last_action_cache = None
    dark = UISetting(True)
    color_coded = UISetting(True)
    loaded_stylesheet = ''
    key_list = []

    format_history = []

    def __init__(self):
        super(MainDialog, self).__init__()
        self.add_fonts()
        self.setup_menubar()
        self.setup_hotkeys()
        self.update_stylesheet.emit()
        QtWidgets.QApplication.instance().installEventFilter(self)
        self.load_state()
        self.populate_presets()

    @property
    def focused_widget(self):
        return QtWidgets.QApplication.focusWidget()

    @property
    def default_stylesheet(self):
        return self.get_stylesheet_qss(self.DEFAULT_QSS)

    @property
    def text_stylesheet(self):
        text_stylesheet = self.LIGHT_TEXT_QSS if self.dark.get() else self.DARK_TEXT_QSS
        return self.get_stylesheet_qss(text_stylesheet)

    def combined_stylesheet(self):
        return self.loaded_stylesheet + self.default_stylesheet + self.text_stylesheet

    def create_controls(self):
        main_widget = self
        if isinstance(self, QtWidgets.QMainWindow):
            self.setCentralWidget(QtWidgets.QWidget())
            main_widget = self.centralWidget()

        self.layout_main = QtWidgets.QVBoxLayout(main_widget)
        self.menu_bar = QtWidgets.QMenuBar()
        self.wgt_drop_area = QtWidgets.QWidget()
        self.wgt_header = QtWidgets.QWidget()
        self.wgt_files = QtWidgets.QFrame()
        self.wgt_stack = QtWidgets.QStackedWidget()

        self.header_layout = QtWidgets.QHBoxLayout()
        self.header_label = QtWidgets.QLabel()
        self.files_layout = QtWidgets.QHBoxLayout()

        self.instance_handler = instance_handler.InstanceHandlerWidget(parent=self)
        self.file_list_view = object_list.FileListWidget()

    def connect_controls(self):
        self.setLayout(self.layout_main)

        self.wgt_header.setLayout(self.header_layout)
        self.header_layout.addWidget(self.header_label)

        self.layout_main.addWidget(self.menu_bar)
        self.layout_main.addWidget(self.wgt_header)
        self.layout_main.addWidget(self.instance_handler)
        self.layout_main.addWidget(self.wgt_stack)

        self.wgt_stack.addWidget(self.file_list_view)
        self.wgt_stack.addWidget(self.wgt_drop_area)

        self.dropped_files.connect(self.file_list_view.populate_objects)
        self.dropped_files.connect(lambda: self.wgt_stack.setCurrentIndex(0))
        self.file_list_view.request_name.connect(self.instance_handler.generate_name)
        self.instance_handler.name_generated.connect(self.file_list_view.set_item_name)
        self.file_list_view.request_state.connect(self.context_menu_state)

        self.instance_handler.format_updated.connect(self.update_format_history)
        self.instance_handler.nomenclate_output.connect(self.file_list_view.get_object_names)
        self.dropped_files.connect(self.file_list_view.get_object_names)

        self.update_stylesheet.connect(self.set_stylesheet)
        self.update_color_coded.connect(self.instance_handler.format_updated)
        self.file_saved.connect(self.populate_presets)

    def context_menu_state(self, qpoint, qitem):
        self.file_list_view.context_menu_for_item(qpoint,
                                                  qitem,
                                              self.instance_handler.NOM)

    def initialize_controls(self):
        font = QtWidgets.QApplication.font()
        font.setStyleStrategy(font.PreferAntialias)
        QtWidgets.QApplication.setFont(font)
        # self.setWindowOpacity(0.96)

        self.setFocus(QtCore.Qt.PopupFocusReason)
        self.load_stylesheet(stylesheet=self.MAIN_QSS)
        self.setWindowTitle(self.NAME)
        self.setObjectName('MainFrame')
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setAcceptDrops(True)

        self.wgt_stack.setObjectName('Stack')
        self.wgt_header.setObjectName('HeaderWidget')
        self.header_label.setObjectName('HeaderLabel')

        self.header_label.setText(self.NAME.upper())
        self.layout_main.setContentsMargins(0, 0, 0, 0)
        self.layout_main.setSpacing(0)
        self.setBaseSize(self.WIDTH, self.HEIGHT)
        self.layout_main.setAlignment(QtCore.Qt.AlignTop)
        self.instance_handler.fold()

    def setup_hotkeys(self):
        # self.hotkey_close = QtWidgets.QShortcut(QtGui.QKeySequence("Escape"), self)
        # self.hotkey_close.activated.connect(self.close)
        # self.hotkey_fold = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+Space"), self)
        # self.hotkey_fold.activated.connect(self.instance_handler.fold)
        pass

    def setup_menubar(self):
        self.file_menu = self.menu_bar.addMenu('File')
        self.edit_menu = self.menu_bar.addMenu('Edit')
        self.presets_menu = self.menu_bar.addMenu('Presets')
        self.view_menu = self.menu_bar.addMenu('View')
        self.themes_menu = self.menu_bar.addMenu('Themes')
        self.format_menu = self.edit_menu.addMenu('Previous Formats')
        self.presets_list_menu = self.presets_menu.addMenu('User Presets')

        self.preset_load_action = QtWidgets.QAction('Load Preset...')
        self.preset_load_action.setShortcut('Ctrl+Alt+L')
        self.preset_load_action.triggered.connect(lambda: self.run_action(self.load_state, None, True))

        self.preset_save_action = QtWidgets.QAction('Save New Preset...')
        self.preset_save_action.setShortcut('Ctrl+Alt+S')
        self.preset_save_action.triggered.connect(lambda: self.run_action(self.save_state, None, True))

        presets_action_load_from_config = self.presets_menu.addAction('Reload defaults from config.yml')
        presets_action_load_from_config.triggered.connect(lambda: self.instance_handler.load_settings_from_config())

        edit_action_load_last_format = self.presets_menu.addAction('Clear all fields')
        edit_action_load_last_format.setShortcut('Ctrl+R')
        edit_action_load_last_format.triggered.connect(lambda: self.restore_defaults())

        edit_action_load_last_format = self.presets_menu.addAction('Load last format')
        edit_action_load_last_format.setShortcut('Ctrl+D')
        edit_action_load_last_format.triggered.connect(lambda: self.load_format(None))

        view_action_color_code = self.view_menu.addAction('Color code tokens')
        view_action_color_code.setShortcut('Ctrl+E')
        view_action_color_code.triggered.connect(self.set_color_coded)

        view_action_refresh = self.view_menu.addAction('Refresh StyleSheets from Folder')
        view_action_refresh.setShortcut('Ctrl+U')
        view_action_refresh.triggered.connect(lambda: self.run_action(self.populate_qss_styles))

        view_action = self.view_menu.addAction('Expand/Collapse Tokens')
        view_action.setShortcut('Ctrl+H')
        view_action.triggered.connect(lambda: self.run_action(self.instance_handler.fold, None))

        view_action = self.view_menu.addAction('Swap Light/Dark Text')
        view_action.setShortcut('Ctrl+W')
        view_action.triggered.connect(lambda: self.run_action(self.set_color_mode, None))

        repeat_action = self.edit_menu.addAction('Repeat last menu action')
        repeat_action.setShortcut('Ctrl+G')
        repeat_action.triggered.connect(self.repeat_last_action)

        save_action = self.presets_menu.addAction('Save Window Settings')
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(lambda: self.run_action(self.save_state, None, False))


        load_action = self.presets_menu.addAction('Reload Current Preset')
        load_action.setShortcut('Ctrl+L')
        load_action.triggered.connect(lambda: self.run_action(self.load_state, None, False))

        exit_action = self.file_menu.addAction('Exit')
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(lambda: self.run_action(self.close, None, True))

        exit_no_save_action = self.file_menu.addAction(unicode(u' ↳ Exit without saving settings...'))
        exit_no_save_action.setShortcut('Ctrl+Alt+Q')
        exit_no_save_action.triggered.connect(lambda: self.run_action(self.close, None, False))

        self.populate_qss_styles()

    def load_format(self, format, *args):
        if not self.format_history:
            return
        if format is None:
            # Swap two last formats
            self.format_history = [self.format_history[1], self.format_history[0]] + self.format_history[2:]
            format = self.format_history[0]
        else:
            self.format_history.remove(format)
            self.format_history.insert(0, format)

        if format != self.instance_handler.input_format.text_utf:
            self.instance_handler.input_format.setText(format)
        self.refresh_format_history_menu()

    def update_format_history(self, format_string, format_order, swapped):
        if not format_string in self.format_history:
            self.format_history.insert(0, format_string)
        self.refresh_format_history_menu()

    def refresh_format_history_menu(self):
        self.format_menu.clear()
        for format_history in self.format_history:
            menu_action = self.format_menu.addAction(format_history)
            action = partial(self.run_action, self.load_format, None, format_history)
            menu_action.triggered.connect(action)

    def restore_defaults(self):
        gui_save.WidgetState.restore_state(self, defaults=True)

    def save_state(self, mode=False):
        result = None if not mode else QtWidgets.QFileDialog.getSaveFileName(self, 'Save UI Settings',
                                                                             gui_save.NomenclateFileContext.DEFAULT_PRESETS_PATH,
                                                                             filter='*.json')
        result = self.process_dialog_result(result)
        gui_save.WidgetState.generate_state(self, fullpath_override=result)
        self.file_saved.emit()

    def load_state(self, mode=False):
        result = None if not mode else QtWidgets.QFileDialog.getOpenFileName(self, 'Load UI Settings',
                                                                             gui_save.NomenclateFileContext.DEFAULT_PRESETS_PATH,
                                                                             filter='*.json')
        result = self.process_dialog_result(result)
        gui_save.WidgetState.restore_state(self, fullpath_override=result)

    def process_dialog_result(self, path):
        if path is None:
            return path
        path, file_filter = path
        if not path:
            return None
        path = os.path.normpath(path)
        ext = file_filter.replace('*', '')
        return path if path.endswith(ext) else path + ext

    def run_action(self, action_function, qevent, *args, **kwargs):
        self.last_action_cache = {'function': action_function, 'args': args, 'kwargs': kwargs, 'event': qevent}
        action_function(*args, **kwargs)

    def repeat_last_action(self):
        if self.last_action_cache is not None:
            self.last_action_cache['function'](*self.last_action_cache['args'], **self.last_action_cache['kwargs'])

    def set_color_coded(self):
        self.color_coded.set(not self.color_coded.get())
        self.update_color_coded.emit(self.instance_handler.NOM.format, self.instance_handler.NOM.format_order, True)

    def set_color_mode(self, mode=None):
        if mode:
            self.dark.set(mode)
        else:
            self.dark.set(not self.dark.get())
        self.update_stylesheet.emit()

    def populate_presets(self):
        self.presets_list_menu.clear()
        for preset_file in sorted(gui_save.WidgetState.list_presets()):
            menu_action = self.presets_list_menu.addAction(os.path.basename(preset_file))
            menu_action.triggered.connect(partial(self.run_action,
                                                  gui_save.WidgetState.restore_state,
                                                  self,
                                                  fullpath_override=preset_file))
        self.presets_list_menu.addSeparator()
        self.presets_list_menu.addAction(self.preset_save_action)
        self.presets_list_menu.addAction(self.preset_load_action)

    def populate_qss_styles(self):
        self.themes_menu.clear()
        for qss_style in glob(os.path.join(utils.RESOURCES_PATH, self.QSS_GLOB)):
            file_name = os.path.basename(qss_style)
            style_name = os.path.splitext(file_name)[0]

            if file_name not in [self.DARK_TEXT_QSS, self.LIGHT_TEXT_QSS]:
                menu_action = self.themes_menu.addAction(style_name.capitalize())
                menu_action.triggered.connect(partial(self.run_action, self.load_stylesheet, stylesheet=file_name))

    @utils.cache_function
    def get_stylesheet_qss(self, stylesheet):
        file_path = os.path.join(utils.RESOURCES_PATH, stylesheet)
        stylesheet_file = os.path.normpath(file_path)
        return open(stylesheet_file).read() if os.path.isfile(stylesheet_file) else ''

    def load_stylesheet(self, btn_event=None, stylesheet=''):
        self.dark.set('dark' in stylesheet)
        qss_data = self.get_stylesheet_qss(stylesheet=stylesheet)
        self.loaded_stylesheet = qss_data
        self.update_stylesheet.emit()

    def set_stylesheet(self):
        QtWidgets.QApplication.instance().setStyleSheet(self.combined_stylesheet())

    def add_fonts(self):
        for font_file in [os.path.join(utils.FONTS_PATH, path) for path in os.listdir(utils.FONTS_PATH)]:
            QtGui.QFontDatabase.addApplicationFont(font_file)

    def next_stack_frame(self, *args):
        current_index = self.wgt_stack.currentIndex()
        next_index = current_index + 1
        if next_index + 1 > self.wgt_stack.count():
            next_index = 0
        self.wgt_stack.setCurrentIndex(next_index)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls:
            event.accept()
            self.wgt_stack.setCurrentIndex(1)
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        event.accept()
        self.wgt_stack.setCurrentIndex(0)

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            event.setDropAction(QtCore.Qt.CopyAction)
            event.accept()
            self.dropped_files.emit([str(url.toLocalFile()) for url in event.mimeData().urls()])

        if utils.get_application_type() == 'Maya':
            if event.mimeData().hasText():
                self.dropped_files.emit(event.mimeData().text().split())

    def eventFilter(self, source, event):
        if event.type() == QtCore.QEvent.KeyPress:
            if event.key() in [QtCore.Qt.Key_Tab, QtCore.Qt.Key_Backtab]:
                if self.focused_widget.parent() in self.instance_handler.token_widgets:
                    if self.instance_handler.select_next_token_line_edit(event.key() == QtCore.Qt.Key_Backtab):
                        return True

        if event.type() == QtCore.QEvent.Close:
            self.LOG.debug(
                'Close event %s detected from widget %s with parent %s' % (event, source, source.parent()))

        return super(MainDialog, self).eventFilter(source, event)

    def keyPressEvent(self, QKeyPressEvent):
        if QKeyPressEvent.key() in [QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return]:
            pass
        super(MainDialog, self).keyPressEvent(QKeyPressEvent)

    def mousePressEvent(self, event):
        focused_widget = self.focused_widget
        if isinstance(focused_widget, QtWidgets.QLineEdit):
            focused_widget.clearFocus()
        super(MainDialog, self).mousePressEvent(event)

    def close(self, save_state=True):
        if save_state:
            self.save_state()
        super(MainDialog, self).close()

    def closeEvent(self, e):
        if not issubclass(type(self.focused_widget), QtWidgets.QLineEdit):
            self.LOG.info('closeEvent and not within a QLineEdit, exiting.')
            QtWidgets.QApplication.instance().removeEventFilter(self)
            self.deleteLater()
            return exit()
