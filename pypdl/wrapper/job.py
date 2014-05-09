import uuid
from pypdl.wrapper.exceptions import NoWrapperIdError, NoResourcesError

from pypdl.util import wrap_in_list
from pypdl.protocol import classify


class Resources(object):
    CPU_NEGLIGIBLE, CPU_SINGLE, CPU_ALL = 0, 1, -1

    def __init__(self, mem_mb=100, cpu=CPU_ALL, high_io=False):
        self.mem_mb = mem_mb
        self.cpu = cpu
        self.high_io = high_io

    def __call__(self, obj):
        obj._requirements = self
        return obj

    def __json__(self):
        return {
            '$$type': 'resources',
            'mem_mb': self.mem_mb,
            'cpu': self.cpu,
            'high_io': self.high_io,
        }

    @classmethod
    def from_dict(cls, d):
        return cls(**d)


class Outputs(object):
    def __init__(self, outputs_dict=None):
        self.outputs = outputs_dict
        for k, v in self.outputs.items():
            if isinstance(v, basestring):
                self.outputs[k] = [v]
            elif v is None:
                self.outputs[k] = []
            else:
                self.outputs[k] = list(v)

    def __json__(self):
        return {
            '$$type': 'outputs',
            'outputs': self.outputs,
        }

    @classmethod
    def from_dict(cls, d):
        return cls(outputs_dict=d.get('outputs', {}))

    def __repr__(self):
        return 'Outputs(%s)' % self.outputs


class BaseJob(object):
    PENDING, RUNNING, DONE = 'pending', 'running', 'done'

    def __init__(self, job_id=None, args=None):
        self.job_id = job_id or 'job-%s' % uuid.uuid4()
        self.args = args or {}
        self.resolved_args = {}
        self.status = BaseJob.PENDING

    def __json__(self):
        return {
            '$$type': 'job',
            'job_id': self.job_id,
            'args': self.resolved_args or self.args,
        }


class Job(BaseJob):
    def __init__(self, wrapper_id, job_id=None, resources=None, context=None, args=None,
                 method=None, inputs=None, params=None):
        if not isinstance(wrapper_id, basestring):
            wrapper_id = '.'.join([wrapper_id.__module__, wrapper_id.__name__])
        BaseJob.__init__(self, job_id, args)
        self.wrapper_id = wrapper_id
        self.context = context or {}
        self.resources = resources or Resources()
        self.args['$inputs'] = inputs or self.args.get('$inputs', {})
        self.args['$params'] = params or self.args.get('$params', {})
        self.args['$method'] = method or self.args.get('$method', None)
        self.job_id = job_id or '%s-%s-%s' % \
            (wrapper_id[wrapper_id.rfind('.') + 1:], self.args['$method'] or 'initial', uuid.uuid4())

    def __json__(self):
        return dict(BaseJob.__json__(self),
                    wrapper_id=self.wrapper_id,
                    context=self.context,
                    resources=self.resources)

    @classmethod
    def from_dict(cls, obj):
        if 'wrapper_id' not in obj:
            raise NoWrapperIdError('Wrapper ID not specified.')
        if 'resources' not in obj:
            raise NoResourcesError('Resources not specified')
        return cls(wrapper_id=obj['wrapper_id'],
                   job_id=obj.get('job_id'),
                   args=classify(obj.get('args', {})),
                   resources=classify(obj.get('resources')),
                   context=obj.get('context'))


class Join(BaseJob):
    def __init__(self, *jobs):
        BaseJob.__init__(self, args={'jobs': jobs})

    def __call__(self):
        result = {}
        # Assume dict job results are outputs struct. Join with others to act as inputs downstream.
        for job_result in filter(lambda i: isinstance(i, dict), self.resolved_args['jobs']):
            for k, v in job_result.iteritems():
                result[k] = wrap_in_list(result[k], v) if k in result else wrap_in_list(v)
        return result


class Do(BaseJob):
    def __init__(self, func, **args):
        BaseJob.__init__(self, args=args)
        self.func = func

    def __call__(self):
        return self.func(**self.resolved_args) if callable(self.func) else self.func


class Connect(BaseJob):
    def __init__(self, outputs, src_name, dst_name):
        BaseJob.__init__(self)
        self.args['outputs'] = outputs
        self.src_name = src_name
        self.dst_name = dst_name

    def __call__(self):
        return {self.dst_name: self.resolved_args['outputs'][self.src_name]}
