import logging
import os
import stat
from pypdl.protocol import from_json, to_json
from pypdl.wrapper.exceptions import ValidationError, JobError, ProtocolError
from pypdl.job import BaseJob, Job, Outputs
from pypdl.util import import_name


class Executor(object):
    def execute(self, job):
        pass

    def exec_wrapper_job(self, job):
        pass


class Tassadar(Executor):
    def __init__(self):
        self.results = {}
        self.job_executors = {
            Job: self.exec_wrapper_job,
        }

    def execute(self, job):
        logging.debug('Job started: %s' % to_json(job))
        if job.job_id in self.results:
            return self.results[job.job_id]
        for key, val in job.args.iteritems():
            job.resolved_args[key] = self.resolve(val)
        if job.__class__ not in self.job_executors and not callable(job):
            raise NotImplementedError('Tassadar unable to run job of type %s.' % job.__class__.__name__)
        job.status = BaseJob.RUNNING
        result = job() if callable(job) else self.job_executors[job.__class__](job)
        self.results[job.job_id] = result
        job.status = BaseJob.DONE
        if isinstance(result, BaseJob):
            return self.execute(result)
        logging.debug('Job result: %s' % to_json(result))
        return result

    def exec_wrapper_job(self, job):
        cls = import_name(job.wrapper_id)
        try:
            wrp = cls(inputs=job.resolved_args.pop('$inputs', {}),
                      params=job.resolved_args.pop('$params', {}),
                      context=job.context,
                      resources=job.resources)
            result = wrp(job.resolved_args.pop('$method', None), job.resolved_args)
        except (ValidationError, ProtocolError):
            raise
        except Exception as e:
            msg = get_exception_message(e)
            logging.exception('Job failed: %s', msg)
            raise JobError(msg)
        return result if result is not None else Outputs(wrp.outputs.__json__())

    def resolve(self, val):
        if isinstance(val, BaseJob):
            return self.execute(val)
        if isinstance(val, (list, tuple)):
            return [self.resolve(item) for item in val]
        if isinstance(val, dict):
            return {k: self.resolve(v) for k, v in val.iteritems()}
        return val


def get_exception_message(exception):
    return exception.message or str(exception)


class Adun(Executor):
    def __init__(self, runner):
        self.runner = runner

    def execute(self, job, one_container=False):
        logging.info('Job started: %s' % job.job_id)
        logging.debug('Job: %s' % to_json(job))

        if one_container:
            return self.exec_wrapper_full(job)

        job.resolved_args = self.resolve(job.args)
        job.status = Job.RUNNING
        result = self.exec_wrapper_job(job)
        if isinstance(result, JobError):
            raise result
        job.status = Job.DONE
        if isinstance(result, Job):
            return self.execute(result)
        logging.info('Job finished: %s' % to_json(job))
        return result

    def exec_wrapper_full(self, job):
        job_dir = job.job_id
        os.mkdir(job_dir)
        os.chmod(job_dir, os.stat(job_dir).st_mode | stat.S_IROTH | stat.S_IWOTH | stat.S_IXOTH)
        os.chdir(job_dir)
        with open('__in__.json', 'w') as fp:
            logging.debug('Writing job order to %s', os.path.abspath('__in__.json'))
            to_json(job, fp)
        self.runner.run_wrapper('__in__.json', cwd=job_dir)
        with open('__out__.json') as fp:
            logging.debug('Reading job output from %s', os.path.abspath('__out__.json'))
            result = from_json(fp)
        os.chdir('..')
        return result

    def exec_wrapper_job(self, job):
        job_dir = job.job_id
        os.mkdir(job_dir)
        os.chmod(job_dir, os.stat(job_dir).st_mode | stat.S_IROTH | stat.S_IWOTH | stat.S_IXOTH)
        in_file, out_file = [os.path.join(job_dir, f) for f in '__in__.json', '__out__.json']
        with open(in_file, 'w') as fp:
            logging.debug('Writing job order to %s', in_file)
            to_json(job, fp)
        self.runner.run_job('__in__.json', '__out__.json', cwd=job_dir)
        with open(out_file) as fp:
            logging.debug('Reading job output from %s', out_file)
            result = from_json(fp)
        from subprocess import Popen
        Popen(['sudo chmod -R 777 ' + job_dir], shell=True)  # TODO: remove
        Popen(['sudo chown -R 1001:1001 ' + job_dir], shell=True)  # TODO: remove
        return result

    def resolve(self, val):
        if isinstance(val, Job):
            return self.execute(val)
        if isinstance(val, (list, tuple)):
            return [self.resolve(item) for item in val]
        if isinstance(val, dict):
            return {k: self.resolve(v) for k, v in val.iteritems()}
        return val
