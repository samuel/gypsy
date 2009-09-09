
from django.db import models
from django.db.models import signals

from gypsy.dbfields.jsonfield import JSONField
from gypsy.dbfields.picklefield import PickleField
from gypsy.dbfields.related import ForeignKeyWithDefault, ForeignKeyUnrelated
from gypsy.dbfields.listfield import StringListField, StringSetField

class UniqueFilefield(models.FileField):
    """A version of FileField that doesn't check for other rows referencing
       the same file before deleting."""

    def delete_file(self, instance, sender, **kwargs):
        file = getattr(instance, self.attname)
        # If no other object of this type references the file,
        # and it's not the default value for future objects,
        # delete it from the backend.
        if file and file.name != self.default:
            file.delete(save=False)
        elif file:
            # Otherwise, just close the file, so it doesn't tie up resources.
            file.close()
