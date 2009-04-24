from django.conf import settings
from pprint import pformat

def _get_traceback(exc_info=None):
    "Helper function to return the traceback as a string"
    import traceback, sys
    return '\n'.join(traceback.format_exception(*(exc_info or sys.exc_info())))

def email_traceback(request=None, exc_info=None, locals=None):
    # Get the exception info now, in case another exception is thrown later.
    if not exc_info:
        import sys
        exc_info = sys.exc_info()

    # When DEBUG is False, send an error message to the admins.
    if request:
        subject = 'Error (%s IP): %s' % \
            ((request.META.get('REMOTE_ADDR') in settings.INTERNAL_IPS and 'internal' or 'EXTERNAL'), request.path)
        try:
            request_repr = repr(request)
        except:
            request_repr = "Request repr() unavailable"
        message = "%s\n\n%s" % (_get_traceback(exc_info), request_repr)
    else:
        subject = 'Error: ' + str(exc_info[0])
        message = _get_traceback(exc_info)

    if locals:
        message = "%s\n\nLocals:\n\n%s" % (message, pformat(locals))

    from django.core.mail import mail_admins
    mail_admins(subject, message, fail_silently=True)
