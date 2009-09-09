from django.db import models as django_models 
from django.db.models.query import EmptyQuerySet

class EmptyManager(django_models.Manager):
    def get_query_set(self):
        return EmptyQuerySet()
    
    #Is this ok!?
    def delete_manager(self, dummy):
        class A(object):
            def all(self):
                return EmptyQuerySet()
        return A()


class ForeignKeyUnrelated(django_models.ForeignKey):
    """This is a HACK.
    This class is a replacement for ForeignKey such that a backwards
    relationship does not get created in the related class. By avoiding
    the link we can avoid getting deleted in the cascade.

    TODO: A better way needs to be developed, hopefuly something along
          the lines of the normal ON DELETE CASCADE/SET NULL/RESTRICT
    """
    def __init__(self, *args, **kwargs):
        kwargs['related_name'] = "_unrelated_%d" % id(self) # TODO: we don't really need a related_name but until it can really be removed just generate a unique one
        super(ForeignKeyUnrelated, self).__init__(*args, **kwargs)

    def contribute_to_related_class(self, cls, related):
        setattr(cls, related.get_accessor_name(), EmptyManager())


class _VirtualRelatedObjectsDescriptor(object):
    """
    This class serves to simplify template code
    by making commonly used query sets available
    as attributes of model instances.
    """
    def __init__(self, getter):
        """
        The getter retrieves a query set to be wrapped
        by a VirtualRelatedManager.
        """
        self.getter = getter
    
    def __get__(self, instance, instance_type = None):
        if instance is None:
            raise AttributeError("Manager must be accessed via instance")

        qs = self.getter(instance)
        qs_type = type(qs.model._default_manager)

        VirtualRelatedManager = self.get_virtual_related_manager_cls(qs_type)
        return VirtualRelatedManager(qs)

    def __set__(self, instance, value):
        raise AttributeError("VirtualManager cannot be set directly.")

    def get_virtual_related_manager_cls(self, supertype):
        class VirtualRelatedManager(supertype):
            """
            Makes all the common manager methods available, using
            the passed query set.
            """
            def __init__(self, query_set):
                super(VirtualRelatedManager, self).__init__()
                self._query_set = query_set
        
            def get_empty_query_set(self):
                return EmptyQuerySet(self._query_set.model)
        
            def get_query_set(self):
                return self._query_set
        return VirtualRelatedManager


def virtually_related():
    """
    A more decorator syntax friendly way to add
    a VirtualRelatedObjectDescriptor to your class.
    """
    return _VirtualRelatedObjectsDescriptor


class _ReverseSingleRelatedObjectDescriptorWithDefault(django_models.fields.related.ReverseSingleRelatedObjectDescriptor):
    """
    See docs for ForeignKeyWithDefault
    """
    def __init__(self, *args, **kwargs):
        self.null_default = kwargs.pop('null_default')
        super(_ReverseSingleRelatedObjectDescriptorWithDefault, self).__init__(*args, **kwargs)

    def get_default(self, instance):
        return self.null_default(instance)  # TODO: Cache instance instead of recreating everytime

    def __get__(self, instance, instance_type=None):
        if instance is None:
            raise AttributeError("%s must be accessed via instance" % self.field.name)
        cache_name = self.field.get_cache_name()
        try:
            val = getattr(instance, cache_name)
            if val.id == 0:
                return self.get_default(instance)
            return val
        except AttributeError:
            val = getattr(instance, self.field.attname)
            if val is None:
                return self.get_default(instance)
            other_field = self.field.rel.get_related_field()
            if other_field.rel:
                params = {'%s__pk' % self.field.rel.field_name: val}
            else:
                params = {'%s__exact' % self.field.rel.field_name: val}
            rel_obj = self.field.rel.to._default_manager.get(**params)
            if rel_obj.id == 0:
                rel_obj = self.get_default(instance)
            setattr(instance, cache_name, rel_obj)
            return rel_obj

    def __set__(self, instance, value):
        if instance is None:
            raise AttributeError("%s must be accessed via instance" % self._field.name)

        # TODO: Need to check "value" to see what it is

        # Set the value of the related field
        try:
            val = getattr(value, self.field.rel.get_related_field().attname)
        except AttributeError:
            val = None
        setattr(instance, self.field.attname, val)

        # Clear the cache, if it exists
        try:
            delattr(instance, self.field.get_cache_name())
        except AttributeError:
            pass


class ForeignKeyWithDefault(django_models.ForeignKey):
    """
    Subclass of ForeignKey that returns a user define value (null_default) when value is None
    """
    def __init__(self, *args, **kwargs):
        self.null_default = kwargs.pop('null_default')
        super(ForeignKeyWithDefault, self).__init__(*args, **kwargs)

    def contribute_to_class(self, cls, name):
        super(ForeignKeyWithDefault, self).contribute_to_class(cls, name)
        setattr(cls, self.name, _ReverseSingleRelatedObjectDescriptorWithDefault(self, null_default = self.null_default))
