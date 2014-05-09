class Container(object):
    def __init__(self, docker_client, container):
        self.docker = docker_client
        self.container = container

    def inspect(self):
        return self.docker.inspect_container(self.container)

    def is_running(self):
        return self.inspect()['State']['Running']

    def wait(self):
        if self.is_running():
            self.docker.wait(self.container)
        return self

    def is_success(self):
        self.wait()
        return self.inspect()['State']['ExitCode'] == 0

    def remove(self):
        self.wait()
        self.docker.remove_container(self.container)

    def stop(self, nice=False):
        return self.docker.stop(self.container) if nice else self.docker.kill(self.container)

    def print_log(self):
        if self.is_running():
            for out in self.docker.attach(container=self.container, stream=True):
                print(out.rstrip())
        else:
            print(self.docker.logs(self.container))

    def commit(self, message=None, conf=None):
        self.image = self.docker.commit(self.container['Id'], message=message, conf=conf)
        return self
