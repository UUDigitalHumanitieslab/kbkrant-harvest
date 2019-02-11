import os
import os.path as op
import sys
import re
import gzip
import tarfile

from lxml import etree

from common import PROGRESS_DIR

ID_DIR_PATTERN = re.compile(r'^\d{2}$')
DATE_XPATH = '//srw_dc:dcx/dc:date/text()'
DATE_PATTERN = re.compile(r'(\d{4})-(\d{2}-\d{2})')


def main(argv):
    """ Group the newspapers by year and date.

        Takes one positional argument: the harvesting root directory.
        Depends on the directory structure from organize.py, containing
        the tarballs from harvest_ocr.py.
    """
    root = op.abspath(argv[1])
    assert os.access(root, os.R_OK | os.W_OK), 'Path not read/writeable.'
    progress = op.join(root, PROGRESS_DIR)
    for path, subdirs, filenames in os.walk(root):
        # This script will create symlinks to directories. os.walk does
        # not follow symlinks into directories by default, so it is safe
        # to restart this script if it crashed halfway.
        if path == root:
            continue
        # recurse only one level
        subdirs.clear()
        if ID_DIR_PATTERN.match(op.basename(path)):
            reorganize_directory(path, filenames, root, progress)
