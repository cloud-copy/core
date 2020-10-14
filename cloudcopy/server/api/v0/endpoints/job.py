import json
import copy
from typing import Optional, List

from adbc.store import Database as Storage
from pydantic import BaseModel
from fastapi import Depends

from cloudcopy.server.api import api
from cloudcopy.server.models import Job
from cloudcopy.server.storage import get_internal_database
from ...utils import from_request, to_response

VERSION = 'v0'
ENDPOINT = 'jobs'


class In(BaseModel):
    pass


class Out(BaseModel):
    pass


class JobBase(BaseModel):
    pass


class JobIn(JobBase):
    pass


class JobOut(JobBase):
    id: str
    status: str
    workflow_id: str
    created: str
    updated: str
    started: Optional[str]
    completed: Optional[str]
    log: Optional[str]
    result: Optional[dict] = None


class GetJobOut(Out):
    data: JobOut


class GetJobsOut(Out):
    data: List[JobOut]


class DeleteJobOut(Out):
    data: str


@api.get(f"/{VERSION}/{ENDPOINT}/", response_model=GetJobsOut)
async def get_jobs(db: Storage = Depends(get_internal_database), f__workflow_id: Optional[str] = None):
    model = await Job.initialize(db)
    query = model
    if f__workflow_id:
        query = query.where({'=': ['workflow_id', f'"{f__workflow_id}"']})

    result = await query.get()
    return to_response(result)


@api.get(f"/{VERSION}/{ENDPOINT}/{{id}}/", response_model=GetJobOut)
async def get_job(id: str, db: Storage = Depends(get_internal_database)):
    model = await Job.initialize(db)
    result = await model.get_record(id)
    return to_response(result)


@api.delete(f'/{VERSION}/{ENDPOINT}/{{id}}/', status_code=204)
async def delete_job(id: str, db: Storage = Depends(get_internal_database)):
    model = await Job.initialize(db)
    result = await model.delete_record(id)
    # return 204 (No Content) with empty body
    return {}
