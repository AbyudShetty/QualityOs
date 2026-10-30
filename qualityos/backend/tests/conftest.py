"""Fresh product-local stores; never purge an existing runtime or pytest history."""
from pathlib import Path
from uuid import uuid4

import pytest


@pytest.fixture
def tmp_path():
    path = Path(__file__).parents[2] / "var/test-runs" / uuid4().hex
    path.mkdir(parents=True, exist_ok=False)
    return path
