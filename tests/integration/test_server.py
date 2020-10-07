import pytest
import uuid
import os
import json
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
        db = None
        try:
            async with AsyncClient(app=app, base_url='http://test') as client:
                db = await get_internal_database(reset=True)
                database = await db.get_model('database')
                values = [
                    {
                        'name': 'test1',
                        'url': 'file:test1',
                        'scope': {
                            'schemas': {
                                'public': True
                            }
                        }
                    },
                    {
                        'name': 'test2',
                        'url': 'postgres://localhost:5432/test2',
                        'scope': {
                            'schemas': {
                                'public': True
                            }
                        }
                    }
                ]
                # POST
                for value in values:
                    response = await client.post(
                        '/v0/databases/',
                        data=json.dumps({'data': value})
                    )
                    assert response.status_code == 201
                    response = response.json()['data']
                    for k, v in value.items():
                        assert response[k] == v
                    value['id'] = response['id']

                # GET (collection)
                response = await client.get('/v0/databases/')

                assert response.status_code == 200
                response = response.json()['data']
                for i, value in enumerate(values):
                    for k, v in value.items():
                        assert response[i][k] == v

                # GET (record)
                id = values[0]['id']
                response = await client.get(f'/v0/databases/{id}/')

                assert response.status_code == 200
                response = response.json()['data']
                for k, v in values[0].items():
                    assert response[k] == v

                assert response['created']
                created = response['created']

                assert response['updated']
                updated = response['updated']

                # PUT
                # all writable fields not in response
                # should be reset to defaults
                response = await client.put(
                    f'/v0/databases/{id}/',
                    data=json.dumps({
                        'data': {
                            'name': 'foo',
                            'url': 'file:foo'
                        }
                    })
                )
                assert response.status_code == 200
                response = response.json()['data']
                assert response['name'] == 'foo'
                assert response['url'] == 'file:foo'
                # unset "scope" was set to null
                assert response['scope'] == None
                # unchanged
                assert response['created'] == created
                assert response['updated'] >= updated
                updated = response['updated']

                # PATCH (by name)
                response = await client.patch(
                    f'/v0/databases/foo/',
                    data=json.dumps({
                        'data': {
                            'name': 'bar'
                        }
                    })
                )
                assert response.status_code == 200
                response = response.json()['data']
                assert response['name'] == 'bar'
                # unchanged
                assert response['url'] == 'file:foo'
                assert response['updated'] >= updated

                # DELETE (by newly changed name)
                response = await client.delete(f'/v0/databases/bar/')
                assert response.status_code == 204

                response = await client.get('/v0/databases/')
                assert len(response.json()['data']) == 1
        finally:
            # clean up test sqlite DB
            if db and os.path.exists(db.host.name):
                os.remove(db.host.name)
