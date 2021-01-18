import os
import re
import json
import base64
from urllib.parse import unquote, urljoin
import scrapy
from pymongo import MongoClient


class AutoyoulaSpider(scrapy.Spider):
    name = 'autoyoula'
    allowed_domains = ['auto.youla.ru']
    start_urls = ['https://auto.youla.ru/']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db = MongoClient(os.getenv('MONGO_DB_URL'))['gb_parse_youla']
        print(os.getenv('MONGO_DB_URL'))

    def parse(self, response, **kwargs):
        brands = response.css('a.blackLink')
        print(len(brands))
        for brand_link in brands:
            yield response.follow(brand_link.attrib.get('href', '/'),
                                  callback=self.brand_parse)

    def brand_parse(self, response):
        pag_links = response.css('div.Paginator_block__2XAPy a.Paginator_button__u1e7D')
        for pag_link in pag_links:
            yield response.follow(pag_link.attrib.get('href'), callback=self.brand_parse)

        ads_links = response.css('article.SerpSnippet_snippet__3O1t2 a.SerpSnippet_photoWrapper__3W9J4')
        for ads_link in ads_links:
            yield response.follow(ads_link.attrib.get('href'),
                                  callback=self.ads_parse)

    def parse_youla_data(self, data):
        if type(data) is not list:
            return data
        if len(data) == 1:
            return self.parse_youla_data(data[0])
        if len(data) == 0 or type(data[0]) is list:
            return [self.parse_youla_data(entry) for entry in data]
        new_dict = {}
        i = 0
        while i in range(len(data)):
            if data[i] == '^1':
                return [self.parse_youla_data(entry) for entry in data[i + 1]]
            elif data[i] == '^0':
                return self.parse_youla_data(data[i + 1])
            try:
                new_dict[data[i]] = self.parse_youla_data(data[i + 1])
            except TypeError as e:
                print(e.args)
            i += 2

        return new_dict

    def _form_specs(self, tag_list):
        specs = {}
        for entry in tag_list:
            label = entry.css('div.AdvertSpecs_label__2JHnS::text').get()
            link = entry.css('a.blackLink::text')
            if link:
                value = link.extract()[0]
            else:
                value = entry.css('div.AdvertSpecs_data__xK2Qx::text').get()
            specs[label] = value

        return specs

    def _form_link(self, ad_dict):
        if ad_dict['isAutosalon']:
            link = urljoin('https://auto.youla.ru', ad_dict['sellerLink'])
        elif ad_dict['isIndividual']:
            link = urljoin('https://youla.ru/user/', ad_dict['youlaProfile']['youlaId'])

        return link

    def ads_parse(self, response: scrapy.http.HtmlResponse):
        page_data = json.loads(unquote(re.findall(
            r'window\.transitState = decodeURIComponent\("(.*)"\)',
            response.text)[0]))
        page_dict = self.parse_youla_data(page_data)
        ad_dict = page_dict['~#iM']['advertCard']
        specs = self._form_specs(response.css('div.AdvertSpecs_row__ljPcX'))
        data = {
            'url': response.url,
            'title': response.css('div.AdvertCard_advertTitle__1S1Ak::text').get(),
            'price': response.css('div.AdvertCard_price__3dDCr::text').get().replace('\u2009', ''),
            'specs': specs,
            'photos': [entry['big'] for entry in ad_dict['media'] if entry['type'] == 'photo'],
            'description': response.css('div.AdvertCard_descriptionInner__KnuRi::text').get(),
            'seller': {
                'name': ad_dict['contacts']['seller'],
                'link': self._form_link(ad_dict),
                'phone': base64.b64decode(base64.b64decode(ad_dict['contacts']['phones'][0]['phone'])[:-1]).decode()
                    if ad_dict['contacts']['phones'] else None,
            }
        }
        collection = self.db[self.name]
        collection.insert_one(data)
