import os
import os.path as op
import sys
import time
import gzip

from lxml import etree
from parse import compile as fcompile

from harvest_ocr import attempt_download, download_core
from common import ARTICLE_FORMAT, METADATA_FORMAT, NEWSPAPER_FORMAT

MISSING_FNAME = 'missing.txt'
OCR_XPATH = "//didl:Resource[@dcx:filename='{}']"

parse_article = fcompile(ARTICLE_FORMAT)


def main(argv):
    """ Work through the missing articles until there are no more, round-robin.

        Update the file of missing articles after every cycle, and in case of an
        exception.
    """
    root = op.abspath(argv[1])
    assert os.access(root, os.R_OK | os.W_OK), 'Path not read/writeable.'
    missing_path = op.join(root, MISSING_FNAME)
    with open(missing_path) as missing_file:
        missing = missing_file.readlines()
    try_again = []
    try:
        while len(missing):
            # After every cycle through the list, update the file.
            process_list(root, missing, try_again)
            missing, try_again = try_again, missing
            with open(missing_path, 'w') as missing_file:
                missing_file.writelines(missing)
    except:
        with open(missing_path, 'w') as missing_file:
            missing_file.writelines(missing)
            missing_file.writelines(try_again)
        raise


def process_list(root, before, after):
    """ Try to download articles in `before`, put failures in `after`.

        Modifies `before` and `after` in-place to preserve information in case
        of an exception.
    """
    current_id = None
    while len(before):
        success = False
        item = before.pop(0).split()  # pop from the front
        if len(item) == 3:
            # we already have all information, no need to dig into XML
            fname, checksum, url = item
            tried_before = True
        else:
            fname = item[0]
            tried_before = False
        paper_id, article_serial = parse_article(fname)
        id_tail = paper_id[-2:]
        paper_dir = NEWSPAPER_FORMAT.format(paper_id)
        paper_symlink = op.join(root, id_tail, paper_dir)
        if paper_id == current_id and not extracted or not op.exists(paper_symlink):
            extracted = False
        else:
            extracted = True
        current_id = paper_id
        paper_path = op.realpath(paper_symlink)
        article_path = op.join(paper_path, fname)
        try:
            if tried_before:
                download_core(article_path, checksum, url)
                success = True
            elif extracted:
                attempt_download
