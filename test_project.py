import pytest
from project import suma

def test_suma():
    assert suma(2,3) is 5
    assert suma(4,5) is 9
    assert suma(5,5) is 10