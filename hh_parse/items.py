# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class VacancyItem(scrapy.Item):
    _id = scrapy.Field()
    title = scrapy.Field()
    url = scrapy.Field()
    salary = scrapy.Field()
    desc = scrapy.Field()
    tag_list = scrapy.Field()
    employer_url = scrapy.Field()


class EmployerItem(scrapy.Item):
    _id = scrapy.Field()
    name = scrapy.Field()
    site_id = scrapy.Field()
    url = scrapy.Field()
    site = scrapy.Field()
    areas = scrapy.Field()
    desc = scrapy.Field()
