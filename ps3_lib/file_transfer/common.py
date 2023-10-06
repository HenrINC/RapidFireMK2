from pathlib import Path
from abc import abstractmethod, ABC

from ps3_lib import PS3Path

class PS3AbstractFileTransfer(ABC):
    def __init__(self, ps3_host, ps3_port) -> None:
        self.ps3_host = ps3_host
        self.ps3_port = ps3_port
    
    @abstractmethod
    async def connect(self):
        pass

    @abstractmethod
    async def disconnect(self):
        pass

    @abstractmethod
    async def send(self, from_path: Path, to_path: PS3Path):
        pass

    @abstractmethod
    async def get(self, from_path: PS3Path, to_path: Path):
        pass

    @abstractmethod
    async def get_bytes(self, from_path: PS3Path):
        pass

    @abstractmethod
    async def delete(self, path: PS3Path):
        pass

    @abstractmethod
    async def stat(self, path: PS3Path):
        pass

    @abstractmethod
    async def exists(self, path: PS3Path):
        pass

    @abstractmethod
    async def mkdir(self, path: PS3Path):
        pass
        