#Wrapper around the PFD tool
import asyncio


class PFDTool:
    """
    TIPS: use the pfd_sfo_tools docker image to have an already compiled version of the pfdtool
    """
    def __init__(self, binary_path="pfdtool", working_directory = "./"):
        self.binary_path = binary_path
        self.working_directory = working_directory
    
    async def _run(self, command:str, folder, filename = None, game = None, partial = False):
        cmd = [
            self.binary_path,
            *(["-g", game] if game else []),
            *(["-p"] if partial else []),
            command,
            folder,
            *([filename] if filename else []),
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=self.working_directory
        )

        stdout, stderr = await proc.communicate()
        return stdout.decode(), stderr.decode()

    async def decrypt(self, folder, filename = None, game = None, partial = False):
        return await self._run("-d", folder, filename, game, partial)


    async def update(self, folder, filename = None, game = None, partial = False):
        return await self._run("-u", folder, filename, game, partial)
    
    async def encrypt(self, folder, filename = None, game = None, partial = False):
        return await self._run("-e", folder, filename, game, partial)
