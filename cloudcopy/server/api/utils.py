from fastapi.responses import Response


def from_request(item, patch=False):
    """Extract data from a Pydantic request body item"""
    return item.dict(exclude_unset=patch)['data']


def to_response(data, raw=False):
    """Convert data to a response"""
    if raw:
        assert isinstance(data, str)
        return Response(
            content=f'{{"data":{data}}}', media_type='application/json'
        )

    return {'data': data}
