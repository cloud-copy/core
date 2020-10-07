from .base import Model
from adbc.generators import G


class Database(Model):
    name = 'database'
    columns = {
        'id': {
            'type': 'text',
            'primary': True
        },
        'url': {
            'type': 'text',
        },
        'name': {
            'unique': True,
            'type': 'text'
        },
        'scope': {
            'type': 'text',
            'null': True
        }
    }
