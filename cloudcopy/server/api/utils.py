def from_request(item, patch=False):
    return item.dict(exclude_unset=patch)['data']


def to_response(data):
    return {'data': data}
