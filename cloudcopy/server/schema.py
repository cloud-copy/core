from .models import Database, Workflow, Job


def get_schema():
    """Get application model schema"""
    main = {}
    for model in (Database, Workflow, Job):
        main[model.name] = model.get_table_schema()
    schema = {'main': main}
    return schema
