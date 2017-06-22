import os
from PyQt5 import QtWidgets, QtCore, QtGui
import nomenclate.settings as settings
import nomenclate.ui.filesystem as filesystem
import nomenclate.ui.instance_handler as instance_handler
import nomenclate.ui.drag_drop as drag_drop
import nomenclate.ui.file_list as file_list

MODULE_LOGGER_LEVEL_OVERRIDE = None


class MainDialog(QtWidgets.QDialog):
    NAME = 'Nomenclate'
    LOG = settings.get_module_logger(__name__, module_override_level=MODULE_LOGGER_LEVEL_OVERRIDE)
    WIDTH = 800
    HEIGHT = 600

    def __init__(self):
        super(MainDialog, self).__init__()
        self.add_fonts()
        self.setup()

    def setup(self):
        self.create_controls()
        self.initialize_controls()
        self.connect_controls()

    def create_controls(self):
        self.layout_main = QtWidgets.QVBoxLayout()

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

    def initialize_controls(self):
        self.setAcceptDrops(True)
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.setWindowTitle(self.NAME)
        self.setObjectName('MainFrame')
        self.wgt_header.setObjectName('HeaderWidget')
        self.header_label.setObjectName('HeaderLabel')
        self.header_label.setText(self.NAME.upper())
        self.layout_main.setContentsMargins(0, 0, 0, 0)
        self.layout_main.setSpacing(0)
        self.setBaseSize(self.WIDTH, self.HEIGHT)
        self.layout_main.setAlignment(QtCore.Qt.AlignTop)
        self.load_stylesheet()

    def load_stylesheet(self, btn_event=None, stylesheet='style.qss'):
        stylesheet_file = os.path.normpath(os.path.abspath('.\\resource\\%s' % stylesheet))
        qss_data = open(stylesheet_file).read()
        self.setStyleSheet(qss_data)

    def connect_controls(self):
        self.setLayout(self.layout_main)
        self.wgt_header.setLayout(self.header_layout)
        self.header_layout.addWidget(self.header_label)

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

    def add_fonts(self):
        font_dir = os.path.join(os.path.abspath('.'), 'resource', 'fonts')
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
