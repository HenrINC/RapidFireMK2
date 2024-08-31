from .import commands

def __getitem__(syscall_id):
    return Syscall[syscall_id]

class Syscall:
    syscalls = {}
    def __init__(self, syscall_id, args, return_type = None):
        self.syscall_id = syscall_id
        self.args = args
        self.return_type = return_type
        found_optional = False
        for arg in self.args:
            if arg.optional:
                found_optional = True
            elif found_optional:
                raise ValueError("Cannot have required arguments after optional arguments")
    
    def __repr__(self):
        return f"<Syscall {self.syscall_id} Args: {self.args}>"
    
    def validate(self, *args):
        required_args = [arg for arg in self.args if not arg.optional]
        if not len(required_args) > len(args) > len(self.args):
            raise TypeError(f"Invalid number of arguments, expected between {len(required_args)} and {len(self.args)} got {len(args)}")
        for arg, value in zip(self.args, args):
            if not (isinstance(value, arg.type) if arg.allow_subtypes else type(value) == arg.type):
                raise TypeError(f"Invalid type for argument {arg.name}, expected {arg.type} got {type(value)}")
            if not len(value) == arg.size:
                raise ValueError(f"Invalid size for argument {arg.name}, expected {arg.size} got {len(value)}")

    def invoke(self, ps3_url, *args):
        self.validate(*args)
        commands.syscall(ps3_url, self.syscall_id, *args)

    __run__ = invoke
    
    @classmethod
    def __getitem__(cls, syscall_id):
        return cls.syscalls[syscall_id]

class SyscallArg:
    def __init__(self, name, type, size, optional=False, allow_subtypes=True):
        self.name = name
        self.type = type
        self.size = size
        self.optional = optional
        self.allow_subtypes = allow_subtypes

    def __repr__(self):
        return f"<Arg {self.name}: {self.type}{'(and subtypes)' if self.allow_subtypes else ''} of size {self.size} {'(optional)' if self.optional else ''}>"
    
sys_process_getpid = Syscall(
    syscall_id=1,
    args=[],
    return_type=int,
)

sys_process_exit = Syscall(
    syscall_id=3,
    args=[
        SyscallArg(name="process_id", type=int, size=4),
    ],
    return_type=None,
)

sys_dbg_get_console_type = Syscall(
    syscall_id=985,
    args=[],
    return_type=int,
)