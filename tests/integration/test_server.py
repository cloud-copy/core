import pytest
import uuid
import os
import json
from contextlib import AsyncExitStack
from adbc.testing import setup_test_database
from httpx import AsyncClient
from tests.utils import override_settings

from cloudcopy.server.config import settings
from cloudcopy.server.storage import get_internal_database


async def setup_db(db, tables=('test', ), rows=10):
    for name in tables:
        await db.create_table(
            name, {
                'columns': {
                    'id': {
                        'type': 'integer',
                        'primary': True,
                        'sequence': True
                    },
                    'name': {
                        'type': 'text',
                        'unique': True
                    }
                }
            }
        )
        values = [
            [i, f'name-{i}']
            for i in range(rows)
        ]
        await db.execute({
            'insert': {
                'table': name,
                'columns': ['id', 'name'],
                'values': values
            }
        })


@pytest.mark.asyncio
async def test_server():
    with override_settings(
        ASYNC_TASKS=False,
        DEBUG=True,
        INTERNAL_DATABASE_FILE=settings.INTERNAL_DATABASE_FILE + '.test'
    ):
        from cloudcopy.server.app import api as app, tasks
        try:
            async with AsyncExitStack() as stack:
                client = await stack.enter_async_context(AsyncClient(app=app, base_url='http://test'))
                test0 = await stack.enter_async_context(
                    setup_test_database('test0', url='file:test0')
                )
                test1 = await stack.enter_async_context(
                    setup_test_database('test1', url='file:test1')
                )
                test2 = await stack.enter_async_context(
                    setup_test_database('test2', url='file:test2')
                )

                await setup_db(test0, tables=('test1', 'test2', 'test3'))
                await setup_db(test1, tables=('test2', 'test3'), rows=5)
                await setup_db(test2, tables=('test3', ))

                databases = [
                    {
                        'name': 'test0',
                        'url': 'file:test0',
                        'scope': {
                            'schemas': {
                                'main': True
                            }
                        }
                    },
                    {
                        'name': 'test2',
                        'url': 'file:test2'
                    },
                    {
                        'name': 'test3',
                        'url': 'file:test3',
                        'scope': {
                            'schemas': {
                                'main': True
                            }
                        }
                    }
                ]
                # POST
                for value in databases:
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
                for i, value in enumerate(databases):
                    for k, v in value.items():
                        assert response[i][k] == v

                # GET (record)
                modify_index = 2
                id = databases[modify_index]['id']
                response = await client.get(f'/v0/databases/{id}/')

                assert response.status_code == 200
                response = response.json()['data']
                for k, v in databases[modify_index].items():
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
                            'url': 'file:test1'
                        }
                    })
                )
                assert response.status_code == 200
                response = response.json()['data']
                assert response['name'] == 'foo'
                assert response['url'] == 'file:test1'
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
                            'name': 'test1'
                        }
                    })
                )
                assert response.status_code == 200
                response = response.json()['data']
                assert response['name'] == 'test1'
                # unchanged
                assert response['url'] == 'file:test1'
                assert response['updated'] >= updated

                # Workflows
                response = await client.get(
                    f'/v0/workflows'
                )
                assert response.status_code == 200
                response = response.json()['data']
                assert response == []

                workflows = [{
                    "name": "diff-0-1",
                    "schedule": {
                        "immediate": True
                    },
                    "steps": [{
                        "type": "compare",
                        "hashes": True,
                        "source": databases[0]['id'],  # by id (test0)
                        "target": "test1" # by name reference (test1)
                    }]
                }, {
                    "name": "info-2",
                    "steps": [{
                        "type": "info",
                        "source": "file:test2"
                    }],
                    "schedule": {
                        "delay": "1 minute"
                    }
                }]
                # add workflow
                for workflow in workflows:
                    response = await client.post(
                        '/v0/workflows/',
                        data=json.dumps({'data': workflow})
                    )
                    assert response.status_code == 201
                    response = response.json()['data']
                    for k, v in workflow.items():
                        assert response[k] == v
                    workflow['id'] = response['id']

                # DELETE (by newly changed name)
                response = await client.delete(f'/v0/databases/test1/')
                assert response.status_code == 204

                response = await client.get('/v0/databases/')
                assert len(response.json()['data']) == len(databases) - 1

                immediate_workflow = workflows[0]
                delayed_workflow = workflows[1]

                scheduled = tasks.scheduled()

                assert len(scheduled) == 1
                assert scheduled[0].name == 'workflow-execute'
                args, kwargs = scheduled[0].data
                assert args[0] == delayed_workflow['id']

                immediate_id = immediate_workflow['id']
                response = await client.get(f'/v0/jobs/?f__workflow_id={immediate_id}')
                assert response.status_code == 200
                data = response.json()['data']

                assert len(data) == 1
                data = data[0]
                assert data['status'] == 'Succeeded'
                result = data['result']
                assert result == []
        finally:
            # clean up test sqlite DB
            if os.path.exists(settings.INTERNAL_DATABASE_FILE):
                os.remove(settings.INTERNAL_DATABASE_FILE)
