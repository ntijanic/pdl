import copy
from .attrdef import AttrDef


class SchemaBased(object):
    def __init__(self, **kwargs):
        for attr, attr_def in self._attr_defs().iteritems():
            setattr(self, attr, attr_def(attr, kwargs.get(attr)))

    @classmethod
    def _attr_defs(cls):
        result = {}
        for key in dir(cls):
            val = getattr(cls, key)
            if isinstance(val, AttrDef):
                result[key] = val
        return result

    @classmethod
    def _get_schema(cls):
        schema = []
        attr_defs = cls._attr_defs().items()
        for attr, attr_def in sorted(attr_defs, cmp=lambda x, y: cmp(x[1]._order, y[1]._order)):
            attr_def(attr)  # Set default name and desc if none supplied.
            attr_schema = dict(attr_def.get_schema(), id=attr)
            schema.append(attr_schema)
        return schema

    def _validate(self, assert_=False):
        errors = {}
        for attr, attr_def in self._attr_defs().iteritems():
            try:
                attr_def.validate(getattr(self, attr))
            except (ValueError, TypeError) as e:
                errors[attr] = str(e)
        if assert_:
            # noinspection PyStringFormat
            assert not errors, 'Following errors encountered: %s' % errors
        return errors

    def _definitions(self):
        result = {}
        for id, attr in self.__class__._attr_defs().iteritems():
            new = copy.deepcopy(attr)
            new.value = getattr(self, id)
            new.id = id
            result[id] = new
        return result

    def __json__(self):
        return dict([(k, v) for k, v in self.__dict__.iteritems() if k[0] != '_' and v is not None])
    __unicode__ = __repr__ = __str__ = lambda self: str(self.__json__())

    def __iter__(self):
        for k, v in self._definitions().iteritems():
            yield v

    def __getitem__(self, item):
        return self.__json__()[item]