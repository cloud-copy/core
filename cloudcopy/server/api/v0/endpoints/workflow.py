import json
import copy
from typing import Optional, List

from adbc.store import Database as Storage
from pydantic import BaseModel
from fastapi import Depends

from cloudcopy.server.api import api
from cloudcopy.server.models import Workflow
from cloudcopy.server.storage import get_internal_database
from ...utils import from_request, to_response

VERSION = 'v0'
ENDPOINT = 'workflows'


class In(BaseModel):
    pass


class Out(BaseModel):
    pass


class WorkflowBase(BaseModel):
    name: str
    steps: list
    max_retries: int = 0
    paused: int = 0
    recent_errors: int = 0
    timeout: int = 0
    schedule: Optional[dict] = None
    running_jobs: int = 0
    concurrency: int = 0
    cooldown: int = 0


class WorkflowIn(WorkflowBase):
    paused: Optional[int] = 0
    name: Optional[str] = None
    steps: Optional[list] = None
    max_retries: Optional[int] = 0
    recent_errors: Optional[int] = 0
    timeout: Optional[int] = 0
    running_jobs: Optional[int] = 0
    concurrency: Optional[int] = 0
    cooldown: Optional[int] = 0


class WorkflowOut(WorkflowBase):
    id: str
    created: str
    updated: str


class GetWorkflowOut(Out):
    data: WorkflowOut


class GetWorkflowsOut(Out):
    data: List[WorkflowOut]


class AddWorkflowOut(GetWorkflowOut):
    pass


class SetWorkflowIn(In):
    data: WorkflowIn


class AddWorkflowIn(In):
    data: WorkflowBase


class SetWorkflowOut(GetWorkflowOut):
    pass


class EditWorkflowIn(SetWorkflowIn):
    pass


class EditWorkflowOut(SetWorkflowOut):
    pass


class DeleteWorkflowOut(Out):
    data: str


@api.get(f"/{VERSION}/{ENDPOINT}/", response_model=GetWorkflowsOut)
async def get_workflows(db: Storage = Depends(get_internal_database)):
    model = await Workflow.initialize(db)
    result = await model.get()
    return to_response(result)


@api.get(f"/{VERSION}/{ENDPOINT}/{{id}}/", response_model=GetWorkflowOut)
async def get_workflow(id: str, db: Storage = Depends(get_internal_database)):
    model = await Workflow.initialize(db)
    result = await model.get_record(id)
    return to_response(result)


@api.post(f"/{VERSION}/{ENDPOINT}/", response_model=AddWorkflowOut, status_code=201)
async def add_workflow(item: AddWorkflowIn, db: Storage = Depends(get_internal_database)):
    item = from_request(item)

    model = await Workflow.initialize(db)
    record = model.to_record(item)
    result = await model.add_record(record)

    return to_response(result)


@api.put(f"/{VERSION}/{ENDPOINT}/{{id}}/", response_model=SetWorkflowOut)
async def set_workflow(id: str, item: SetWorkflowIn, db: Storage = Depends(get_internal_database)):
    item = from_request(item)

    model = await Workflow.initialize(db)
    record = model.to_record(item)
    result = await model.edit_record(id, record)

    return to_response(result)


@api.patch(f'/{VERSION}/{ENDPOINT}/{{id}}/')
async def edit_workflow(id: str, item: EditWorkflowIn, db: Storage = Depends(get_internal_database)):
    item = from_request(item, patch=True)

    model = await Workflow.initialize(db)
    record = model.to_record(item)
    result = await model.edit_record(id, record)

    return to_response(result)


@api.delete(f'/{VERSION}/{ENDPOINT}/{{id}}/', status_code=204)
async def delete_workflow(id: str, db: Storage = Depends(get_internal_database)):
    model = await Workflow.initialize(db)
    result = await model.delete_record(id)
    # return 204 (No Content) with empty body
    return {}
