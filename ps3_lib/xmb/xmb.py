from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .category import Category
    from .view import View
    from .item import Item


class XMB(object):
    def __init__(self, categories: list["Category"]) -> None:
        self.categories = categories

    @property
    def dict(self) -> dict[str, "Category"]:
        return {category.name: category for category in self.categories}

    @property
    def list(self) -> list["Category"]:
        return self.categories
    
    def __getitem__(self, index: int) -> "Category":
        return self.categories[index]
    
    