import logging
import signal
import shlex
from pipes import quote

import docker
from docker.client import APIError

from pypdl.docker.container import Container
from pypdl.docker.utils import find_image, parse_repository_tag
from pypdl.util import handle_signal, import_name


class Runner(object):
    PIP_INSTALL = 'pip install {} .'
    WORKING_DIR = '/mnt/host'  # TODO: Mount points in config

    def __init__(self, docker_client, config, **kwargs):
        self.client = docker_client
        self.config = config
        self.base_cmd = config['base_cmd']
        self.image_id = config['image_id']
        self.dns = config['docker_dns']
        self.docker_config = kwargs
        self.last_container = None

    def run(self, command):
        volumes = {'/sb': {}, Runner.WORKING_DIR: {}}
        volumes.update(self.docker_config.pop('Volumes', {}))
        binds = {self.config['working_dir']: Runner.WORKING_DIR + ":rw"}
        binds.update(self.docker_config.pop('__binds__', {}))
        logging.info("Running command %s\nVolumes: %s\nBinds: %s", command, volumes, binds)
        config = make_config(self.image_id, command)
        config['Volumes'] = volumes
        config['WorkingDir'] = Runner.WORKING_DIR
        config['Dns'] = self.dns
        config.update(self.docker_config)

        try:
            cont = self.client.create_container_from_config(config)
        except APIError as e:
            # 404 means image was not found
            if e.response.status_code == 404:
                logging.info("Trying to fetch image %s" % self.image_id)
                repo, tag = parse_repository_tag(self.image_id)
                self.client.pull(repo, tag)
                self.image_id = find_image(self.client, repo, tag)
                config['Image'] = self.image_id
                cont = self.client.create_container_from_config(config)
            else:
                raise
        self.client.start(container=cont, binds=binds)
        self.last_container = Container(self.client, cont)
        return self.last_container

    def run_and_print(self, command, remove=False):
        cont = self.run(command)

        def handler(signum, frame):
            logging.info('Received %s: %s', signum, frame)
            cont.stop()

        with handle_signal(handler, signal.SIGTERM, signal.SIGINT):
            cont.wait()

        cont.print_log()
        if remove:
            cont.remove()

    @property
    def cmd_install(self):
        pip_options = self.config.get('pip_options', '')
        return Runner.PIP_INSTALL.format(pip_options)

    def run_install(self):
        return self.run(shlex.split(self.cmd_install))

    def run_wrapper(self, input_path, cwd=None):
        run_full = self.base_cmd + ['run-full', '-i', input_path]
        if cwd:
            run_full += ['--cwd', cwd]
        self.run_and_print(multi_command(self.cmd_install, run_full), remove=True)

    def run_job(self, input_path, output_path, cwd=None):
        cli_run = self.base_cmd + ['run', '-i', input_path, '-o', output_path]
        if cwd:
            cli_run += ['--cwd', cwd]
        cmd = multi_command(self.cmd_install, cli_run)
        self.run_and_print(cmd, remove=False)

    def run_tests(self, wrapper):
        cmd = multi_command(self.cmd_install, ['nosetests', wrapper])
        self.run_and_print(cmd, remove=False)

    def schema(self, output=None):
        extra = ['--output', output] if output else []
        name = self.config['project_name']
        cli_schema = self.base_cmd + ['schema'] + (['--package', name] if name else []) + extra
        cmd = multi_command(self.cmd_install, cli_schema)
        self.run_and_print(cmd, remove=False)


class ImageRunner(Runner):
    def __init__(self, docker_client, project, **kwargs):
        Runner.__init__(self, docker_client, project, **kwargs)
        image_id = project.image_id
        info = docker_client.inspect_image(image_id)
        self.base_cmd = info['config']['Cmd']

    def run_wrapper(self, input_path, cwd=None):
        run_full = self.base_cmd + ['run-full', '-i', input_path]
        if cwd:
            run_full += ['--cwd', cwd]
        self.run_and_print(run_full)

    def run_job(self, input_path, output_path, cwd=None):
        run = self.base_cmd + ['run', '-i', input_path, '-o', output_path]
        if cwd:
            run += ['--cwd', cwd]
        self.run_and_print(run)

    def run_tests(self, wrapper):
        self.run_and_print(['nosetests', wrapper])

    def run_install(self):
        raise NotImplementedError("Method 'run_install' not implemented for class ImageRunner.")

    def schema(self, output=None):
        cmd = self.base_cmd + ['schema']
        cmd += ['--output', output] if output else []
        self.run_and_print(cmd)


def make_config(image, command):
    return {'Image': image,
            'Cmd': command,
            'AttachStdin': False,
            'AttachStdout': False,
            'AttachStderr': False,
            'Tty': False,
            'Privileged': False,
            'Memory': 0}


def multi_command(*args):
    strings = [e if isinstance(e, basestring) else shell_join(e) for e in args]
    return ['/bin/sh', '-c', ' && '.join(strings)]


def shell_join(args):
    return ' '.join([quote(s) for s in args])


def make_client(project, **kwargs):
    if project.context.get('docker_client_class'):
        cls = import_name(project.context.get('docker_client_class'))
        return cls(project, **kwargs)

    args = {'base_url': project.docker_daemon_url,
            'version': project.docker_protocol_version}
    args.update(kwargs)
    docker_client = docker.Client(**args)
    return docker_client


def make_runner(project, **kwargs):
    if project.project_data:
        return Runner(make_client(project), project, **kwargs)
    return ImageRunner(make_client(project), project, **kwargs)
