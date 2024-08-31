from pathlib import Path

import aioftp

from ..structs import PS3Path

from .common import PS3AbstractFileTransfer
from .factory import PS3FileTransferFactory

@PS3FileTransferFactory.register("FTP")
class PS3FTPFileTransfer(PS3AbstractFileTransfer):
    def __init__(self, ps3_host, ps3_port = 21, username = None, password = None) -> None:
        super().__init__(ps3_host, ps3_port)
        self.client = None
        self.username = username
        self.password = password
    
    async def connect(self):
        client = aioftp.Client()
        await client.connect(self.ps3_host, self.ps3_port)
        if self.username:
            if self.password:
                await client.login(self.username, self.password)
            else:
                await client.login(self.username)
        else:
            await client.login()
        self.client = client
    
    async def disconnect(self):
        await self.client.quit()
        self.client = None
    
    async def send(self, from_path: Path, to_path: PS3Path, write_into=True):
        assert self.client, "Not connected"
        await self.client.upload(from_path, str(to_path), write_into=write_into)
    
    async def get(self, from_path: PS3Path, to_path: Path, write_into=True):
        assert self.client, "Not connected"
        await self.client.download(str(from_path), to_path, write_into=write_into)
    
    async def get_bytes(self, from_path: PS3Path):
        assert self.client, "Not connected"
        async with self.client.download_stream(str(from_path)) as stream:
            return await stream.read()
    
    async def delete(self, path: PS3Path):
        assert self.client, "Not connected"
        await self.client.remove(str(path))

    async def stat(self, path: PS3Path):
        assert self.client, "Not connected"
        return await self.client.stat(str(path))
    
    async def exists(self, path: PS3Path):
        assert self.client, "Not connected"
        try:
            await self.client.stat(str(path))
            return True
        except aioftp.PathIOError:
            return False
    
    async def mkdir(self, path: PS3Path):
        assert self.client, "Not connected"
        await self.client.make_directory("/"+str(path).strip("/"))
    

