import os
import os.path as op
import sys
import time
import gzip

from lxml import etree
from parse import compile as fcompile

from harvest_ocr import attempt_download, download_core, extract_gzipped_xml
from common import ARTICLE_FORMAT, METADATA_FORMAT, NEWSPAPER_FORMAT

MISSING_FNAME = 'missing.txt'
OCR_XPATH = "//didl:Resource[@dcx:filename='{}']"
GRACE_TIME = 1  # second

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
    while len(before):
        item = before.pop(0).split()  # pop from the front
        print('item:', item)
        tried_before = (len(item) == 3)  # checksum and url already known
        fname = item[0]
        paper_id, article_serial = parse_article(fname)
        print('paper_id:', paper_id)
        id_tail = paper_id[-2:]
        paper_dir = NEWSPAPER_FORMAT.format(paper_id)
        print('paper_dir:', paper_dir)
        paper_symlink = op.join(root, id_tail, paper_dir)
        print('paper_symlink:', paper_symlink)
        success = False
        if tried_before or op.exists(paper_symlink):
            success = process_item(paper_symlink, fname, item)
        else:
            print('Skipping because symlink does not exist yet.')
        if not success:
            after.append(' '.join(item) + '\n')
        # time.sleep(GRACE_TIME)  # give circumstances time to improve
        input('Press enter to continue.')


def process_item(paper_symlink, fname, item):
    """ Try to download a single article.

        Modifies `item` in place if checksum, url are missing and found.
        Returns success: boolean.
    """
    paper_path = op.realpath(paper_symlink)
    print('paper_path:', paper_path)
    article_path = op.join(paper_path, fname)
    print('article_path:', article_path)
    try:
        if len(item) == 3:
            input('Go straight to download_core?')
            _, checksum, url = item
            download_core(article_path, checksum, url)
        else:
            paper_id, article_serial = parse_article(fname)
            metadata = METADATA_FORMAT.format(paper_id)
            print('metadata:', metadata)
            xml, ns = extract_gzipped_xml(op.join(paper_path, metadata))
            resource = xml.xpath(OCR_XPATH, namespaces=ns)[0]
            print('resource:', resource)
            input('Continue to attempt_download?')
            checksum, url = attempt_download(resource, ns, article_path)
            item += [checksum, url]
        return True
    except:
        return False
