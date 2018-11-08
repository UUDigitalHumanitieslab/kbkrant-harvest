""" Post-harvest metadata organizer.

    This script gzips the metadata files and distributes them over
    directories in order to avoid filesystem issues. It is also the
    connecting step between the metadata harvest and the OCR harvest:
    the generated manifest files are fed into the OCR harvester.
"""

import os
import os.path as op
import sys
import datetime as dt
import gzip
import shutil

MANIFEST_DIR = 'manifests'
NOW = dt.datetime.now()
ONE_SECOND = dt.timedelta(seconds=1)


def main(argv):
    """ Distribute and gzip *.didl.xml files in the given directory.

        Takes one positional parameter: the path to the primary
        harvesting directory.
    """
    root = op.abspath(argv[1])
    assert os.access(root, os.R_OK | os.W_OK), 'Path not read/writeable.'
    manifest, m_initial_path, m_final_path = get_manifest(root)
    try:
        for filename in os.listdir(root):
            filename = op.join(root, filename)
            if not filename.endswith('.didl.xml') or is_young(filename):
                continue
            print(organize(filename), file=manifest)
    finally:
        manifest.close()
        os.rename(m_initial_path, m_final_path)


def get_manifest(root):
    """ Provide manifest file with initial and final filesystem paths. """
    manifest_dir = op.join(root, MANIFEST_DIR)
    os.makedirs(manifest_dir, exist_ok=True) # create if not exists
    filename = NOW.strftime('%Y%m%d_%H%M%S.%f.txt')
    initial_path = op.join(root, filename)
    final_path = op.join(manifest_dir, filename)
    manifest = open(initial_path, 'w', buffering=1) # line buffering
    return manifest, initial_path, final_path


def is_young(path):
    """ Return True if `path` was accessed less than a second ago. """
    access_date = dt.datetime.fromtimestamp(op.getatime(path))
    age = NOW - access_date
    return (age < ONE_SECOND)


def organize(source_path):
    """ Gzip `source_path` and move it into a subdirectory.

        Returns the destination path.
    """
    root, name = op.split(source_path)
    serial = name.split(':')[2]
    subdir = op.join(root, serial[-2:])
    os.makedirs(subdir, exist_ok=True) # create if not exists
    destination_path = op.join(subdir, name + '.gz')
    with open(source_path, 'rb') as infile:
        with gzip.open(destination_path, 'wb') as outfile:
            shutil.copyfileobj(infile, outfile)
    os.remove(source_path)
    return destination_path


if __name__ == '__main__':
    sys.exit(main(sys.argv))
