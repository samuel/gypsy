import base64

try:
    import cPickle as pickle
except ImportError:
    import pickle

from django.db import models as django_models

class _PickledMarker(unicode):
    def __init__(self, object):
        self.object = object
        super(_PickledMarker, self).__init__()


class PickleField(django_models.Field):
    __metaclass__ = django_models.SubfieldBase
    
    def to_python(self, value):
        try:
            # test the object for unpickle-ability
            unpickled = pickle.loads(base64.decodestring(value))
        except:
            # if it fails, then value is coming from the user, not the db
            # and should be returned without further processing
            pass
        else:
            # we could unpickle, but the value only came from the db 
            # if it's an instance of _PickledMarker
            if isinstance(unpickled, _PickledMarker):
                return unpickled.object
        
        return value
    
    def get_db_prep_save(self, value):
        # ensure that any value is a _PickledMarker wrapper
        # before saving it's serialization to the db
        if not isinstance(value, _PickledMarker):
            value = _PickledMarker(value)

        return base64.encodestring(pickle.dumps(value))
    
    def get_internal_type(self): 
        return 'TextField'
    
    def get_db_prep_lookup(self, lookup_type, value):
        if lookup_type == 'exact':
            value = self.get_db_prep_save(value)
            return super(PickleField, self).get_db_prep_lookup(lookup_type, value)
        elif lookup_type == 'in':
            value = [self.get_db_prep_save(v) for v in value]
            return super(PickleField, self).get_db_prep_lookup(lookup_type, value)
        else:
            raise TypeError('Lookup type %s is not supported.' % lookup_type)
