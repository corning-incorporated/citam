
from citam.engine.serializer import serializer
from citam.engine.door import Door


from svgpathtools import parse_path

import json


def test_serialize(rect_space):

    path = parse_path("M 0,0 L 100,0")
    test_door = Door(path=path, space1=rect_space)

    obj = json.dumps(rect_space, default=serializer.encoder_default)
    door_decoded = json.loads(obj, object_hook=serializer.decoder_hook)

    print(door_decoded, type(door_decoded))

    assert 1 == 2
