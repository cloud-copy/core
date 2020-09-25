from adbc.store import Database as DatabaseDriver
from cloudcopy.server.api import api
from cloudcopy.server.config import settings
from cloudcopy.server.models import Database
from cloudcopy.server.storage import get_internal_database
from .schemas import DatabaseSchema, AddDatabaseSchema
from fastapi import Depends



@app.get("/v0/databases", response_model=List[DatabaseSchema])
def get_databases(db: Database = Depends(get_internal_database)):
    pass


@app.get("/v0/databases/{id}/", response_model=DatabaseSchema)
def get_database(id: str, db: Database = Depends(get_internal_database)):
    pass


@app.post("/v0/databases/", response_model=AddDatabaseSchema)
def add_database(db: Database = Depends(get_internal_database)):
    pass


