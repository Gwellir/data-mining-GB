import re
from urllib.parse import urljoin
from scrapy import Selector
from scrapy.loader import ItemLoader
from itemloaders.processors import TakeFirst, MapCompose, Identity, Join, Compose

from .items import PostInfoItem, TagItem


def get_count(data):
    if data:
        return data[0]['count']
    return None


def get_id(data):
    if data:
        return data[0]['id']
    return None


def get_captions(data):
    if data:
        return [item['node']['text'] for item in data[0]['edges']]
    return None


class PostInfoLoader(ItemLoader):
    default_item_class = PostInfoItem
    default_output_processor = TakeFirst()
    edge_media_to_comment_in = get_count
    edge_liked_by_in = get_count
    edge_media_preview_like_in = get_count
    owner_in = get_id
    edge_media_to_caption_in = get_captions


class TagLoader(ItemLoader):
    default_item_class = TagItem
    default_output_processor = TakeFirst()

