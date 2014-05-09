from .validators import validate_type, validate_range, validate_enum, validate_pattern, validate_struct
from .base_attr import BaseAttr, default_attr_name


class BaseParam(BaseAttr):
    def __init__(self, name=None, description='', required=False, default=None, category=None,
                 list=False, show_if=None, **extra):
        BaseAttr.__init__(self, name, description, required, list, **extra)
        default = [] if list and default is None else default
        self.default = default() if callable(default) else default
        self.category = category
        self.condition = show_if

    def __call__(self, attr_name, data=None):
        BaseAttr.__call__(self, attr_name, data)
        data = self.default if data is None else data
        if self.list and not isinstance(data, (list, tuple)):
            data = [] if data is None else [data]
        return data


class IntAttr(BaseParam):
    def __init__(self, name=None, description='', required=False, default=None, category=None,
                 list=False, min=None, max=None, step=None, **extra):
        BaseParam.__init__(self, name, description, required, default, category, list, **extra)
        self.type = 'integer'
        self.min = min
        self.max = max
        self.step = step

    def validate(self, instance):
        BaseParam.validate(self, instance)
        validate_type(instance, (int, long), list=self.list)
        validate_range(instance, self.min, self.max, self.step, list=self.list)


class RealAttr(BaseParam):
    def __init__(self, name=None, description='', required=False, default=None, category=None,
                 list=False, min=None, max=None, step=None, **extra):
        BaseParam.__init__(self, name, description, required, default, category, list, **extra)
        self.type = 'float'
        self.min = min
        self.max = max
        self.step = step

    def validate(self, instance):
        BaseParam.validate(self, instance)
        validate_type(instance, (float, int, long), list=self.list)
        validate_range(instance, self.min, self.max, self.step, list=self.list)


class StringAttr(BaseParam):
    def __init__(self, name=None, description='', required=False, default=None, category=None,
                 list=False, pattern=None, **extra):
        BaseParam.__init__(self, name, description, required, default, category, list, **extra)
        self.type = 'string'
        self.pattern = pattern

    def validate(self, instance):
        BaseParam.validate(self, instance)
        validate_type(instance, (basestring,), list=self.list)
        validate_pattern(instance, self.pattern, list=self.list)


class BoolAttr(BaseParam):
    def __init__(self, name=None, description='', required=False, default=None, category=None,
                 list=False, **extra):
        BaseParam.__init__(self, name, description, required, default, category, list, **extra)
        self.type = 'boolean'

    def validate(self, instance):
        BaseParam.validate(self, instance)
        validate_type(instance, (bool,), list=self.list)


class EnumAttr(BaseParam):
    def __init__(self,  values, name=None, description='', required=False, default=None, category=None,
                 list=False, **extra):
        BaseParam.__init__(self, name, description, required, default, category, list, **extra)
        self.type = 'enum'
        self.values = [self._expand_value(v) for v in values]

    def _expand_value(self, val):
        error = ValueError('Please specify a 3-tuple with id, name and description.')
        d = default_attr_name
        if not isinstance(val, (tuple, list)):
            return val, d(val), d(val)
        l = len(val)
        if not l:
            raise error
        elif l == 1:
            return val[0], d(val[0]), d(val[0])
        elif l == 2:
            if not isinstance(val[1], basestring):
                raise error
            return val[0], val[1], d(val[0])
        elif l == 3:
            if not isinstance(val[1], basestring) or not isinstance(val[2], basestring):
                raise error
            return val
        else:
            raise error

    def validate(self, instance):
        BaseParam.validate(self, instance)
        validate_enum(instance, [v[0] for v in self.values], list=self.list)


class StructAttr(BaseParam):
    def __init__(self, schema, item_label=None, name=None, description='', required=False, default=None, category=None,
                 list=False, **extra):
        BaseParam.__init__(self, name, description, required, default, category, list, **extra)
        self.schema = schema
        self.item_label = item_label or schema.__name__
        self.type = 'struct'

    def validate(self, instance):
        BaseParam.validate(self, instance)
        validate_type(instance, (self.schema,), list=self.list)
        validate_struct(instance, list=self.list)

    def __call__(self, attr_name, data=None):
        BaseParam.__call__(self, attr_name, data)
        if not self.list:
            return self.schema(**(data or {}))
        if not data:
            return []
        return [self.schema(**(item or {})) for item in data]