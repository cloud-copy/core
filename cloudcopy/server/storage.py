from cloudcopy.server.schema import get_schema
from cloudcopy.server.config import settings
from adbc.store import Database


database = None


async def get_internal_database(reset=False):
    global database

    if database is None or reset:
        # try to get a handle on the local database
        database = Database(url=settings.INTERNAL_DATABASE_URL, verbose=True)
        # try to apply schema changes, if any
        schema = get_schema()
        await database.apply(schema)
        database.reset()

    return database
