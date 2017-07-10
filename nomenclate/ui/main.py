import os
from glob import glob
from functools import partial
from PyQt5 import QtWidgets, QtCore, QtGui
import nomenclate.ui.utils as utils
import nomenclate.settings as settings
import nomenclate.ui.filesystem as filesystem
import nomenclate.ui.instance_handler as instance_handler
import nomenclate.ui.drag_drop as drag_drop
import nomenclate.ui.object_list as file_list

MODULE_LOGGER_LEVEL_OVERRIDE = settings.DEBUG


class MainDialog(QtWidgets.QWidget):
    NAME = 'Nomenclate'
    LOG = settings.get_module_logger(__name__, module_override_level=MODULE_LOGGER_LEVEL_OVERRIDE)
    WIDTH = 800
    HEIGHT = 600

    DEFAULT_QSS = 'default.qss'
    MAIN_QSS = 'darkseas.qss'
    QSS_GLOB = '*.qss'

    def __init__(self):
        super(MainDialog, self).__init__()
        self.default_css_cache = None
        self.keylist = []
        self.add_fonts()
        self.setup()
        self.setup_menubar()
        self.setup_hotkeys()
        QtWidgets.QApplication.instance().installEventFilter(self)

    @property
    def focused_widget(self):
        return QtWidgets.QApplication.focusWidget()

    @property
    def default_stylesheet(self):
        if not self.default_css_cache:
            self.default_css_cache = self.get_stylesheet_qss(self.DEFAULT_QSS)
        return self.default_css_cache

    def setup_hotkeys(self):
        #self.hotkey_close = QtWidgets.QShortcut(QtGui.QKeySequence("Escape"), self)
        #self.hotkey_close.activated.connect(self.close)
        #self.hotkey_fold = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+Space"), self)
        #self.hotkey_fold.activated.connect(self.instance_handler.fold)
        pass

    def setup_menubar(self):
        self.file_menu = self.menu_bar.addMenu('File')
        self.edit_menu = self.menu_bar.addMenu('Edit')
        self.view_menu = self.menu_bar.addMenu('View')
        self.settings_menu = self.menu_bar.addMenu('Settings')
        self.style_menu = self.settings_menu.addMenu('Set Style')

        view_action_refresh = self.view_menu.addAction('Refresh Stylsheets from Folder')
        view_action_refresh.setShortcut('Ctrl+R')
        view_action_refresh.triggered.connect(self.populate_qss_styles)

        view_action = self.view_menu.addAction('Expand All Tokens')
        view_action.setShortcut('Ctrl+Space')
        view_action.triggered.connect(self.instance_handler.fold)

        exit_action = self.file_menu.addAction('Exit')
        exit_action.setShortcut('Escape')
        exit_action.triggered.connect(self.close)

        redo_action = self.edit_menu.addAction('Placeholder')
        #redo_action.triggered.connect()
        self.populate_qss_styles()

    def populate_qss_styles(self):
        self.style_menu.clear()
        for qss_style in glob(os.path.join(utils.RESOURCES_PATH, self.QSS_GLOB)):
            file_name = os.path.basename(qss_style)
            style_name = os.path.splitext(file_name)[0]
            menu_action = self.style_menu.addAction(style_name.capitalize())
            menu_action.triggered.connect(partial(self.load_stylesheet, stylesheet=file_name))

    def setup(self):
        self.create_controls()
        self.initialize_controls()
        self.connect_controls()

    def create_controls(self):
        main_widget = self
        if isinstance(self, QtWidgets.QMainWindow):
            self.setCentralWidget(QtWidgets.QWidget())
            main_widget = self.centralWidget()
        self.layout_main = QtWidgets.QVBoxLayout(main_widget)

        self.menu_bar = QtWidgets.QMenuBar()

        self.wgt_header = QtWidgets.QWidget()
        self.wgt_files = QtWidgets.QFrame()
        self.wgt_stack = QtWidgets.QStackedWidget()

        self.header_layout = QtWidgets.QHBoxLayout()
        self.header_label = QtWidgets.QLabel()
        self.files_layout = QtWidgets.QHBoxLayout()

        self.instance_handler = instance_handler.InstanceHandlerWidget()
        self.filesystem_view = filesystem.FileSystemWidget()
        self.drag_drop_view = drag_drop.DragDropWidget()
        self.file_list_view = file_list.FileListWidget()

    def connect_controls(self):
        self.setLayout(self.layout_main)

        self.wgt_header.setLayout(self.header_layout)
        self.header_layout.addWidget(self.header_label)

        self.layout_main.addWidget(self.menu_bar)
        self.layout_main.addWidget(self.wgt_header)
        self.layout_main.addWidget(self.instance_handler)
        self.layout_main.addWidget(self.wgt_files)

        self.wgt_stack.addWidget(self.drag_drop_view)
        self.wgt_stack.addWidget(self.filesystem_view)

        self.wgt_files.setLayout(self.files_layout)
        self.files_layout.addWidget(self.file_list_view, 1)
        self.files_layout.addWidget(self.wgt_stack)

        self.drag_drop_view.dropped.connect(self.file_list_view.update_file_paths)
        self.filesystem_view.send_files.connect(self.file_list_view.update_file_paths)

    def initialize_controls(self):
        self.setFocus(QtCore.Qt.PopupFocusReason)
        self.load_stylesheet(stylesheet=self.MAIN_QSS)
        self.setWindowTitle(self.NAME)
        self.setObjectName('MainFrame')
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setAcceptDrops(True)

        self.wgt_header.setObjectName('HeaderWidget')
        self.header_label.setObjectName('HeaderLabel')

        self.header_label.setText(self.NAME.upper())
        self.layout_main.setContentsMargins(0, 0, 0, 0)
        self.layout_main.setSpacing(0)
        self.setBaseSize(self.WIDTH, self.HEIGHT)
        self.layout_main.setAlignment(QtCore.Qt.AlignTop)

    def get_stylesheet_qss(self, stylesheet):
        file_path = os.path.join(utils.RESOURCES_PATH, stylesheet)
        stylesheet_file = os.path.normpath(file_path)
        return open(stylesheet_file).read() if os.path.isfile(stylesheet_file) else ''

    def load_stylesheet(self, btn_event=None, stylesheet=''):
        qss_data = self.get_stylesheet_qss(stylesheet=stylesheet) + self.default_stylesheet
        self.LOG.info('Attempting to load CSS from file %s (appended default CSS).' % stylesheet)
        if not qss_data:
            self.LOG.warning('Invalid stylesheet file specified %s...defaulting to none' % stylesheet)
        self.setStyleSheet(qss_data)
        return qss_data

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
            self.wgt_stack.setCurrentIndex(0)
        else:
            event.ignore()

    def eventFilter(self, source, event):
        if event.type() == QtCore.QEvent.KeyPress:
            if event.key() in [QtCore.Qt.Key_Tab, QtCore.Qt.Key_Backtab]:
                if self.focused_widget.parent() in self.instance_handler.token_widgets:
                    if self.instance_handler.select_next_token_line_edit(event.key() == QtCore.Qt.Key_Backtab):
                        return True

        if event.type() == QtCore.QEvent.Close:
            self.LOG.debug('Close event %s detected from widget %s with parent %s' % (event, source, source.parent()))

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

    def closeEvent(self, e):
        self.LOG.debug('Widget %s has focus during escape press' % self.focused_widget)
        if not issubclass(type(self.focused_widget), QtWidgets.QLineEdit):
            self.LOG.info('Escape pressed and not within a QLineEdit, exiting.')
            QtWidgets.QApplication.instance().removeEventFilter(self)
            self.deleteLater()
            return exit()
