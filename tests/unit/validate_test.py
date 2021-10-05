# Allow direct execution
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from webchela.core.validate import is_bool


def test_is_bool():
    assert is_bool("test", True, False)
    assert not is_bool("test", "", True)
    assert not is_bool("test", "True", False)
