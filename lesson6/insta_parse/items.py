# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class TagItem(scrapy.Item):
    _id = scrapy.Field()
    updated = scrapy.Field()
    id = scrapy.Field()
    name = scrapy.Field()
    profile_pic_url = scrapy.Field()


class PostInfoItem(scrapy.Item):
    _id = scrapy.Field()
    updated = scrapy.Field()
    local_image = scrapy.Field()
    id = scrapy.Field()
    edge_media_to_caption = scrapy.Field()
    shortcode = scrapy.Field()
    edge_media_to_comment = scrapy.Field()
    taken_at_timestamp = scrapy.Field()
    dimensions = scrapy.Field()
    display_url = scrapy.Field()
    edge_liked_by = scrapy.Field()
    edge_media_preview_like = scrapy.Field()
    owner = scrapy.Field()
    is_video = scrapy.Field()
    accessibility_caption = scrapy.Field()
