from huey import SqliteHuey
from cloudcopy.server.config import settings

# if ASYNC_TASKS is False (e.g. in testing)
# async tasks will be executed immediately
# or added to an in-memory schedule registry
app = SqliteHuey(
    'tasks',
    filename=settings.TASK_DATABASE_FILE,
    immediate=not settings.ASYNC_TASKS
)
