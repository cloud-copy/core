import json

from adbc.generators import G

from cloudcopy.server.utils import is_uuid, is_url
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

    async def resolve_steps(self, workflow):
        """Get workflow.steps as an object

        Resolve all database references, either by ID or name
        """

        steps = json.loads(workflow['steps'])
        resolved = {}
        Database = await Database.initialize(self.database)
        for step in steps:
            # look for database references and resolve them
            for key in ('source', 'target'):
                if key not in step:
                    continue
                value = step[key]
                if is_url(value):
                    continue
                if value in resolved:
                    steps[key] = resolved[value]
                else:
                    # memoize lookups
                    resolved[value] = steps[key] = await Database.get_field(
                        'url', value
                    )
        return steps

    async def post_add(self, query, data):
        result = None
        parent = super()
        if hasattr(parent, 'post_add'):
            result = await parent.post_add(query, data)
        print('added workflow', query.data('values'))
        return result if result else None
