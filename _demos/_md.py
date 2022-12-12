from einspect import view

tup = ("a", "b", "c")

v = view(tup)
v[0] = 123
v[1] = "hm..."
v[2] = "🤔"

print(tup)
