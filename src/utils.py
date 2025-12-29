# "Weici_Zhao_qan6vg"
import os
import sys


def resource_path(relative_path):
    """专门打包用的"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

