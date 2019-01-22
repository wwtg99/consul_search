import re
from hsettings import Settings
from consulsearch.client import ConsulClient


class ConsulKvSearch:

    def __init__(self, settings: Settings):
        self._settings = settings
        self._client = ConsulClient(**settings.get('consul', {}))

    def get(self, key, recurse=False, raw=False, keys=False, **kwargs):
        index, vals = self._client.kv().get(key=key, recurse=recurse, keys=keys, **kwargs)
        if not raw and not keys and vals:
            res = []
            for val in vals:
                try:
                    v = val['Value'].decode('utf8') if val['Value'] is not None else None
                except Exception as e:
                    v = val['Value']
                res.append((val['Key'], v))
            return res
        return vals

    def search_key(self, query, root='', limit=10) -> list:
        keys = self.get(key=root, recurse=True, keys=True)
        pattern = re.compile(query)
        res = []
        for key in keys:
            s = pattern.search(key)
            if s:
                res.append({'key': key, 'groups': s.groups()})
                if len(res) >= limit:
                    break
        return res

    def search_value(self, query, root='', limit=10) -> list:
        kvs = self.get(key=root, recurse=True)
        pattern = re.compile(query)
        res = []
        for kv in kvs:
            if not kv[1]:
                continue
            s = pattern.search(kv[1])
            if s:
                res.append({'key': kv[0], 'value': kv[1], 'groups': s.groups()})
                if len(res) >= limit:
                    break
        return res

    @property
    def settings(self) -> Settings:
        return self._settings
