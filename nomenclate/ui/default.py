from PyQt5 import QtWidgets


class DefaultWidget(QtWidgets.QFrame):
    TITLE = 'Default Widget'
    TOP = 10
    LEFT = 10
    WIDTH = 640
    HEIGHT = 480

    def __init__(self):
        super(DefaultWidget, self).__init__()
        self.title = self.TITLE
        self.setup()

    def setup(self):
        self.create_controls()
        self.initialize_controls()
        self.connect_controls()

    def create_controls(self):
        raise NotImplementedError

    def initialize_controls(self):
        raise NotImplementedError

    def connect_controls(self):
        raise NotImplementedError
