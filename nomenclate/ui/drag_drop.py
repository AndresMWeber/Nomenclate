from .default import DefaultWidget
import os
from PyQt5 import QtCore, QtWidgets, QtGui


class DragDropItemModel(QtGui.QStandardItemModel):
    def appendRow(self, *__args):
        for arg in __args:
            if type(arg) == QtGui.QStandardItem:
                items = [self.itemFromIndex(self.index(row_index, 0)) for row_index in range(self.rowCount())]
                if any([arg.text() == row_item.text() for row_item in items]):
                    return
        super(DragDropItemModel, self).appendRow(*__args)


class DragDropWidget(DefaultWidget):
    TITLE = 'Drag and Drop'
    dropped = QtCore.pyqtSignal(list)
    browse = QtCore.pyqtSignal()

    def create_controls(self):
        self.layout_main = QtWidgets.QVBoxLayout()
        self.btn_browse = QtWidgets.QPushButton('Browse...')
        self.text = QtWidgets.QLabel('Drag and Drop Files\nOr Click to Browse')
        self.label = QtWidgets.QLabel()
        self.pixmap = QtGui.QPixmap(os.path.normpath(os.path.abspath('.\\resource\\drag-and-drop-icon.png')))

    def initialize_controls(self):
        self.setAcceptDrops(True)
        self.setFixedSize(320, 320)
        self.label.setFixedSize(250, 250)
        self.label.setObjectName('DragLabel')

    def connect_controls(self):
        self.setLayout(self.layout_main)
        self.label.setPixmap(self.pixmap.scaled(self.label.size(), QtCore.Qt.KeepAspectRatio))
        self.layout_main.addWidget(self.label, 0, QtCore.Qt.AlignCenter)
        self.layout_main.addWidget(self.text, 0, QtCore.Qt.AlignCenter)
        self.layout_main.addWidget(self.btn_browse, 0, QtCore.Qt.AlignCenter)

        self.btn_browse.clicked.connect(self.browser)

    def browser(self):
        print('browsing')

    def resizeEvent(self, QResizeEvent):
        self.label.setPixmap(self.pixmap.scaled(self.label.size(), QtCore.Qt.KeepAspectRatio))

    def sort_model(self):
        self.list_model.sort(QtCore.Qt.AscendingOrder)

    def clear_model(self):
        self.list_model.clear()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls:
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls:
            event.setDropAction(QtCore.Qt.CopyAction)
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasUrls:
            event.setDropAction(QtCore.Qt.CopyAction)
            event.accept()
            self.dropped.emit([str(url.toLocalFile()) for url in event.mimeData().urls()])
        else:
            event.ignore()

    def focusOutEvent(self, *args, **kwargs):
        super(DragDropWidget, self).focusOutEvent(*args, **kwargs)
        self.clear_model()
