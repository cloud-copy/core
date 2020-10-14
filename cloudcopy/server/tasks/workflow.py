import os
import json
import asyncio
import sys

from adbc.workflow import Workflow as Runner

from cloudcopy.server.tasks.core import app
from cloudcopy.server.utils import get_uuid, now
from cloudcopy.server.storage import get_internal_database
from cloudcopy.server.models import Job, Workflow
from cloudcopy.server.config import settings


class Logger(object):
    def __init__(self, verbose=False, stdout=None):
        self.verbose = verbose
        self.stdout = stdout or sys.stdout

    def setLevel(self, level, *args):
        self._level = level

    def log(self, *args, **kwargs):
        if self.verbose and self.stdout != sys.stdout:
            print(*args)
        arg = args[0]
        self.stdout.write(f'{arg}\n')
        if hasattr(self.stdout, 'flush'):
            self.stdout.flush()

    def info(self, *args, **kwargs):
        return self.log(*args, **kwargs)

    def debug(self, *args, **kwargs):
        return self.log(*args, **kwargs)


async def _execute(workflow_id: str):
    db = await get_internal_database()
    workflow_model = await Workflow.initialize(db)
    job_model = await Job.initialize(db)

    # support key-by-name
    key = (
        workflow_model.id_field if workflow_model.is_id(workflow_id)
        else workflow_model.name_field
    )
    try:
        workflow = await workflow_model.where(
            {'=': [key, f'"{workflow_id}"']}
        ).one()
    except Exception:
        # this workflow no longer exists
        # (deleted as this task was scheduled)
        # in this case we have nothing to log against
        return

    job_id = get_uuid()
    concurrency = workflow['concurrency']
    running_jobs = workflow['running_jobs']
    time = now()
    # TODO: solve race condition:
    # implement a lock on WorkflowID
    # to prevent running_jobs from being double-incremented beyond the limit
    if concurrency > 0 and running_jobs >= concurrency:
        # fail with concurrency error
        await job_model.values({
            'id': job_id,
            'workflow_id': workflow_id,
            'result': json.dumps({
                'error': {
                    'type': 'ConcurrencyError',
                    'message': f'At concurrency limit: {concurrency}'
                }
            }),
            'status': job_model.FAILED,
            'started': time,
            'completed': time
        }).add()
        return

    log_file = os.path.join(
        settings.LOG_PATH,
        f"W_{workflow_id}_J_{job_id}.log"
    )

    await job_model.values({
        'id': job_id,
        'workflow_id': workflow_id,
        'log': log_file,
        'status': job_model.STARTED,
        'started': time
    }).add()
    job = await job_model.key(job_id).one()
    # using the current value + 1
    # guarantees that running jobs will be incremented properly
    # even if this code were running in different threads
    await workflow_model.key(workflow_id).values({
        "running_jobs": {
            '+': [
                "running_jobs",
                1
            ]
        }
    }).set()

    steps = await workflow_model.resolve_steps(workflow['steps'])
    name = workflow['name']
    timeout = workflow['timeout']
    if not timeout:
        timeout = None

    max_retries = workflow['max_retries']
    recent_errors = workflow['recent_errors']
    with open(log_file, 'w') as log:
        logger = Logger(
            stdout=log,
            verbose=settings.DEBUG
        )
        runner = Runner(
            name,
            steps=steps,
            logger=logger,
            verbose=settings.DEBUG
        )
        success = False
        result = None

        try:
            result = await asyncio.wait_for(runner.execute(), timeout=timeout)
            success = True
        except Exception as e:
            result = {
                'error': {
                    'type': e.__class__.__name__,
                    'message': str(e)
                }
            }
            recent_errors += 1
        finally:
            # update job with status and completion time
            status = job_model.SUCCEEDED if success else job_model.FAILED
            time = now()
            values = {
                'result': json.dumps({'data': result}),
                'status': status,
                'updated': time,
                'completed': time
            }
            # update job
            await job_model.key(job_id).values(values).set()

            retry = False
            delay = 2 ** recent_errors
            if not success:
                if recent_errors <= max_retries:
                    # retry this task with exponential back-off
                    # TODO: make back-off configurable?
                    retry = True
            else:
                # reset recent_errors
                recent_errors = 0
            await workflow_model.key(workflow_id).values({
                'recent_errors': recent_errors,
                'running_jobs': {
                    '-': [
                        'running_jobs',
                        1
                    ]
                }
            }).set()
            if retry:
                execute.schedule(
                    (workflow_id, ), delay=delay
                )


@app.task(name='workflow-execute')
def execute(workflow_id):
    result = asyncio.run(_execute(workflow_id))
    return result
