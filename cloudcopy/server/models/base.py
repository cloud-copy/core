from adbc.generators.base import Table


class Model(Table):
    def get_schema(self):
        return {
            'type': 'table',
            'columns': self.columns,
            'constraints': self.constraints,
            'indexes': self.indexes
        }
