from .base import Model
from cloudcopy.server.utils import is_uuid


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
        },
        'created': {
            'type': 'text',
        },
        'updated': {
            'type': 'text',
        },
    }

    async def get_url(self, id):
        """Get database URL by ID or name"""
        key = 'id' if is_uuid(value) else 'name'
        return await self.where({'=': [key, f'"{id}"']}).field('url').one()
