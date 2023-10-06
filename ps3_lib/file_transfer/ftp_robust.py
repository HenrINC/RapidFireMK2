from pathlib import Path

import asyncio

import ftputil

from concurrent.futures import ThreadPoolExecutor

from ps3_lib import PS3Path

from .common import PS3AbstractFileTransfer

def reconnect_on_error(func):
    async def wrapper(self, *args, **kwargs):
        try:
            return await func(self, *args, **kwargs)
        except (ftputil.error.FTPOSError, asyncio.TimeoutError) as e:
            try:
                await self.disconnect()
            finally:
                await self.connect()
            return await func(self, *args, **kwargs)
    return wrapper

def reconnect_on_timeout(timeout=10):
    def decorator(func):
        async def wrapper(self, *args, **kwargs):
            try:
                return await asyncio.wait_for(func(self, *args, **kwargs), timeout=timeout)
            except asyncio.TimeoutError as e:
                try:
                    await self.disconnect()
                finally:
                    await self.connect()
                return await asyncio.wait_for(func(self, *args, **kwargs), timeout=timeout)
        return wrapper
    return decorator

class PS3RobustFTPFileTransfer(PS3AbstractFileTransfer):    
    def __init__(self, ps3_host, ps3_port=21, username=None, password=None):
        super().__init__(ps3_host, ps3_port)
        self.host = None
        self.username = username or "anonymous"
        self.password = password or ""

    async def connect(self):
        self.host = ftputil.FTPHost(self.ps3_host, self.username, self.password)

    async def disconnect(self):
        if self.host:
            self.host.close()
            self.host = None

    @reconnect_on_error
    async def send(self, from_path: Path, to_path: PS3Path):
        assert self.host, "Not connected"
        if from_path.is_dir():
            await self.send_dir(from_path, to_path)
        else:
            await self.send_file(from_path, to_path)
    
    @reconnect_on_error
    async def send_dir(self, from_path: Path, to_path: PS3Path):
        assert self.host, "Not connected"
        await self.mkdir(to_path)
        for from_item in from_path.iterdir():
            await self.send(from_item, to_path / from_item.name)
    
    @reconnect_on_error
    @reconnect_on_timeout(timeout=10)
    async def send_file(self, from_path: Path, to_path: PS3Path):
        assert self.host, "Not connected"
        if to_path.is_dir():
            to_path /= from_path.name
        self.host.upload(str(from_path), to_path.resolve())        

    @reconnect_on_error
    @reconnect_on_timeout(timeout=10)
    async def get(self, from_path: PS3Path, to_path: Path):
        assert self.host, "Not connected"
        self.host.download(str(from_path), to_path.resolve())

    @reconnect_on_error
    @reconnect_on_timeout(timeout=10)
    async def delete(self, path: PS3Path):
        assert self.host, "Not connected"
        self.host.remove(path.resolve())

    @reconnect_on_error
    @reconnect_on_timeout(timeout=10)
    async def stat(self, path: PS3Path):
        assert self.host, "Not connected"
        return self.host.stat(path.resolve())

    @reconnect_on_error
    @reconnect_on_timeout(timeout=10)
    async def exists(self, path: PS3Path):
        assert self.host, "Not connected"
        return self.host.path.exists(path.resolve())

    @reconnect_on_error
    @reconnect_on_timeout(timeout=10)
    async def mkdir(self, path: PS3Path):
        assert self.host, "Not connected"
        if not await self.exists(path):
            self.host.mkdir(path.resolve())

    @reconnect_on_error
    @reconnect_on_timeout(timeout=10)
    async def get_bytes(self, path: PS3Path):
        assert self.host, "Not connected"
        return self.host.download_as_bytes(path.resolve())