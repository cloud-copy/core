import pytest
import uuid
import os
from httpx import AsyncClient
from tests.utils import override_settings
from cloudcopy.server.config import settings
from cloudcopy.server.app import app
from cloudcopy.server.storage import get_internal_database


@pytest.mark.asyncio
async def test_server():
    with override_settings(
        INTERNAL_DATABASE_URL=settings.INTERNAL_DATABASE_URL + '.test'
    ):
        try:
            db = await get_internal_database(reset=True)
            database = await db.get_model('database')
            values = [
                {'name': 'test1', 'url': 'file:test1', 'id': str(uuid.uuid4())},
                {'name': 'test2', 'url': 'postgres://localhost:5432/test2', 'id': str(uuid.uuid4())}
            ]
            await database.values(values).add()
            async with AsyncClient(app=app, base_url='http://test') as client:
                response = await client.get('/v0/databases/')
            assert response.status_code == 200
            assert response.json() == {'data': values}
        finally:
            # clean up test sqlite DB
            if os.path.exists(db.host.name):
                os.remove(db.host.name)
