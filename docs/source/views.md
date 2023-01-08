# Intro to Views

## Printing View info

View.info() returns a formatted string of the PyObject struct of an object, and its current attributes.

```python
from einspect import view

ls = [1, 2, 3]
v = view(ls)
print(v.info())

PyListObject(at 0x2833738):
   ob_refcnt: Py_ssize_t = 5
   ob_type: *PyTypeObject = &[list]
   ob_item: **PyObject = &[&[1], &[2], &[3], &[NULL]]
   allocated: Py_ssize_t = 4

```

## Moving Views / objects

- All move operations require an unsafe context.

The left shift operator `<<` / `<<=` can be used to copy memory from a right-side `View` (or object mappable to a supported `View` type) to the left-side view’s memory location.

The operation returns a new view at the left side view’s memory location, created using the right-side view type.

```python
from einspect import view

num = 500
ls = ["abc", "def"]

v = view(num)
with v.unsafe():
    v <<= ls

for i in num:
    print(i)
```

By default, the move is offset by sizeof(Py_ssize_t) to start after `ob_refcnt`.

The `View.move_from` function can also be used, equivalent to the `<<` operator. This function form allows an optional `offset` amount to be specified.

```python
from einspect import view

x = 750

with view(x).unsafe() as v
    v.move_from(50, offset=8)

print(x)   # 40
print(750) # 40
```

- Use caution with memory moves, there is no check for whether the size of the source exceeds that of the destination. Moving from a larger object to a smaller one may write into unowned memory.
