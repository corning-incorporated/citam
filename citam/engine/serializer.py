from svgpathtools import Path, Line, parse_path

class _Serializer:
    def __init__(self, classname_key='__class__'):
        self._key = classname_key
        self._classes = {} # to keep a reference to the classes used

    def __call__(self, class_): # decorate a class
        self._classes[class_.__name__] = class_
        return class_

    def decoder_hook(self, d):
        classname = d.pop(self._key, None)
        if classname:
            if classname == 'Path':
                return parse_path(d['Path'])
            elif classname == 'Line':
                return Line(start=complex(d['start']['real'], d['start']['imag']),
                            end=complex(d['end']['real'], d['end']['imag'])
                    )
            else:
                return self._classes[classname](**d)
        return d

    def encoder_default(self, obj):
        if isinstance(obj, Path):
            d = {'Path': obj.d()}
        elif isinstance(obj, Line):
            d = {'start': {'real': obj.start.real, 'imag': obj.start.imag},
                 'end': {'real': obj.end.real, 'imag': obj.end.imag}
            }
        else:
            d = obj._as_dict()
        d[self._key] = type(obj).__name__

        return d

serializer = _Serializer()