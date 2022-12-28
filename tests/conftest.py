import sys
from multiprocessing import Process
from pathlib import Path

import pytest

TESTS_DIR = Path(__file__).parent


class Unbuffered:
    def __init__(self, stream):
        self.stream = stream

    def write(self, data):
        self.stream.write(data)
        self.stream.flush()

    def writelines(self, datas):
        self.stream.writelines(datas)
        self.stream.flush()

    def __getattr__(self, attr):
        return getattr(self.stream, attr)


def _run(func_path: Path, name: str):
    import importlib

    rel_path = func_path.relative_to(TESTS_DIR)
    mod = importlib.import_module(".".join(rel_path.parts).strip(".py"))
    sys.stdout = Unbuffered(sys.stdout)
    fn = getattr(mod, name)
    return fn()


def pytest_pyfunc_call(pyfuncitem: pytest.Function):
    if "run_in_subprocess" in pyfuncitem.keywords:
        p = Process(target=_run, args=(Path(pyfuncitem.fspath), pyfuncitem.name))
        p.start()
        p.join()
        if p.exitcode != 0:
            raise pytest.fail(
                f"Test executed in a subprocess failed with code {p.exitcode}",
                pytrace=False,
            )
        return True

    # Return None to indicate that we didn't run this test.
    # Signals pytest to try finding a suitable runner.
    return None
