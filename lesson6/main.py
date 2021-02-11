from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings
from insta_parse.spiders.instagram import InstagramSpider

import os
import dotenv
dotenv.load_dotenv('.env')

if __name__ == '__main__':

    crawler_settings = Settings()
    crawler_settings.setmodule('insta_parse.settings')
    crawler_process = CrawlerProcess(settings=crawler_settings)
    crawler_process.crawl(InstagramSpider, login=os.getenv('LOGIN'), password=os.getenv('PASSWORD'), tag_amount=2)
    crawler_process.start()
