import json
import copy
from typing import Optional, List

from adbc.store import Database as Storage
from pydantic import BaseModel
from fastapi import Depends

from cloudcopy.server.api import server
from cloudcopy.server.models import Database
from cloudcopy.server.storage import get_internal_database
from ...utils import from_request, to_response

VERSION = 'v0'
ENDPOINT = 'databases'


class In(BaseModel):
    pass


class Out(BaseModel):
    pass


class Base(BaseModel):
    name: str
    url: str
    scope: Optional[dict] = None


class DatabaseIn(Base):
    name: Optional[str] = None
    url: Optional[str] = None


class DatabaseOut(Base):
    id: str
    created: Optional[str] = None
    updated: Optional[str] = None


class GetDatabaseOut(Out):
    data: DatabaseOut


class GetDatabasesOut(Out):
    data: List[DatabaseOut]


class AddDatabaseOut(GetDatabaseOut):
    pass


class SetDatabaseIn(In):
    data: DatabaseIn


class AddDatabaseIn(In):
    data: Base


class SetDatabaseOut(GetDatabaseOut):
    pass


class EditDatabaseIn(SetDatabaseIn):
    pass


class EditDatabaseOut(SetDatabaseOut):
    pass


class DeleteDatabaseOut(Out):
    data: str



@server.get(f"/{VERSION}/{ENDPOINT}/", response_model=GetDatabasesOut)
async def get_databases(db: Storage = Depends(get_internal_database)):
    model = await Database.initialize(db)
    result = await model.get()
    return to_response(result)


@server.get(f"/{VERSION}/{ENDPOINT}/{{id}}/", response_model=GetDatabaseOut)
async def get_database(id: str, db: Storage = Depends(get_internal_database)):
    model = await Database.initialize(db)
    result = await model.get_record(id)
    return to_response(result)


@server.post(f"/{VERSION}/{ENDPOINT}/", response_model=AddDatabaseOut, status_code=201)
async def add_database(data: AddDatabaseIn, db: Storage = Depends(get_internal_database)):
    item = from_request(data)

    model = await Database.initialize(db)
    record = model.to_record(item)
    result = await model.add_record(record)

    return to_response(result)


@server.put(f"/{VERSION}/{ENDPOINT}/{{id}}/", response_model=SetDatabaseOut)
async def set_database(id: str, data: SetDatabaseIn, db: Storage = Depends(get_internal_database)):
    item = from_request(data)

    model = await Database.initialize(db)
    record = model.to_record(item)
    result = await model.edit_record(id, record)

    return to_response(result)


@server.patch(f'/{VERSION}/{ENDPOINT}/{{id}}/')
async def edit_database(id: str, data: EditDatabaseIn, db: Storage = Depends(get_internal_database)):
    item = from_request(data, patch=True)

    model = await Database.initialize(db)
    record = model.to_record(item)
    result = await model.edit_record(id, record)

    return to_response(result)


@server.delete(f'/{VERSION}/{ENDPOINT}/{{id}}/', status_code=204)
async def delete_database(id: str, db: Storage = Depends(get_internal_database)):
    model = await Database.initialize(db)
    result = await model.delete_record(id)
    # return 204 (No Content) with empty body
    return {}
