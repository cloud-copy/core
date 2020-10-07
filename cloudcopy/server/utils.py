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
