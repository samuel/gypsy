"""
Modified filesystem backed storage backend for Django.

The difference between this one and Django's is that this backend allows
you to specify the storage path on disk relative to the MEDIA_ROOT.
settings.FILESYSTEM_STORAGE_POSTFIX gets appended to the MEDIA_ROOT to
create the path.
"""

import os

from django.conf import settings
from django.core.files import storage

class FileSystemStorage(storage.FileSystemStorage):
    def __init__(self, location=settings.MEDIA_ROOT + settings.FILESYSTEM_STORAGE_POSTFIX, base_url=settings.MEDIA_URL + settings.FILESYSTEM_STORAGE_POSTFIX):
        self.location = os.path.abspath(location)
        self.base_url = base_url
        if self.base_url[-1] != '/':
            self.base_url += '/'
