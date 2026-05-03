import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from cell import Cell


@pytest.fixture(autouse=True)
def _reset_cell_id():
    Cell._next_id = 0
    yield
    Cell._next_id = 0
