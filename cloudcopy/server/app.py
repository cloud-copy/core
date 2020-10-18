import os

from .api.loader import load as load_endpoints
from .tasks.loader import load as load_tasks
from .setup import setup_environment
from .api.core import api
from .tasks.core import app as tasks

from cloudcopy.server.config import settings

# loads FastAPI endpoints
load_endpoints()
# loads Huey tasks
load_tasks()
# create required directory
setup_environment()
