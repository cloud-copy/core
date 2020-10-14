import json

from adbc.generators import G

from cloudcopy.server.utils import is_uuid, is_url, to_seconds
from cloudcopy.server.config import settings
from .database import Database
from .base import Model


class Workflow(Model):
    name = 'workflow'
    columns = {
        'id': {
            'type': 'text',
            'primary': True,
            'uuid': True,
            # static UUID
        },
        'paused': {
            'type': 'integer',
            'default': 0,
            # boolean
            # 0 means not paused (default)
            # 1 means paused (should not execute)
        },
        'steps': {
            'type': 'text',
            'json': True,
            # JSON array of steps:
            # step:
            #   source: str (Database ID)
            #   target: Optional[str] (Other Database ID)
            #   scope: Optional[dict]
        },
        'max_retries': {
            'type': 'integer',
            'default': 0,
            # number of times to retry a task
            # 0 means do not retry (retry)
            # 1 means retry once only
            # -1 means retry indefinitely
        },
        'recent_errors': {
            'type': 'integer',
            'default': 0,
            # number of times the task has recently failed consecutively
        },
        'timeout': {
            'type': 'integer',
            'default': 0
            # max number of seconds this workflow's job can run
            # 0 means no limit (default)
        },
        'name': {
            'unique': True,
            'type': 'text'
            # human-readable unique identifier
            # may be changed by the user
        },
        'schedule': {
            'type': 'text',
            'null': True,
            'json': True
            # JSON object with either "rate" or "cron" key:
            # rate: "5 minutes" (or seconds, hours, days)
            # cron: ["*", "*", "*", "*", "0", "1"]
            # if set, the workflow will be triggered on the schedule
            # if not set, the workflow can still be triggered manually
        },
        'task_id': {
            'type': 'text',
            'null': True,
            # UUID value of task ID
            # representing the next scheduled invocation of this workflow
        },
        'running_jobs': {
            'type': 'integer',
            'default': 0
        },
        'concurrency': {
            'type': 'integer',
            'null': True,
            'default': 0
            # number of simultaneous job executions
            # default of 0 = unlimited
            # if a workflow is triggered when the concurrency limit is reached,
            # the job will immediately fail
        },
        'cooldown': {
            'type': 'integer',
            'null': True,
            'default': 0
            # time (seconds) to wait before the next execution
            # after the previous one has finished
        },
        'created': {
            'type': 'text',
            'created': True
        },
        'updated': {
            'type': 'text',
            'updated': True
        }
    }

    async def resolve_steps(self, steps):
        """Get workflow.steps as an object

        Resolve all database references, either by ID or name
        """
        if not steps:
            return None

        steps = json.loads(steps) if isinstance(steps, str) else steps
        resolved = {}
        db = await Database.initialize(self._database)
        for step in steps:
            # look for database references and resolve them
            for key in ('source', 'target'):
                if key not in step:
                    continue
                value = step[key]
                if is_url(value):
                    continue
                if value in resolved:
                    step[key] = resolved[value]
                else:
                    # memoize lookups
                    try:
                        step[key] = await db.get_field(
                            'url', value
                        )
                        resolved[value] = step[key]
                    except Exception as e:
                        raise ValueError(
                            f'Error resolving {key} for step: {step}\nMessage: {e}'
                        )
        return steps


    async def pre_add(self, query):
        # validate steps
        parent = super()
        if hasattr(parent, 'pre_add'):
            # perform base manipulations/checks
            await parent.pre_add(query)

        # perform validation of "steps"
        values = query.data('values')
        if isinstance(values, list):
            return await self.pre_add_many(values)
        else:
            return await self.pre_add_one(values)

    async def pre_add_many(self, values):
        for value in values:
            await self.pre_add_one(value)

    async def pre_add_one(self, values):
        steps = values.get('steps')
        await self.resolve_steps(steps)

    async def post_add_record(self, record, result):
        # IMPORTANT: this import deferred to avoid circular import
        # between the co-dependent model and workflow
        from cloudcopy.server.tasks.workflow import execute, _execute

        id = result['id']
        schedule = result['schedule']
        task = None
        if schedule:
            if schedule.get('immediate'):
                if settings.ASYNC_TASKS:
                    task = execute(id)
                else:
                    # running in test mode
                    task = await _execute(id)
            if 'delay' in schedule:
                delay = to_seconds(schedule['delay'])
                task = execute.schedule((id, ), delay=delay)
            if task:
                # save current task ID onto the workflow
                # so that it can be revoked later
                await self.key(id).values({'task_id': task.id}).set()
