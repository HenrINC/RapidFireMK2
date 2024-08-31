from .common import PS3AbstractFileTransfer


class PS3FileTransferFactory:
    registered_types: dict[str : type[PS3AbstractFileTransfer]] = {}

    @classmethod
    def register(cls, name: str):
        def decorator(ps3_file_transfer_class: type[PS3AbstractFileTransfer]):
            cls.registered_types[name] = ps3_file_transfer_class
            return ps3_file_transfer_class

        return decorator

    @classmethod
    def create(self, name: str, *args, **kwargs) -> PS3AbstractFileTransfer:
        if name not in self.registered_types:
            raise ValueError(
                f"Unknown type: {name}, valid types are: {set.__str__(self.registered_types.keys())}"
            )
        cls = self.registered_types[name]
        return cls(*args, **kwargs)
