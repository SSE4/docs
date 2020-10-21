"""Sphinx ReadTheDocs theme.

From https://github.com/ryan-roemer/sphinx-bootstrap-theme.

"""

import os
import xml.etree.ElementTree as ET

__version__ = '0.2.0'
__version_full__ = __version__


def setup(app):
    pass

def get_html_theme_path():
    """Return list of HTML theme paths."""
    cur_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    return [cur_dir]
