from fastapi import Depends
from adbc.store import Database
from cloudcopy.server.api import api
from cloudcopy.server.api.utils import (
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


@api.get(f"/{version}/{endpoint}/", response_model=GetDatabasesOut)
async def get_databases(db: Database = Depends(get_internal_database)):
    return await get_records(db, model)


@api.get(f"/{version}/{endpoint}/{{id}}/", response_model=GetDatabaseOut)
async def get_database(id: str, db: Database = Depends(get_internal_database)):
    return await get_record(db, model, id)


@api.post(f"/{version}/{endpoint}/", response_model=AddDatabaseOut)
async def add_database(item: AddDatabaseIn, db: Database = Depends(get_internal_database)):
    item = item.data
    return await add_record(db, model, item)


@api.put(f"/{version}/{endpoint}/{{id}}/", response_model=SetDatabaseOut)
async def set_database(id: str, item: SetDatabaseIn, db: Database = Depends(get_internal_database)):
    item = item.data
    return await edit_record(db, model, id, item)


@api.patch(f'/{version}/{endpoint}/{{id}}/')
async def edit_database(id: str, item: EditDatabaseIn, db: Database = Depends(get_internal_database)):
    item = item.data
    return await edit_record(db, model, id, item)


@api.delete(f'/{version}/{endpoint}/{{id}}/')
async def delete_database(id: str, db: Database = Depends(get_internal_database)):
    return await delete_record(db, model, id)


loaded = 1
