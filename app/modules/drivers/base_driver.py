from abc import ABC


class BaseDriver(ABC):

    def probe(self, *args, **kwargs):
        raise NotImplementedError

    def device_info(self, *args, **kwargs):
        return {}

    def capability(self, *args, **kwargs):
        return {}

    def snapshot(self, *args, **kwargs):
        return None

    def rtsp(self, *args, **kwargs):
        return None

    def health(self, *args, **kwargs):
        return {}

    def configure(self, *args, **kwargs):
        return False
