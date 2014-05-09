import tempfile
import os

from pypdl.wrapper.exceptions import InputsValidationError, ParamsValidationError, NoSuchMethodError
from pypdl.wrapper.schema import SchemaBased, IODef
from pypdl.job import Job, Resources, Outputs
from pypdl.executor import Tassadar


class Wrapper(object):
    class Inputs(IODef):
        pass

    class Outputs(IODef):
        pass

    class Params(SchemaBased):
        pass

    def __init__(self, inputs, params, context=None, resources=None):
        self.inputs = inputs if isinstance(inputs, IODef) else self.Inputs(**inputs)
        self.params = params if isinstance(params, SchemaBased) else self.Params(**params)
        self.outputs = self.Outputs()
        self.context = context or {}
        self.resources = resources or Resources()
        self.inputs._load_meta()

    def execute(self):
        pass

    def __call__(self, method, args):
        method = method or '_entry_point'
        if not callable(getattr(self, method, None)):
            raise NoSuchMethodError('Wrapper has no method %s' % method)
        result = getattr(self, method)(**args)
        if result is None:
            self.outputs._save_meta()
            return Outputs(self.outputs.__json__())
        return result

    def get_requirements(self):
        return _get_method_requirements(self, 'execute') or Resources()

    def _entry_point(self):
        errors = self.inputs._validate()
        if errors:
            raise InputsValidationError(unicode(self.__class__)+u'\n'+unicode(errors))
        errors = self.params._validate()
        if errors:
            raise ParamsValidationError(unicode(errors))
        return self.job('execute', requirements=self.get_requirements())

    @classmethod
    def _get_schema(cls):
        return {
            'inputs': cls.Inputs._get_schema(),
            'outputs': cls.Outputs._get_schema(),
            'params': cls.Params._get_schema(),
        }

    # noinspection PyUnusedLocal
    def job(self, method=None, args=None, requirements=None, name=None):
        return Job(self.__class__, method=method,
                   resources=requirements or _get_method_requirements(self, method) or Resources(), args=args,
                   inputs=self.inputs.__json__(), params=self.params.__json__(), context=self.context)

    def test(self):
        test_exec_dir = tempfile.mkdtemp(prefix='test_%s_' % self.__class__.__name__, dir='.')
        os.chdir(test_exec_dir)
        try:
            self.inputs._validate(assert_=True)
            self.params._validate(assert_=True)
            self.inputs._save_meta()
            outputs = Tassadar().execute(self.job()).outputs
            self.outputs = self.Outputs(**outputs)
            self.outputs._load_meta()
            self.outputs._validate(assert_=True)
        finally:
            os.chdir('..')
        return self.outputs

    def get_allocated_memory(self, units='MB'):
        units = units.upper()
        converter = {
            'B': lambda b: b,
            'KB': lambda b: b / 1024,
            'MB': lambda b: b / 1024**2,
            'GB': lambda b: b / 1024**3,
        }
        if units not in converter:
            raise ValueError('Units argument must be one of: %s' % converter.keys())
        return converter[units](self.resources.mem_mb * 1024**2)


def _get_method_requirements(wrapper, method_name):
    if not method_name:
        return getattr(wrapper, '_requirements', None)
    m = getattr(wrapper, method_name, None)
    return getattr(m, '_requirements', None) or getattr(wrapper, '_requirements', None)