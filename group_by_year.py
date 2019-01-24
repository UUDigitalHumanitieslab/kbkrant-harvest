import os
import os.path as op
import sys
import re
import gzip
import tarfile

from lxml import etree

from common import MANIFEST_DIR, TARBALL_FORMAT, PROGRESS_DIR

DATE_XPATH = '//srw_dc:dcx/dc:date/text()'
DATE_PATTERN = re.compile(r'(\d{4})-(\d{2})-(\d{2})')
