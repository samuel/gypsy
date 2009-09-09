from django.db import models

class BaseListField(models.Field):
    def __init__(self, *args, **kwargs):
        self.delim = kwargs.pop('delim', u'||')
        super(BaseListField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        if isinstance(value, basestring):
            value = [x for x in value.split(self.delim) if x]
        return value

    def get_db_prep_save(self, value):
        return u"%s%s%s" % (self.delim, self.delim.join(value), self.delim)

    def get_internal_type(self): 
        return 'TextField'

    def get_db_prep_lookup(self, lookup_type, value):
        if lookup_type == 'exact':
            value = self.get_db_prep_save(value)
            return super(BaseListField, self).get_db_prep_lookup(lookup_type, value)
        # elif lookup_type == 'in':
        #     value = [self.get_db_prep_save(v) for v in value]
        #     return super(BaseListField, self).get_db_prep_lookup(lookup_type, value)
        elif lookup_type == 'contains':
            value = u"%s%s%s" % (self.delim, value, self.delim)
            return super(BaseListField, self).get_db_prep_lookup(lookup_type, value)
        else:
            raise TypeError('Lookup type %s is not supported.' % lookup_type)

class StringListField(BaseListField):
    __metaclass__ = models.SubfieldBase

class StringSetField(BaseListField):
    __metaclass__ = models.SubfieldBase

    def to_python(self, value):
        value = super(StringSetField, self).to_python(value)
        if isinstance(value, (list, tuple)):
            value = set(value)
        return value
