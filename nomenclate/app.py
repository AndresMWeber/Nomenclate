#!/usr/bin/python
from core.nomenclature import Nomenclate
import sys

def run():
    arg_dict = {}
    for arg in sys.argv:
        arg_split = arg.split('=')
        if len(arg_split) == 2:
            arg_dict[arg_split[0]] = arg_split[1]
    nom = Nomenclate(arg_dict)
    nom.format = 'working_file'
    return nom.get()
