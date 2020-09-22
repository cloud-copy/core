from .base import Model


class Database(Model):
    columns = {
        'id': {
            'type': 'text',
            'null': False
        },
        'url': {
            'type': 'text',
            'null': False
        },
        'name': {
            'type': 'text',
            'null': False
        },
        'scope': {
            'type': 'text',
            'null': True
        }
    }
    constraints = {
        'database__id': {
            'type': 'primary',
            'columns': ['id']
        },
        'database__name': {
            'type': 'unique',
            'columns': ['name']
        }
    }
