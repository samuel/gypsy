from django.core import signals
from django.utils.datastructures import SortedDict

class RequestQueue(SortedDict):
    def push(self, unique, func, args=(), kwargs=None):
        self[unique] = (func, args, kwargs or {})

    def push_lazy(self, unique, lunc):
        if unique not in self:
            self.push(unique, *lunc())

request_queue = RequestQueue()

def flush_request_queue(**kwargs):
    if not request_queue:
        return

    for func, args, kwargs in request_queue.values():
        func(*args, **kwargs)

    request_queue.clear()

signals.request_finished.connect(flush_request_queue)
