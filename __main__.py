#!/usr/bin/python

if __name__ == '__main__':
    import sys
    import nomenclate
    reload(nomenclate)
    from nomenclate import app
    sys.exit(app.run())
