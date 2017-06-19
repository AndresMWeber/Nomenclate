#!/usr/bin/python

if __name__ == '__main__':
    import sys
    import os

    # Add the top directory into sys.path
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    import nomenclate.ui.run as run

    run.create()
