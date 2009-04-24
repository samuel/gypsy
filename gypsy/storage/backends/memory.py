"""
Memory backed storage backend for Django.

This backend is for running tests only. Files are lost when the process dies.
"""

from cStringIO import StringIO

from django.core.files.storage import Storage

class MemoryStorage(Storage):
    def __init__(self):
        self.files = {}

    def _open(self, name, mode='rb'):
        return StringIO(self.files[name])

    def _save(self, name, content):
        self.files[name] = content.read()
        return name

    # def get_valid_name(self, name):
    #     return name

    def delete(self, name):
        del self.files[name]

    def exists(self, name):
        return name in self.files

    def size(self, name):
        return len(self.files[name])

    # def listdir(self, path):
    #     """
    #     Lists the contents of the specified path, returning a 2-tuple of lists;
    #     the first item being directories, the second item being files.
    #     """
    #     raise NotImplementedError()

    def url(self, name, expires_in=None):
        return "TODO"
