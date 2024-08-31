import io
from pathlib import Path
from typing import Iterable

from pydantic import BaseModel, ConfigDict

SFO_MAGIC = 0x46535000
SFO_VERSION = 0x0101  # Version 1.1

SFO_ACCOUNT_ID_SIZE = 16
SFO_PSID_SIZE = 16


class SFOHeader(BaseModel):
    magic: int
    version: int
    key_table_offset: int
    data_table_offset: int
    num_entries: int

    @classmethod
    def from_bytes(cls, data: bytes) -> "SFOHeader":
        magic, version, key_table_offset, data_table_offset, num_entries = cls._unpack(
            data
        )
        return cls(
            magic=magic,
            version=version,
            key_table_offset=key_table_offset,
            data_table_offset=data_table_offset,
            num_entries=num_entries,
        )

    @staticmethod
    def _unpack(data: bytes) -> tuple[int, int, int, int, int]:
        # Unpack the bytes according to the SFO header structure
        return (
            int.from_bytes(data[0:4], "little"),
            int.from_bytes(data[4:6], "little"),
            int.from_bytes(data[8:12], "little"),
            int.from_bytes(data[12:16], "little"),
            int.from_bytes(data[16:20], "little"),
        )

    def __bytes__(self) -> bytes:
        return (
            self.magic.to_bytes(4, "little")
            + self.version.to_bytes(4, "little")
            + self.key_table_offset.to_bytes(4, "little")
            + self.data_table_offset.to_bytes(4, "little")
            + self.num_entries.to_bytes(4, "little")
        )


class SFOIndexTableEntry:
    def __init__(
        self,
        key_offset: int,
        param_format: int,
        param_length: int,
        param_max_length: int,
        data_offset: int,
    ):
        self.key_offset = key_offset
        self.param_format = param_format
        self.param_length = param_length
        self.param_max_length = param_max_length
        self.data_offset = data_offset

    @classmethod
    def from_bytes(cls, data: bytes) -> "SFOIndexTableEntry":
        (
            key_offset,
            param_format,
            param_length,
            param_max_length,
            data_offset,
        ) = cls._unpack(data)
        return cls(
            key_offset, param_format, param_length, param_max_length, data_offset
        )

    @staticmethod
    def _unpack(data: bytes) -> tuple[int, int, int, int, int]:
        # Unpack the bytes according to the SFO index table entry structure
        return (
            int.from_bytes(data[0:2], "little"),  # key_offset
            int.from_bytes(data[2:4], "little"),  # param_format
            int.from_bytes(data[4:8], "little"),  # param_length
            int.from_bytes(data[8:12], "little"),  # param_max_length
            int.from_bytes(data[12:16], "little"),  # data_offset
        )

    def __bytes__(self) -> bytes:
        return (
            self.key_offset.to_bytes(2, "little")
            + self.param_format.to_bytes(2, "little")
            + self.param_length.to_bytes(4, "little")
            + self.param_max_length.to_bytes(4, "little")
            + self.data_offset.to_bytes(4, "little")
        )


class SFOIndexTable(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    entries: list[SFOIndexTableEntry]

    def __iter__(self):
        return iter(self.entries)

    def __len__(self):
        return len(self.entries)

    def __bytes__(self) -> bytes:
        return b"".join(bytes(entry) for entry in self.entries)

    def __getitem__(self, index: int) -> SFOIndexTableEntry:
        return self.entries[index]


class SFOEntry(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    key: str
    value: bytes
    format: int = None
    length: int = None
    max_length: int = None
    actual_length: int = None
    related_index_table_entry: SFOIndexTableEntry = None

    def __repr__(self) -> str:
        return f"<SFOParam: {self.key}={self.value}>"

    def __iter__(self) -> Iterable:
        return iter((self.key, self.value))


class SFO:
    def __init__(
        self, header: SFOHeader, index_table: SFOIndexTable, params: list[SFOEntry]
    ) -> None:
        self.header = header
        self.index_table = index_table
        self.params = params

    @classmethod
    def read(cls, value) -> "SFO":
        if isinstance(value, bytes):
            return cls.from_bytes(value)
        elif isinstance(value, Path) or isinstance(value, str):
            return cls.from_file(value)
        elif isinstance(value, io.BytesIO):
            return cls.from_buffer(value)
        else:
            raise TypeError(f"Invalid type: {type(value)}")

    @classmethod
    def from_bytes(cls, data: bytes) -> "SFO":
        return cls.from_buffer(io.BytesIO(data))

    @classmethod
    def from_file(cls, file: Path | str) -> "SFO":
        with open(file, "rb") as f:
            return cls.from_buffer(f)

    from_path = from_file

    @classmethod
    def from_buffer(cls, buffer: io.BytesIO) -> "SFO":
        header = SFOHeader.from_bytes(buffer.read(20))
        index_table = SFOIndexTable(
            entries=[
                SFOIndexTableEntry.from_bytes(buffer.read(16))
                for _ in range(header.num_entries)
            ]
        )
        content_offset = 20 + 16 * header.num_entries
        key_offset = header.key_table_offset - content_offset
        value_offset = header.data_table_offset - content_offset
        content = buffer.read()
        params = []
        for entry in index_table:
            key_start = entry.key_offset + key_offset
            key_end = content.find(b"\x00", key_start)
            key = content[key_start:key_end].decode("utf-8")
            value_start = entry.data_offset + value_offset
            value_end = value_start + entry.param_length
            value = content[value_start:value_end]
            params.append(
                SFOEntry(
                    key=key,
                    value=value,
                    format=entry.param_format,
                    length=entry.param_length,
                    max_length=entry.param_max_length,
                    actual_length=len(value),
                    related_index_table_entry=entry,
                )
            )
        return cls(header, index_table, params)

    def __repr__(self) -> str:
        return f"<SFO V{hex(self.header.version)}: {self.params}>"

    @property
    def keys(self) -> list[str]:
        return [param.key for param in self.params]

    def __contains__(self, key: str) -> bool:
        return key in self.keys

    def __getitem__(self, key: str) -> SFOEntry:
        for param in self.params:
            if param.key == key:
                return param
        raise KeyError(f"{key} not found in SFO")

    def __setitem__(self, key: str, value: bytes) -> None:
        if key in self:
            self._update_item(self[key], value)
        else:
            self._add_item(key, value)

    def _update_item(self, item: SFOEntry, value: bytes) -> None:
        value_length = len(value)
        index_table_entry = item.related_index_table_entry
        assert (
            value_length <= index_table_entry.param_max_length
        ), f"Value length ({value_length}) is greater than the maximum length ({index_table_entry.param_max_length})"
        item.value = value
        item.actual_length = value_length
        item.length = value_length
        index_table_entry.param_length = value_length

    def _add_item(self, key: str, value: bytes, format: int) -> None:
        raise NotImplementedError

    def __bytes__(self) -> bytes:
        header_bytes = bytes(self.header)
        index_table_bytes = b"".join(bytes(entry) for entry in self.index_table.entries)
        content_offset = 20 + 16 * self.header.num_entries
        key_offset = self.header.key_table_offset - content_offset
        value_offset = self.header.data_table_offset - content_offset
        assert content_offset == len(header_bytes) + len(index_table_bytes)
        last_index_table_entry = max(
            self.index_table.entries, key=lambda entry: entry.data_offset
        )
        content_size = (
            value_offset
            + last_index_table_entry.data_offset
            + last_index_table_entry.param_max_length
        )
        content = bytearray(b"\x00" * content_size)
        for param in self.params:
            key_start = param.related_index_table_entry.key_offset + key_offset
            content[key_start : key_start + len(param.key)] = param.key.encode("utf-8")
            value_start = param.related_index_table_entry.data_offset + value_offset
            content[value_start : value_start + param.actual_length] = param.value
        return header_bytes + index_table_bytes + bytes(content)

    def to_dict(self) -> dict:
        return {
            "header": {
                "magic": self.header.magic,
                "version": self.header.version,
                "key_table_offset": self.header.key_table_offset,
                "data_table_offset": self.header.data_table_offset,
                "num_entries": self.header.num_entries
            },
            "index_table": [
                {
                    "key_offset": entry.key_offset,
                    "param_format": entry.param_format,
                    "param_length": entry.param_length,
                    "param_max_length": entry.param_max_length,
                    "data_offset": entry.data_offset
                } for entry in self.index_table.entries
            ],
            "params": [
                {
                    "key": param.key,
                    "value": param.value.decode('utf-8', errors='ignore') if isinstance(param.value, bytes) else param.value,
                    "format": param.format,
                    "length": param.length,
                    "max_length": param.max_length,
                    "actual_length": param.actual_length
                } for param in self.params
            ]
        }

    def write_to_buffer(self, buffer: io.BytesIO) -> None:
        buffer.write(bytes(self))

    def write_to_file(self, file: Path | str) -> None:
        with open(file, "wb") as f:
            self.write_to_buffer(f)

    def to_buffer(self, buffer: io.BytesIO = io.BytesIO()) -> io.BytesIO:
        self.write_to_buffer(buffer)
        return buffer

    to_file = write_to_file

    def wite(self, value: Path | str | io.BytesIO) -> None:
        if isinstance(value, Path) or isinstance(value, str):
            self.write_to_file(value)
        elif isinstance(value, io.BytesIO):
            self.write_to_buffer(value)
        else:
            raise TypeError(f"Invalid type: {type(value)}")

    def update(
        self, other: "SFO", subset: list[str] | None = None, add_new=False
    ) -> None:
        subset = subset or other.keys
        for key in subset:
            if key in self or add_new:
                self[key] = other[key].value


if __name__ == "__main__":
    template = SFO.from_file("./tropdata/TEMPLATE.SFO")
    template_account_id_key = "ACCOUNT_ID" if "ACCOUNT_ID" in template else "ACCOUNTID"
    param = SFO.from_file("./tropdata/PARAM.SFO")
    param_account_id_key = "ACCOUNT_ID" if "ACCOUNT_ID" in param else "ACCOUNTID"
    param[param_account_id_key] = template[template_account_id_key].value
    bytes(param)
    print(param)
