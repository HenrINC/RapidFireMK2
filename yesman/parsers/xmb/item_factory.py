from typing import Iterable, Union, Optional, Any, TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, SkipValidation
from bs4 import BeautifulSoup

from .item_registry import xmb_item_types

from .xmb import XMB
from .category import Category
from .view import View
from .item import Item

if TYPE_CHECKING:
    from ..structs import PS3Path
    from ..ps3 import PS3


class XMBMLContext(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    ps3: "PS3" if TYPE_CHECKING else Any
    xmbml_soup: BeautifulSoup | None = None
    xmbml_version: str | None = None
    unprocessed_items: list[Item] = []
    views: dict[str, View] = {}


class XMBFactory(object):
    def __init__(self, ps3: "PS3"):
        self.ps3 = ps3

    def build_context(self) -> XMBMLContext:
        return XMBMLContext(ps3=self.ps3)

    def build_xmb(self, categories: dict[str, bytes]) -> XMB:
        context = self.build_context()
        categories = [
            self.build_category(category, name=name, context=context)
            for name, category in categories.items()
        ]
        return XMB(categories=categories)

    def build_category(
        self,
        xmbml_data: Union[str, bytes, BeautifulSoup, "PS3Path"],
        context: XMBMLContext,
        name: Optional[str] = None,
    ) -> "Category":
        if isinstance(xmbml_data, bytes):
            xmbml_data = xmbml_data.decode("utf-8")
        if isinstance(xmbml_data, str):
            return self._build_category_from_soup(
                BeautifulSoup(xmbml_data, "xml"), name=name, context=context
            )

    def _build_category_from_soup(
        self, xmbml_soup: BeautifulSoup, context: XMBMLContext, name: str | None = None
    ):
        context.xmbml_soup = xmbml_soup
        xmbml_version = xmbml_soup.find("XMBML").attrs["version"]
        views = [
            self._build_view_from_soup(view_soup, context=context)
            for view_soup in xmbml_soup.find_all("View")
        ]
        category = Category(xmbml_version=xmbml_version, views=views, name=name)
        for item in context.unprocessed_items:
            item.post_process()
        return category

    def _build_view_from_soup(
        self, view_soup: BeautifulSoup, context: XMBMLContext
    ) -> "View":
        view_id = view_soup.attrs["id"]
        items = sum(
            [
                list(self._build_item_from_soup(item_soup, context=context))
                for item_soup in view_soup.select("Items>*")
            ],
            start=[],
        )
        context.unprocessed_items.extend(items)
        view = View(view_id=view_id, items=items)
        context.views[view_id] = view
        return view

    def _build_item_from_soup(
        self, item_soup: BeautifulSoup, context: XMBMLContext
    ) -> Iterable["Item"]:
        item_name = item_soup.name
        item_class = item_soup.attrs.get("class")
        item_key = item_soup.attrs.get("key")
        item_src = item_soup.attrs.get("src")
        yield from self._match_item(
            item_name, item_class, item_key, item_src
        ).from_soup(item_soup, context=context)

    def _match_item(self, item_name, item_class, item_key, item_src) -> type["Item"]:
        matches = [
            item_type
            for item_type in xmb_item_types
            if item_type.match(
                item_name=item_name,
                item_class=item_class,
                item_key=item_key,
                item_src=item_src,
            )
        ]
        if not matches:
            raise ValueError(
                f"Unknown item type: {item_name} {item_class} {item_key} {item_src}"
            )

        matches.sort(key=lambda x: x.priority, reverse=True)

        if matches[0].priority == matches[1].priority:
            ambiguous_matches = [
                match.__class__.__name__
                for match in matches
                if match.priority == matches[0].priority
            ]
            raise ValueError(
                f"Ambiguous item type: {ambiguous_matches} for {item_name} {item_class} {item_key} {item_src}"
            )

        return matches[0]
