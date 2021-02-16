import json

import scrapy
from datetime import datetime
from ..items import User, Follow


class InstagramSpider(scrapy.Spider):
    name = 'instagram'
    login_url = 'https://www.instagram.com/accounts/login/ajax/'
    allowed_domains = ['www.instagram.com']
    start_urls = ['https://www.instagram.com/']
    graphql_api = 'http://www.instagram.com/graphql/query/'
    query_hash = {
        'followers': '5aefa9893005572d237da5068082d8d5',
        'following': '3dec7e2c57367ef3da3d987d89f9dbc8',
    }

    def __init__(self, login, password, *args, **kwargs):
        self.login = login
        self.password = password
        self.user_list = ['bsnbooks', 'nazmiyesumer', 'missguard']

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
                for user in self.user_list:
                    yield response.follow(f'/{user}', callback=self.parse_user)

    def parse_user(self, response):
        data = self.js_data_extract(response)['entry_data']['ProfilePage'][0]['graphql']['user']
        yield User(date_parse=datetime.now(), data=data)
        yield from self.iterate_follows(response, data)

    def create_link(self, query_name, variables):
        var_str = json.dumps(variables)
        return f'{self.graphql_api}?query_hash={self.query_hash[query_name]}&variables={var_str}'

    def iterate_follows(self, response, user_data):
        variables = {
            'id': user_data['id'],
            'first': 100,
        }
        if b'application/json' in response.headers['Content-Type']:
            data = response.json()
            edge_follow = data['data']['user']['edge_follow']
            yield from self.make_follow_item(user_data, edge_follow['edges'])
            if edge_follow['page_info']['has_next_page']:
                variables['after'] = edge_follow['page_info']['end_cursor']

        link = self.create_link('following', variables)
        yield response.follow(link, callback=self.iterate_follows, cb_kwargs={'user_data': user_data})

    def make_follow_item(self, user_data, follow_data):
        for following in follow_data:
            yield Follow(
                user_id=user_data['id'],
                follow_id=following['node']['id']
            )

            yield User(date_parse=datetime.now(), data=following['node'])

    def js_data_extract(self, response):
        script = response.xpath('//script[contains(text(), "window._sharedData = ")]/text()').get()
        return json.loads(script.replace('window._sharedData = ', '')[:-1])
