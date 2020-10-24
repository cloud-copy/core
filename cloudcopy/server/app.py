import os

from .api.loader import load as load_endpoints
from .tasks.loader import load as load_tasks
from .setup import setup_environment
from .api import server
from .tasks import worker

from cloudcopy.server.config import settings

# loads FastAPI endpoints
load_endpoints()
# loads Huey tasks
load_tasks()
# create required directory
setup_environment()
