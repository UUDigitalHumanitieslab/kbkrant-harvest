import os
import os.path as op
import sys
import time

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
        tried_before = (len(item) == 3)  # checksum and url already known
        fname = item[0]
        paper_id, article_serial = parse_article.parse(fname)
        id_tail = paper_id[-2:]
        paper_dir = NEWSPAPER_FORMAT.format(paper_id)
        paper_symlink = op.join(root, id_tail, paper_dir)
        success = False
        if tried_before or op.exists(paper_symlink):
            success = process_item(paper_symlink, fname, item)
        if not success:
            after.append(' '.join(item) + '\n')
        time.sleep(GRACE_TIME)  # give circumstances time to improve


def process_item(paper_symlink, fname, item):
    """ Try to download a single article.

        Modifies `item` in place if checksum, url are missing and found.
        Returns success: boolean.
    """
    paper_path = op.realpath(paper_symlink)
    article_path = op.join(paper_path, fname)
    try:
        if len(item) == 3:
            _, checksum, url = item
            download_core(article_path, checksum, url)
        else:
            paper_id, article_serial = parse_article.parse(fname)
            metadata = METADATA_FORMAT.format(paper_id)
            xml, ns = extract_gzipped_xml(op.join(paper_path, metadata))
            xpath = OCR_XPATH.format(fname)
            resource = xml.xpath(xpath, namespaces=ns)[0]
            checksum, url = attempt_download(resource, ns, article_path)
            item += [checksum, url]
        return True
    except:
        return False


if __name__ == '__main__':
    sys.exit(main(sys.argv))
