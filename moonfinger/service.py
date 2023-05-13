import requests
from .handlers import Handlers


class RPCMeta(type):
    """The metaclass for RPC service class, implement same check."""

    def __init__(self, *args, **kwargs):
        attrs = args[2]
        if self.__name__ != "RPCService":
            session = requests.Session()
            session.mount(
                attrs["SCHEME"] + "://", requests.adapters.HTTPAdapter(max_retries=3)
            )
            self.session = session
        if "cookies" not in attrs:
            self.cookies = None
        if "headers" not in attrs:
            self.headers = {}
        if "handlers" not in attrs:
            self.handlers = Handlers()
        super().__init__(*args, **kwargs)


class RPCService(metaclass=RPCMeta):
    """The base class for RPC service classes, all service classes should inherit
    it."""

    pass

