import os
from cloudcopy.common.utils import Settings

# INTERNAL_DATABASE_FILE: path to server's SQLite file
# TODO: support cloud database
INTERNAL_DATABASE_FILE = os.environ.get(
    'CLCP_INTERNAL_DATABASE_FILE', os.path.expanduser('~/.clcp.sqlite3')
)
INTERNAL_DATABASE_URL = f'file:{INTERNAL_DATABASE_FILE}'

# LOG_FILE: path to server's log file
# TODO: support cloud logging
LOG_FILE = os.environ.get(
    'CLCP_LOG_FILE', os.path.expanduser('~/.clcp.log')
)

# all upper-case values in this file are added to a settings object
# this object can be mocked in tests
settings = Settings({
    k: v for k, v in locals().items() if k == k.upper()
})
