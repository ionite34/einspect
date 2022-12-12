from types import CodeType

import _main2
import dis

co: CodeType = _main2.__spec__.loader.get_code("_main2")
print(co.co_consts)
