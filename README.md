# einspect

<!-- start badges -->

[![Build](https://github.com/ionite34/einspect/actions/workflows/build.yml/badge.svg)](https://github.com/ionite34/einspect/actions/workflows/build.yml)
[![codecov](https://codecov.io/gh/ionite34/einspect/branch/main/graph/badge.svg?token=v71SdG5Bo6)](https://codecov.io/gh/ionite34/einspect)
[![security](https://snyk-widget.herokuapp.com/badge/pip/einspect/badge.svg)](https://security.snyk.io/package/pip/einspect)

[![PyPI](https://img.shields.io/pypi/v/einspect)][pypi]
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/einspect)][pypi]

[pypi]: https://pypi.org/project/einspect/

<!-- end badges -->

> Extended Inspections for CPython

## [Documentation](https://docs.ionite.io/einspect)

- [View and modify memory structures of live objects.](#check-detailed-states-of-built-in-objects)
- [Able to mutate immutable objects like tuples and ints.](#mutate-tuples-strings-ints-or-other-immutable-types)
- [Modify slot functions or attributes of built-in types.](#modify-attributes-of-built-in-types-get-original-attributes-with-orig)
- [Fully typed, extensible framework in pure Python.](#move-objects-in-memory)

<!-- start intro -->

## Check detailed states of built-in objects
```python
from einspect import view

ls = [1, 2, 3]
v = view(ls)
print(v.info())
```
```python
PyListObject(at 0x2833738):
   ob_refcnt: Py_ssize_t = 5
   ob_type: *PyTypeObject = &[list]
   ob_item: **PyObject = &[&[1], &[2], &[3]]
   allocated: Py_ssize_t = 4
```

[doc_tuple_view]: https://docs.ionite.io/einspect/api/views/view_tuple.html#einspect.views.view_tuple
[doc_str_view]: https://docs.ionite.io/einspect/api/views/view_str.html#einspect.views.view_str
[py_doc_mutable_seq]: https://docs.python.org/3/library/stdtypes.html#mutable-sequence-types
## Mutate tuples, strings, ints, or other immutable types
> [TupleView][doc_tuple_view] and [StrView][doc_str_view] supports all [MutableSequence][py_doc_mutable_seq] methods (append, extend, insert, pop, remove, reverse, clear).

> ⚠️ A note on [safety.](#safety)
```python
from einspect import view

tup = (1, 2)
v = view(tup)

v[1] = 500
print(tup)      # (1, 500)
v.append(3)
print(tup)      # (1, 500, 3)

del v[:2]
print(tup)      # (3,)
print(v.pop())  # 3

v.extend([1, 2])
print(tup)      # (1, 2)

v.clear()
print(tup)      # ()
```
```python
from einspect import view

text = "hello"

v = view(text)
v[1] = "3"
v[4:] = "o~"
v.append("!")

print(text)  # h3llo~!
v.reverse()
print(text)  # !~oll3h
```
```python
from einspect import view

n = 500
view(n).value = 10

print(500)        # 10
print(500 == 10)  # True
```

## Modify attributes of built-in types, get original attributes with `orig`
```python
from einspect import view, orig

v = view(int)
v["__name__"] = "custom_int"
v["__iter__"] = lambda s: iter(range(s))
v["__repr__"] = lambda s: "custom: " + orig(int).__repr__(s)

print(int)
for i in 3:
    print(i)
```
```
<class 'custom_int'>
custom: 0
custom: 1
custom: 2
```

## Implement methods on built-in types
> See the [Extending Types](https://docs.ionite.io/einspect/extending_types.html) docs page for more information.
```python
from einspect import impl, orig

@impl(int)
def __add__(self, other):
    other = int(other)
    return orig(int).__add__(self, other)

print(50 + "25")  # 75
```

## Move objects in memory
```python
from einspect import view

s = "meaning of life"

v = view(s)
with v.unsafe():
    v <<= 42

print("meaning of life")        # 42
print("meaning of life" == 42)  # True
```

<!-- end intro -->

## Fully typed interface
<img width="551" alt="image" src="https://user-images.githubusercontent.com/13956642/211129165-38a1c405-9d54-413c-962e-6917f1f3c2a1.png">

## Safety

 This project is mainly for learning purposes or inspecting and debugging CPython internals for development and fun. You should not violate language conventions like mutability in production software and libraries.

The interpreter makes assumptions regarding types that are immutable, and changing them causes all those usages to be affected. While the intent of the project is to make a memory-correct mutation without further side effects, there can be very significant runtime implications of mutating interned strings with lots of shared references, including interpreter crashes.

For example, some strings like "abc" are interned and used by the interpreter. Changing them changes all usages of them, even attribute calls like `collections.abc`.

> The spirit of safety maintained by einspect is to do with memory layouts, not functional effects.

### For example, appending to tuple views (without an unsafe context) will check that the resize can fit within allocated memory
```python
from einspect import view

tup = (1, 2)
v = view(tup)

v.append(3)
print(tup)  # (1, 2, 3)

v.append(4)
# UnsafeError: insert required tuple to be resized beyond current memory allocation. Enter an unsafe context to allow this.
```
- Despite this, mutating shared references like empty tuples can cause issues in interpreter shutdown and other runtime operations.
```python
from einspect import view

tup = ()
view(tup).append(1)
```
```
Exception ignored in: <module 'threading' from '/lib/python3.11/threading.py'>
Traceback (most recent call last):
  File "/lib/python3.11/threading.py", line 1563, in _shutdown
    _main_thread._stop()
  File "/lib/python3.11/threading.py", line 1067, in _stop
    with _shutdown_locks_lock:
TypeError: 'str' object cannot be interpreted as an integer
```

### Similarly, memory moves are also checked for GC-header compatibility and allocation sizes
```python
from einspect import view

v = view(101)
v <<= 2

print(101)  # 2

v <<= "hello"
# UnsafeError: memory move of 54 bytes into allocated space of 32 bytes is out of bounds. Enter an unsafe context to allow this.
```

- However, this will not check the fact that small integers between (-5, 256) are interned and used by the interpreter. Changing them may cause issues in any library or interpreter Python code.
```python
from einspect import view

view(0) << 100

exit()
# sys:1: ImportWarning: can't resolve package from __spec__ or __package__, falling back on __name__ and __path__
# IndexError: string index out of range
```

## Table of Contents
- [Views](#views)
  - [Using the `einspect.view` constructor](#using-the-einspectview-constructor)
  - [Inspecting struct attributes](#inspecting-struct-attributes)

## Views

### Using the `einspect.view` constructor

This is the recommended and simplest way to create a `View` onto an object. Equivalent to constructing a specific `View` subtype from `einspect.views`, except the choice of subtype is automatic based on object type.

```python
from einspect import view

print(view(1))
print(view("hello"))
print(view([1, 2]))
print(view((1, 2)))
```
> ```
> IntView(<PyLongObject at 0x102058920>)
> StrView(<PyUnicodeObject at 0x100f12ab0>)
> ListView(<PyListObject at 0x10124f800>)
> TupleView(<PyTupleObject at 0x100f19a00>)
> ```

### Inspecting struct attributes

Attributes of the underlying C Struct of objects can be accessed through the view's properties.
```python
from einspect import view

ls = [1, 2]
v = view(ls)

# Inherited from PyObject
print(v.ref_count)  # ob_refcnt
print(v.type)       # ob_type
# Inherited from PyVarObject
print(v.size)       # ob_size
# From PyListObject
print(v.item)       # ob_item
print(v.allocated)  # allocated
```
> ```
> 4
> <class 'tuple'>
> 3
> <einspect.structs.c_long_Array_3 object at 0x105038ed0>
> ```

## 2. Writing to view attributes

Writing to these attributes will affect the underlying object of the view.

Note that most memory-unsafe attribute modifications require entering an unsafe context manager with `View.unsafe()`
```python
with v.unsafe():
    v.size -= 1

print(obj)
```
> `(1, 2)`

Since `items` is an array of integer pointers to python objects, they can be replaced by `id()` addresses to modify
index items in the tuple.
```python
from einspect import view

tup = (100, 200)

with view(tup).unsafe() as v:
    s = "dog"
    v.item[0] = id(s)

print(tup)
```
> ```
> ('dog', 200)
>
> >> Process finished with exit code 139 (interrupted by signal 11: SIGSEGV)
> ```

So here we did set the item at index 0 with our new item, the string `"dog"`, but this also caused a segmentation fault.
Note that the act of setting an item in containers like tuples and lists "steals" a reference to the object, even
if we only supplied the address pointer.

To make this safe, we will have to manually increment a ref-count before the new item is assigned. To do this we can
either create a `view` of our new item, and increment its `ref_count += 1`, or use the apis from `einspect.api`, which
are pre-typed implementations of `ctypes.pythonapi` methods.
```python
from einspect import view
from einspect.api import Py

tup = (100, 200)

with view(tup).unsafe() as v:
    a = "bird"
    Py.IncRef(a)
    v.item[0] = id(a)

    b = "kitten"
    Py.IncRef(b)
    v.item[1] = id(b)

print(tup)
```
> `('bird', 'kitten')`

🎉 No more seg-faults, and we just successfully set both items in an otherwise immutable tuple.

To make the above routine easier, you can access an abstraction by simply indexing the view.

```python
from einspect import view

tup = ("a", "b", "c")

v = view(tup)
v[0] = 123
v[1] = "hm"
v[2] = "🤔"

print(tup)
```
> `(123, 'hm', '🤔')`
