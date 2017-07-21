import PyQt5.QtWidgets as QtWidgets

SET = 'SET'
GET = 'GET'


class WidgetState(object):
    WIDGETS = {
        QtWidgets.QComboBox: {GET: QtWidgets.QComboBox.currentIndex,
                              SET: QtWidgets.QComboBox.setCurrentIndex},

        QtWidgets.QLineEdit: {GET: QtWidgets.QLineEdit.text,
                              SET: QtWidgets.QLineEdit.setText},

        QtWidgets.QCheckBox: {GET: QtWidgets.QCheckBox.checkState,
                              SET: QtWidgets.QCheckBox.setCheckState},

        QtWidgets.QSpinBox: {GET: QtWidgets.QSpinBox.value,
                             SET: QtWidgets.QSpinBox.setValue},

        QtWidgets.QTimeEdit: {GET: QtWidgets.QTimeEdit.setTime,
                              SET: QtWidgets.QTimeEdit.time},

        QtWidgets.QDateEdit: {GET: QtWidgets.QDateEdit.date,
                              SET: QtWidgets.QDateEdit.setDate},

        QtWidgets.QDateTimeEdit: {GET: QtWidgets.QDateTimeEdit.dateTime,
                                  SET: QtWidgets.QDateTimeEdit.setDateTime},

        QtWidgets.QRadioButton: {GET: QtWidgets.QRadioButton.isChecked,
                                 SET: QtWidgets.QRadioButton.checkStateSet},

        QtWidgets.QSlider: {GET: QtWidgets.QSlider.value,
                            SET: QtWidgets.QSlider.setValue},
    }

    @property
    def supported_widget_types(self):
        return list(self.WIDGETS)

    @staticmethod
    def get_ui_members(ui):
        return get_all_widget_children(ui)
        # Shitty web-found implementation that only gets immediate children:
        # return inspect.getmembers(ui, lambda a: not (inspect.isroutine(a)))

    @classmethod
    def get_widget_method(cls, widget_type, type):
        if not widget_type in list(cls.WIDGETS):
            for supported_widget_type in list(cls.WIDGETS):
                if issubclass(widget_type, supported_widget_type):
                    #print 'detected subclassed object %s of supported type %s' % (widget_type, supported_widget_type)
                    widget_type = supported_widget_type
        return cls.WIDGETS.get(widget_type).get(type)

    @classmethod
    def serialize_widget_settings(cls, widget):
        return cls.get_widget_method(type(widget), GET)(widget)

    @classmethod
    def deserialize_widget_settings(cls, widget, settings):
        return cls.get_widget_method(widget, SET)(widget, settings[widget.objectName()])

    @classmethod
    def generate_state(cls, ui):
        """ save "ui" controls and values to registry "setting"
        """
        settings = {}
        unhandled_types = []
        for widget in cls.get_ui_members(ui):
            try:
                settings[cls.get_widget_path(widget)] = cls.serialize_widget_settings(widget)
            except AttributeError:
                unhandled_types.append(type(widget))
        #pprint(list(set(unhandled_types)))
        return settings

    def get_ui_custom_attributes(self):
        pass
        # import inspect
        # inspect.getmembers(MyClass, lambda a: not (inspect.isroutine(a)))

    @classmethod
    def restore_state(cls, ui, settings):
        """ restore "ui" controls with values stored in registry "settings"
        """
        for name, widget in cls.get_ui_members(ui):
            try:
                cls.deserialize_widget_settings(widget)
            except IndexError:
                pass

    @classmethod
    def get_widget_path(cls, qwidget):
        widget_path = cls.get_widget_name(qwidget)
        while qwidget.parent():
            widget_path = cls.get_widget_name(qwidget.parent()) + ' -> ' + widget_path
            qwidget = qwidget.parent()
        return widget_path

    @staticmethod
    def get_widget_name(widget):
        object_name = '#' + widget.objectName() if widget.objectName() else ''
        return str(type(widget)) + object_name


def get_all_widget_children(widget, path=None):
    if path is None:
        path = []
    path.append(widget)

    if widget.children():
        for child in widget.children():
            get_all_widget_children(child, path)
    else:
        pass
    return path