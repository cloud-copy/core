import json
import copy
from fastapi import Depends
from adbc.store import Database
from cloudcopy.server.api import api
from cloudcopy.server.utils import (
    get_records,
    get_record,
    add_record,
    edit_record,
    delete_record,
)
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

version = 'v0'
model = 'database'
endpoint = 'databases'


def to_item(record):
    item = dict(record)
    # turn json strings into objects
    for field in ('scope', ):
        if item.get(field) is not None:
            item[field] = json.loads(item[field])
    return item


def to_record(item, exclude_unset=False):
    item = item.dict(exclude_unset=exclude_unset)
    item = item['data']
    # turn json fields into json strings
    for field in ('scope', ):
        if item.get(field) is not None:
            item[field] = json.dumps(item[field])
    return item


@api.get(f"/{version}/{endpoint}/", response_model=GetDatabasesOut)
async def get_databases(db: Database = Depends(get_internal_database)):
    return await get_records(db, model, translate=to_item)


@api.get(f"/{version}/{endpoint}/{{id}}/", response_model=GetDatabaseOut)
async def get_database(id: str, db: Database = Depends(get_internal_database)):
    return await get_record(db, model, id, translate=to_item)


@api.post(f"/{version}/{endpoint}/", response_model=AddDatabaseOut, status_code=201)
async def add_database(item: AddDatabaseIn, db: Database = Depends(get_internal_database)):
    record = to_record(item)
    return await add_record(db, model, record, translate=to_item)


@api.put(f"/{version}/{endpoint}/{{id}}/", response_model=SetDatabaseOut)
async def set_database(id: str, item: SetDatabaseIn, db: Database = Depends(get_internal_database)):
    record = to_record(item)
    return await edit_record(db, model, id, record, translate=to_item)


@api.patch(f'/{version}/{endpoint}/{{id}}/')
async def edit_database(id: str, item: EditDatabaseIn, db: Database = Depends(get_internal_database)):
    record = to_record(item, exclude_unset=True)
    return await edit_record(db, model, id, record, translate=to_item)


@api.delete(f'/{version}/{endpoint}/{{id}}/', status_code=204)
async def delete_database(id: str, db: Database = Depends(get_internal_database)):
    return await delete_record(db, model, id)


loaded = 1
