import random
import configparser
from pathlib import Path
from functools import lru_cache

@lru_cache(maxsize=1)
def get_npuserid():
    # Makes easy to use the git-ignored custom_config.ini file if you are a contributor
    try:
        config_path = next(Path().glob("**/custom_config.ini"))
    except StopIteration:
        config_path = next(Path().glob("**/test_config.ini"))

    config = configparser.ConfigParser()
    config.read(config_path)
    return config["USER"]["NPUSERID"]

@lru_cache(maxsize=1)
def get_dummy_npuserid():
    return format(random.getrandbits(64), '016x')