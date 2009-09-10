
import rfc822, time
from email.Utils import formatdate
try:
    from hashlib import md5
except ImportError:
    from md5 import new as md5

from django.http import HttpResponse, HttpResponseNotModified

def was_modified_since(request, last_modified):
    if_modified_since = request.META.get('HTTP_IF_MODIFIED_SINCE')
    if not if_modified_since:
        return True

    try:
        req_last_modified = rfc822.mktime_tz(rfc822.parsedate_tz(if_modified_since))
    except (TypeError, OverflowError):
        return True

    return req_last_modified != int(time.mktime(last_modified.timetuple()))

DEFAULT_ETAG = '"%s"' % md5("-").hexdigest()

def cached_response(request, data=None, response=None, last_modified=None, mimetype=None, etag=None, expires=None, cache_control=None):
    """
    This function checks cache headers and returns the appropriate response.
    If the data has not changed then HttpResponseNotModified is returned,
    otherwise the data is sent in the response along with the caching headesr.

    Data can be a string, a response, or callable. If data is a callable
    then it is only called when the requester does not have the data
    already cached.

    An etag of '-' means the hash of the data doesn't matter and a static etag
    used instead.
    """
    if last_modified and not was_modified_since(request, last_modified):
        return HttpResponseNotModified()

    if not etag and data:
        if hasattr(data, '__call__'):
            data = data()
        etag = '"%s"' % md5(data).hexdigest().lower()
    elif etag == '-':
        etag = DEFAULT_ETAG
    req_etag = request.META.get('HTTP_IF_NONE_MATCH', '').lower()
    if etag and etag == req_etag:
        return HttpResponseNotModified()

    if response:
        if hasattr(response, '__call__'):
            response = response()
    else:
        assert(data is not None)
        if hasattr(data, '__call__'):
            data = data()

        response = HttpResponse(data, **(mimetype and dict(mimetype=mimetype) or dict()))

    if etag:
        response['ETag'] = etag
    if last_modified:
        response['Last-Modified'] = last_modified.strftime('%a, %d %b %Y %H:%M:%S GMT')
    if expires:
        response['Expires'] = expires.strftime('%a, %d %b %Y %H:%M:%S GMT')
        # TODO:
        # formatdate(time.time() + cache_timeout)[:26] + "GMT"

    if cache_control:
        cc = []
        for k,v in cache_control.items():
            name = k.replace('_', '-')
            if not isinstance(v, bool):
                cc.append('%s=%d' % (name, cache_control[k]))
            elif v:
                cc.append(name)
        response['Cache-Control'] = ", ".join(cc)

    return response
