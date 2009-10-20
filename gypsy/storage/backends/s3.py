"""
S3 backed storage backend for Django.

Settings are specified in settings.STORAGE_S3:
    API_KEY = AWS api key
    SECRET_KEY = AWS secret key
    BUCKET = S3 bucket
    PUBLIC = If all files should be world readable (default is False)
    CNAME = True if urls should use the bucket name as the domain (cname) instead of s3.amazonaws.com/bucket/ (default is False)
    URL_TIMEOUT = Default timeout for urls (default is no timeout)

The Content object passed to save can include the following attributes:
    public = If the file should be world readable
    backend_headers = Dictionary of optional HTTP headers
"""

import logging
from time import sleep
from urllib import quote
from httplib import BadStatusLine

from boto.exception import S3ResponseError
from boto.s3.key import Key
from boto.s3.bucket import Bucket
from boto.s3.connection import S3Connection

from django.conf import settings
from django.core.files.base import File
from django.core.files.storage import Storage

from gypsy.utils.mimetype import guess_type

def retry(func, *args, **kwargs):
    """retry all commands a few times func because S3 occasionally returns 500 errors"""
    retry_sleep = 0.2
    for i in range(3):
        try:
            return func(*args, **kwargs)
        except (S3ResponseError, BadStatusLine, ValueError), exc:
            # ValueError is raised when httplib doesn't handle an invalid response properly
            # "ValueError: invalid literal for int() with base 16: ''"

            if not isinstance(exc, (BadStatusLine, ValueError)) and exc.status != 500:
                raise

            last_error = exc
            sleep(retry_sleep)
            retry_sleep *= 2

    raise last_error

class S3File(File):
    def __init__(self, bucket, name):
        self._bucket = bucket
        self._name = name
        self._key = Key(bucket=bucket, name=name.encode('utf-8'))
        self._pos = 0
        self._open = False
        self._fake_open = False
        self._mode = 'r'

    @property
    def name(self):
        return self._name

    @property
    def mode(self):
        return self._key.mode

    @property
    def closed(self):
        return self._fake_open

    def size():
        doc = "The size property."
        def fget(self):
            raise NotImplementedError("S3File doesn't implement size and __len__")
        def fset(self, value):
            raise NotImplementedError("S3File doesn't implement size and __len__")
        return locals()

    def open(self, mode="r"):
        self.close()
        self._mode = (mode or 'r')[0]
        self._fake_open = True

    def close(self):
        if self._open:
            self._pos = 0
            self._key.close()
        self._fake_open = False

    def seek(self, position):
        if position != 0:
            raise NotImplementedError("S3File doesn't implement seek at positions other than 0")
        if self._pos != 0:
            # TODO: This is a bit flakey I imagine
            self._key.resp = None
            self._pos = 0

    def tell(self):
        return self._pos

    def read(self, num_bytes=None):
        if not self._open:
            self._key.open(self._mode)
            self._open = True
        data = self._key.read(num_bytes)
        self._pos += len(data)
        return data

    def write(self, content):
        raise NotImplementedError("S3File doesn't implement write")

    def flush(self):
        raise NotImplementedError("S3File doesn't implement flush")

    def close(self):
        self._key.close()


class S3Storage(Storage):
    def __init__(self, bucket=None, api_key=None, secret_key=None, url_timeout=None, cname=None, public=None, overwrite=None):
        self.api_key = api_key or settings.STORAGE_S3['API_KEY']
        self.secret_key = secret_key or settings.STORAGE_S3['SECRET_KEY']

        self.public = public if public is not None else settings.STORAGE_S3.get('PUBLIC', False)
        self.bucket_name = bucket or settings.STORAGE_S3['BUCKET']
        self.url_timeout = url_timeout or settings.STORAGE_S3.get('URL_TIMEOUT')
        self.cname = cname if cname is not None else settings.STORAGE_S3.get('CNAME', False)
        self.overwrite = overwrite if overwrite is not None else settings.STORAGE_S3.get('OVERWRITE', False)

        self.conn = S3Connection(self.api_key, self.secret_key)

        self.bucket = self.conn.get_bucket(self.bucket_name)
        if not self.bucket:
            self.bucket = self.conn.create_bucket(bucket) # Can raise boto.exception.S3CreateError
            # self.bucket.set_acl('public-read')

    def _open(self, name, mode='rb'):
        s3file = S3File(self.bucket, name)
        s3file.open(mode)
        return s3file

    def _save(self, name, content, mimetype=None, public=None):
        if not mimetype:
            mimetype = guess_type(name)[0] or "application/x-binary"

        if hasattr(content, 'public'):
            public = content.public
        else:
            public = self.public if public is None else public

        key = Key(self.bucket, name.encode('utf-8'))
        key.content_type = mimetype
        headers = getattr(content, 'backend_headers', {})

        success = False

        for i in range(3):
            content.seek(0)
            retry(key.set_contents_from_file, content, headers=headers)

            if public:
                try:
                    retry(key.set_acl, 'public-read')
                except S3ResponseError, exc:
                    if exc.status == 404:
                        continue
                    raise

            # Make sure file actually exists on S3
            # TODO: Maybe only do this if not settings the acl as that should have the same effect?
            success = bool(retry(self.bucket.lookup, name.encode('utf-8')))
            if success:
                break

            logging.warning(u"Failed to write to S3: %s" % name)

        if not success:
            raise Exception("Failed to write file '%s'" % name)

        return name

    # def get_valid_name(self, name):
    #     name = super(S3Storage, self).get_valid_name(name)
    #     if isinstance(name, unicode):
    #         name = name.encode('utf-8')
    #     return name

    def get_available_name(self, name):
        if self.overwrite:
            return name
        return super(S3Storage, self).get_available_name(name)

    def delete(self, name):
        return retry(self.bucket.delete_key, name.encode('utf-8'))

    def exists(self, name):
        return bool(retry(self.bucket.lookup, name.encode('utf-8')))

    # def size(self, name):
    #     pass

    # def listdir(self, path):
    #     """
    #     Lists the contents of the specified path, returning a 2-tuple of lists;
    #     the first item being directories, the second item being files.
    #     """
    #     raise NotImplementedError()

    def url(self, name, expires_in=None):
        if expires_in or self.url_timeout:
            key = Key(self.bucket, name.encode('utf-8'))
            url = retry(key.generate_url, expires_in=expires_in or self.url_timeout)
        else:
            if self.cname:
                url = "http://%s/%s" % (
                    self.bucket.name,
                    quote(name.encode('utf-8')))
            else:
                url = "%s://%s/%s/%s" % (
                    self.conn.protocol,
                    force_string(self.conn.server_name),
                    force_string(self.bucket_name),
                    quote(name.encode('utf-8')))
                url = url.replace('https://', 'http://').replace(':443/', '/')
        if url and url.startswith('http://'):
            url = url.replace(':80/', '/')
        elif url and url.startswith('https://'):
            url = url.replace(':443/', '/')
        return url

def force_string(v):
    if hasattr(v, '__call__'):
        return v()
    return v
