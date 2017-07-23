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
    MAIN_QSS = 'darkTooCool.qss'
    QSS_GLOB = '*.qss'

    default_css_cache = None

    last_action_cache = None
    dark = UISetting(True)
    color_coded = UISetting(True)
    loaded_stylesheet = ''
    key_list = []

    def __init__(self):
        super(MainDialog, self).__init__()
        self.add_fonts()
        self.setup_menubar()
        self.setup_hotkeys()
        self.update_stylesheet.emit()
        QtWidgets.QApplication.instance().installEventFilter(self)
        self.load_state()

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

        self.dropped_files.connect(self.update_names)
        self.instance_handler.nomenclate_output.connect(self.update_names)
        self.update_stylesheet.connect(self.set_stylesheet)
        self.update_color_coded.connect(self.instance_handler.format_updated)

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
        self.view_menu = self.menu_bar.addMenu('View')
        self.settings_menu = self.menu_bar.addMenu('Settings')
        self.style_menu = self.settings_menu.addMenu('Set Style')

        view_action_color_code = self.view_menu.addAction('Color code tokens')
        view_action_color_code.setShortcut('Ctrl+E')
        view_action_color_code.triggered.connect(self.set_color_coded)

        view_action_refresh = self.view_menu.addAction('Refresh StyleSheets from Folder')
        view_action_refresh.setShortcut('Ctrl+R')
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

        save_action = self.file_menu.addAction('Save Window Settings')
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(lambda: self.run_action(self.save_state, None, False))

        save_as_action = self.file_menu.addAction('   Save Window Settings As...')
        save_as_action.setShortcut('Ctrl+Alt+S')
        save_as_action.triggered.connect(lambda: self.run_action(self.save_state, None, True))

        load_action = self.file_menu.addAction('Load Last Window Settings ')
        load_action.setShortcut('Ctrl+L')
        load_action.triggered.connect(lambda: self.run_action(self.load_state, None, False))

        load_as_action = self.file_menu.addAction('   Load Window Settings From File...')
        load_as_action.setShortcut('Ctrl+Alt+L')
        load_as_action.triggered.connect(lambda: self.run_action(self.load_state, None, True))

        exit_action = self.file_menu.addAction('Exit')
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(lambda: self.run_action(self.close, None, True))

        exit_no_save_action = self.file_menu.addAction('   Exit without saving settings...')
        exit_no_save_action.setShortcut('Ctrl+Alt+Q')
        exit_no_save_action.triggered.connect(lambda: self.run_action(self.close, None, False))

        self.populate_qss_styles()

    def save_state(self, mode=False):
        filename = None if not mode else QtWidgets.QFileDialog.getSaveFileName(self, 'Save UI Settings',
                                                                               gui_save.NomenclateFileContext.DEFAULT_DIR,
                                                                               filter='*.json')
        if not isinstance(filename, tuple):
            gui_save.WidgetState.generate_state(self, filename=filename)
            print('Successfully wrote state to file %s' % gui_save.NomenclateFileContext.FILE_HISTORY[-1])

    def load_state(self, mode=False):
        filename = None if not mode else QtWidgets.QFileDialog.getSaveFileName(self, 'Load UI Settings',
                                                                               gui_save.NomenclateFileContext.DEFAULT_DIR,
                                                                               filter='*.json')
        if not isinstance(filename, tuple):
            data = gui_save.WidgetState.restore_state(self, filename=filename)
            if data:
                print('Successfully Loaded state from file %s' % gui_save.WidgetState.FILE_CONTEXT.FILE_HISTORY[-1])
                return
            else:
                print('No data was found from dirs %s' % gui_save.WidgetState.FILE_CONTEXT.get_valid_dirs())

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

    def populate_qss_styles(self):
        self.style_menu.clear()
        for qss_style in glob(os.path.join(utils.RESOURCES_PATH, self.QSS_GLOB)):
            file_name = os.path.basename(qss_style)
            style_name = os.path.splitext(file_name)[0]

            if file_name not in [self.DARK_TEXT_QSS, self.LIGHT_TEXT_QSS]:
                menu_action = self.style_menu.addAction(style_name.capitalize())
                action = partial(self.run_action, self.load_stylesheet, stylesheet=file_name)
                menu_action.triggered.connect(action)

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

    def update_names(self, object_paths=None):
        object_paths = object_paths if isinstance(object_paths,
                                                  list) else self.file_list_view.wgt_list_view.object_paths
        if object_paths:
            self.file_list_view.update_object_paths(self.generate_names(object_paths))

    def generate_names(self, object_paths):
        return [(target, self.instance_handler.get_index(index)) for index, target in enumerate(object_paths)]

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
        if event.mimeData().hasUrls:
            event.setDropAction(QtCore.Qt.CopyAction)
            event.accept()
            self.dropped_files.emit([str(url.toLocalFile()) for url in event.mimeData().urls()])
            self.wgt_stack.setCurrentIndex(0)

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
