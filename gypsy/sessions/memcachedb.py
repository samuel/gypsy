import memcache
from django.conf import settings
from django.contrib.sessions.backends.base import SessionBase, CreateError

DEFAULT_PORT = 21201

class SessionStore(SessionBase):
    """
    A memcachedb based session store.
    """
    def __init__(self, session_key=None):
        # memcachedb uses a different default port than memcache. So, if the
        # port isn't specified then force it to the default memcachedb port
        servers = []
        for host in settings.SESSION_MEMCACHEDB_SERVERS:
            if ':' not in host:
                host = '%s:%d' % (host, DEFAULT_PORT)
            servers.append(host)
        self._conn = memcache.Client(servers, memcachedb=True)
        super(SessionStore, self).__init__(session_key)

    def load(self):
        session_data = self._conn.get(self.session_key)
        if session_data is not None:
            return session_data['data']
        self.create()
        return {}

    def create(self):
        while True:
            self.session_key = self._get_new_session_key()
            try:
                # Save immediately to ensure we have a unique entry
                self.save(must_create=True)
            except CreateError:
                # Key wasn't unique. Try again.
                continue
            self.modified = True
            self._session_cache = {}
            return

    def save(self, must_create=False):
        if must_create:
            func = self._conn.add
        else:
            func = self._conn.set
        data = dict(
            data = self._get_session(no_load=must_create),
            expires = self.get_expiry_age(),
        )
        result = func(self.session_key, data) #, self.get_expiry_age())
        if must_create and not result:
            raise CreateError

    def exists(self, session_key):
        return bool(self._conn.get(session_key))

    def delete(self, session_key=None):
        if session_key is None:
            if self._session_key is None:
                return
            session_key = self._session_key
        self._conn.delete(session_key)
