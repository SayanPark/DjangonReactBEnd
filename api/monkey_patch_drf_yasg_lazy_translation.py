from django.utils.functional import Promise

from rest_framework.utils import representation

original_smart_repr = representation.smart_repr

def patched_smart_repr(value):
    # Handle lazy translation objects (__proxy__) safely
    if isinstance(value, Promise):
        try:
            return str(value)
        except Exception:
            return repr(value)
    # fallback to original smart_repr behavior
    return original_smart_repr(value)

# Monkey patch rest_framework.utils.representation.smart_repr
import rest_framework.utils.representation
rest_framework.utils.representation.smart_repr = patched_smart_repr
