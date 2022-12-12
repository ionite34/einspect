import sys

def foo():
    return "abc 123 def"
print(sys.getrefcount(foo()))

s2 = "500 def 123"
print(sys.getrefcount(s2))
