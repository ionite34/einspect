# einspect

[![Build](https://github.com/ionite34/einspect/actions/workflows/build.yml/badge.svg)](https://github.com/ionite34/einspect/actions/workflows/build.yml)
[![codecov](https://codecov.io/gh/ionite34/einspect/branch/main/graph/badge.svg?token=v71SdG5Bo6)](https://codecov.io/gh/ionite34/einspect)
[![security](https://snyk-widget.herokuapp.com/badge/pip/einspect/badge.svg)](https://security.snyk.io/package/pip/einspect)

[![PyPI](https://img.shields.io/pypi/v/einspect)][pypi]
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/einspect)][pypi]

[pypi]: https://pypi.org/project/einspect/

> Extended Inspections for CPython

### [Documentation](https://docs.ionite.io/einspect)

- [View and modify memory structures of live objects.](#check-detailed-states-of-built-in-objects)
- [Able to mutate immutable objects like tuples and ints.](#mutate-tuples-strings-ints-or-other-immutable-types)
- [Modify slot functions or attributes of built-in types.](#modify-attributes-on-built-in-types)
- [Fully typed, extensible framework in pure Python.](#move-objects-in-memory)

### Check detailed states of built-in objects
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

### Mutate tuples, strings, ints, or other immutable types
```python
from einspect import view

t = ("A", "B")
view(t)[1] = 10
print(t)
```
```python
("A", 10)
```

```python
from einspect import view

a = "hello"
b = 100

view(a).buffer[:] = b"world"
view(b).value = 5

print("hello", 100)
```
```python
world 5
```

### Modify attributes of built-in types
```python
from einspect import view

v = view(int)
v["__iter__"] = lambda self: iter(range(self))
v["__str__"] = lambda self: "custom: " + repr(self)

for i in 3:
    print(i)
```
```python
custom: 0
custom: 1
custom: 2
```

### Move objects in memory
```python
from einspect import view

s = "meaning of life"

v = view(s)
with v.unsafe():
    v <<= 42

print("meaning of life")
print("meaning of life" == 42)
```
```python
42
True
```

### Fully typed interface
<img width="551" alt="image" src="https://user-images.githubusercontent.com/13956642/211129165-38a1c405-9d54-413c-962e-6917f1f3c2a1.png">

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
