import urllib2
from urllib import urlencode

import socket
if hasattr(socket, 'setdefaulttimeout'):
    socket.setdefaulttimeout(5)

__version__ = "1.0"

user_agent = "%%s | spamish.py/%s" % __version__

AKISMET_URL = "rest.akismet.com/1.1/"
TYPEPAD_URL = "api.antispam.typepad.com/1.1/"

class SpamishError(Exception):
    """Base class for all spamish exceptions."""

class Spamish(object):
    required_values = ('user_ip', 'user_agent', 'comment_content')
    encoding = "utf-8"

    def __init__(self, key, blog_url=None, agent=None, base_url=TYPEPAD_URL):
        self.user_agent = user_agent % agent
        self.key = key
        self.blog_url = blog_url
        self.base_url = base_url

    def smart_encode(self, s):
        if not isinstance(s, basestring):
            s = unicode(s)
        if isinstance(s, unicode):
            return s.encode(self.encoding)
        return s

    @property
    def url(self):
        return 'http://%s.%s' % (self.key, self.base_url)

    @property
    def headers(self):
        return {
            'User-Agent': self.user_agent,
            # 'Content-Type': "application/x-www-form-urlencoded; charset=%s" % self.encoding,
        }

    def _request(self, url, data, headers):
        try:
            req = urllib2.Request(url, data, headers)
            h = urllib2.urlopen(req)
            resp = h.read()
        except (urllib2.HTTPError, urllib2.URLError, IOError), e:
            raise SpamishError(str(e))       
        return resp

    def verify_key(self):
        data = {'key': self.key, 'blog': self.blog_url}
        url = 'http://%sverify-key' % self.base_url
        resp = self._request(url, urlencode(data), self.headers)
        return resp.lower() == 'valid'

    def _validate_args(self, args):
        args.setdefault('blog', self.blog_url)

        for req in self.required_values:
            if req not in args:
                raise SpamishError("Submission must include '%s'" % req)

        for k in args:
            args[k] = self.smart_encode(args[k])

    def comment_check(self, **kwargs):
        self._validate_args(kwargs)
        url = '%scomment-check' % self.url
        resp = self._request(url, urlencode(kwargs), self.headers)
        try:
            return {'true':True, 'false':False}[resp.lower()]
        except KeyError:
            raise SpamishError(resp)

    def submit_spam(self, **kwargs):
        self._validate_args(kwargs)
        url = '%ssubmit-spam' % self.url
        self._request(url, urlencode(kwargs), self.headers)

    def submit_ham(self, **kwargs):
        self._validate_args(kwargs)
        url = '%ssubmit-ham' % self.url
        self._request(url, urlencode(kwargs), self.headers)

if __name__ == "__main__":
    spamish = Spamish("test", "http://www.example.com/", "Example")
    assert spamish.verify_key()
    print spamish.comment_check(
        comment_type = "comment",
        comment_content = "This is a test",
        user_ip = "127.0.0.1",
        user_agent = "Test/1.5",
        referrer = "",
        permalink = "http://www.example.com/",
        comment_author = "test",
        comment_author_url = "",
    )
