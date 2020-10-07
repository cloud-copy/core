import json
import copy
from fastapi import Depends
from adbc.store import Database as Storage
from cloudcopy.server.api import api
from cloudcopy.server.models import Database
from cloudcopy.server.storage import get_internal_database
from .schemas import (
    GetDatabaseOut,
    GetDatabasesOut,
    AddDatabaseOut,
    AddDatabaseIn,
    EditDatabaseIn,
    EditDatabaseOut,
    SetDatabaseIn,
    SetDatabaseOut,
    DeleteDatabaseOut
)

VERSION = 'v0'
ENDPOINT = 'databases'


def from_request(item, patch=False):
    return item.dict(exclude_unset=patch)['data']


def to_response(data):
    return {'data': data}


@api.get(f"/{VERSION}/{ENDPOINT}/", response_model=GetDatabasesOut)
async def get_databases(db: Storage = Depends(get_internal_database)):
    model = await Database.initialize(db)
    result = await model.get()
    return to_response(result)


@api.get(f"/{VERSION}/{ENDPOINT}/{{id}}/", response_model=GetDatabaseOut)
async def get_database(id: str, db: Storage = Depends(get_internal_database)):
    model = await Database.initialize(db)
    result = await model.get_record(id)
    return to_response(result)


@api.post(f"/{VERSION}/{ENDPOINT}/", response_model=AddDatabaseOut, status_code=201)
async def add_database(item: AddDatabaseIn, db: Storage = Depends(get_internal_database)):
    item = from_request(item)

    model = await Database.initialize(db)
    record = model.to_record(item)
    result = await model.add_record(record)

    return to_response(result)


@api.put(f"/{VERSION}/{ENDPOINT}/{{id}}/", response_model=SetDatabaseOut)
async def set_database(id: str, item: SetDatabaseIn, db: Storage = Depends(get_internal_database)):
    item = from_request(item)

    model = await Database.initialize(db)
    record = model.to_record(item)
    result = await model.edit_record(id, record)

    return to_response(result)


@api.patch(f'/{VERSION}/{ENDPOINT}/{{id}}/')
async def edit_database(id: str, item: EditDatabaseIn, db: Storage = Depends(get_internal_database)):
    item = from_request(item, patch=True)

    model = await Database.initialize(db)
    record = model.to_record(item)
    result = await model.edit_record(id, record)

    return to_response(result)


@api.delete(f'/{VERSION}/{ENDPOINT}/{{id}}/', status_code=204)
async def delete_database(id: str, db: Storage = Depends(get_internal_database)):
    model = await Database.initialize(db)
    result = await model.delete_record(id)
    # return 204 (No Content) with empty body
    return {}


loaded = 1
