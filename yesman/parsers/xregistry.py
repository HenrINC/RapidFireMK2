import io
from pathlib import Path
from typing import Iterable, Optional

from pydantic import BaseModel, ConfigDict, validator


class XRegHeader(BaseModel):
    header_start_mark: bytes
    unknown1: bytes
    unknown2: bytes
    header_end_mark: bytes

    @validator("header_start_mark", "header_end_mark")
    def check_header_mark(cls, v):
        assert v == b"\xbc\xad\xad\xbc", "Invalid header start or end mark"
        return v

    @classmethod
    def from_bytes(cls, data: bytes) -> "XRegHeader":
        (
            header_start_mark,
            unknown1,
            unknown2,
            header_end_mark,
        ) = cls._unpack(data)
        return cls(
            header_start_mark=header_start_mark,
            unknown1=unknown1,
            unknown2=unknown2,
            header_end_mark=header_end_mark,
        )

    @staticmethod
    def _unpack(data: bytes) -> tuple[bytes, int, int, bytes]:
        return (
            data[0:4],  # header_start_mark
            data[4:8],  # unknown1
            data[8:12],  # unknown2
            data[12:16],  # header_end_mark
        )


class XRegKey(BaseModel):
    unknown1: bytes
    key_length: int
    key_type: int
    key: str
    terminator: bytes

    @classmethod
    def from_bytes(cls, data: bytes) -> "XRegKey":
        unknown1, key_length, key_type, key, terminator = cls._unpack(data)
        return cls(
            unknown1=unknown1,
            key_length=key_length,
            key_type=key_type,
            key=key,
            terminator=terminator,
        )

    @staticmethod
    def _unpack(data: bytes) -> tuple[int, int, int, str, bytes]:
        unknown1 = data[0:2]
        key_length = int.from_bytes(data[2:4], "big")
        key_type = int.from_bytes(data[4:5], "big")
        key = data[5 : 5 + key_length].decode(encoding="utf-8")
        terminator = data[5 + key_length : 6 + key_length]
        return (unknown1, key_length, key_type, key, terminator)

    def __len__(self) -> int:
        return self.key_length + 6


class XRegValue(BaseModel):
    unknown1: bytes
    key_offset: int
    unknown2: bytes
    value_length: int
    value_type: int
    value: bytes
    terminator: bytes
    offset: Optional[int] = None

    @classmethod
    def from_bytes(cls, data: bytes) -> "XRegValue":
        (
            unknown1,
            key_offset,
            unknown2,
            value_length,
            value_type,
            value,
            terminator,
        ) = cls._unpack(data)
        return cls(
            unknown1=unknown1,
            key_offset=key_offset,
            unknown2=unknown2,
            value_length=value_length,
            value_type=value_type,
            value=value,
            terminator=terminator,
        )

    @staticmethod
    def _unpack(data: bytes) -> tuple[bytes, int, int, int, int, bytes, bytes]:
        unknown1 = data[0:2]
        key_offset = int.from_bytes(data[2:4], "big")
        unknown2 = data[4:6]
        value_length = int.from_bytes(data[6:8], "big")
        value_type = int.from_bytes(data[8:9], "big")
        value = data[9 : 9 + value_length]
        terminator = data[9 + value_length : 10 + value_length]
        return (
            unknown1,
            key_offset,
            unknown2,
            value_length,
            value_type,
            value,
            terminator,
        )

    def __len__(self) -> int:
        return self.value_length + 10

    @property
    def processed_value(self) -> bool | int | str | bytes:
        if self.value_type == 0:
            return bool(self.value)
        elif self.value_type == 1:
            return int.from_bytes(self.value, "big")
        elif self.value_type == 2:
            return self.value.strip(b"\x00")
        else:
            raise ValueError(f"Unknown value type {self.value_type}")


class XRegEntry(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    key: XRegKey
    value: XRegValue


class XRegistry:
    def __init__(self, header: XRegHeader, entries: Iterable[XRegEntry]) -> None:
        self.header = header
        self.entries = entries

    @classmethod
    def from_buffer(cls, buffer: io.BytesIO) -> None:
        header = XRegHeader.from_bytes(buffer.read(0x10))
        key_part = buffer.read(0xFFF0)
        value_part = buffer.read(0x10000)
        entries = []
        value_offset = 0
        while True:
            value = XRegValue.from_bytes(value_part)
            value.offset = value_offset
            value_offset += len(value)
            value_part = value_part[len(value) :]
            key = XRegKey.from_bytes(key_part[value.key_offset :])
            if key.key == "":
                break
            entry = XRegEntry(key=key, value=value)
            entries.append(entry)
        return cls(header=header, entries=entries)

    @classmethod
    def from_file(cls, file: Path) -> "XRegistry":
        with file.open("rb") as f:
            return cls.from_buffer(f)

    @classmethod
    def from_bytes(cls, data: bytes) -> "XRegistry":
        with io.BytesIO(data) as f:
            return cls.from_buffer(f)

    def __getitem__(self, key: str | XRegKey) -> XRegValue:
        if isinstance(key, str):
            return self.get_entry(key).value
        elif isinstance(key, XRegKey):
            return self.get_entry(key.key).value
        else:
            raise TypeError("Key must be str or XRegKey")

    def get_entry(self, key: str) -> XRegEntry:
        for entry in self.entries:
            if entry.key.key == key:
                return entry
        raise KeyError(f"Key {key} not found")

    @property
    def hierarchy(self):
        def add_to_hierarchy(hierarchy, key_path, value):
            parts = key_path.strip("/").split("/")
            current_dict = hierarchy

            for part in parts[:-1]:
                current_dict = current_dict.setdefault(part, {})

            current_dict[parts[-1]] = value

        hierarchy_dict = {}
        for entry in self.entries:
            add_to_hierarchy(hierarchy_dict, entry.key.key, entry.value.processed_value)

        return hierarchy_dict


if __name__ == "__main__":
    import pprint

    registry = XRegistry.from_file(Path("./tropdata/xRegistry.sys"))
    pprint.pprint(registry.hierarchy)
