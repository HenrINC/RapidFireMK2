"""
YES commands do actually break pep8 but have you seen the __new__ command ? its not even a class at this point its templated functions

https://github.com/aldostools/webMAN-MOD/wiki/Web-Commands
"""

from typing import Literal, Optional, Union


import cv2
import requests
import numpy as np
from bs4 import BeautifulSoup

from ...structs import (
    PS3_REBOOT_MODES,
    PS3_INPUT,
    PS3_LED_COLORS,
    PS3_LED_MODES,
    PS3_BUZZER_SOUNDS,
    PS3_SYSCALL_LEVELS,
)


def reboot(url, mode: Optional[PS3_REBOOT_MODES] = None):
    """
    Reboots the PS3 using the specified mode.

    Args:
        url (str): The base URL for the PS3.
        mode (Optional[PS3_REBOOT_MODES]): The mode in which to reboot the PS3. If None, default reboot is used.
    """

    command_path = "/reboot.ps3"
    if mode is not None:
        command_path += f"?{PS3_REBOOT_MODES(mode).value}"
    requests.get(url + command_path)


def led(url, color, mode):
    """
    Sets the LED color and mode of the PS3.

    Args:
        url (str): The base URL for the PS3.
        color (int): The color of the LED.
        mode (int): The mode of the LED.
    """

    command_path = "/led.ps3mapi"
    command_path += (
        f"?color={PS3_LED_COLORS(color).value}&mode={PS3_LED_MODES(mode).value}"
    )
    requests.get(url + command_path)


def buzzer(url, sound):
    """
    Plays a buzzer sound on the PS3.

    Args:
        url (str): The base URL for the PS3.
        sound (int): The sound to play.
    """

    command_path = "/buzzer.ps3mapi"
    command_path += f"?snd={PS3_BUZZER_SOUNDS(sound).value}"
    requests.get(url + command_path)


def pad(url, button):
    """
    Simulates a button press on the PS3 controller.

    Args:
        url (str): The base URL for the PS3.
        button (str): The button to press.
    """

    command_path = "/pad.ps3"
    command_path += f"?{PS3_INPUT(button).value}"
    requests.get(url + command_path)


def screenshot(url, mode: Optional[Literal["fast"]] = None):
    """
    Takes a screenshot of the PS3.

    Args:
        url (str): The base URL for the PS3.
        mode (Optional[str]): The mode in which to take the screenshot. If None, default mode is used.
    """

    command_path = "/xmb.ps3$screenshot?show"
    if mode is not None:
        command_path += f"?{mode}"
    response = requests.get(url + command_path)
    response.raise_for_status()
    nparr = np.frombuffer(response.content, np.uint8)
    return cv2.imdecode(nparr, cv2.IMREAD_COLOR)


def explore_plugin(url, command):
    """
    Executes a command in the explore_plugin.

    Args:
        url (str): The base URL for the PS3.
        command (str): The command to execute.
    """

    command_path = f"/xmb.ps3${command}"
    requests.get(url + command_path)


def user_id(url):
    """
    Gets the current user id of the PS3.

    Args:
        url (str): The base URL for the PS3.
    """

    command_path = "/dev_hdd0/home/$USERID$/"
    response = requests.get(url + command_path)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, "html.parser")
    return soup.select_one("#content > a:not(.f)").text


def get(url, path):
    """
    Gets the content of a file on the PS3.

    Args:
        url (str): The base URL for the PS3.
        path (str): The path of the file to get.
    """

    if not path.startswith("/"):
        path = "/" + path
    response = requests.get(url + path)
    response.raise_for_status()
    return response


def uptime(url):
    """
    Gets the uptime of the PS3.

    Args:
        url (str): The base URL for the PS3.
    """

    command_path = "/cpursx.ps3?/sman.ps3"
    response = requests.get(url + command_path)
    soup = BeautifulSoup(response.content, "html.parser")
    uptime_str = soup.select_one("[href*='/dev_hdd0/home/']").text
    hours, minutes, seconds = uptime_str.split(":")[-3:]
    return int(seconds) + int(minutes) * 60 + int(hours) * 60 * 60


def popup(url, message):
    """
    Shows a popup message on the PS3.

    Args:
        url (str): The base URL for the PS3.
        message (str): The message to show.
    """

    command_path = f"/popup.ps3/{message}"
    requests.get(url + command_path)


def info(url, info):
    """
    Uses the popup formatting to get system information.

    """
    command_path = f"/popup.ps3/{info}"
    response = requests.get(url + command_path)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, "html.parser")
    return soup.select_one("#content").text


def syscall(url, syscall, *args):
    """
    Calls a syscall on the PS3.

    Args:
        url (str): The base URL for the PS3.
        syscall (int): The syscall to call.
        args (int): The arguments to pass to the syscall.
    """

    command_path = f"/syscall.ps3?{syscall}"
    if args:
        command_path += "|" + "|".join(args)
    response = requests.get(url + command_path)
    response.raise_for_status()
    return response


def syscall8(url, mode: Union[PS3_SYSCALL_LEVELS, int]):
    """
    Set the syscall level of the PS3.
    """
    command_path += f"?mode={mode}"
    response = requests.get(url + command_path)
    response.raise_for_status()
    return response


def delete_history(url):
    """
    Deletes the history of the PS3.
    """
    command_path = "/delete_history.ps3?history"
    response = requests.get(url + command_path)
    response.raise_for_status()
    return response


def rebuild_database(url):
    """
    Rebuilds the database of the PS3.
    """
    command_path = "/rebuild.ps3"
    response = requests.get(url + command_path)
    response.raise_for_status()
    return response


def listdir(url, path):
    """
    Lists the contents of a directory on the PS3.

    Args:
        url (str): The base URL for the PS3.
        path (str): The path of the directory to list.
    """

    if not path.startswith("/"):
        path = "/" + path
    response = requests.get(url + path)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, "html.parser")
    return [
        i.text
        for i in soup.select(
            "table#files tr>td:first-child:not([colspan])>*:first-child:not([href='..'])"
        )
    ]


def update_registry(url, key, value):
    """
    Updates a registry entry on the PS3.

    Args:
        url (str): The base URL for the PS3.
        key (str): The key of the entry to update.
        value (bytes): The value to set the entry to.
    """

    command_path = f"/xmb.ps3$xregistry({key})={value}"
    response = requests.get(url + command_path)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, "html.parser")
    return soup.select_one("h2").get_text().strip().rsplit(" ", 1)[-1]
