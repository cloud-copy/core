from typing import Optional, List
from pydantic import BaseModel


class In(BaseModel):
    pass


class Out(BaseModel):
    pass


class Database(BaseModel):
    name: str
    url: str


class DatabaseIn(Database):
    name: Optional[str] = None
    url: Optional[str] = None


class DatabaseOut(Database):
    id: str


class GetDatabaseOut(Out):
    data: DatabaseOut


class GetDatabasesOut(Out):
    data: List[DatabaseOut]


class AddDatabaseOut(GetDatabaseOut):
    pass


class SetDatabaseIn(In):
    data: DatabaseIn


class AddDatabaseIn(In):
    data: Database


class SetDatabaseOut(GetDatabaseOut):
    pass


class EditDatabaseIn(SetDatabaseIn):
    pass


class EditDatabaseOut(SetDatabaseOut):
    pass


class DeleteDatabaseOut(Out):
    data: str
