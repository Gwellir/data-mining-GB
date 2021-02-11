import json
from urllib.parse import urlencode

import scrapy
from datetime import datetime
from random import randint, choice
from ..loaders import TagLoader, PostInfoLoader


class InstagramSpider(scrapy.Spider):
    name = 'instagram'
    login_url = 'https://www.instagram.com/accounts/login/ajax/'
    hashtag_directory = '/directory/hashtags/'
    allowed_domains = ['www.instagram.com']
    start_urls = ['https://www.instagram.com/']
    graphql_api = 'http://www.instagram.com/graphql/query/'
    query_hash = {
        'tag_paginate': '9b498c08113f1e09617a1703c22b2f32',
    }
    tag_fields = ['id', 'name', 'profile_pic_url']
    post_info_fields = ['id', 'edge_media_to_caption', 'shortcode', 'edge_media_to_comment',
                        'taken_at_timestamp', 'dimensions', 'display_url', 'edge_liked_by',
                        'edge_media_preview_like', 'owner', 'is_video', 'accessibility_caption']

    def __init__(self, login, password, tag_amount, *args, **kwargs):
        self.login = login
        self.password = password
        self.tag_amount = tag_amount
        self.tag_links = []

        super().__init__(*args, **kwargs)

    def parse(self, response):
        try:
            js_data = self.js_data_extract(response)
            yield scrapy.FormRequest(
                self.login_url,
                method='POST',
                callback=self.parse,
                formdata={
                    'username': self.login,
                    'enc_password': self.password,
                },
                headers={
                    'X-CSRFToken': js_data['config']['csrf_token']
                }
            )
        except AttributeError:
            if response.json().get('authenticated'):
                for _ in range(self.tag_amount):
                    rand_link = f'{self.hashtag_directory}{randint(1, 10)}-{randint(1, 9)}/?__a=1'
                    yield response.follow(rand_link, self.get_random_tag, )
                # for link in self.tag_links:
                #     yield response.follow(link, self.tag_parse)

    def js_data_extract(self, response):
        script = response.xpath('//script[contains(text(), "window._sharedData = ")]/text()').get()
        return json.loads(script.replace('window._sharedData = ', '')[:-1])

    def get_random_tag(self, response: scrapy.http.HtmlResponse):
        data = response.json()
        tag_list = json.loads(data['hashtag_data']['hashtag_list'])
        yield response.follow(f'/explore/tags/{choice(tag_list)}', self.tag_parse)

    def tag_parse(self, response: scrapy.http.HtmlResponse):
        try:
            data = self.js_data_extract(response)
            tag_data = data['entry_data']['TagPage'][0]['graphql']['hashtag']
            tag_item = self.make_tag(tag_data, response)
            yield tag_item
        except KeyError:
            return
        except AttributeError:
            try:
                data = response.json()
                tag_data = data['data']['hashtag']
            except json.JSONDecodeError:
                return
        yield from self.make_posts(tag_data, response)
        next_page = self.get_next_page(tag_data)
        if next_page:
            yield response.follow(next_page, self.tag_parse)

    def get_next_page(self, data):
        page_info = data['edge_hashtag_to_media']['page_info']
        if page_info['has_next_page']:
            variables = {
                'tag_name': data['name'],
                'first': 100,
                'after': page_info['end_cursor'],
            }
            var_str = json.dumps(variables)
            link = f'{self.graphql_api}?query_hash={self.query_hash["tag_paginate"]}&variables={var_str}'
            return link

        return None

    def make_tag(self, data, response):
        loader = TagLoader(response=response)
        loader.add_value('updated', datetime.now())
        for field in self.tag_fields:
            loader.add_value(field, data[field])
        return loader.load_item()

    def make_posts(self, data, response):
        edges = data['edge_hashtag_to_media']['edges']
        for entry in edges:
            loader = PostInfoLoader(response=response)
            loader.add_value('updated', datetime.now())
            for field in self.post_info_fields:
                loader.add_value(field, entry['node'][field])
            item = loader.load_item()
            yield item
