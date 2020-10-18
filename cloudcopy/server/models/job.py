from .base import Model


class Job(Model):
    name = 'job'
    QUEUED = 'Queued'
    STARTED = 'Started'
    SUCCEEDED = 'Succeeded'
    FAILED = 'Failed'
    STATUS_CHOICES = [QUEUED, STARTED, SUCCEEDED, FAILED]
    columns = {
        'id': {
            'type': 'text',
            'primary': True,
            'uuid': True
        },
        'status': {
            'type': 'text',
            'default': f'`{QUEUED}`',
            'choices': STATUS_CHOICES
        },
        'workflow_id': {
            'type': 'text',
            'related': {
                'to': 'workflow',
                'by': 'id'
            },
        },
        'created': {
            'type': 'text',
            'created': True
        },
        'updated': {
            'type': 'text',
            'updated': True
        },
        'started': {
            'type': 'text',
            'null': True,
        },
        'log': {
            'type': 'text',
            'null': True
        },
        'result': {
            'type': 'text',
            'null': True,
            'json': True
        },
        'completed': {
            'type': 'text',
            'null': True
        },
    }
