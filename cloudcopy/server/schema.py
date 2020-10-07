from .models import Database


def get_schema():
    return {
        'main': {
            Database.name: Database.get_schema()
        }
    }
