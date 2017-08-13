from nomenclate.ui.main import MainDialog
import nomenclate.ui.platforms as platforms

WINDOW_INSTANCE = None


def create():
    global WINDOW_INSTANCE
    try:
        WINDOW_INSTANCE.show()
    except (AttributeError, RuntimeError):
        WINDOW_INSTANCE = MainDialog()

    platforms.current.show(WINDOW_INSTANCE)
    return WINDOW_INSTANCE


def delete():
    global WINDOW_INSTANCE
    if WINDOW_INSTANCE is None:
        return
    WINDOW_INSTANCE.deleteLater()
    WINDOW_INSTANCE = None


if __name__ == '__main__':
    create()
