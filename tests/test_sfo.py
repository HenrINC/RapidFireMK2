import io
from pathlib import Path

import pytest
from ps3_lib import SFO

from .common import get_dummy_npuserid, get_npuserid

_test_params = pytest.mark.parametrize(
    "sfo_path", set(Path().glob("**/test_trophies/*/PARAM.SFO"))
)

@_test_params
def test_read(sfo_path):
    sfo = SFO.from_file(sfo_path)
    assert "ACCOUNTID" in sfo, "We are testing trophies, not games saves"
    assert sfo["ACCOUNTID"].value == get_npuserid().encode()

@_test_params
def test_write(sfo_path):
    with open(sfo_path, "rb") as f:
        original = f.read()
    sfo = SFO.from_bytes(original)
    assert "ACCOUNTID" in sfo, "We are testing trophies, not games saves"
    sfo["ACCOUNTID"].value = get_dummy_npuserid().encode()
    buffer = io.BytesIO()
    sfo.to_buffer(buffer)
    buffer.seek(0)
    modified = buffer.read()
    assert modified != original
    assert len(modified) == len(original)
    assert SFO.from_bytes(modified)["ACCOUNTID"].value == get_dummy_npuserid().encode()

if __name__ == "__main__":
    pytest.main()
