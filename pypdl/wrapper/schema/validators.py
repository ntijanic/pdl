import re
import os


def validator(func):
    def f(val, *args, **kwargs):
        if not kwargs.pop('list'):
            return func(val, *args, **kwargs)
        for v in val:
            func(v, *args, **kwargs)
    return f


# noinspection PyUnusedLocal
@validator
def validate_type(val, t_tuple, **kw):
    if val is None:
        return
    if not isinstance(val, t_tuple):
        raise ValueError('Expected %s, got %s' % (' or '.join([t.__name__ for t in t_tuple]), type(val).__name__))


# noinspection PyUnusedLocal
@validator
def validate_range(val, min=None, max=None, step=None, **kw):
    if val is None:
        return
    if min is not None and val < min:
        raise ValueError('Value cannot be less than %s. Got %s.' % (min, val))
    if max is not None and val > max:
        raise ValueError('Value cannot be more than %s. Got %s.' % (max, val))


# noinspection PyUnusedLocal
@validator
def validate_pattern(val, pattern, **kw):
    if val is None or pattern is None:
        return
    if not re.match(pattern, val):
        raise ValueError('Value "%s" does not match pattern "%s."' % (val, pattern))


# noinspection PyUnusedLocal
@validator
def validate_enum(val, valid_vals, **kw):
    if val is None:
        return
    if val not in valid_vals:
        raise ValueError('Invalid value. Expected %s. Got %s.' % (' or '.join(valid_vals), val))


# noinspection PyUnusedLocal
@validator
def validate_file_type(val, types, **kw):
    if val is None:
        return
    file_type, types = val.meta.file_type, types
    if types and file_type not in types:
        raise ValueError('File type is %s. Expected %s' % (file_type, ' or '.join(types)))


# noinspection PyUnusedLocal
@validator
def validate_file_exists(val, **kw):
    if val is None:
        return
    if not os.path.exists(val.file):
        raise ValueError('File does not exist: %s' % val.file)


# noinspection PyUnusedLocal
@validator
def validate_struct(val, **kw):
    if val is None:
        return
    errors = val._validate()
    if errors:
        raise ValueError(str(errors))