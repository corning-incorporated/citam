import json

from citam.engine.serializer import serializer


def test_serialize(rect_space):

    obj = json.dumps(rect_space, default=serializer.encoder_default)
    rect_space_decoded = json.loads(obj, object_hook=serializer.decoder_hook)

    assert rect_space_decoded.id == rect_space.id
    assert rect_space_decoded.path == rect_space.path
    assert rect_space_decoded.boundaries == rect_space.boundaries
    assert rect_space_decoded.facility == rect_space.facility
    assert rect_space_decoded.department == rect_space.department
    assert rect_space_decoded.unique_name == rect_space.unique_name
    assert rect_space_decoded.floor == rect_space.floor
    assert rect_space_decoded.capacity == rect_space.capacity
    assert rect_space_decoded.building == rect_space.building


def test_serialize_2(x_space):

    obj = json.dumps(x_space, default=serializer.encoder_default)
    x_space_decoded = json.loads(obj, object_hook=serializer.decoder_hook)

    assert x_space_decoded.id == x_space.id
    assert x_space_decoded.path == x_space.path
    assert x_space_decoded.boundaries == x_space.boundaries
    assert x_space_decoded.facility == x_space.facility
    assert x_space_decoded.department == x_space.department
    assert x_space_decoded.unique_name == x_space.unique_name
    assert x_space_decoded.floor == x_space.floor
    assert x_space_decoded.capacity == x_space.capacity
    assert x_space_decoded.building == x_space.building
