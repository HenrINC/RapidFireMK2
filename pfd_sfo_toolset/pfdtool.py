#Wrapper around the PFD tool
import asyncio


class PFDTool:
    """
    TIPS: use the pfd_sfo_tools docker image to have an already compiled version of the pfdtool
    """
    def __init__(self, binary_path="pfdtool", working_directory = "./"):
        self.binary_path = binary_path
        self.working_directory = working_directory
    
    async def _run(self, command:str, pfd_folder, pfd_filename, game = None, partial = False):
        cmd = [
            self.binary_path,
            *(["-g", game] if game else []),
            *(["-p"] if partial else []),
            command,
            pfd_folder,
            pfd_filename,
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=self.working_directory
        )

        stdout, stderr = await proc.communicate()
        return stdout.decode(), stderr.decode()

    async def decrypt(self, pfd_folder, pfd_filename, game = None, partial = False):
        return await self._run("-d", pfd_folder, pfd_filename, game, partial)


    async def update(self, pfd_folder, pfd_filename, game = None, partial = False):
        return await self._run("-u", pfd_folder, pfd_filename, game, partial)
    
    async def encrypt(self, pfd_folder, pfd_filename, game = None, partial = False):
        return await self._run("-e", pfd_folder, pfd_filename, game, partial)
