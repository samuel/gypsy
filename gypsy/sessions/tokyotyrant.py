import time
import pytyrant
from django.conf import settings
from django.core.exceptions import SuspiciousOperation
from django.contrib.sessions.backends.base import SessionBase, CreateError

class SessionStore(SessionBase):
    """
    A Tokyo Tyrant based session store.
    """
    def __init__(self, session_key=None):
        self._tyrant = pytyrant.PyTableTyrant.open(*settings.SESSION_TT_ADDR)
        super(SessionStore, self).__init__(session_key)

    def load(self):
        try:
            session_data = self._tyrant[self.session_key]
        except KeyError:
            self.create()
            return {}

        if int(session_data['expires']) < time.time():
            return {}

        try:
            return self.decode(session_data['data'])
        except SuspiciousOperation:
            return {}

    def create(self):
        while True:
            self.session_key = self._get_new_session_key()
            try:
                self.save(must_create=True)
            except CreateError:
                continue
            self.modified = True
            self._session_cache = {}
            return

    def save(self, must_create=False):
        data = dict(
            data = self.encode(self._get_session(no_load=must_create)),
            expires = str(int(time.time() + self.get_expiry_age())),
        )
        if must_create:
            try:
                self._tyrant.t.misc("putkeep", 0, [self.session_key] + pytyrant.dict_to_list(data))
            except pytyrant.TyrantError, exc:
                if exc.message == 1:
                    raise CreateError()
                raise
        else:
            self._tyrant[self.session_key] = data

    def exists(self, session_key):
        return bool(self._tyrant.get(session_key))

    def delete(self, session_key=None):
        if session_key is None:
            if self._session_key is None:
                return
            session_key = self._session_key
        try:
            del self._tyrant[session_key]
        except KeyError:
            pass

    def clean(self):
        q = pytyrant.Query(self._tyrant)
        q = q.filter(expires__numle=str(int(time.time())))
        for x in q:
            del self._tyrant[x]
