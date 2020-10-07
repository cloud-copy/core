from cloudcopy.server.config import settings

class override_settings():
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def __enter__(self, *args, **kwargs):
        self.backup = {}
        self.reset(self.kwargs, self.backup)

    def reset(self, source, backup=None):
        for key, value in source.items():
            if backup:
                backup[key] = value
            setattr(settings, key, value)

    def __exit__(self, *args, **kwargs):
        self.reset(self.backup)
