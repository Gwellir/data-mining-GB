# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import os

import pymongo
from datetime import datetime
from scrapy import Request
from scrapy.pipelines.images import ImagesPipeline


class MongoPipeline:
    def __init__(self):
        self.db = pymongo.MongoClient(os.getenv('MONGO_DB_URL'))['insta_parse']

    def process_item(self, item, spider):
        entry = {
            'data': item,
            'date_parse': datetime.now(),
        }
        self.db[item.__class__.__name__].insert_one(entry)
        return item


class InstaImagePipeline(ImagesPipeline):
    def get_media_requests(self, item, info):
        # for img_url in item.get('display_url', []):
        img_url = item.get('display_url', None)
        if img_url:
            yield Request(img_url)

    def item_completed(self, results, item, info):
        if results:
            item['local_image'] = results[0][1]
        return item
