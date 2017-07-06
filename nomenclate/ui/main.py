import os
from glob import glob
from functools import partial
from PyQt5 import QtWidgets, QtCore, QtGui
import nomenclate.settings as settings
import nomenclate.ui.filesystem as filesystem
import nomenclate.ui.instance_handler as instance_handler
import nomenclate.ui.drag_drop as drag_drop
import nomenclate.ui.file_list as file_list

MODULE_LOGGER_LEVEL_OVERRIDE = settings.QUIET


class MainDialog(QtWidgets.QWidget):
    NAME = 'Nomenclate'
    LOG = settings.get_module_logger(__name__, module_override_level=MODULE_LOGGER_LEVEL_OVERRIDE)
    WIDTH = 800
    HEIGHT = 600

    def __init__(self):
        super(MainDialog, self).__init__()
        self.default_css_cache = None
        self.add_fonts()
        self.keylist = []
        self.setup()
        self.setup_menubar()
        QtWidgets.QApplication.instance().installEventFilter(self)

    @property
    def default_stylesheet(self):
        if not self.default_css_cache:
            self.default_css_cache = self.get_stylesheet_qss('default.qss')
        return self.default_css_cache

    def setup_menubar(self):
        self.file_menu = self.menu_bar.addMenu('File')
        self.edit_menu = self.menu_bar.addMenu('Edit')
        self.settings_menu = self.menu_bar.addMenu('Settings')
        exit_action = self.file_menu.addAction('Exit')
        exit_action.triggered.connect(self.close)
        redo_action = self.edit_menu.addAction('Redo')
        # redo_action.triggered.connect()

        style_menu = self.settings_menu.addMenu('Set Style')
        for qss_style in glob(os.path.join(os.path.dirname(__file__), 'resource', '*.qss')):
            file_name = os.path.basename(qss_style)
            style_name = os.path.splitext(file_name)[0]
            menu_action = style_menu.addAction(style_name.capitalize())
            menu_action.triggered.connect(partial(self.load_stylesheet, stylesheet=file_name))

    def setup(self):
        self.create_controls()
        self.initialize_controls()
        self.connect_controls()

    def create_controls(self):
        self.layout_main = QtWidgets.QVBoxLayout()

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
        self.setObjectName('MainFrame')
        self.setWindowFlags(QtCore.Qt.Tool)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setAcceptDrops(True)
        self.setWindowTitle(self.NAME)
        self.setFocusPolicy(QtCore.Qt.NoFocus)

        self.wgt_header.setObjectName('HeaderWidget')
        self.header_label.setObjectName('HeaderLabel')
        self.header_label.setText(self.NAME.upper())
        self.layout_main.setContentsMargins(0, 0, 0, 0)
        self.layout_main.setSpacing(0)
        self.setBaseSize(self.WIDTH, self.HEIGHT)
        self.layout_main.setAlignment(QtCore.Qt.AlignTop)
        self.load_stylesheet()

    def get_stylesheet_qss(self, stylesheet):
        file_path = os.path.join(os.path.dirname(__file__), 'resource', stylesheet)
        stylesheet_file = os.path.normpath(file_path)
        return open(stylesheet_file).read() if os.path.isfile(stylesheet_file) else ''

    def load_stylesheet(self, btn_event=None, stylesheet='darkseas.qss'):
        qss_data = self.get_stylesheet_qss(stylesheet=stylesheet) + self.default_stylesheet
        self.LOG.info('Attemping to load CSS from file %s (appended default CSS).' % stylesheet)
        self.LOG.debug('CSS data:\n%s' % qss_data)
        if not qss_data:
            self.LOG.warning('Invalid stylesheet file specified %s...defaulting to none' % stylesheet)
        self.setStyleSheet(qss_data)
        return qss_data

    def add_fonts(self):
        font_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'resource', 'fonts')
        for font_file in os.listdir(font_dir):
            QtGui.QFontDatabase.addApplicationFont(os.path.join(font_dir, font_file))

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
                if QtWidgets.QApplication.focusWidget().parent() in self.instance_handler.token_widgets:
                    if self.instance_handler.select_next_token_line_edit(event.key() == QtCore.Qt.Key_Backtab):
                        return True

            if event.key() == QtCore.Qt.Key_Escape:
                self.close()

        if event.type() == QtCore.QEvent.MouseButtonPress:
            self.LOG.debug('Widgets under cursor: %s' % ' -> '.join(reversed(widgets_at(QtGui.QCursor.pos()))))
            return False

        return super(MainDialog, self).eventFilter(source, event)

    def closeEvent(self, e):
        QtWidgets.QApplication.instance().removeEventFilter(self)
        super(MainDialog, self).closeEvent(e)
        return exit()


def widgets_at(pos):
    """ Debugging function for getting all widgets at cursor position
    :arg pos: QtCore.QPoint, Position at which to get widgets
    :return: list(QtWidgets.QWidget), all widgets at mouse cursor
    """
    widgets = []
    widgets.append(QtWidgets.QApplication.widgetAt(pos))

    # Restore attribute
    for index, widget in enumerate(widgets):
        widget_name = widget.objectName()
        widget = widget if 'qt_scrollarea_viewport' != widget_name else widget.parent()
        widgets[index] = str(widget).split('.')[-1].split(' ')[0]
    return widgets
