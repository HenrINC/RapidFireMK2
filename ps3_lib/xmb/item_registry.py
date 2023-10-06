from typing import TYPE_CHECKING, Iterable

if TYPE_CHECKING:
    from .item import Item

xmb_item_types = []


def register_xmb_item_type(cls):
    xmb_item_types.append(cls)
    return cls


def __getitem__(index: int) -> "Item":
    return xmb_item_types[index]


def __iter__() -> Iterable["Item"]:
    return iter(xmb_item_types)


def __len__() -> int:
    return len(xmb_item_types)
