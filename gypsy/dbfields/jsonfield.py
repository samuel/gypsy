try:
    from django.utils import simplejson
except ImportError:
    import simplejson

from django.db import models as django_models

class JSONField(django_models.Field):
    __metaclass__ = django_models.SubfieldBase

    MAGIC = "JSON"

    def to_python(self, value):
        if isinstance(value, basestring) and value.startswith(self.MAGIC):
            value = simplejson.loads(value[len(self.MAGIC):])

        return value

    def get_db_prep_save(self, value):
        return self.MAGIC + simplejson.dumps(value)
    
    def get_internal_type(self): 
        return 'TextField'
    
    def get_db_prep_lookup(self, lookup_type, value):
        if lookup_type == 'exact':
            value = self.get_db_prep_save(value)
            return super(JSONField, self).get_db_prep_lookup(lookup_type, value)
        elif lookup_type == 'in':
            value = [self.get_db_prep_save(v) for v in value]
            return super(JSONField, self).get_db_prep_lookup(lookup_type, value)
        else:
            raise TypeError('Lookup type %s is not supported.' % lookup_type)
