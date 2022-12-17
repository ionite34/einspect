# einspect

[![Build](https://github.com/ionite34/einspect/actions/workflows/build.yml/badge.svg)](https://github.com/ionite34/einspect/actions/workflows/build.yml)
[![codecov](https://codecov.io/gh/ionite34/einspect/branch/main/graph/badge.svg?token=v71SdG5Bo6)](https://codecov.io/gh/ionite34/einspect)

Extended Inspect for CPython

Provides simple and robust ways to view and modify the base memory structures of Python objects at runtime.

Note: The below examples show interactions with a `TupleView`, but applies much the same way generically for
many of the specialized `View` subtypes that are dynamically returned by the `view` function. If no specific
view is implemented, the base `View` will be used which represents limited interactions on the assumption of
`PyObject` struct parts.


```python
from einspect import view

print(view((1, 2)))
print(view([1, 2]))
print(view("hello"))
print(view(256))
print(view(object()))
```
> ```
> TupleView[tuple](<PyTupleObject at 0x100f19a00>)
> ListView[list](<PyListObject at 0x10124f800>)
> StrView[str](<PyUnicodeObject at 0x100f12ab0>)
> IntView[int](<PyLongObject at 0x102058920>)
> View[object](<PyObject at 0x100ea08a0>)
> ```

## 1. Viewing python object struct attributes

State information of the underlying `PyTupleObject` struct can be accessed through the view's attributes.
```python
print(v.ref_count)  # ob_refcnt
print(v.type)       # ob_type
print(v.size)       # ob_size
print(v.items)      # ob_item
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
