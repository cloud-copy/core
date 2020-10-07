import json
import uuid
from functools import wraps

from copy import deepcopy
from cloudcopy.server.utils import is_uuid, now
from adbc.store import Table
from adbc.query import Query
from adbc.zql.parsers.base import get_parser
from adbc.zql.dialect import Backend
from adbc.generators import G


class ModelMethodProxy:
    def __init__(self, model, method, leveled=False, level=None):
        self.model = model
        self.query = self.model._query
        self.method = method
        self.leveled = leveled
        self.level = level

    def __getattr__(self, key):
        if not self.leveled:
            raise NotImplementedError()

        if self.level:
            level = "{}.{}".format(self.level, key)
        else:
            level = key
        return ModelMethodProxy(
            model=self.model,
            method=self.method,
            level=level,
            leveled=self.leveled
        )

    def __call__(self, *args, **kwargs):
        if self.leveled:
            args = [self.level] + list(args)
            query = getattr(self.query, "_{}".format(self.method))(*args, **kwargs)
        else:
            query = getattr(self.query, self.method)(*args, **kwargs)
        return self.model.__class__(query)


class Model(object):
    COLUMN_EXTRAS = {'uuid', 'created', 'updated', 'json'}
    COMMAND_FUNCTIONS = {
        'add',
        'set',
        'get',
        'count',
        'one',
        'delete',
        'truncate',
        'execute'
    }
    STATE_FUNCTIONS = {
        'source',
        'field',
        'key',
        'method',
        'values',
        'limit',
    }
    LEVELED_FUNCTIONS = {
        'where',
        'take',
        'sort',
        'join'
    }
    def __init__(self, query):
        self._query = query
        self._database = self._query.database

    @property
    def id_field(self):
        if not hasattr(self, '_id_field'):
            self._id_field = self._field_where(lambda column: column.get('primary'))
        return self._id_field

    @property
    def name_field(self):
        if not hasattr(self, '_name_field'):
            self._name_field = self._field_where(
                lambda column: column.get('unique') and not column.get('primary')
            )
        return self._name_field

    @property
    def created_field(self):
        if not hasattr(self, '_created_field'):
            self._created_field = self._field_where(
                lambda column: column.get('created')
            )
        return self._created_field

    @property
    def updated_field(self):
        if not hasattr(self, '_updated_field'):
            self._updated_field = self._field_where(
                lambda column: column.get('updated')
            )
        return self._updated_field

    @classmethod
    def _field_where(cls, check):
        field = None
        for name, column in cls.columns.items():
            if check(column):
                field = name
                break
        return field

    def __getattr__(self, key):
        if key in self.COMMAND_FUNCTIONS:
            pre_command = getattr(self, f'pre_{key}', None)
            post_command = getattr(self, f'post_{key}', None)
            pre = getattr(self, 'pre', None)
            post = getattr(self, 'post', None)
            query = self._query
            command = getattr(query, key)
            values = None
            if not (pre or post or pre_command or post_command):
                # return original command
                return command

            @wraps(command)
            async def wrapped(*args, **kwargs):
                if pre:
                    await pre(key, query)
                if pre_command:
                    await pre_command(query)
                result = await command(*args, **kwargs)
                post_result = None
                if post:
                    post_result = await post(key, query, result)
                    if post_result:
                        result = post_result
                if post_command:
                    post_result = await post_command(query, result)
                    if post_result:
                        result = post_result

                return result

            # return a new callable that calls the original method
            # and also the pre/post commands
            return wrapped
        elif key in self.STATE_FUNCTIONS:
            return ModelMethodProxy(
                model=self,
                method=key
            )
        elif key in self.LEVELED_FUNCTIONS:
            return ModelMethodProxy(
                model=self,
                method=key,
                leveled=True
            )
        try:
            # fallback to own property
            result = self.__getattribute__(key)
            return result
        except KeyError:
            # if no own property, fallback to query
            return getattr(self._query, key)

    @classmethod
    async def initialize(cls, db):
        model = await db.get_model(cls.name)
        return cls(model)

    @classmethod
    def get_table_schema(cls):
        columns = []
        constraints = []

        for name, column in cls.columns.items():
            column = deepcopy(column)

            # exclude extras that are not known to storage
            for key in cls.COLUMN_EXTRAS:
                column.pop(key, None)

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

    async def pre_set(self, query):
        updated = self.updated_field
        if not updated:
            return

        data = query.data('values')

        if not isinstance(data, list):
            data = [data]

        # set updated to now
        time = now()
        for d in data:
            d[updated] = time

    async def pre_add(self, query):
        updated = self.updated_field
        created = self.created_field

        if not updated or not created:
            return
        data = query.data('values')

        if not isinstance(data, list):
            data = [data]

        # set created to now
        time = now()
        for d in data:
            d[created] = time
            d[updated] = time

    async def post_get(self, query, result):
        final = []
        changes = False
        for row in result:
            post = await self.post_one(query, row)
            if post is None:
                final.append(row)
            else:
                changes = True
                final.append(post)
        return final if changes else None

    async def post_one(self, query, result):
        field = query.data('field')
        if field:
            # one field's worth of data
            column = self.columns.get(field)
            if column.get('json'):
                return json.loads(result)
            # no changes -> return None
            return None
        else:
            # many fields
            final = {}
            changes = False
            for key in result.keys():
                value = result[key]
                column = self.columns.get(key)
                if column.get('json'):
                    value = json.loads(value)
                    changes = True
                final[key] = value
            # no changes -> return None
            return final if changes else None

    def is_id(self, value):
        id_field = self.columns[self.id_field]
        id_type = id_field.get('type').lower()
        uuid = id_field.get('uuid')
        if uuid or id_type == 'uuid':
            # uuids only
            return is_uuid(value)

        if id_type.startswith('int'):
            # integers only
            try:
                int(value)
                return True
            except ValueError:
                return False

        # otherwise, anything can be an id
        return True

    async def get_field(self, field, id):
        """Get field value by key"""
        key = self.id_field if self.is_id(value) else self.name_field
        if not key:
            raise ValueError(
                f'Cannot get field "{field}", id or name field is missing'
            )

        return await self.where({'=': [key, f'"{id}"']}).field(field).one()

    def to_record(self, item):
        for name, column in self.columns.items():
            if (
                column.get('json') and
                name in item and
                not column.get('type').startswith('json')
            ):
                # convert json -> text
                item[name] = json.dumps(item[name])
        return item

    async def get_record(
        self,
        id: str,
    ):
        """Get one record"""
        key = self.id_field if self.is_id(id) else self.name_field
        if not key:
            raise ValueError(
                f'Cannot get record "{id}", id or name field is missing'
            )

        query = self.where({"=": [key, f"'{id}'"]})
        return await query.one()

    async def add_record(
        self,
        record: dict,
    ):
        """Add one record"""
        id_field = self.id_field
        name_field = self.name_field

        if (
            id_field and
            self.columns[id_field].get('uuid', False) and
            id_field not in record
        ):
            # add a uuid
            # SQLite does not support this field
            record[id_field] = str(uuid.uuid4())

        id = name = None
        if id_field in record:
            id = record[id_field]

        if name_field and name_field in record:
            name = record[name_field]

        await self.values(record).add()
        # fetch from DB for default values
        # SQLite does not support RETURNING so we cannot do this in one statement
        # for flexibility, support either ID or name
        if id is None and name is None:
            raise ValueError('Must pass either ID or name to create record')

        key, value = ('id', id) if id is not None else ('name', name)
        return await self.where({"=": [key, f"'{value}'"]}).one()


    async def edit_record(
        self,
        id: str,
        record: dict,
    ):
        """Edit one record"""
        query = self.values(record)
        id_field = self.id_field
        is_id = self.is_id(id)
        key = id_field if is_id else self.name_field
        if not key:
            raise ValueError(
                f'Cannot edit record "{id}", id or name field is missing'
            )

        where = {'=': [key, f"'{id}'"]}
        if is_id:
            # use passed in ID to refetch
            real_id = id
        else:
            # get real ID first to refetch
            # this avoids a corner case where we are changing the name
            # and keying the update by name, not ID
            real_id = await self.where(where).field(id_field).one()

        # update results
        await self.values(record).where(where).set()
        # refetch from DB for triggered value updates
        # always refetch by ID because other fields like name can change
        return await self.where({'=': [id_field, real_id]}).one()


    async def delete_record(
        self,
        id: str,
    ):
        """Delete one record"""
        key = self.id_field if self.is_id(id) else self.name_field
        if not key:
            raise ValueError(
                f'Cannot edit record "{id}", id or name field is missing'
            )
        query = self.where({"=": [key, f"'{id}'"]})
        await query.delete()
