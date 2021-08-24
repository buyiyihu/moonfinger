import inspect
from copy import deepcopy
from functools import partial, reduce, wraps
import requests

# TODO: Setup logger and establiish error

class communicate:

    """A class for rpc methods.

    Usage:
        Use it as class decorator for each RPC method of the RPC Sercive class.
        Claim the url path method and more parameters for the method.
        If passed, the Sercive's attributes with the same name as the passed parameters will
        be OVERWRITTEN.
    """

    # A default value for page size for traversing when not assigned
    DEFAULT_SIZE = 50
    # Default value for page count when traversing, a safety for dead loop
    TRAVERSE_MAX = 50

    def __init__(
        self,
        path,
        method="GET",
        params=None,
        data=None,
        headers=None,
        hooks=None,
        **kwargs,
    ):
        self.path = path
        self._path = None
        self.method = method
        self.params = params
        self.data = data
        self.header_update = headers
        self.headers = None
        self.path_param = []
        self._find_path_params(path)
        self.request_kwargs = kwargs
        self.hooks = hooks or {}

    def _find_path_params(self, path):
        # XXX: replace this with a RE (buyiyihu)
        start = path.find("{")
        while start > -1:
            end = path.find("}")
            self.path_param.append(path[start + 1 : end])
            path = path[end + 1 :]
            start = path.find("{")

    def __call__(self, func):
        """Decorator for RPC methods.Run a parameter check when loading."""
        if not all(
            map(
                lambda x: x.kind
                in (inspect.Parameter.KEYWORD_ONLY, inspect.Parameter.VAR_KEYWORD),
                list(inspect.signature(func).parameters.values())[1:],
            )
        ):
            raise RuntimeError(
                "Noncompliant parameters for the method, only key-word-only and var-keyword supported. Put a * before all parameters and after cls"
            )
        if "{" not in self.path:
            self._path = self.path

        @wraps(func)
        def wrapper(*args, **kwargs):
            if "response" in kwargs or "responses" in kwargs:
                raise RuntimeError("You cannot pass in response(s) manually")
            service = args[0]
            if self._path is None:
                _params = {
                    key: kwargs.get(key)
                    for key in self.path_param
                    if kwargs.get(key) is not None
                }
                self._path = self.path.format(**_params)
            url = service.SCHEME + "://" + service.ADDRESS + self._path
            _kwargs = deepcopy(kwargs)
            data = _kwargs.pop("data", {})
            params = _kwargs
            if self.params or params:
                params.update(self.params) if self.params else params
            if self.data or data:
                data.update(self.data) if self.data else data
            else:
                data = None
            if self.header_update:
                self.headers = deepcopy(service.headers) if service.headers else {}
                self.headers.update(self.header_update)
            else:
                self.headers = service.headers

            cookies = service.cookies or None

            if hasattr(wrapper, "_traverse"):
                responses = []
                traverser = wrapper._traverse
                size = service.PAGE_SIZE and traverser["size"] and self.DEFAULT_SIZE
                params.update({traverser["page_size"]: size})
                req = partial(
                    requests.Request,
                    self.method,
                    url=url,
                    data=self.data,
                    headers=self.headers,
                    cookies=cookies,
                    **self.request_kwargs,
                )
                cnt, response = 0, None
                _chain = [response]
                _chain.extend(traverser["flag"])
                while cnt == 0 or reduce(lambda res, y: y(res), _chain):
                    # FIXME: What if exceptions or complex logic (buyiyihu)
                    params.update({traverser["page"]: cnt + 1})
                    request = req(params=params)
                    prepared = service.session.prepare_request(request)
                    response = service.session.send(prepared)
                    response = self.handle(service, request, prepared, response)
                    responses.append(response)
                    cnt += 1
                    _chain[0] = response
                    if cnt >= self.TRAVERSE_MAX:
                        print(
                            f"==RPC ERROR: too many times for pagination\n {url}|{self.method}|{params}"
                        )
                        raise RuntimeError(
                            f"Too many times for pagination,URL:{url},times:{cnt},params:{params}"
                        )
                return func(*args, **kwargs, responses=responses)

            else:
                params = params or None
                request = requests.Request(
                    self.method,
                    url=url,
                    params=params,
                    data=self.data,
                    headers=self.headers,
                    cookies=cookies,
                    **self.request_kwargs,
                )
                prepared = service.session.prepare_request(request)
                response = service.session.send(prepared)
                response = self.handle(service, request, prepared, response)
                return func(*args, **kwargs, response=response)

        return wrapper

    def handle(self, service, request, prepared, response):
        """Execute the handlers for each designated scenarios."""
        if service.handlers.is_ok(response):
            print(f"==RPC successfully: {service.NAME}  {self._path}")
            return response
        for flag, operation in service.handlers.handlers.items():
            if flag(response):
                # FIXME: class method or instance method.(buyiyihu)
                response = operation(
                    service=service,
                    request=request,
                    prepared=prepared,
                    communicator=self,
                )
                # XXX: Optimize params, too verbose.(buyiyihu)
        if service.handlers.is_ok(response):
            print(f"==RPC successfully: {service.NAME}  {self._path}")
            return response
        else:
            print(
                f"==RPC failed: {service.NAME} {self._path}: {response.status_code}-{response.reason}-{response.text}"
            )
            raise RuntimeError(
                f"Got {response.status_code} at {service.NAME}:{self._path}\n {response.reason}-{response.text} \n"
            )

def traverse_pagination(page="page", page_size="page_size", size=50, *, flag):
    """A pagination traverser.

    Put this decorator upon a RPC method, the api will be taken as a
    pagination, and will be automatically traversed.
    """
    def wrapper(func):
        func._traverse = dict(page=page, page_size=page_size, size=size, flag=flag)
        return func
    return wrapper
