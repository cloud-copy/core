from .base import Model
from cloudcopy.server.utils import is_uuid, now


class Database(Model):
    name = 'database'
    columns = {
        'id': {
            'type': 'text',
            'primary': True,
            'uuid': True
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
            'null': True,
            'json': True
        },
        'created': {
            'type': 'text',
            'created': True
        },
        'updated': {
            'type': 'text',
            'updated': True
        },
    }
