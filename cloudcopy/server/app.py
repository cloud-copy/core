from .api.loader import load
from .api.core import api

# loads FastAPI endpoints from .api...
load()
# expose the FastAPI instance as cloudcopy.server.app:app for convenience
app = api
