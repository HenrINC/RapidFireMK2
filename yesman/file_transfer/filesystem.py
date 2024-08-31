import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory

import aiofiles

from ..structs import PS3Path

from .common import PS3AbstractFileTransfer
from .factory import PS3FileTransferFactory


@PS3FileTransferFactory.register("FileSystem")
class PS3FileSystemFileTransfer(PS3AbstractFileTransfer):
    def __init__(self, ps3_host, ps3_port=21, username=None, password=None) -> None:
        super().__init__(ps3_host, ps3_port)
        self.username = username
        self.password = password
        self.temporary_directory = TemporaryDirectory()
        self.mount_point = Path(self.temporary_directory.name)

    async def connect(self):
        cmd = [
            "mount",
            "-t",
            "ftpfs",
            "-o",
            f"host={self.ps3_host},port={self.ps3_port},"
            + ("user={self.username}," if self.username else "")
            + ("pass={self.password}" if self.password else ""),
            str(self.mount_point),
        ]
        proc = await asyncio.create_subprocess_exec(*cmd)
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(f"Failed to mount PS3: {stderr}")

    async def disconnect(self):
        cmd = ["umount", str(self.mount_point)]
        proc = await asyncio.create_subprocess_exec(*cmd)
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(f"Failed to unmount PS3: {stderr}")
        self.temporary_directory.cleanup()

    async def send(self, from_path: Path, to_path: PS3Path, write_into=True):
        assert self.mount_point, "Not connected"
        dest_path = self.mount_point / to_path

        if from_path.is_dir():
            await aiofiles.os.mkdir(dest_path, exist_ok=True)
            async for item in aiofiles.os.scandir(from_path):
                await self.send(
                    from_path / item.name, to_path / item.name, write_into=write_into
                )
        else:
            async with (
                aiofiles.open(from_path, mode="rb") as src_file,
                aiofiles.open(dest_path, mode="wb") as dest_file,
            ):
                while True:
                    chunk = await src_file.read(4096)
                    if not chunk:
                        break
                    await dest_file.write(chunk)

    async def get(self, from_path: PS3Path, to_path: Path, write_into=True):
        assert self.mount_point, "Not connected"
        src_path = self.mount_point / from_path
        async with (
            aiofiles.open(src_path, mode="rb") as src_file,
            aiofiles.open(to_path, mode="wb") as dest_file,
        ):
            while True:
                chunk = await src_file.read(4096)
                if not chunk:
                    break
                await dest_file.write(chunk)

    async def get_bytes(self, from_path: PS3Path):
        assert self.mount_point, "Not connected"
        src_path = self.mount_point / from_path
        async with aiofiles.open(src_path, mode="rb") as src_file:
            return await src_file.read()

    async def delete(self, path: PS3Path):
        assert self.mount_point, "Not connected"
        target_path = self.mount_point / path
        await aiofiles.os.remove(target_path)

    async def stat(self, path: PS3Path):
        assert self.mount_point, "Not connected"
        target_path = self.mount_point / path
        return await aiofiles.os.stat(target_path)

    async def exists(self, path: PS3Path):
        assert self.mount_point, "Not connected"
        target_path = self.mount_point / path
        try:
            await aiofiles.os.stat(target_path)
            return True
        except FileNotFoundError:
            return False

    async def mkdir(self, path: PS3Path):
        assert self.mount_point, "Not connected"
        target_path = self.mount_point / path
        await aiofiles.os.mkdir(target_path)
