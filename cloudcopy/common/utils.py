class Settings(object):
    """Simple configuration object class"""
    def __init__(self, data):
        self._data = data

    def __getattr__(self, key):
        return self.get(key)

    def get(self, key, default=None):
        return self._data.get(key, None)


def to_boolean(value):
    if isinstance(value, bool):
        return value
    elif isinstance(value, int):
        return bool(value)
    elif isinstance(value, str):
        return value.lower() in {'1', 'true', 'yes', 'ok'}
