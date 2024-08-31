import json
from pathlib import Path

import aiofiles

from yesman import PS3
from yesman.parsers import XRegistry, SFO

def decode_bytes(input_data: dict[str, bytes | str | dict | list | tuple], **kwargs) -> dict[str, str]:
    """
    Recursively decode byte objects in a nested structure to strings.

    :param input_data: The input data, could be any nested structure.
    :return: Input structure with bytes decoded to strings.
    """
    if isinstance(input_data, bytes):
        return input_data.decode(**kwargs)
    elif isinstance(input_data, dict):
        return {key: decode_bytes(value, **kwargs) for key, value in input_data.items()}
    elif isinstance(input_data, list):
        return [decode_bytes(item, **kwargs) for item in input_data]
    elif isinstance(input_data, tuple):
        return tuple(decode_bytes(item, **kwargs) for item in input_data)
    else:
        return input_data
class PS3DumpTool:
    def __init__(self, ps3_host: str, ps3_port: int = 80):
        self.ps3_host = ps3_host
        self.ps3_port = ps3_port
        self.ps3 = PS3(host=ps3_host, port=ps3_port)

    async def dump_registry(self, output_folder: Path):
        registry_bytes =  self.ps3.get_file("/dev_flash2/etc/xRegistry.sys")
        registry = XRegistry.from_bytes(registry_bytes)
        async with aiofiles.open(output_folder / "xRegistry.sys", "wb") as f:
            await f.write(registry_bytes)

        async with aiofiles.open(output_folder / "xRegistry.json", "w") as f:
            hierarchy = decode_bytes(registry.hierarchy, encoding="utf-8", errors="ignore")
            await f.write(json.dumps(hierarchy, indent=4))
    
    async def dump_sfo(self, sfo_path, output_folder: Path):
        sfo_bytes =  self.ps3.get_file(sfo_path)
        sfo = SFO.from_bytes(sfo_bytes)
        async with aiofiles.open(output_folder / sfo_path.name, "wb") as f:
            await f.write(sfo_bytes)

        async with aiofiles.open(output_folder / f"{sfo_path.name}.json", "w") as f:
            sfo_dict = decode_bytes(sfo.to_dict(), encoding="utf-8", errors="ignore")
            await f.write(json.dumps(sfo_dict, indent=4))
