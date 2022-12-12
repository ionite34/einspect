from einspect import view

t = (1, 2, 3)
t_view = view(t)
print(t_view)

print(t)

# t_view[3] = "hm"

with t_view.unsafe():
    t_view[3] = "hm"
    t_view[4] = "hm"
    t_view.size += 2

print(t)

i = t_view[1]
print(i)
i_view = view(i)

with i_view.unsafe():
    i_view.value = 5

print(t)
print(1+1)
