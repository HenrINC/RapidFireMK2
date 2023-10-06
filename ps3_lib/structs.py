import enum
from pathlib import Path


class PS3Path:
    def __init__(self, path: Path | None) -> None:
        if isinstance(path, PS3Path):
            self._path = path._path
        else:
            self._path = Path(path)

    def __str__(self) -> str:
        return str(self._path).replace("\\", "/")

    __repr__ = __str__

    def __truediv__(self, other: str) -> str:
        return PS3Path(self._path / other)
    
    def is_dir(self) -> bool:
        """
        TODO: Find a better way
        """
        return "." not in self.name

    @property
    def parent(self) -> str:
        return PS3Path(self._path.parent)

    @property
    def name(self) -> str:
        return self._path.name

    def resolve(self) -> str:
        return "/"+str(self)

class PS3_INPUT(enum.Enum):
    up = "up"
    down = "down"
    left = "left"
    right = "right"
    cross = "cross"
    circle = "circle"
    square = "square"
    triangle = "triangle"
    r1 = "r1"
    r2 = "r2"
    l1 = "l1"
    l2 = "l2"
    psbtn = "psbtn"
    select = "select"
    start = "start"
    hold = "hold"
    release = "release"
    analogL_up = "analogL_up"
    analogL_down = "analogL_down"
    analogL_left = "analogL_left"
    analogL_right = "analogL_right"
    analogR_up = "analogR_up"
    analogR_down = "analogR_down"
    analogR_left = "analogR_left"
    analogR_right = "analogR_right"
    accept = "accept"
    cancel = "cancel"


class PS3_XMB_COLS(enum.Enum):
    user_login = "user_login"
    user = "user"
    sysconf = "sysconf"
    photo = "photo"
    music = "music"
    video = "video"
    tv = "tv"  # Not working
    game = "game"
    network = "network"
    psn = "psn"
    friend = "friend"


class PS3_LED_COLORS(enum.Enum):
    red = 0
    green = 1
    yellow = 2


class PS3_LED_MODES(enum.Enum):
    off = 0
    on = 1
    blink_fast = 2
    blink_slow = 3
    


class PS3_BUZZER_SOUNDS(enum.Enum):
    simple = 1
    single = 1
    double = 2
    triple = 3
    ## snd_cancel and other does not work and were not implemented


class PS3_XMB_APPS(enum.Enum):
    cannot_support_remoteplay = "cannot_support_remoteplay"
    cddb_dialog = "cddb_dialog"
    DelAfterInstall = "DelAfterInstall"
    edit_wo_titleinput = "edit_wo_titleinput"
    EulaOK = "EulaOK"
    ExecInstallOK = "ExecInstallOK"
    ExecInstallNG = "ExecInstallNG"
    ExecNetCheckOK = "ExecNetCheckOK"
    ExecNetCheckNG = "ExecNetCheckNG"
    NaviCommandCheckGameBootFinish = "NaviCommandCheckGameBootFinish"
    NaviNotAllowed = "NaviNotAllowed"
    OnlineOK = "OnlineOK"
    open_update_confirm_dialog = "open_update_confirm_dialog"
    recover_ok = "recover_ok"
    shopdemo = "shopdemo"
    signup_finish = "signup_finish"
    SignupOK = "SignupOK"
    start_netcheck = "start_netcheck"
    start_netconf = "start_netconf"
    start_store = "start_store"
    start_update = "start_update"
    start_welcome_headline = "start_welcome_headline"
    start_without_worning_guest_signin = "start_without_worning_guest_signin"
    UrlOK = "UrlOK"


class PS3_CFW_INFOS(enum.Enum):
    free_space_hdd0 = "@info"
    free_space_usb000 = "@info1"
    free_space_usb001 = "@info2"
    free_space_usb002 = "@info3"
    free_space_usb003 = "@info4"
    free_space_ntfs0 = "@info5"
    free_memory = "@info6"
    memory_usage = "@info7"
    syscall_status = "@info8"
    temp = "@info9"
    fan_mode = "@info10"
    startup_time = "@info11"
    play_time = "@info12"
    runtime_time = "@info13"
    date_time = "@info14"
    game_id = "@info15"
    process_id = "@info16"
    psid = "@info17"
    idps_lv2 = "@info18"
    idps_eid0 = "@info19"
    firmware_version = "@info20"
    mac_address = "@info21"
    ip_address = "@info22"
    user_home_directory = "@info23"
    webman_mod_version = "@info24"

class PS3_SYSCALL_LEVELS(enum.Enum):
    fully_enabled = 0
    fake_disabled = 3
    fully_disabled = 4