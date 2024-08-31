from typing import Any, Callable, Iterable, Optional, TYPE_CHECKING


from .item_registry import register_xmb_item_type

if TYPE_CHECKING:
    from bs4 import BeautifulSoup
    from .item_factory import XMBMLContext

class ItemMatcher(object):
    @staticmethod
    def not_none(value):
        return value is not None

    @staticmethod
    def build_matcher(
        match: Callable[[str | None], bool] | list | str | None
    ) -> Callable[[str | None], bool]:
        if match is None:
            raise ValueError("None match not overridden by parent matcher")
        if isinstance(match, list):
            return lambda x: x in match
        elif isinstance(match, str):
            if match == "*":
                return lambda x: True
            return lambda x: x == match
        else:
            return match

    def __init__(
        self,
        parent_matcher: Optional["ItemMatcher"] = None, 
        item_name: Callable[[str | None], bool] | list | str | None = None,
        item_class: Callable[[str | None], bool] | list | str | None = None,
        item_key: Callable[[str | None], bool] | list | str | None = None,
        item_src: Callable[[str | None], bool] | list | str | None = None,
    ):
        
        if parent_matcher is None:
            self.name_matcher = self.build_matcher(item_name)
            self.class_matcher = self.build_matcher(item_class)
            self.key_matcher = self.build_matcher(item_key)
            self.src_matcher = self.build_matcher(item_src)
        
        else:
            self.name_matcher = self.build_matcher(item_name or parent_matcher.name_matcher)
            self.class_matcher = self.build_matcher(item_class or parent_matcher.class_matcher)
            self.key_matcher = self.build_matcher(item_key or parent_matcher.key_matcher)
            self.src_matcher = self.build_matcher(item_src or parent_matcher.src_matcher)

    def __call__(self, item_name, item_class, item_key, item_src):
        return (
            self.name_matcher(item_name)
            and self.class_matcher(item_class)
            and self.key_matcher(item_key)
            and self.src_matcher(item_src)
        )


@register_xmb_item_type
class Item(object):
    match = ItemMatcher(
        item_name="Item",
        item_class=ItemMatcher.not_none,
        item_key=ItemMatcher.not_none,
        item_src=lambda x: x is None,
    )

    def __init__(self, class_, key, context: "XMBMLContext") -> None:
        self.class_ = class_
        self.key = key
        self.context: "XMBMLContext" = context

    def post_process(self) -> None:
        pass

    @property
    def name(self) -> str:
        return str(self.key)
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.name}>"

    @classmethod
    @property
    def priority(cls):
        return len(cls.__mro__)

    @classmethod
    def from_soup(cls, soup: "BeautifulSoup", context: "XMBMLContext") -> Iterable["Item"]:
        class_ = soup.attrs.get("class")
        key = soup.attrs.get("key")
        yield cls(class_=class_, key=key, context=context)


@register_xmb_item_type
class Query(Item):
    match = ItemMatcher(
        item_name="Query",
        item_class=ItemMatcher.not_none,
        item_key=ItemMatcher.not_none,
        item_src=ItemMatcher.not_none,
    )

    def __init__(self, class_, key, src, context: "XMBMLContext") -> None:
        super().__init__(class_=class_, key=key, context=context)
        self.src = src

    @classmethod
    def from_soup(cls, soup: "BeautifulSoup", context: "XMBMLContext") -> Iterable[Item]:
        class_ = soup.attrs.get("class")
        key = soup.attrs.get("key")
        src = soup.attrs.get("src")
        yield cls(class_=class_, key=key, src=src, context=context)


@register_xmb_item_type
class DirectReferenceQuery(Query):
    match = ItemMatcher(
        parent_matcher=Query.match,
        item_src=lambda x: isinstance(x, str) and x.startswith("#"),
    )
    
    def post_process(self) -> None:
        sub_view_id = self.context.xmbml_soup.select_one(self.src).attrs["id"]
        self.src = self.context.views[sub_view_id]

@register_xmb_item_type
class UnpackUsersQuery(Query):
    match = ItemMatcher(
        parent_matcher=Query.match,
        item_src="user://localhost/users",
    )

    def __init__(self, class_, key, src, username: str, context: "XMBMLContext") -> None:
        super().__init__(class_=class_, key=key, src=src, context=context)
        self.username = username

    @property
    def name(self) -> str:
        return self.username
    
    @classmethod
    def from_soup(cls, soup: "BeautifulSoup", context: "XMBMLContext") -> Iterable[Item]:
        class_ = soup.attrs.get("class")
        key = soup.attrs.get("key")
        for user in context.ps3.users:
            yield cls(class_=class_, key=key, src=None, context=context, username=user.name)

class ActionItem(Item):
    def __call__(self, *args: Any, **kwds: Any) -> Any:
        raise NotImplementedError(f"ActionItem {self.__class__.__name__} not implemented")

class XXmbActionItem(ActionItem):
    match = ItemMatcher(
        parent_matcher=ActionItem.match,
        item_class=lambda x: isinstance(x, str) and x.startswith("type:x-xmb/"),
    )

@register_xmb_item_type
class PowerOffItem(XXmbActionItem):
    match = ItemMatcher(
        parent_matcher=XXmbActionItem.match,
        item_key="poweroff",
    )

    def __call__(self) -> bool:
        return self.context.ps3.shutdown()
    
    


