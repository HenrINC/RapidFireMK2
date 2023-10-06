"""
YES commands do actually break pep8 but have you seen the __new__ command ? its not even a class at this point its templated functions

https://github.com/aldostools/webMAN-MOD/wiki/Web-Commands
"""
import io
import enum
import zipfile
import datetime


import cv2
import requests
import numpy as np
from bs4 import BeautifulSoup
from pydantic import BaseModel, field_validator, ConfigDict


from .structs import (
    PS3Path,
    PS3_INPUT,
    PS3_LED_COLORS,
    PS3_LED_MODES,
    PS3_BUZZER_SOUNDS,
    PS3_SYSCALL_LEVELS
)


class CommandKwargsModel(BaseModel):
    def __str__(self) -> str:
        return "&".join(
            [
                f"{key}={value}"
                for key, value in self.model_dump().items()
                if value is not None
            ]
        )

    def __bool__(self) -> bool:
        return any([value is not None for value in self.model_dump().values()])


class EmptyKwargs:
    def __init__(self, **kwargs) -> None:
        assert kwargs == {}, "Invalid keyword arguments"

    def __str__(self) -> str:
        return ""

    def __bool__(self) -> bool:
        return False


def post_process_nullify(response: requests.Response) -> None:
    response.raise_for_status()
    return None


class Command:
    path: str | None = None
    available_args: tuple = ()
    kwargs_validator: CommandKwargsModel | None = None
    args_separator: str = "&"
    args_prefix: str = "?"

    def __new__(cls, url, *args, timeout=5, **kwargs):
        no_args_allowed = cls.available_args in (None, ())
        no_kwargs_allowed = cls.kwargs_validator == None
        allow_no_args = no_args_allowed or None in cls.available_args
        has_args = args != ()
        has_kwargs = kwargs != {}
        if not allow_no_args:
            assert args != (), "No arguments provided"
            args = [arg.value if isinstance(arg, enum.Enum) else arg for arg in args]
        if not no_kwargs_allowed:
            assert kwargs != {}, "No keyword arguments provided"
            kwargs = cls.kwargs_validator(**kwargs)
        else:
            kwargs = EmptyKwargs(**kwargs)
        if not no_args_allowed:
            assert "*" in cls.available_args or all(
                [arg in cls.available_args for arg in args]
            ), f"Invalid arguments provided, available arguments are: {cls.available_args}"

        command_path = cls.path
        if has_args or has_kwargs:
            command_path += cls.args_prefix

        if has_args:
            command_path += cls.args_prefix.join(args)
            if has_kwargs:
                command_path += cls.args_prefix

        if has_kwargs:
            command_path += str(kwargs)

        command_url = url + command_path
        return cls.post_process(requests.get(command_url, timeout=timeout))

    @classmethod
    def post_process(cls, response: requests.Response) -> requests.Response:
        return response


class reboot(Command):
    path = "/reboot.ps3"
    available_args = (
        "hard",  # hard reboot
        "soft",  # soft reboot
        "quick",  # quick reboot (load LPAR id 1)
        "vsh",  # reboot using VSH command (same as /restart.ps3)
        None,  # hard reboot
    )

    post_process = post_process_nullify


class stat(Command):
    path = "/stat.ps3"
    available_args = ("*",)
    args_prefix = "/"
    args_separator = "/"


class led(Command):
    path = "/led.ps3mapi"
    available_args = None

    class kwargs_validator(CommandKwargsModel):
        color: PS3_LED_COLORS
        mode: PS3_LED_MODES

        @field_validator("color")
        def validate_color(cls, color: PS3_LED_COLORS) -> int:
            return color.value

        @field_validator("mode")
        def validate_mode(cls, mode: PS3_LED_MODES) -> int:
            return mode.value

    post_process = post_process_nullify


class buzzer(Command):
    path = "/buzzer.ps3mapi"
    available_args = None

    class kwargs_validator(CommandKwargsModel):
        snd: PS3_BUZZER_SOUNDS

        @field_validator("snd")
        def validate_snd(cls, snd: PS3_BUZZER_SOUNDS) -> int:
            return snd.value

    post_process = post_process_nullify


class pad(Command):
    path = "/pad.ps3"
    available_args = [member.value for member in PS3_INPUT.__members__.values()]
    post_process = post_process_nullify


class screenshot(Command):
    path = "/xmb.ps3$screenshot"
    available_args = ("*",)
    args_prefix = "/"
    post_process = post_process_nullify


class show_screenshot(Command):
    path = "/xmb.ps3$screenshot?show"
    available_args = ("fast",None)

    @classmethod
    def post_process(cls, response: requests.Response) -> requests.Response:
        response.raise_for_status()
        nparr = np.frombuffer(response.content, np.uint8)
        return cv2.imdecode(nparr, cv2.IMREAD_COLOR)


class explore_plugin(Command):
    path = "/xmb.ps3"
    args_prefix = "$"
    available_args = ("*",)
    post_process = post_process_nullify


class xmb_plugin(Command):
    path = "/xmb.ps3"
    args_prefix = "*"
    available_args = ("*",)
    post_process = post_process_nullify


class file(Command):
    path = "/"
    args_prefix = ""
    available_args = ("*",)


class user_id(Command):
    path = "/dev_hdd0/home/$USERID$/"
    available_args = None

    @classmethod
    def post_process(cls, response: requests.Response) -> str:
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        return soup.select_one("#content > a:not(.f)").text


class zip(Command):
    path = "/dozip.ps3"
    args_prefix = "/"
    available_args = ("*",)

    class kwargs_validator(CommandKwargsModel):
        model_config = ConfigDict(arbitrary_types_allowed=True)
        to: PS3Path | str

        @field_validator("to")
        def validate_path(cls, path: PS3Path | str) -> str:
            return str(PS3Path(path))

    post_process = post_process_nullify


class get(Command):
    path = "/"
    args_prefix = ""
    available_args = ("*",)

    @classmethod
    def post_process(cls, response: requests.Response) -> requests.Response:
        response.raise_for_status()
        return response


class mkdir(Command):
    path = "/mkdir.ps3"
    args_prefix = "/"
    available_args = ("*",)
    post_process = post_process_nullify


class mount(Command):
    path = "/mount.ps3"
    args_prefix = "/"
    available_args = ("*",)
    post_process = post_process_nullify


class uptime(Command):
    path = "/cpursx.ps3?/sman.ps3"

    @classmethod
    def post_process(cls, response: requests.Response) -> requests.Response:
        soup = BeautifulSoup(response.content, "html.parser")
        uptime_str = soup.select_one(
            "[href*='/dev_hdd0/home/']"
        ).text
        hours, minutes, seconds = uptime_str.split(":")[-3:]
        return int(seconds) + int(minutes) * 60 + int(hours) * 60 * 60


class popup(Command):
    path = "/popup.ps3"
    args_prefix = "/"
    args_separator = ""
    available_args = ("*",)
    post_process = post_process_nullify


class info(Command):
    path = "/popup.ps3"
    args_prefix = "/"
    args_separator = ""
    available_args = ("*",)

    @classmethod
    def post_process(cls, response: requests.Response) -> dict:
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        return soup.select_one("#content").text

class syscall(Command):
    path = "/syscall.ps3"
    args_prefix = "?"
    args_separator = "|"
    available_args = ("*",)

class syscall8(Command):
    path = "/syscall8.ps3mapi"
    args_prefix = "?"
    available_args = None
    class kwargs_validator(CommandKwargsModel):
        model_config = ConfigDict(arbitrary_types_allowed=True)
        mode: PS3_SYSCALL_LEVELS | int

        @field_validator("mode")
        def validate_path(cls, mode: PS3Path | str) -> str:
            if isinstance(mode, PS3_SYSCALL_LEVELS):
                return mode.value
            else:
                return PS3_SYSCALL_LEVELS(mode).value

class delete_history(Command):
    path = "/delete_history.ps3?history"
    available_args = None

class rebuild_database(Command):
    path = "/rebuild.ps3"
    available_args = None

class listdir(Command):
    path = "/"
    args_prefix = ""
    available_args = ("*",)

    @classmethod
    def post_process(cls, response: requests.Response) -> requests.Response:
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        return [i.text for i in soup.select("table#files tr>td:first-child:not([colspan])>*:first-child:not([href='..'])")]



## Shortcuts and other higher level commands


def very_fast_screenshot(url):
    raise ValueError("Very unstable and not working yet")
    very_fast_screenshot_root = PS3Path("dev_hdd0/tmp/very_fast_screenshot/")
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    screenshot_folder = very_fast_screenshot_root / timestamp
    mkdir(url, str(screenshot_folder))
    screenshot_path = screenshot_folder / "screenshot.bmp"
    screenshot(url, str(screenshot_path))
    zip_path = PS3Path(str(screenshot_folder) + ".zip")
    zip(url, str(screenshot_folder), to=zip_path)
    zipped_screenshot = get(url, str(zip_path))
    with zipfile.ZipFile(io.BytesIO(zipped_screenshot), "r") as zip_ref:
        with zip_ref.open("screenshot.bmp") as bmp_file:
            screenshot_img = bmp_file.read()
    nparr = np.frombuffer(screenshot_img, np.uint8)
    return cv2.imdecode(nparr, cv2.IMREAD_COLOR)
