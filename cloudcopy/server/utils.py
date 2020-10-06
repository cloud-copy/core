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


async def get_records(db: Database, model: str, translate=None):
    """Get many records of a given model

    Arguments:
        db: DB instance
        model: model name
    """
    # TODO: support filtering, ordering, etc
    # for other record types
    model = await db.get_model(model)
    records = await model.get()
    if translate:
        records = [translate(r) for r in records]
    return {"data": records}


async def get_record(
    db: Database,
    model: str,
    id: str,
    name_field="name",
    id_field="id",
    translate=None
):
    """Get one record of a given model

    Arguments:
        db: DB instance
        model: model name
        name_field: model's name field name
        id_field: model's id field name
    """
    model = await db.get_model(model)
    query = model
    key = id_field if is_uuid(id) else name_field
    query = query.where({"=": [key, f"'{id}'"]})
    record = await query.one()
    if translate:
        record = translate(record)
    return {"data": record}


async def add_record(
    db: Database,
    model: str,
    record: dict,
    id_field='id',
    name_field="name",
    created_field="created",
    updated_field="updated",
    is_uuid=True,
    translate=None
):
    """Add one record of a given model

    Arguments:
        db: DB instance
        model: model name
        name_field: model's name field name
        updated_field: model's updated field name
        created_field: model's created field name
        is_uuid: if true, create and add a UUID if unset
    """
    model = await db.get_model(model)
    if is_uuid and id_field not in record:
        # add a uuid
        # SQLite does not support this field
        record[id_field] = str(uuid.uuid4())

    id = name = None
    if id_field in record:
        id = record[id_field]

    if name_field and name_field in record:
        name = record[name_field]

    time = now()

    if created_field:
        record[created_field] = time
    if updated_field:
        record[updated_field] = time

    await model.values(record).add()
    # fetch from DB for default values
    # SQLite does not support RETURNING so we cannot do this in one statement
    # for flexibility, support either ID or name
    if id is None and name is None:
        raise ValueError('must pass either ID or name to create record')

    key, value = ('id', id) if id is not None else ('name', name)
    record = await model.where({"=": [key, f"'{value}'"]}).one()
    if translate:
        record = translate(record)
    return {"data": record}


async def edit_record(
    db: Database,
    model: str,
    id: str,
    record: dict,
    name_field="name",
    id_field="id",
    updated_field="updated",
    translate=None
):
    """Edit one record of a given model

    Works for both partial (PATCH) and full (PUT) updates

    Arguments:
        db: DB instance
        id: ID or name
        record: record data
        name_field: model's name field name
        id_field: model's id field name
    """
    model = await db.get_model(model)
    if updated_field:
        record[updated_field] = now()
    query = model.values(record)
    key = id_field if is_uuid(id) else name_field
    query = query.where({"=": [key, f"'{id}'"]})
    # update results
    await query.set()
    # refetch from DB for triggered value updates
    record = await query.one()
    if translate:
        record = translate(record)
    return {"data": record}


async def delete_record(
    db: Database,
    model: str,
    id: str,
    name_field="name",
    id_field="id",
):
    """Delete one record"""
    model = await db.get_model(model)
    key = id_field if is_uuid(id) else name_field
    query = model.where({"=": [key, f"'{id}'"]})
    await query.delete()
    return {}
