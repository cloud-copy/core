from adbc.store import Table
from adbc.zql.parsers.base import get_parser
from adbc.zql.dialect import Backend
from adbc.generators import G


class Model(Table):
    @classmethod
    def get_schema(cls):
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
