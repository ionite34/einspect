# types

```{eval-rst}
.. autoclass:: einspect.types.ptr
   :members:

.. autoclass:: einspect.types._Ptr
   :members:
   :special-members: __new__, __class_getitem__
   :show-inheritance:

.. class:: einspect.types.Array

   A typing alias for ctypes.Array for non-simple types.
   Resolves to ctypes.Array directly at runtime.
   `__getitem__` is hinted returns the Array generic type,
   instead of `Any`, like the `ctypes.Array` typeshed currently does.
```
