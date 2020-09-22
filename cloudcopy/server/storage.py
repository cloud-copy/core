from cloudcopy.schema import get_schema


database = None


def get_internal_database():
    global database
    global schema

    if database is None:
        # try to get a handle on the local database
        database = Database(
            url=settings.INTERNAL_DATABASE_PATH
        )
        # try to apply schema changes, if any
        schema = get_schema()
        await database.apply(schema)

    return database
