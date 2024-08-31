import io
from pathlib import Path

import pytest
from yesman.parsers import SFO

from common import get_dummy_npuserid, get_npuserid

_test_params = pytest.mark.parametrize(
    "sfo_path", set(Path().glob("**/test_trophies/*/PARAM.SFO"))
)