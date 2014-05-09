import itertools


class AttrDef(object):
    _count = itertools.count(0)  # Total number of attributes defined

    def __init__(self):
        self._order = AttrDef._count.next()

    def __call__(self, attr_name, data=None):
        """ Override to instantiate an attribute. """
        pass

    def validate(self, instance):
        """ Override to validate an attribute. """
        pass

    def get_schema(self):
        def get_value(val):
            return val._get_schema() if callable(getattr(val, '_get_schema', None)) else val
        return dict([(k,get_value(v)) for k,v in self.__dict__.iteritems() if k[0] != '_'])