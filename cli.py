from pathlib import Path
from typing import Optional

import fire

from tools import PS3TrophyTool, PS3DumpTool

from yesman.ps3 import PS3


async def add_trophies(
    ps3_host: str,
    user: str,
    trophy_folder: str,
    file_transfer_mode: str = "FileSystem",
    config_folder: Optional[str] = "./config/",
):
    trophy_folder = Path(trophy_folder).resolve()
    config_folder = Path(config_folder).resolve()
    tool = PS3TrophyTool(
        ps3_host=ps3_host,
        file_transfer_mode=file_transfer_mode,
        config_folder=config_folder,
    )
    await tool.add_trophies(user=user, trophy_folder=trophy_folder)


async def dump_registry(
    ps3_host: str,
    output_folder: str,
):
    output_folder = Path(output_folder).resolve()

    tool = PS3DumpTool(ps3_host=ps3_host)
    await tool.dump_registry(output_folder=output_folder)


async def dump_remote_sfo(
    ps3_host: str,
    sfo_path: str,
    output_folder: str,
):
    output_folder = Path(output_folder).resolve()

    tool = PS3DumpTool(ps3_host=ps3_host)
    await tool.dump_sfo(output_folder=output_folder)


async def wakeup(
    ps3_host: str,
    ps3_port: int = 80,
):
    tool = PS3(host=ps3_host, port=ps3_port)
    tool.wakeup()


async def force_enable_wake_on_lan(
    ps3_host: str,
    ps3_port: int = 80,
):
    """
    This modifies the xRegistry.sys file to force enable Wake On Lan.
    So yeah this is a pretty dangerous operation, use it at your own risk.
    """
    tool = PS3(host=ps3_host, port=ps3_port)
    tool.update_registry_entry("/setting/premo/remoteBoot", "1")


async def force_disable_hdcp(
    ps3_host: str,
    ps3_port: int = 80,
):
    """
    This modifies the xRegistry.sys file to force disable HDCP.
    So yeah this is a pretty dangerous operation, use it at your own risk.
    """
    tool = PS3(host=ps3_host, port=ps3_port)
    tool.update_registry_entry("/setting/display/0/hdcp", "0")


if __name__ == "__main__":
    fire.Fire()
