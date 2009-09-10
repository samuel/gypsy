
import random
import time

class Stash(object):
    def __init__(self, cache, key_prefix=None):
        self.cache = cache
        self.key_prefix = key_prefix or ""

    def _gen_key(self, key, namespace=None):
        return "%s%s:%s" % (self.key_prefix,
            namespace and self._get_namespace_key(namespace) or "", key)

    def _get_namespace_key(self, name):
        """
        Returns the key for the given namespace generating it if necessary.
        The namespace key is used to mass invalidate a group of keys that
        belong to the namespace.
        """
        key = "%snamespace:%s" % (self.key_prefix, name)
        ns_key = self.cache.get(key)
        if not ns_key:
            ns_key = str(random.randint(0, 2000000000))
            self.cache.set(key, ns_key, 60*60*24*10)
        ns_key = "ns:%s:%s" % (name, ns_key)
        return ns_key

    def clear_namespace(self, name):
        """
        Delete the key for the given namespace thus invalidating all
        keys in that namespace.
        """
        key = "%snamespace:%s" % (self.key_prefix, name)
        if hasattr(getattr(self.cache, '_cache', None), 'incr'):
            try:
                self.cache._cache.incr(key)
            except ValueError:
                pass
        else:
            self.cache.delete(key)

    def __contains__(self, key):
        return key in self.cache

    def __call__(self, key, func, timeout=None, namespace=None, raw_key=False):
        if not isinstance(key, basestring):
            return self.__call_many(key, func, timeout, namespace, raw_key)

        if not raw_key:
            key = self._gen_key(key, namespace)

        val = self.get(key, raw_key=True)
        if val is None:
            if hasattr(timeout, '__call__'):
                start_time = time.time()
                val = func()
                end_time = time.time()
                timeout = timeout(end_time - start_time)
            else:
                val = func()
            self.set(key, val, timeout, raw_key=True)

        return val

    def __call_many(self, keys, func, timeout=None, namespace=None, raw_key=False):
        okeys = keys
        if not raw_key:
            keys = dict((self._gen_key(k, namespace), k) for k in set(keys))

        vals = self.get_many(keys, raw_key=True)
        if keys:
            if hasattr(timeout, '__call__'):
                start_time = time.time()
                newvals = func(keys.values())
                end_time = time.time()
                timeout = timeout(end_time - start_time)
            else:
                newvals = func(keys.values())
            for k, v in newvals.iteritems():
                inv = dict((v,k) for k,v in keys.iteritems())
                self.set(inv[k], v, timeout, raw_key=True)
            vals.update(newvals)

        return vals

    def get(self, key, namespace=None, raw_key=False):
        if not raw_key:
            key = self._gen_key(key, namespace)
        return self.cache.get(key)

    def set(self, key, value, timeout=None, namespace=None, raw_key=False):
        if not raw_key:
            key = self._gen_key(key, namespace)
        self.cache.set(key, value, timeout)

    def delete(self, key, namespace=None, raw_key=False):
        if not raw_key:
            key = self._gen_key(key, namespace)
        self.cache.delete(key)

    def get_many(self, keys, namespace=None, raw_key=False):
        """
        If raw_key is True, keys must be a dict and it WILL BE modified, and
        upon return keys will include only the keys that were not in the cache.
        """
        if not raw_key:
            keys = dict((self._gen_key(k, namespace), k) for k in set(keys))

        d = {}

        if keys:
            for k, v in self.cache.get_many(keys.keys()).iteritems():
                d[keys[k]] = v
                del keys[k]

        return d
