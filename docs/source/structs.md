# Guide to Structs

- The [`structs`](api/structs/index) submodule contains definitions and protocols for interacting with primitive Python objects as C Structs.

## 1. The [`ptr`](api/types) type

You may see a [`ptr`](api/types) type being used by einspect in lieu of the usual {py:func}`ctypes.pointer` and {py:func}`ctypes.POINTER` types. This type behaves as {py:func}`ctypes.pointer` when called.
```python
from ctypes import pointer
from einspect.types import ptr

ptr(...) == pointer(...)
```

At type checking time, `ptr` is a direct alias to ctypes.pointer. You can subscript `ptr` as you would with {py:func}`ctypes.pointer` to indicate a generic pointer type.
```python
from ctypes import pointer, c_char
from einspect.types import ptr

def foo() -> ptr[c_char]:
    ...
```

The difference is, `ptr` lets you do this at runtime as well. For example, `ptr[c_char]` resolves to a runtime call to `ctypes.POINTER(c_char)`.
```python
from ctypes import pointer, c_char
from einspect.types import ptr

ptr[c_char] == POINTER(c_char)
```

When using einspect `@struct` decorators to make new Structs, you can use the `ptr` type hint to allow both static type checking and the decorator's runtime type parsing to work.

In other cases there is no difference in using `types.ptr` or `ctypes.pointer` / `ctypes.POINTER` types.

## 2. Working with {class}`~einspect.structs.py_object.PyObject`

Firstly, all {class}`~einspect.structs.py_object.PyObject` and inherited types are compatible standard {py:class}`ctypes.Structure` types. This means they work with ctypes methods as usual.

### Converting to and from Python objects

The following interfaces allow conversion to and from python objects

- {func}`~einspect.structs.py_object.PyObject.from_object`
- {func}`~einspect.structs.py_object.PyObject.into_object`

```python
from einspect.structs import PyObject

x = 100
obj = PyObject.from_object(x)
print(obj) # <PyObject[int] at 0x1060535a0>

base = obj.into_object()
assert base is x
```

### The {class}`~einspect.structs.traits.AsRef` trait

PyObjects also implement the AsRef trait, which provides an as_ref() method that returns a pointer to the object, equivalent to ctypes.pointer(object)

```python
from ctypes import pointer
from einspect.structs import PyObject

obj = PyObject.from_object(5)

print(pointer(obj))
# <einspect.types.LP_PyObject object at 0x10467c750>

print(obj.as_ref())
# <einspect.types.LP_PyObject object at 0x10467c750>
```

### Mutating PyObject attributes

All modifications to PyObject attributes will directly modify the underlying memory. So these will reflect on the python objects.

For example, let's add a tuple to itself 🤔

```python
from einspect.structs import PyTupleObject

t = (1, 2)
obj = PyTupleObject.from_object(t)
obj.ob_size = 3
obj.ob_item[2] = obj.as_ref()

print(t)
# (1, 2, (...))
print(t[2][2][2])
# (1, 2, (...))
```

You can also create PyObject structs first, and then get the python reference.

For example, small integers (-5 to 255) are normally cached in CPython:

```python
x = 1
print(x is 1)
# True
```

But we can create our own new `1` int

```python
from einspect.structs import PyLongObject, PyTypeObject

st = PyLongObject(
    ob_refcnt=1,
    ob_type=PyTypeObject.from_object(int).as_ref(),
    ob_size=1,
    ob_digit=[1]
)

x = st.into_object()
print(x)
# 1
print(x == 1)
# True
print(x is 1)
# False
```
