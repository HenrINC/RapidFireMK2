import asyncio

from pathlib import Path
from functools import lru_cache

import aiohttp

from ps3_lib import PS3Path

from .common import PS3AbstractFileTransfer
from .http_server import get_server

class TempRouteContextManager:
    def __init__(self, path, port) -> None:
        self.path = path
        self.port = port
        self.session = aiohttp.ClientSession()

    async def __aenter__(self):
        with open(self.path, "rb") as f:
            url = f"http://127.0.0.1:{self.port}/{hash(self)}"
            async with self.session.put(url = url, data=f.read()) as response:
                response.raise_for_status()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        async with self.session.delete(url = f"http://127.0.0.1:{self.port}/{hash(self)}") as response:
            response.raise_for_status()
        await self.session.close()

    # @lru_cache(maxsize=1)
    def __hash__(self) -> int:
        return abs(int(hash(self.path)))


class PS3HTTPFileTransfer(PS3AbstractFileTransfer):
    def __init__(
        self, ps3_host, ps3_port=80, server_host="0.0.0.0", server_port=9898
    ) -> None:
        super().__init__(ps3_host, ps3_port)
        self.session = None
        self.server = None
        self.server_host = server_host
        self.server_port = server_port

    def temp_route(self, path: Path):
        return TempRouteContextManager(path, self.server_port)

    async def connect(self):
        self.session = aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=5))
        async with self.session.get(
            f"http://{self.ps3_host}:{self.ps3_port}/"
        ) as response:
            response.raise_for_status()
        server = get_server(self.server_port)
        self.server = asyncio.create_task(server.serve())

    async def disconnect(self):
        await self.session.close()
        self.session = None
        self.server.cancel()
        await self.server
        self.server = None

    async def send(self, from_path: Path, to_path: PS3Path):
        if from_path.is_dir():
            await self._send_dir(from_path, to_path)
        else:
            await self._send_file(from_path, to_path)

    async def _send_dir(self, from_path: Path, to_path: PS3Path):
        # assert to_path.is_dir(), f"{to_path} is not a directory"
        await self.mkdir(to_path)
        await asyncio.gather(
            *(self.send(path, to_path / path.name) for path in from_path.iterdir())
        )

    async def _send_file(self, from_path: Path, to_path: PS3Path):
        if to_path.is_dir():
            to_path /= from_path.name

        async with self.temp_route(from_path) as route:
            file_url = (
                f"http://{self.server_host}:{self.server_port}/{hash(route)}"
            )
            print(f"http://{self.ps3_host}:{self.ps3_port}/xmb.ps3/download.ps3?{file_url}")
            await asyncio.sleep(float("inf"))
            async with self.session.get(
                f"http://{self.ps3_host}:{self.ps3_port}/xmb.ps3/download.ps3?to={to_path}&url={file_url}"
            ) as response:
                response.raise_for_status()

    async def get(self, from_path: PS3Path, to_path: Path):
        raise NotImplementedError

    async def get_bytes(self, from_path: PS3Path):
        raise NotImplementedError

    async def delete(self, path: PS3Path):
        raise NotImplementedError

    async def stat(self, path: PS3Path):
        raise NotImplementedError

    async def exists(self, path: PS3Path):
        raise NotImplementedError

    async def mkdir(self, path: PS3Path):
        async with self.session.get(
            f"http://{self.ps3_host}:{self.ps3_port}/mkdir.ps3/{path}"
        ) as response:
            response.raise_for_status()
