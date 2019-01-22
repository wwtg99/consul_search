import consul


class ConsulClient:

    def __init__(self, **kwargs):
        self._client = consul.Consul(**kwargs)

    def kv(self):
        return self.client.kv

    @property
    def client(self):
        return self._client
