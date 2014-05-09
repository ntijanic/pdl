import json


def classify(obj):
    """ Make a deep copy of obj that contains classes in place of {"$type": "<type>", ...} dicts """
    from pypdl.job import Job, Resources, Outputs
    from pypdl.wrapper.exceptions import JobError
    type_map = {
        'job': Job,
        'resources': Resources,
        'outputs': Outputs,
        'error': JobError,
    }
    if isinstance(obj, (list, tuple)):
        return [classify(item) for item in obj]
    if isinstance(obj, dict):
        if '$$type' not in obj:
            return {k: classify(v) for k, v in obj.iteritems()}
        return type_map[obj.pop('$$type')].from_dict(obj)
    return obj


def from_json(str_or_fp, object_hook=None):
    """ Load json and make classes from certain dicts (see classify() docs) """
    if isinstance(str_or_fp, basestring):
        obj = json.loads(str_or_fp, object_hook=object_hook)
    else:
        obj = json.load(str_or_fp, object_hook=object_hook)
    return classify(obj)


def to_json(obj, fp=None):
    default = lambda o: o.__json__() if callable(getattr(o, '__json__', None)) else str(o)
    kwargs = dict(default=default, indent=2, sort_keys=True)
    return json.dump(obj, fp, **kwargs) if fp else json.dumps(obj, **kwargs)