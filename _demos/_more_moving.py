import gc

def replace_tuple(self, new):
    for container in gc.get_referrers(self):
        if isinstance(container, dict):
            for k, v in container.items():
                if v is self:
                    container[k] = new
        elif isinstance(container, list):
            for i, v in enumerate(container):
                if v is self:
                    container[i] = new
        elif isinstance(container, tuple):
            for i, v in enumerate(container):
                if v is self:
                    temp = list(container)
                    temp[i] = new
                    replace_tuple(container, tuple(temp))
        elif isinstance(container, set):
            container.remove(self)
            container.add(new)

x = (1, 2, 3)
print(id(x))

def fn():
    t = (1, 2, 3)
    print(id(t))
    return t

replace_tuple(x, ("replaced", "tuple"))

print(x)
print(fn())
