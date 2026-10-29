import json
import shutil
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def assessment():
    return json.loads((ROOT / "examples/complete.json").read_text())


@pytest.fixture
def evidence_root(tmp_path):
    target = tmp_path / "exports"
    shutil.copytree(ROOT / "examples/evidence", target)
    return target
