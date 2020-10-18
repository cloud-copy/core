import re
import arrow
import uuid
from adbc.store import Database
from adbc.utils import is_url


def get_uuid():
    return str(uuid.uuid4())


def now(as_str=True):
    result = arrow.utcnow()
    return result.isoformat() if as_str else result.datetime()


def is_uuid(uid, version=4):
    # TODO: real uuid check
    try:
        uuid.UUID(uid, version=version)
        return True
    except:
        return False

TIME_REGEX = re.compile(r'^([1-9][0-9]*) (seconds?|minutes?|hours?|days?)$')

def to_seconds(value):
    if isinstance(value, int):
        return value
    elif isinstance(value, str):
        match = TIME_REGEX.match(value)
        if not match:
            raise ValueError(f'Cannot extract seconds from "{value}"')

        value = int(match.group(1))
        increment = match.group(2)
        if increment.endswith('s'):
            increment = increment[:-1]
        multiplier = {
            'second': 1,
            'minute': 60,
            'hour': 60*60,
            'day': 60*60*24
        }[increment]
        return value * multiplier
