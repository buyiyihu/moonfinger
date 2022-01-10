

# TODO: For cookie based authorization, request have to be prepared afresh, implement it here
class Handlers:
    """
    A handler class for exceptional scenarios.
    Usage:
        Initialize this class and put the instance as class attribute of Service class:

        class SomeService:
            handlers = Handlers()
        Write your own handle methods inside the service class, and decorate them with
        the instance, and pass condition detecting function as a parameter of the decorator.

        A handle method will be passed in 4 keyword parameters:
            - service: the Service class
            - request: the just-sent requests.Request instance
            - prepared: the requests.PreparedRequest instance from the request instance above
            - communicator: the communicate instance
        Accept the parameters you need explicitly, add a `**kwargs` if the rest are not needed.
        Please note: all the parameters have to be keyword-only.

        ...
            @handlers(lambda response:response.status_code==202)
            def handler_for_202(*, service, request, **kwargs):
                ...
        The handler has a default `is_ok` method to determine whether the response is ok and
        the workflow should move on, the default logic is `response.status_code==200`,
        it also has a `set_ok` decorator to set the ok condition determining method.

    """

    def __init__(self):
        self._handlers = {}

    def is_ok(self, response):
        return response.status_code == 200

    @property
    def handlers(self):
        return self._handlers

    def set_ok(self, f):
        self.is_ok = f
        return f

    def __call__(self, flag):
        def wrapper(f):
            self._handlers[flag] = f
            return f

        return wrapper

