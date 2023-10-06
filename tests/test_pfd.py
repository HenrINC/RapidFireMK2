import io
from pathlib import Path

import pytest
from ps3_lib import SFO

from .common import _test_params, get_dummy_npuserid, get_npuserid

_test_params = pytest.mark.parametrize(
    "sfo_path", set(Path().glob("**/test_trophies/*/PARAM.SFO"))
)