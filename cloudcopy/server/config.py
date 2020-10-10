import os
from cloudcopy.common.utils import Settings, to_boolean

ASYNC_TASKS = to_boolean(
    os.environ.get('ASYNC_TASKS', True)
)

BASE_PATH = os.path.expanduser(
    os.environ.get('CLCP_PATH', '~/.clcp')
)

# INTERNAL_DATABASE_FILE: path to server's SQLite file
# TODO: support cloud database
INTERNAL_DATABASE_FILE = os.environ.get(
    'CLCP_INTERNAL_DATABASE_FILE', os.path.join(BASE_PATH, 'data.db')
)
TASK_DATABASE_FILE = os.environ.get(
    'CLCP_TASK_DATBASE_FILE', os.path.join(BASE_PATH, 'tasks.db')
)

DEBUG = os.environ.get(
    'CLCP_DEBUG', True
)

# LOG_PATH: path to server's log files
# TODO: support cloud logging
LOG_PATH = os.environ.get(
    'CLCP_LOG_PATH', os.path.join(BASE_PATH, 'logs')
)

# all upper-case values in this file are added to a settings object
# this object can be mocked in tests
settings = Settings({
    k: v for k, v in locals().items() if k == k.upper()
})
