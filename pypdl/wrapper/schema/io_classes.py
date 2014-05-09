from .schema_based import SchemaBased
from .base_attr import BaseAttr
from .validators import validate_file_type
from .io_value import IOValue
from .io_list import IOList


class IOAttr(BaseAttr):
    def __init__(self, name=None, description='', file_types=None, required=False, list=False, **extra):
        BaseAttr.__init__(self, name, description, required, list=list, **extra)
        self.types = file_types or []

    def __call__(self, attr_name, data=None):
        data = BaseAttr.__call__(self, attr_name, data)
        return IOList(data) if self.list else IOValue(data)

    def validate(self, instance):
        BaseAttr.validate(self, instance)
        if instance:
            validate_file_type(instance, self.types, list=self.list)
#            validate_file_exists(instance, list=self.list)
        elif self.required:
            raise ValueError('This input is required')


class IODef(SchemaBased):
    def __setattr__(self, key, value):
        attr_def = getattr(self.__class__, key)
        if not attr_def:
            raise AttributeError('%s does not define %s' % (self.__class__.__name__, key))
        if value is None:
            return object.__setattr__(self, key, None)
        if attr_def.list and isinstance(value, list):
            return SchemaBased.__setattr__(self, key, IOList(value))
        if not attr_def.list and not isinstance(value, IOValue):
            return SchemaBased.__setattr__(self, key, IOValue(value))
        if isinstance(value, (IOValue, IOList)):
            return SchemaBased.__setattr__(self, key, value)
        raise ValueError('Unsupported type: %s' % type(value))

    def _save_meta(self):
        for v in self:
            v.value._save_meta()

    def _load_meta(self):
        for v in self:
            getattr(self, v.id)._load_meta()
