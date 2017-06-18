from PyQt5 import QtWidgets, QtCore
import nomenclate.settings as settings
import nomenclate.ui.filesystem as filesystem
import nomenclate.ui.instance_handler as instance_handler
import nomenclate.ui.drag_drop as drag_drop
import nomenclate.ui.file_list as file_list

MODULE_LOGGER_LEVEL_OVERRIDE = None


class MainDialog(QtWidgets.QDialog):
    NAME = 'Nomenclate'
    LOG = settings.get_module_logger(__name__, module_override_level=MODULE_LOGGER_LEVEL_OVERRIDE)

    def __init__(self):
        super(MainDialog, self).__init__()
        self.setup()

    def setup(self):
        self.create_controls()
        self.initialize_controls()
        self.connect_controls()

    def create_controls(self):
        self.layout_main = QtWidgets.QVBoxLayout()

        self.instance_handler = instance_handler.InstanceHandlerWidget()

        self.wgt_stack = QtWidgets.QStackedWidget()
        self.filesystem_view = filesystem.FileSystemWidget()
        self.drag_drop_view = drag_drop.DragDropWidget()
        self.file_list_view = file_list.FileListWidget()

        self.wgt_btn_incr_stack = QtWidgets.QPushButton('turn page')

    def initialize_controls(self):
        self.setAcceptDrops(True)
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.setWindowTitle(self.NAME)
        # self.setFixedSize(285, 320)

        self.layout_main.setContentsMargins(5, 5, 5, 5)
        self.layout_main.setSpacing(0)
        self.layout_main.setAlignment(QtCore.Qt.AlignTop)

    def connect_controls(self):
        self.setLayout(self.layout_main)

        self.layout_main.addWidget(self.instance_handler)
        self.layout_main.addWidget(self.wgt_stack)
        self.layout_main.addWidget(self.wgt_btn_incr_stack)

        self.wgt_stack.addWidget(self.file_list_view)
        self.wgt_stack.addWidget(self.drag_drop_view)
        self.wgt_stack.addWidget(self.filesystem_view)

        self.wgt_btn_incr_stack.clicked.connect(self.next_stack_frame)
        self.drag_drop_view.dropped.connect(self.main_frame)
        self.drag_drop_view.dropped.connect(self.file_list_view.update_file_paths)
        self.filesystem_view.send_files.connect(self.file_list_view.update_file_paths)

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

    def main_frame(self, *args, **kwargs):
        if self.wgt_stack.currentIndex() != 0:
            self.wgt_stack.setCurrentIndex(0)
