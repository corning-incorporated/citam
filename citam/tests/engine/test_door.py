
from citam.engine.serializer import serializer
from citam.engine.door import Door


from svgpathtools import parse_path

import json


def test_serialize(rect_space):

    path = parse_path("M 0,0 L 100,0")
    test_door = Door(path=path, space1=rect_space)

    obj = json.dumps(test_door, default=serializer.encoder_default)
    door_decoded = json.loads(obj, object_hook=serializer.decoder_hook)

    assert test_door.path == door_decoded.path
    assert test_door.emergency_only == door_decoded.emergency_only
    assert test_door.space1.id == door_decoded.space1
    assert test_door.space2 == door_decoded.space2
    assert test_door.in_service == door_decoded.in_service
    assert test_door.special_access == door_decoded.special_access
