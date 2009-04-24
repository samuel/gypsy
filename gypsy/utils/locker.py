"""Distributed locking"""

import time, os, socket
from django.conf import settings
from django.core.cache import cache

class MemcacheLock(object):
    def __init__(self):
        self.cache = getattr(cache, '_cache', None)
        if self.cache and not hasattr(self.cache, "add"):
            # Make sure the cache backend has an "add" which is probably only memcache
            self.cache = None
        self.unique_id = "%s:%d" % (socket.gethostname(), os.getpid())
        self.lock_timeout = 10
        self.key_prefix = "%s:lock" % settings.CACHE_MIDDLEWARE_KEY_PREFIX
        self.locks = set()

    def unlock(self, name):
        if not self.cache:
            return

        val = self.cache.get(self._key(name))
        if val == self.unique_id:
            self.cache.delete(self._key(name))
        self.locks.discard(name)

    def lock(self, name, timeout=None, max_time=None):
        if not self.cache:
            return False

        start_time = time.time()
        while not self.cache.add(self._key(name), self.unique_id,
                max_time or self.lock_timeout) and (not timeout or time.time() - start_time < timeout):
            time.sleep(0.5)
        success = not timeout or time.time() - start_time < timeout
        if success:
            self.locks.add(name)
        return success

    def _key(self, name):
        return self.key_prefix + name

    def __del__(self):
        for name in self.locks:
            self.unlock(name)

class locker(object):
    def __init__(self, name, *args, **kwargs):
        self._lock = MemcacheLock()
        self._name = name
        self._args = args
        self._kwargs = kwargs

    def __enter__(self):
        return self._lock.lock(self._name, *self._args, **self._kwargs)

    def __exit__(self, etype, value, traceback):
        self._lock.unlock(self._name)
        return True if etype is None else False
