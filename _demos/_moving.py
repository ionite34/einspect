from einspect import view
from einspect.views import View

v1 = view(view)
ctx = v1.unsafe()

with ctx:
    v2 = view(ctx.__exit__)
    with v2.unsafe():
        view(None).move_to(v2)
    view(None).move_to(v1)

