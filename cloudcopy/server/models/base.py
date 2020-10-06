from adbc.store import Table
from adbc.zql.parsers.base import get_parser
from adbc.zql.dialect import Backend
from adbc.generators import G


class Model(object):
    def __init__(self, model):
        self.model = model
        self.database = self.model.database

    def __getattr__(self, key):
        if hasattr(self, key):
            return super(Model, self).__getattr__(key)
        return getattr(self.model, key)

    @classmethod
    async def initialize(cls, db):
        model = await db.get_model(cls.name)
        return cls(model)

    @classmethod
    def get_table_schema(cls):
        columns = []
        constraints = []

        for name, column in cls.columns.items():
            column = G('column', **column)
            column['name'] = name
            columns.append(column)
        for name, constraint in getattr(cls, 'constraints', {}).items():
            constraint = G('constraint', **constraint)
            constraint['name'] = name
            constraints.append(constraint)

        table = Table(
            cls.name,
            backend=get_parser(Backend.SQLITE),
            columns=columns,
            constraints=constraints
        )

        return {
            'type': 'table',
            'columns': table.columns,
            'constraints': table.constraints,
            'indexes': table.indexes
        }
