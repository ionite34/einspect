# Extending types

- {class}`~einspect.views.view_type.TypeView` subscripting can be used to set attributes on type objects, including built-in types.
- The {meth}`~einspect.views.view_type.impl` decorator can implement the decorated method onto a type.

## Using the {meth}`~einspect.views.view_type.impl` decorator

> Works for normal methods, dunder methods, or decorated static / class / property methods.
```python
from einspect import impl

@impl(int)
def is_even(self):
    return self % 2 == 0

print((2).is_even())  # True

@impl(int)
def __matmul__(self, other):
    return self * other

print(5 @ 3)  # 15

@impl(int)
@property
def real(self):
    return self + 1

print((2).real)  # 3

@impl(int)
@classmethod
def try_from(cls, x):
    try:
        return cls(x)
    except ValueError:
        return None

print(int.try_from('2'))  # 2
print(int.try_from('a'))  # None

@impl(list)
@staticmethod
def abc():
    return "abc"

print(list.abc())  # "abc"
print([].abc())  # "abc"
```
## Using {class}`~einspect.type_orig.orig` to get original attributes
Sometimes you may want to defer to the original implementation of a method or attribute before it was overriden by `impl` or `TypeView`, in this case calling `orig(<type>)` will return a proxy object of the type where attribute access will yield original attributes.

For example, we want to override the `__add__` of floats, by adding a print statement, but we want to still call the original `__add__` after our print.

Calling `orig(float)` will give us the float proxy object, where `orig(float).__add__` will give us the original `float.__add__` method before our override.

```python
from einspect import impl, orig

@impl(float)
def __add__(self, other):
    print(f"Adding {self} and {other}")
    return orig(float).__add__(self, other)
```

## Using {meth}`~einspect.views.view_type.TypeView` subscripting
Views of types can be subscripted to either get or set attributes on the type. This works in all cases where `@impl` can be used.

In addition, this form can also set static attributes like `__dict__` or `__name__`.
```python
from einspect import view

v = view(int)
print(v["__name__"])  # int

v["is_even"] = lambda self: self % 2 == 0
print((2).is_even())  # True

v["__name__"] = "MyInt"
print(int.__name__)  # MyInt
print(int)  # <class 'MyInt'>
```

Multiple attributes can be set together by passing multiple attribute names.
```python
from einspect import view

v = view(str)
v["__truediv__", "__floordiv__"] = str.split

print("Hello, world!" / ", ")  # ['Hello', 'world!']
print("abc-xyz" // "-")        # ['abc', 'xyz']
```
