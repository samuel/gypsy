#!/usr/bin/env python

from django.test import TestCase
from django.test.client import Client
from django.conf import settings
from django.core.files.base import ContentFile

from gypsy.storage.backends.memory import MemoryStorage

class StorageTestCase(TestCase):
    def setUp(self):
        self.storage = MemoryStorage()

    def testUnicode(self):
        name = self.storage.get_valid_name(u"mit\u00e4")
        content = "test"
        self.storage.save(name, ContentFile(content))
        f = self.storage.open(name)
        self.failUnlessEqual(f.read(), content)

if hasattr(settings, 'TEST_STORAGE_S3'):
    from gypsy.storage.backends.s3 import S3Storage
    class S3TestCase(StorageTestCase):
        def setUp(self):
            kw = dict((k.lower(), v) for k, v in settings.TEST_STORAGE_S3.items())
            self.storage = S3Storage(**kw)

        def testUnicode(self):
            name = self.storage.get_valid_name(u"mit\u00e4")
            content = "test"
            self.storage.save(name, ContentFile(content))
            f = self.storage.open(name)
            self.failUnlessEqual(f.read(), content)
