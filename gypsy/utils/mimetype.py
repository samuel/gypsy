"""
Memoized versions of functions from Python's mimetypes.

The original functions reread the mimetypes files on every call which is very slow. 
"""

from mimetypes import guess_extension as original_guess_extension, guess_type as original_guess_type
from django.utils.functional import memoize

guess_extension = memoize(original_guess_extension, {}, 2)
guess_type = memoize(original_guess_type, {}, 2)
