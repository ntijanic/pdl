import pkg_resources
import argparse
import os
import sys
import logging
import logging.config

from pypdl.wrapper.exceptions import exit_code_for_exception, NotAJobError, ValidationError, JobError, ProtocolError
from pypdl.protocol import from_json, to_json
from pypdl.job import Job
from pypdl.util import import_name
from pypdl.wrapper.wrapper import Wrapper
from pypdl.executor import Tassadar


def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--logging-config', help='Path to json file for logging.config.dictConfig', default='')
    subparsers = parser.add_subparsers()

    sch = subparsers.add_parser('schema', help='Print schema for all wrappers on stdout')
    sch.set_defaults(cmd_func=cmd_schema)
    sch.add_argument('--package', help='Look for wrappers in this package.')
    sch.add_argument('--output', help='Print schema to this file.', default='')

    run = subparsers.add_parser('run', help='Run wrapper job.')
    run.set_defaults(cmd_func=cmd_run, run_method=run_job)
    run.add_argument('--cwd', default='.', help='cd here before running job.')
    run.add_argument('-i', '--input', default='__in__.json', help='JSON file that contains arguments for wrapper job.')
    run.add_argument('-o', '--output', default='__out__.json', help='Where to write the job result.')

    run = subparsers.add_parser('run-full', help='Run whole wrapper.')
    run.set_defaults(cmd_func=cmd_run, run_method=run_wrapper)
    run.add_argument('--cwd', default='.', help='cd here before running job.')
    run.add_argument('-i', '--input', default='__in__.json', help='JSON file with entry point args')
    run.add_argument('-o', '--output', default='__out__.json', help='Where to write the outputs.')

    return parser


def get_wrapper_schemas(package=None):
    group = 'pypdl.wrappers'
    map_id_class = {}
    classname = lambda wrp_cls: '.'.join([wrp_cls.__module__, wrp_cls.__name__])
    if package:
        pkg = import_name(package)
        for var in dir(pkg):
            obj = getattr(pkg, var)
            if isinstance(obj, type) and issubclass(obj, Wrapper):
                map_id_class[classname(obj)] = obj

    for entry_point in pkg_resources.iter_entry_points(group=group):
        wrp_cls = entry_point.load()
        full_class_name = classname(wrp_cls)
        map_id_class[full_class_name] = wrp_cls
    return [dict(schema=v._get_schema(), wrapper_id=k) for k, v in map_id_class.iteritems()]


def run_job(job):
    job.resolved_args = job.args
    return Tassadar().exec_wrapper_job(job)


def run_wrapper(job):
    return Tassadar().execute(job)


# noinspection PyUnusedLocal
def cmd_schema(output, **kwargs):
    sch = get_wrapper_schemas(kwargs.pop('package', None))
    if output:
        with open(output, 'w') as fp:
            to_json(sch, fp)
    else:
        print(to_json(sch))


# noinspection PyUnusedLocal
def cmd_run(cwd, input, output, run_method=run_job, **kwargs):
    if not os.path.isdir(cwd):
        raise Exception('No such directory: %s', cwd)
    os.chdir(cwd)

    if not os.path.isfile(input):
        raise Exception('No such file: %s' % input)
    with open(input) as fp:
        job = from_json(fp)
    if not isinstance(job, Job):
        raise NotAJobError('Input JSON must describe a job.')

    try:
        result = run_method(job)
    except JobError as e:
        result = e

    with open(output, 'w') as fp:
        to_json(result, fp)


def run_script():
    args = vars(create_parser().parse_args())
    if args['logging_config']:
        with open(args['logging_config']) as fp:
            logging.config.dictConfig(from_json(fp))
    try:
        args['cmd_func'](**args)
    except ProtocolError as e:
        logging.exception("Bad Job: %s", args)
        return exit_code_for_exception(e)
    except ValidationError as e:
        logging.exception("Input or params validation failed: %s", args)
        return exit_code_for_exception(e)
    except JobError as e:
        logging.exception("Wrapper error: %s", args)
        return exit_code_for_exception(e)
    except Exception:
        logging.exception("Internal error: %s", args)
        return 120
    return 0


if __name__ == '__main__':
    sys.exit(run_script())
