DEFAULT_CONFIG = {
    'image_id': 'ubuntu',
    'shell_type': 'bash',
    'pip_options': '-q --download-cache /sb/pip_cache',
    'sdk_runner_command': ['/usr/bin/python', '-m', 'pypdl.cli'],
    'docker_daemon_url': 'unix://var/run/docker.sock',
    'docker_protocol_version': '1.8',
    'docker_entrypoint': ['/sbin/my_init', '--quiet', '--']
}


class Config(dict):
    def __init__(self, **kwargs):
        super(dict, self).__init__()
        self.update(DEFAULT_CONFIG, **kwargs)
