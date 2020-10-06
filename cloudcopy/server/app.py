import os

from .api.loader import load
from .api.core import api

from cloudcopy.server.config import settings
# loads FastAPI endpoints from .api...
load()

# initialization procedures
# TODO: move to module
os.makedirs(settings.BASE_PATH, exist_ok=True)
os.makedirs(settings.LOG_PATH, exist_ok=True)

# expose the FastAPI instance as cloudcopy.server.app:app for convenience
app = api
