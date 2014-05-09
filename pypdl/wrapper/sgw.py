from pypdl.wrapper.wrapper import Wrapper, _get_method_requirements


error = NotImplementedError('Methods split, work and merge must be overridden.')


class ScatterGatherWrapper(Wrapper):
    def _entry_point(self):
        return self.job('_split', requirements=_get_method_requirements(self, 'split'), name='split')

    def _split(self):
        args_list = self.split()
        jobs = [self.job('_work', requirements=_get_method_requirements(self, 'work'),
                         name='work_%s' % ndx, args={'job': args})
                for ndx, args in enumerate(args_list)]
        return self.job('_merge', name='merge', requirements=_get_method_requirements(self, 'merge'),
                        args={'job_results': jobs})

    def _work(self, job):
        return self.work(job)

    def _merge(self, job_results):
        return self.merge(job_results)

    def split(self):
        raise error

    def work(self, job):
        raise error

    def merge(self, job_results):
        raise error
