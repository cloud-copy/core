from cloudcopy.server.schema import get_schema
from cloudcopy.server.config import settings
from adbc.store import Database


database = None


async def get_internal_database(reset=False):
    global database

    if database is None or reset:
        schema = get_schema()
        scope = {'schemas': schema}
        # try to get a handle on the local database
        database = Database(
            scope=scope,
            url=settings.INTERNAL_DATABASE_URL,
            verbose=settings.DEBUG
        )
        # try to apply schema changes, if any
        await database.apply(schema)
        # reset the database to trigger a schema refresh
        database.reset()

    return database
