from typing import Iterable, TYPE_CHECKING

if TYPE_CHECKING:
    from .view import View

class Category():
    def __init__(self, xmbml_version: str, views: list["View"], name: str | None = None):
        self.xmbml_version = xmbml_version
        self.views = views
        self.name = name

    @property
    def dict(self):
        return {view.view_id: view for view in self.views}

    @property
    def list(self):
        return self.views
    
    @property
    def view(self):
        return self.dict["root"]
    
    def __getitem__(self, index: int) -> "View":
        return self.views[index]
    
    def __iter__(self) -> Iterable["View"]:
        return iter(self.views)
    
    def __len__(self) -> int:
        return len(self.views)
    
    def __repr__(self) -> str:
        return f"<Category {self.views}>"