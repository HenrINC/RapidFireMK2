import os
import time
import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory

import fire
import shutil

from pfd_sfo_toolset import PFDTool

from ps3_lib import (
    PS3,
    SFO,
    XRegistry,
    PS3_LED_COLORS,
    PS3_LED_MODES,
    PS3_INPUT,
    PS3_BUZZER_SOUNDS,
    PS3Path,
    PS3_XMB_COLS,
)

from ps3_lib import file_transfer

from ps3_lib.file_transfer import PS3AbstractFileTransfer, PS3RobustFTPFileTransfer


class PS3TrophyToolset:
    TEMP_TROPHY_DATA_SUFFIX = "TROPDATA"

    def __init__(
        self,
        ps3_host,
        ps3_port=80,
        config_folder="./config/",
        file_transfer_backend: type[PS3AbstractFileTransfer] = PS3RobustFTPFileTransfer,
        file_transfer_backend_kwargs={},
    ) -> None:
        self.ps3 = PS3(f"http://{ps3_host}:{ps3_port}/")
        self.config_folder = Path(config_folder)
        file_transfer_backend_kwargs = {
            "ps3_host": ps3_host,
            **file_transfer_backend_kwargs,
        }
        self.file_transfer = file_transfer_backend(**file_transfer_backend_kwargs)

    async def update_and_upload_trophy_folder(
        self, path: Path | str, account_id: bytes
    ):
        path = Path(path).resolve()
        assert path.is_dir(), f"{path} is not a directory"
        content = os.listdir(path)
        sub_folders = [f for f in content if (path / f).is_dir()]
        if sub_folders:
            await asyncio.gather(
                *(
                    self.update_and_upload_trophy_folder(path / sub_folder, account_id)
                    for sub_folder in sub_folders
                )
            )
            return
        print(f"Processing {path.name}")
        with TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            tropdata_folder = tmpdir / self.TEMP_TROPHY_DATA_SUFFIX
            shutil.copytree(path, tropdata_folder, dirs_exist_ok=True)
            shutil.copytree(self.config_folder, tmpdir, dirs_exist_ok=True)
            print(f"Updating {path.name}")
            np_comm_id = await self.update_trophy_folder(tmpdir, account_id)
            print(f"Uploading {path.name}")
            await self.upload_trophy_folder(tropdata_folder, np_comm_id=np_comm_id)
        print(f"Processed {path.name}")

    async def update_trophy_folder(self, path: Path | str, account_id: bytes):
        pfd_tool = PFDTool(working_directory=path)

        sfo_files = tuple((path / self.TEMP_TROPHY_DATA_SUFFIX).glob("*.SFO"))
        assert sfo_files, f"No sfo files found in {path}"
        assert len(sfo_files) == 1, f"Multiple sfo files found in {path}"
        sfo_path = Path(sfo_files[0])
        sfo = SFO.from_file(sfo_path)
        title_id = sfo["TITLEID000"].value.decode()
        np_comm_id = sfo["NPCOMMID"].value.decode()

        sfo["ACCOUNTID"] = account_id
        sfo.to_file(sfo_path)

        await pfd_tool.update(self.TEMP_TROPHY_DATA_SUFFIX, "PARAM.SFO", game=title_id)
        return np_comm_id

    async def upload_trophy_folder(self, path: Path | str, np_comm_id: str):
        trophy_dir = (
            PS3Path("dev_hdd0")
            / "home"
            / self.ps3.get_current_user_id()
            / "trophy"
            / np_comm_id
        )
        await self.file_transfer.send(path, trophy_dir)

    def get_account_id(self) -> bytes:
        user_id = self.ps3.get_current_user_id()
        registry = XRegistry.from_bytes(
            self.ps3.get_file("/dev_flash2/etc/xRegistry.sys")
        )
        try:
            account_id = registry.hierarchy["setting"]["user"][user_id]["npaccount"][
                "accountid"
            ]
            if not account_id:
                raise ValueError(
                    f"The current account id is blank, the user {user_id} is not logged in"
                )
        except KeyError:
            raise ValueError("The current account id has no account id in the registry")

        return account_id

    async def login(self, username: str):
        if self.ps3.is_logged_in:
            assert (
                self.ps3.get_file(
                    PS3Path("dev_hdd0") / "home" / "$USERID$" / "localusername"
                ).decode()
                == username
            ), "The current user is not the one you provided"
            return
        self.ps3.goto(
            category=PS3_XMB_COLS.user_login,
            item="user_provider_1",
            item_index=[i.name for i in self.ps3.users].index(username),
        )
        self.ps3.press_key(PS3_INPUT.accept)
        await asyncio.wait_for(self.ps3.await_user_login(), timeout=10)

    async def run(self, trophy_folder, user, restrict_syscall8_access=False):
        self.ps3.play_buzzer_sound(PS3_BUZZER_SOUNDS.simple)
        self.ps3.set_led_color(PS3_LED_COLORS.green, PS3_LED_MODES.blink_fast)
        try:
            if not restrict_syscall8_access:
                self.ps3.enable_syscalls()
            await self.file_transfer.connect()
            await self.login(user)
            try:
                account_id = self.get_account_id()
            except Exception as e:
                if not restrict_syscall8_access:
                    time.sleep(1)
                    self.ps3.clear_history()
                    self.ps3.disable_syscalls(fake=True)
                    print(
                        "Could not get account id, you likely never logged in with this user before, "
                        "i already disabled syscalls so you can safely do it manually, "
                        "don't worry, they re-enable on restart"
                    )
                raise e
            await self.file_transfer.mkdir(
                PS3Path("dev_hdd0") / "home" / self.ps3.get_current_user_id() / "trophy"
            )
            await self.update_and_upload_trophy_folder(trophy_folder, account_id)
            await self.ps3.rebuild_database()

        except Exception as e:
            time.sleep(1)
            self.ps3.play_buzzer_sound(PS3_BUZZER_SOUNDS.triple)
            self.ps3.set_led_color(PS3_LED_COLORS.red, PS3_LED_MODES.blink_slow)
            raise e
        else:
            self.ps3.play_buzzer_sound(PS3_BUZZER_SOUNDS.double)
            self.ps3.set_led_color(PS3_LED_COLORS.green, PS3_LED_MODES.on)

    __call__ = run


async def entrypoint(
    ps3_host=None,
    ps3_port=None,
    trophy_folder=None,
    config_folder=None,
    restrict_syscall8_access=False,
    file_transfer_backend=None,
    file_transfer_backend_kwargs={},
    user=None,
):
    ps3_host = ps3_host or os.environ.get("PS3_HOST", None)
    assert ps3_host, "Please provide a ps3 host"

    ps3_port = ps3_port or os.environ.get("PS3_PORT", None) or 80

    trophy_folder = (
        trophy_folder or os.environ.get("TROPHY_FOLDER", None) or "/trophies"
    )

    config_folder = config_folder or os.environ.get("CONFIG_FOLDER", None) or "/config"

    restrict_syscall8_access = (
        restrict_syscall8_access
        or bool(int(os.environ.get("RESTRICT_SYSCALL8_ACCESS", 0)))
        or False
    )

    file_transfer_backend = getattr(
        file_transfer,
        file_transfer_backend
        or os.environ.get("FILE_TRANSFER_BACKEND", None)
        or "PS3RobustFTPFileTransfer",
    )

    user = user or os.environ.get("PS3_USER", None)

    toolset = PS3TrophyToolset(
        ps3_host,
        ps3_port,
        config_folder=config_folder,
        file_transfer_backend=file_transfer_backend,
        file_transfer_backend_kwargs=file_transfer_backend_kwargs,
    )
    await toolset.run(
        trophy_folder, user=user, restrict_syscall8_access=restrict_syscall8_access
    )


if __name__ == "__main__":
    fire.Fire(entrypoint)
