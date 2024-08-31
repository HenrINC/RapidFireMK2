from typing import TYPE_CHECKING, Iterable

if TYPE_CHECKING:
    from .item import Item


class View():
    def __init__(self, view_id: str, items: list["Item"]):
        self.view_id = view_id
        self.items = items
    
    def __getitem__(self, index: int) -> "Item":
        return self.items[index]
    
    def __iter__(self) -> Iterable["Item"]:
        return iter(self.items)
    
    def __len__(self) -> int:
        return len(self.items)
    
    def __repr__(self) -> str:
        return f"<View id={self.view_id} {self.items}>"