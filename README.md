# moonfinger

A RPC tool for HTTP API 

Automatically handle authentication, result mashaller, and pages.


## Usage

```python
from moonfinger import RPCService, communicate

class SomeHTTPService(RPCService):
    NAME = "service_name"
    SCHEME = "https"

    ADDRESS = "localhost"

    @classmethod
    @communicate("/path/to/api", params={"param": "ABC"})
    def get_all_experiment_list(cls, *, response) -> list:
        return response.json()

```