""" Wrapper around oaiharvest.harvest that sends pyoai logs to a file.

    Pass the path of the file that should receive the pyoai logs as the
    first argument. The remaining arguments are passed as-is to
    oaiharvest.harvest.main.
"""

import sys
import logging
from logging.handlers import RotatingFileHandler

from oaiharvest.harvest import main

log_path = sys.argv[1]
del sys.argv[1]

handler = RotatingFileHandler(log_path, maxBytes=65536, backupCount=2)
logging.getLogger('oaipmh.client').addHandler(handler)

if __name__ == '__main__':
    sys.exit(main())
