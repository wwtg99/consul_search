import re
import logging
from hsettings import Settings
import consul
from diskcache import Cache


def get_consul_client(**kwargs):
    return consul.Consul(**kwargs)


class SearchCache:

    def __init__(self, settings: Settings):
        self._settings = settings
        self._cache_file = settings.get('search.cache', '.cache')
        self.cache_ttl = settings.get('consul.cache_ttl', 600)

    def get_cache(self, key, default=None, expire_time=False):
        with Cache(self._cache_file) as ref:
            return ref.get(key=key, default=default, expire_time=expire_time)

    def set_cache(self, key, value, expire):
        with Cache(self._cache_file) as ref:
            ref.set(key=key, value=value, expire=expire)

    def clear_cache(self):
        with Cache(self._cache_file) as ref:
            ref.clear()

    @property
    def settings(self) -> Settings:
        return self._settings


class ConsulKvSearch(SearchCache):

    def __init__(self, settings: Settings):
        super().__init__(settings)
        self._client = get_consul_client(**settings.get('consul', {}))
        self._root = settings.get('search.root', '')
        self._limit = settings.get('search.limit', 10)
        self._regex = bool(settings.get('search.regex', False))
        self._field = ''

    def get(self, key, recurse=False, raw=False, keys=False, **kwargs):
        """
        Get key value from consul kv.

        :param key:
        :param recurse:
        :param raw:
        :param keys:
        :param kwargs:
        :return:
        """
        index, vals = self._client.kv.get(key=key, recurse=recurse, keys=keys, **kwargs)
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

    def search(self, query, field) -> list:
        """
        Search consul.

        :param query:
        :param field:
        :return: result list
        """
        self._field = field
        if field == 'values':
            return self.search_values(query)
        else:
            return self.search_keys(query)

    def search_keys(self, query) -> list:
        """
        Search query in the key.

        :param query:
        :return: result list
        """
        cache_key = self._get_cache_key(self._field)
        data = self.get_cache(cache_key)
        if not data:
            data = self.get(key=self._root, recurse=True, keys=True)
            self.set_cache(cache_key, data, expire=self.cache_ttl)
        if self._regex:
            query = re.compile(query)
        res = []
        for d in data:
            find = False
            try:
                find = self._search_match(d, query)
            except Exception as e:
                logging.warning('Failed to search in {}, skip'.format(d))
            if find:
                res.append(d)
                if len(res) >= self._limit:
                    break
        return res

    def search_values(self, query) -> list:
        """
        Search query in the value.

        :param query:
        :return: result list
        """
        cache_key = self._get_cache_key(self._field)
        data = self.get_cache(cache_key)
        if not data:
            data = self.get(key=self._root, recurse=True)
            self.set_cache(cache_key, data, expire=self.cache_ttl)
        if self._regex:
            query = re.compile(query)
        res = []
        for d in data:
            if not d[1]:
                continue
            find = False
            try:
                find = self._search_match(d[1], query)
            except Exception as e:
                logging.warning('Failed to search in {}, skip'.format(d[1]))
            if find:
                res.append(d)
                if len(res) >= self._limit:
                    break
        return res

    def _get_cache_key(self, field) -> str:
        return ':'.join([
            str(self.settings.get('consul.host', '')),
            str(self.settings.get('consul.port', 80)),
            str(self._root),
            str(field)
        ])

    def _search_match(self, data, query) -> bool:
        if self._regex:
            s = query.search(data)
            return True if s else False
        else:
            return query in data
