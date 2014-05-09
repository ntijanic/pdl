from pypdl.wrapper.schema.io_value import IOValue
from pypdl.util import DotAccessDict, intersect_dicts


class IOList(object):
    def __init__(self, value=None):
        value = value or []
        if isinstance(value, basestring):
            value = [value]
        self._values = [IOValue(v) for v in value or []]

    def __len__(self):
        return len(self._values)

    def __iter__(self):
        return iter(self._values)

    def __getitem__(self, i):
        return self._values[i]

    def __json__(self):
        return self._values

    __str__ = __unicode__ = __repr__ = lambda self: str(self._values)

    def add_file(self, path=None):
        """ Add new file to list of outputs and return the object. """
        value = IOValue(path)
        self._values.append(value)
        return value

    def make_metadata(self, **kwargs):
        """ Intersect metadata dictionaries of each file in list and returns the new metadata object. """
        if not self._values:
            return DotAccessDict(**kwargs)
        if len(self._values) == 1:
            return self[0].make_metadata(**kwargs)
        return DotAccessDict(reduce(intersect_dicts, [v.meta for v in self._values]), **kwargs)

    def _save_meta(self):
        for val in self:
            val._save_meta()

    def _load_meta(self):
        for val in self:
            val._load_meta()
