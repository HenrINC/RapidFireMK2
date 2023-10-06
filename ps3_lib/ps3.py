import asyncio

from typing import TYPE_CHECKING
from collections import OrderedDict

from . import commands
from .user import User
from .xmb.item_factory import XMBFactory

from .structs import (
    PS3_INPUT,
    PS3_XMB_COLS,
    PS3_LED_COLORS,
    PS3_LED_MODES,
    PS3_BUZZER_SOUNDS,
    PS3_XMB_APPS,
    PS3Path,
    PS3_CFW_INFOS,
    PS3_SYSCALL_LEVELS,
)

if TYPE_CHECKING:
    from .xmb.xmb import XMB


class PS3:
    def __init__(self, url) -> None:
        self.url = url.rstrip("/")

    def set_led_color(
        self, color: PS3_LED_COLORS, mode: PS3_LED_MODES, clean: bool = True
    ):
        if clean:
            self.set_led_off()
        commands.led(self.url, color=color, mode=mode)

    def set_led_off(self):
        self.set_led_color(PS3_LED_COLORS.yellow, PS3_LED_MODES.off, clean=False)

    def play_buzzer_sound(self, sound: PS3_BUZZER_SOUNDS):
        commands.buzzer(self.url, snd=sound)

    def get_screenshot(self, fast: bool = False):
        if fast:
            return commands.show_screenshot(self.url, "fast")
        else:
            return commands.show_screenshot(self.url)

    def get_screenshot_very_fast(self):
        return commands.very_fast_screenshot(self.url)

    def go_to_category(self, category: PS3_XMB_COLS):
        explore_plugin_command = f"focus_category {category.value}"
        commands.explore_plugin(self.url, explore_plugin_command)

    def go_to_item(self, item: str | int, index: int = 0):
        if isinstance(item, int):
            explore_plugin_command = f"focus_index {item} {index}"
        else:
            explore_plugin_command = f"focus_segment_index {item} {index}"
        commands.explore_plugin(self.url, explore_plugin_command)

    def go_to_index(self, index: int):
        explore_plugin_command = f"focus_index {index}"
        commands.explore_plugin(self.url, explore_plugin_command)

    def run_xmb_app(self, app: PS3_XMB_APPS):
        explore_plugin_command = f"exec_app {app.value}"
        commands.explore_plugin(self.url, explore_plugin_command)

    def get_current_user_id(self):
        return commands.user_id(self.url)

    def goto(self, category: PS3_XMB_COLS, item: str | int, item_index: int = 0):
        self.go_to_category(category)
        self.go_to_item(item, index=item_index)

    def mount_game(self, game_id: str):
        game_path = PS3Path("dev_hdd0") / "game" / game_id / "USRDIR" / "EBOOT.BIN"
        commands.mount(self.url, str(game_path))

    def press_key(self, key: PS3_INPUT):
        commands.pad(self.url, key.value)

    def reboot(self, mode=None):
        if mode is None:
            commands.reboot(self.url)
        else:
            commands.reboot(self.url, mode)

    def get_file(self, path: str | PS3Path):
        response = commands.get(self.url, str(PS3Path(path)))
        return response.content

    def get_uptime(self):
        return commands.uptime(self.url)

    async def await_restart(self, current_uptime=None):
        uptime = self.get_uptime() if current_uptime is None else current_uptime
        while True:
            try:
                if self.get_uptime() < uptime:
                    return
            except:
                pass
            await asyncio.sleep(1)

    async def await_startup(self, target_uptime=5):
        while True:
            try:
                if self.get_uptime() < target_uptime:
                    return
            except:
                pass
            await asyncio.sleep(1)

    async def await_uptime(self, target_uptime=5):
        while True:
            try:
                if self.get_uptime() >= target_uptime:
                    return
            except:
                pass
            await asyncio.sleep(1)

    async def await_user_login(self, username: str | None = None):
        while True:
            try:
                if username is None:
                    if self.is_logged_in:
                        return
                else:
                    if (
                        self.get_file(
                            PS3Path("dev_hdd0") / "home" / "$USERID$" / "localusername"
                        ).decode()
                        == username
                    ):
                        return
            except:
                pass

    def get_info(self, info: PS3_CFW_INFOS):
        return commands.info(self.url, info.value)

    def disable_syscalls(self, fake=True):
        if fake:
            self.set_syscalls(PS3_SYSCALL_LEVELS.fake_disabled)
        else:
            self.set_syscalls(PS3_SYSCALL_LEVELS.fully_disabled)

    def enable_syscalls(self):
        self.set_syscalls(PS3_SYSCALL_LEVELS.fully_enabled)

    def set_syscalls(self, level: PS3_SYSCALL_LEVELS):
        commands.syscall8(self.url, mode=level.value)

    def clear_history(self):
        commands.delete_history(self.url)

    async def rebuild_database(self):
        commands.rebuild_database(self.url)
        await asyncio.sleep(5)
        await self.await_uptime(10)
        self.press_key(PS3_INPUT.accept)
        await self.await_restart(20)

    @property
    def is_logged_in(self):
        try:
            self.get_current_user_id()
        except:
            return False
        else:
            return True

    @property
    def xmb(self) -> "XMB":
        return self.get_xmb()

    def get_xmb(self) -> "XMB":
        xmb_root_path = PS3Path("dev_flash/vsh/resource/explore/xmb/")
        factory = XMBFactory(self)

        return factory.build_xmb(
            categories=OrderedDict(
                (
                    category.value,
                    self.get_file(xmb_root_path / f"category_{category.value}.xml"),
                )
                for category in (
                    [
                        PS3_XMB_COLS.user,
                        PS3_XMB_COLS.sysconf,
                        PS3_XMB_COLS.photo,
                        PS3_XMB_COLS.music,
                        PS3_XMB_COLS.video,
                        PS3_XMB_COLS.tv,
                        PS3_XMB_COLS.game,
                        PS3_XMB_COLS.network,
                        PS3_XMB_COLS.psn,
                        PS3_XMB_COLS.friend,
                    ]
                    if self.is_logged_in
                    else [PS3_XMB_COLS.user_login]
                )
            )
        )

    def listdir(self, path: PS3Path):
        for file in commands.listdir(self.url, str(path)):
            yield path / file

    @property
    def users(self):
        for user in self.listdir(PS3Path("dev_hdd0/home")):
            username = self.get_file(user / "localusername").decode("utf-8").strip()
            user_id = int(user.name)
            yield User(id=user_id, name=username)
