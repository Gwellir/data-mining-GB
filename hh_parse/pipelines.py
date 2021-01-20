# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import os

import pymongo
from itemadapter import ItemAdapter


class MongoPipeline:
    def __init__(self):
        self.db = pymongo.MongoClient(os.getenv('MONGO_DB_URL'))['hh_parse']

    def process_item(self, item, spider):
        if not self.db[item.__class__.__name__].find_one({'url': item['url']}):
            self.db[item.__class__.__name__].insert_one(item)
        return item
