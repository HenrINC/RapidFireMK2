#Wrapper around the SFO patcher
import asyncio


class SFOPatcher:
    def __init__(self, binary_path="sfopatcher"):
        self.binary_path = binary_path

    async def build(self, input_file, tpl_file, output_file, copy_title=False, copy_detail=False):
        command = [self.binary_path, "build", input_file, tpl_file, output_file]
        if copy_title:
            command.append("--copy-title")
        if copy_detail:
            command.append("--copy-detail")

        proc = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await proc.communicate()
        return stdout.decode(), stderr.decode()
