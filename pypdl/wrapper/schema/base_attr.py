from .attrdef import AttrDef


def default_attr_name(name):
    if not isinstance(name, basestring):
        name = str(name)
    if name.startswith('-') or name.isupper():
        return name
    return name.replace('_', ' ').capitalize()


class BaseAttr(AttrDef):
    def __init__(self, name=None, description='', required=False, list=False, **extra):
        AttrDef.__init__(self)
        self.name = name
        self.description = description
        self.required = required
        self.list = list
        self._extra = extra

    @property
    def extra(self):
        return self._extra

    def __call__(self, attr_name, data=None):
        if attr_name.startswith('_'):
            raise ValueError('Input, output and parameter IDs cannot start with "_" (%s)' % attr_name)
        if not self.name:
            self.name = default_attr_name(attr_name)
        if not self.description:
            self.description = self.name
        return data

    def validate(self, instance):
        from io_list import IOList
        if self.list and not isinstance(instance, (tuple, list, IOList)):
            raise ValueError('Value must be tuple or list.')
        if not self.required:
            return
        if instance is None:
            raise ValueError('You must specify a value.')
        if self.list and not instance:
            raise ValueError('You must specify a value.')
