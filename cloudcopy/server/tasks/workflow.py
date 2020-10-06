import json
import asyncio
import sys

import aiofiles
from adbc.workflow import Workflow as Runner

from cloudcopy.server.tasks.core import app
from cloupcopy.server.utils import get_log_directory, get_uuid, now
from cloudcopy.server.storage import get_internal_database
from cloudcopy.server.models import Job, Workflow
from cloudcopy.server.config import settings


class WorkflowLogger(object):
    def __init__(self, verbose=False, stdout=None):
        self.verbose = verbose
        self.stdout = stdout or sys.stdout

    def setLevel(self, level, *args):
        self._level = level

    def log(self, *args, **kwargs):
        if verbose and self.stdout != sys.stdout:
            print(*args)
        self.stdout.write(*args)
        if hasattr(self.stdout, 'flush'):
            self.stdout.flush()

    def info(self, *args, **kwargs):
        return self.log(*args, **kwargs)

    def debug(self, *args, **kwargs):
        return self.log(*args, **kwargs)


async def _execute(workflow_id: str):
    db = await get_internal_database()
    Workflow = await Workflow.initialize(db)
    Job = await Job.initialize(db)

    try:
        workflow = await Workflow.key(workflow_id).one()
    except Exception:
        # this workflow no longer exists
        # (deleted as this task was scheduled)
        # in this case we have nothing to log against
        return

    id = get_uuid()
    workflow_id = workflow['id']
    log_file = os.path.join(
        settings.LOG_PATH,
        f"W_{workflow_id}_J_{id}.log"
    )
    await Job.values({
        'id': id,
        'workflow_id': workflow_id,
        'log': log_file,
        'status': Job.STARTED,
        'started': now()
    }).add()
    job = await Job.key(id).one()

    steps = await Workflow.resolve_steps(workflow)
    async with aiofiles.open(log_file, mode='w') as log:
        logger = WorkflowLogger(
            stdout=log,
            verbose=settings.DEBUG
        )
        runner = Runner(
            workflow['name'],
            steps=steps,
            logger=logger
        )
        success = False
        try:
            result = await runner.run()
            success = True
        finally:
            # update job with status and completion time
            status = Job.SUCCEEDED if success else Job.FAILED
            time = now()
            values = {
                'result': json.dumps(result),
                'status': status,
                'updated': time,
                'completed': time
            }
            await Job.key(id).values(values).set()


@app.task()
def execute(workflow_id):
    result = asyncio.run(_execute(workflow_id))
    return result
