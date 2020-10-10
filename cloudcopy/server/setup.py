import os
from .config import settings

def setup_environment():
    os.makedirs(settings.BASE_PATH, exist_ok=True)
    os.makedirs(settings.LOG_PATH, exist_ok=True)
