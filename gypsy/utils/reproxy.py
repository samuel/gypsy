"""
Reproxy responses for use with Perlbal and Pound.

Perlbal initially came up with the idea for reproxy. A web server behind
the reverse proxy can return a response that causes Perlbal to fetch the
data from a URL or a FILE. This allows the web app to avoid feeding data
to the client, and it leaves the job up to the proxy which is better
equipped to handle it.

http://www.danga.com/perlbal/
http://poundpatch.pbwiki.com/
http://d.hatena.ne.jp/perezvon/20080418/1208531594
"""

from django.http import HttpResponse

def HttpResponseReproxy(typ, url, size=None, mimetype=None):
    kw = (mimetype and {'mimetype': mimetype}) or {}
    res = HttpResponse(**kw)
    if not isinstance(url, basestring):
        url = " ".join(url)
    res['X-Accel-Redirect'] = "/reproxy" # Nginx
    res['X-REPROXY-%s' % typ.upper()] = url
    if size is not None:
        res['X-REPROXY-EXPECTED-SIZE'] = str(size)
    return res

def HttpResponseReproxyURL(*args, **kwargs):
    return HttpResponseReproxy("URL", *args, **kwargs)

def HttpResponseReproxyFile(*args, **kwargs):
    return HttpResponseReproxy("FILE", *args, **kwargs)
