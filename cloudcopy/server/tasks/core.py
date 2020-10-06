from huey import SqliteHuey
from cloudcopy.server.config import settings

app = SqliteHuey(settings.TASK_DATABASE_FILE)
