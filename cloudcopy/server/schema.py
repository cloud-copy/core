from .models import Database


def get_schema():
    return {
        'main': {
            'database': Database.get_schema()
        }
    }
