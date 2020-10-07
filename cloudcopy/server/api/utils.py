import re
import uuid
from adbc.store import Database

UUID_REGEX = re.compile(r"[0-9a-f-]*")


def is_id(uid):
    # TODO: real uuid check
    return UUID_REGEX.match(uid)


async def get_records(db: Database, model: str):
    """Get many records of a given model

    Arguments:
        db: DB instance
        model: model name
    """
    # TODO: support filtering, ordering, etc
    # for other record types
    model = await db.get_model(model)
    records = await model.get()
    return {"data": records}


async def get_record(
    db: Database, model: str, id: str, name_field="name", id_field="id"
):
    """Get one record of a given model

    Arguments:
        db: DB instance
        model: model name
        name_field: model's name field name
    """
    model = await db.get_model(model)
    query = model
    key = id_field if is_id(id) else name_field
    query = query.where({"=": [key, f"'{id}'"]})
    record = await query.one()
    return {"data": record}


async def add_record(db: Database, model: str, record, id_field='id', name_field="name", is_uuid=True):
    """Add one record of a given model

    Arguments:
        db: DB instance
        model: model name
        name_field: model's name field name
    """
    record = record.dict()
    name = getattr(item, name_field)
    model = await db.get_model(model)
    if is_uuid:
        # add a uuid
        # SQLite does not support this field
        record[id_field] = str(uuid.uuid4())
    print(record)
    await model.values(record).add()
    # fetch from DB for default values
    # SQLite does not support RETURNING so we cannot do this in one statement
    added = await model.where({"=": ["name", f"'{name}'"]}).one()
    return {"data": added}


async def edit_record(
    db: Database, model: str, id: str, record, name_field="name", id_field="id"
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
    query = model.values(record.dict())
    key = id_field if is_id(id) else name_field
    query = query.where({"=": [key, f"'{id}'"]})
    # update results
    await query.set()
    # refetch from DB for triggered value updates
    updated = await query.one()
    return {"data": updated}


async def delete_record(
    db: Database, model: str, id: str, record, name_field="name", id_field="id"
):
    """Delete one record"""
    model = await db.get_model(model)
    key = id_field if is_id(id) else name_field
    query = query.where({"=": [key, f"'{id}'"]})
    await query.delete()
    return {"data": "ok"}
