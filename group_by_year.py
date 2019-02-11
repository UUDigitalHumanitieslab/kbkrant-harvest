import os
import os.path as op
import sys
import re
import gzip
import tarfile
import logging

from lxml import etree
from parse import compile as fcompile

from common import PROGRESS_DIR, TARBALL_FORMAT

ID_DIR_PATTERN = re.compile(r'^\d{2}$')
DATE_XPATH = '//srw_dc:dcx/dc:date/text()'
DATE_PATTERN = re.compile(r'(\d{4})-(\d{2}-\d{2})')
LOG_BASENAME = 'group_by_year_errors.log'
METADATA_FORMAT = 'DDD:ddd:{}:mpeg21.didl.xml.gz'

tarball_parser = fcompile(TARBALL_FORMAT)


def main(argv):
    """ Group the newspapers by year and date.

        Takes one positional argument: the harvesting root directory.
        Depends on the directory structure from organize.py, containing
        the tarballs from harvest_ocr.py.
    """
    root = op.abspath(argv[1])
    assert os.access(root, os.R_OK | os.W_OK), 'Path not read/writeable.'
    logging.basicConfig(filename=op.join(root, LOG_BASENAME))
    for path, subdirs, filenames in os.walk(root):
        # This script will create symlinks to directories. os.walk does
        # not follow symlinks into directories by default, so it is safe
        # to restart this script if it crashed halfway.
        if path == root:
            continue
        # recurse only one level
        subdirs.clear()
        if ID_DIR_PATTERN.match(op.basename(path)):
            reorganize_directory(path, filenames, root)


def reorganize_directory(dir, filenames, root):
    """ Expand and order all newspapers in `dir` by date. """
    for name in filenames:
        match = tarball_parser.parse(name)
        if match:  # this is a newspaper tarball
            (paper_id,) = match.fixed
            reorganize_newspaper(dir, name, paper_id, root)


def reorganize_newspaper(dir, tarball_name, paper_id, root):
    """ Expand tarball, extract paper date, order by date, leave symlink. """
    tarball_path = op.join(dir, tarball_name)
    paper_name, _ = op.splitext(tarball_name)
    progress = op.join(root, PROGRESS_DIR, paper_name)
    metadata_path = op.join(progress, METADATA_FORMAT.format(paper_id))
    try:
        os.mkdir(progress)
        with tarfile.open(tarball_path) as tarball:
            tarball.extractall(progress)
        with gzip.open(metadata_path, 'rb') as metadata:
            xml = etree.parse(metadata)
        ns = xml.getroot().nsmap.copy()
        ns.pop(None, None) # duplicate of xmlns:didl (default namespace)
        date_string = xml.xpath(DATE_XPATH, namespaces=ns)[0]
        year, date = DATE_PATTERN.match(date_string).groups()
        target_dir = op.join(root, year, date)
        os.makedirs(target_dir, exist_ok=True)
        os.rename(progress, op.join(target_dir, paper_name))
    except:
        # Do nothing else, we rather have two copies than zero.
        logging.exception('Error when trying to reorganize %s', paper_name)
        sys.exit(1)
    else:
        # Also stop for now, let's just first check that this works for a single
        # newspaper.
        sys.exit(0)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
