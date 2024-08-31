import re
import os
import time
import asyncio
import logging
from pathlib import Path
from tempfile import TemporaryDirectory

import shutil
import pytesseract
from PIL import Image

from yesman import PS3
from yesman.parsers import SFO, XRegistry
from yesman.file_transfer import PS3FileTransferFactory
from yesman.wrappers import PFDTool
from yesman.structs import (
    PS3_LED_COLORS,
    PS3_LED_MODES,
    PS3_INPUT,
    PS3_BUZZER_SOUNDS,
    PS3Path,
    PS3_XMB_COLS,
)
from yesman.constants import (
    CORRUPTED_TROPHY_SYNC_ERRORS,
    FATAL_TROPHY_SYNC_ERRORS,
    PLATINUM_TROPHY_SYNC_ERRORS,
)

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)

class XRegistryError(ValueError):
    pass


class PS3TrophyTool:
    TEMP_TROPHY_DATA_SUFFIX = "TROPHY_DATA"

    def __init__(
        self,
        ps3_host,
        ps3_port=80,
        config_folder="./config/",
        file_transfer_mode: str = "FileSystem",
        file_transfer_backend_kwargs={},
    ) -> None:
        self.ps3 = PS3(host=ps3_host, port=ps3_port)
        self.config_folder = Path(config_folder)
        file_transfer_backend_kwargs = {
            "ps3_host": ps3_host,
            **file_transfer_backend_kwargs,
        }
        self.file_transfer = PS3FileTransferFactory.create(
            file_transfer_mode, **file_transfer_backend_kwargs
        )

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
        logger.debug(f"Processing {path.name}")
        with TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            trophy_data_folder = tmpdir / self.TEMP_TROPHY_DATA_SUFFIX
            shutil.copytree(path, trophy_data_folder, dirs_exist_ok=True)
            shutil.copytree(self.config_folder, tmpdir, dirs_exist_ok=True)
            logger.debug(f"Updating {path.name}")
            np_comm_id = await self.update_trophy_folder(tmpdir, account_id)
            logger.debug(f"Uploading {path.name}")
            await self.upload_trophy_folder(trophy_data_folder, np_comm_id=np_comm_id)
        logger.info(f"Processed {path.name}")

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
        await pfd_tool.update(self.TEMP_TROPHY_DATA_SUFFIX, game=title_id, partial=True)
        await pfd_tool.update(self.TEMP_TROPHY_DATA_SUFFIX, game=title_id)
        return np_comm_id

    async def upload_trophy_folder(self, path: Path | str, np_comm_id: str):
        trophy_dir = (
            PS3Path("dev_hdd0") / "home" / str(self.user_id) / "trophy" / np_comm_id
        )
        await self.file_transfer.send(path, trophy_dir)

    def get_account_id(self) -> bytes:
        registry = XRegistry.from_bytes(
            self.ps3.get_file("/dev_flash2/etc/xRegistry.sys")
        )
        try:
            account_id = registry.hierarchy["setting"]["user"][str(self.user_id)][
                "npaccount"
            ]["accountid"]
            if not account_id:
                raise XRegistryError(
                    f"The current account id is blank, the user {self.username} is not logged in"
                )
        except KeyError:
            raise XRegistryError(
                "The current account id has no account id in the registry"
            )

        return account_id

    async def login(self, user: str):
        """
        Logs the ps3 into the user provided, it can be either the username or the user id
        """
        users = tuple(self.ps3.users)
        if user in [i.name for i in users]:
            self.username = user
            self.user_id = [i.id for i in users if i.name == user][0]
        else:
            self.username = [i.name for i in users if i.id == user][0]
            self.user_id = user

        if self.ps3.is_logged_in:
            if int(self.ps3.get_current_user_id()) == self.user_id:
                return
            user_xmb_category = PS3_XMB_COLS.user
        else:
            user_xmb_category = PS3_XMB_COLS.user_login

        user_xmb_index = [i.name for i in users].index(self.username)

        self.ps3.goto(
            category=user_xmb_category,
            item="user_provider_1",
            item_index=user_xmb_index,
        )
        self.ps3.press_key(PS3_INPUT.accept)
        if user_xmb_category == PS3_XMB_COLS.user:
            # We have to confirm the logout
            self.ps3.press_key(PS3_INPUT.accept)
        await asyncio.wait_for(self.ps3.await_user_login(), timeout=10)

    async def await_sync_error(self):
        screenshot = self.ps3.get_screenshot()
        screenshot = Image.fromarray(screenshot)
        text = pytesseract.image_to_string(screenshot)
        re.search(r'\b\d{4}[a-fA-F0-9]{4}\b', text)
        

    async def add_trophies(self, trophy_folder, user, restrict_syscall8_access=False):
        self.ps3.play_buzzer_sound(PS3_BUZZER_SOUNDS.simple)
        self.ps3.set_led_color(PS3_LED_COLORS.green, PS3_LED_MODES.blink_fast)
        try:
            if not restrict_syscall8_access:
                self.ps3.enable_syscalls()
            await self.ps3.await_uptime(20)
            await self.file_transfer.connect()
            await self.login(user)
            try:
                account_id = self.get_account_id()
            except XRegistryError as e:
                if not restrict_syscall8_access:
                    time.sleep(1)
                    self.ps3.clear_history()
                    self.ps3.disable_syscalls(fake=True)
                    logging.fatal(
                        "Could not get account id, you likely never logged in with this user before, "
                        "i already disabled syscalls so you can safely do it manually, "
                        "don't worry, they re-enable on restart"
                    )
                raise e
            ps3_trophy_folder = (
                PS3Path("dev_hdd0") / "home" / str(self.user_id) / "trophy"
            )
            try:
                await self.file_transfer.delete(ps3_trophy_folder)
            except:
                pass
            await self.file_transfer.mkdir(ps3_trophy_folder)
            await self.update_and_upload_trophy_folder(trophy_folder, account_id)
            await self.ps3.rebuild_database()
            await self.ps3.await_uptime(10)
            await self.login(self.user_id)
            self.ps3.disable_syscalls(fake=True)
            await asyncio.sleep(3)
            self.ps3.goto(category=PS3_XMB_COLS.psn, item="seg_regist")
            await asyncio.sleep(1)
            self.ps3.press_key(PS3_INPUT.accept)
            await asyncio.sleep(1)
            self.ps3.press_key(PS3_INPUT.accept)
            await asyncio.sleep(15)
            while True:
                self.ps3.goto(category=PS3_XMB_COLS.psn, item="seg_trophy")
                await asyncio.sleep(1)
                self.ps3.press_key(PS3_INPUT.triangle)
                await asyncio.sleep(1)
                self.ps3.press_key(PS3_INPUT.accept)
                break
                sync_error = await self.await_sync_error()
                if sync_error in CORRUPTED_TROPHY_SYNC_ERRORS:
                    ...
                elif sync_error in PLATINUM_TROPHY_SYNC_ERRORS:
                    for trophy_folder in self.file_transfer.listdir(ps3_trophy_folder):
                        if trophy_folder.name.startswith("_SK"):
                            await self.file_transfer.delete(trophy_folder)
                elif sync_error in FATAL_TROPHY_SYNC_ERRORS:
                    raise RuntimeError(
                        f"Fatal trophy sync error {sync_error} while syncing trophies"
                    )

        except Exception as e:
            time.sleep(1)
            self.ps3.play_buzzer_sound(PS3_BUZZER_SOUNDS.triple)
            self.ps3.set_led_color(PS3_LED_COLORS.red, PS3_LED_MODES.blink_slow)
            raise e
        else:
            self.ps3.play_buzzer_sound(PS3_BUZZER_SOUNDS.double)
            self.ps3.set_led_color(PS3_LED_COLORS.green, PS3_LED_MODES.on)
