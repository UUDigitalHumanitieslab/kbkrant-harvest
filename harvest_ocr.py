import os
import os.path as op
import sys
import time
import traceback
import gzip
import tarfile
from hashlib import md5

from lxml import etree
import requests

from common import MANIFEST_DIR, TARBALL_FORMAT, PROGRESS_DIR

FINISHED_DIR = 'ocr_complete'
OCR_XPATH = "//didl:Resource[../didl:Descriptor/didl:Statement/text()='ocr']"
ERROR_LOG = 'failures.log'
TIMEOUT = 1 # second
RETRY_INTERVAL = 0.25 # second
MAX_RETRIES = 5


def main(argv):
    """ Process manifest files until there are no more.

        Takes one positional argument: the harvesting root directory.
        Depends on organize.py being run periodically as a cron job.
        You can stop this process by emptying the manifests directory.
    """
    root = op.abspath(argv[1])
    assert os.access(root, os.R_OK | os.W_OK), 'Path not read/writeable.'
    todo, progress, finished = get_directories(root)
    todo_list = os.listdir(todo)
    while len(todo_list):
        # We ask for a list but use only the first. This makes us robust
        # against filesystem changes in the meanwhile.
        manifest = todo_list[0]
        source = op.join(todo, manifest)
        workon = op.join(progress, manifest)
        done = op.join(finished, manifest)
        os.rename(source, workon)
        process_manifest(workon)
        os.rename(workon, done)
        todo_list = os.listdir(todo)


def get_directories(root):
    """ Provides the lifecycle directories for the manifests. """
    todo = op.join(root, MANIFEST_DIR)
    progress = op.join(root, PROGRESS_DIR)
    finished = op.join(root, FINISHED_DIR)
    result = (todo, progress, finished)
    for directory in result:
        os.makedirs(directory, exist_ok=True)
    return result


def process_manifest(manifest):
    """ Process all newspapers in a manifest. """
    # A single call to this function may take a whole day.
    with open(manifest) as open_file:
        lines = open_file.read().splitlines()
    for path in lines:
        subdir, newspaper = op.split(path)
        harvested = process_newspaper(subdir, newspaper)
        serial = newspaper.split(':')[2]
        tarball_path = op.join(subdir, TARBALL_FORMAT.format(serial))
        with tarfile.open(tarball_path, 'w:gz') as tarball:
            tarball.add(path, arcname=newspaper)
            for fullpath, article in harvested:
                tarball.add(fullpath, arcname=article)
        os.remove(path)
        for fullpath, article in harvested:
            os.remove(fullpath)
        print(tarball_path) # useful in case of an exception


def process_newspaper(subdir, newspaper):
    """ Harvest OCR from all articles in newspaper and return their paths. """
    with gzip.open(op.join(subdir, newspaper), 'rb') as archive:
        xml = etree.parse(archive)
    ns = xml.getroot().nsmap.copy()
    ns.pop(None, None) # duplicate of xmlns:didl (default namespace)
    resources = xml.xpath(OCR_XPATH, namespaces=ns)
    harvest = []
    for node in resources:
        result = fetch_ocr(node, ns, subdir)
        if result is not None:
            harvest.append(result)
    return harvest


def fetch_ocr(resource, ns, subdir):
    """ Try hard to get the article OCR. Return path on success, else None. """
    target_fname = 'undetermined'
    for retry_count in range(MAX_RETRIES):
        if retry_count > 0:
            time.sleep(RETRY_INTERVAL)
        try:
            target_fname = resource.xpath('@dcx:filename', namespaces=ns)[0]
            checksum = resource.xpath('@dcx:md5_checksum', namespaces=ns)[0]
            url = resource.get('ref')
            response = requests.get(url, timeout=TIMEOUT)
            response.raise_for_status()
            if checksum:
                hasher = md5()
                hasher.update(response.content)
                assert hasher.hexdigest() == checksum
            target_path = op.join(subdir, target_fname)
            with open(target_path, 'wb') as outfile:
                outfile.write(response.content)
            return target_path, target_fname
        except:
            trace = traceback.format_exc()
    with open(op.join(subdir, ERROR_LOG), 'a') as error_log:
        print(target_fname, file=error_log)
        print(trace, file=error_log)
        print(file=error_log)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
