import os
from cloudcopy.common.utils import Settings

INTERNAL_DATABASE_PATH = os.environ.get(
    'CLCP_INTERNAL_DATABASE_PATH', os.path.expanduser('~/.clcp.sqlite3')
)

# all upper-case values in this file are added to a settings object
# this object can be mocked in tests
settings = Settings({
    k: v for k, v in locals().items() if k == k.upper()
})
