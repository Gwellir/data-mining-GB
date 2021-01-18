import os
from datetime import datetime

import requests
import time
import bs4
from urllib.parse import urljoin
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv('.env')

MONTHS = {
    'января': 1,
    'февраля': 2,
    'марта': 3,
    'апреля': 4,
    'мая': 5,
    'июня': 6,
    'июля': 7,
    'августа': 8,
    'сентября': 9,
    'октября': 10,
    'ноября': 11,
    'декабря': 12,
}


class StatusCodeError(Exception):
    def __init__(self, string):
        super().__init__(string)


class MagnitParser:
    _base_url = 'https://magnit.ru/'

    def __init__(self, start_path, db_client):
        self.start_url = urljoin(self._base_url, start_path)
        self.collection = db_client['gb_parse_12']['magnit']

    @staticmethod
    def _get_response(url: str, **kwargs) -> requests.Response:
        while True:
            try:
                response = requests.get(url, **kwargs)
                if response.status_code == 200:
                    return response
                raise StatusCodeError(f'{response.status_code}')
            except (requests.exceptions.HTTPError,
                    requests.exceptions.ConnectTimeout,
                    StatusCodeError):
                time.sleep(0.2)

    @staticmethod
    def _get_soup(response: requests.Response) -> bs4.BeautifulSoup:
        soup = bs4.BeautifulSoup(response.text, 'lxml')
        return soup

    def run(self):
        page_soup = self._get_soup(self._get_response(self.start_url))
        for product in self._get_product(page_soup):
            self.save(product)

    def _get_product(self, soup: bs4.BeautifulSoup) -> dict:
        catalog = soup.find('div', attrs={'class': 'сatalogue__main'})
        for tag_product in catalog.find_all('a', recursive=False):
            if not tag_product.get('target'):
                yield self._product_parse(tag_product)

    def _form_date(self, date_str):
        day, mon_str = date_str.split()[1:]
        month = MONTHS[mon_str]
        now = datetime.now()
        year = now.year if month >= now.month else now.year + 1
        dt = datetime(day=int(day), month=month, year=year)

        return dt

    def _form_price(self, price_str):
        try:
            num, decimal = price_str.split()
        except ValueError:
            return None

        return float(f'{num}.{decimal}')

    def _product_parse(self, tag: bs4.Tag) -> dict:
        old_price_tag = tag.find('div', attrs={'class': 'label__price_old'})
        new_price_tag = tag.find('div', attrs={'class': 'label__price_new'})
        name_tag = tag.find('div', attrs={'class': 'card-sale__header'})
        date_tags = tag.find('div', attrs={'class': 'card-sale__date'}).find_all('p')
        product = {
            'url': urljoin(self._base_url, tag.get('href')),
            'promo_name': name_tag.text if name_tag else None,
            'product_name': tag.find('div', attrs={'class': 'card-sale__title'}).text,
            'old_price': self._form_price(old_price_tag.text) if old_price_tag else None,
            'new_price': self._form_price(new_price_tag.text) if new_price_tag else None,
            'image_url': urljoin(self._base_url, tag.find('source').get('data-srcset')),
            'date_from': self._form_date(date_tags[0].text),
            'date_to': self._form_date(date_tags[1].text),
        }

        return product

    def save(self, product: dict):
        self.collection.insert_one(product)
        print(1)


if __name__ == '__main__':
    db_client = MongoClient(os.getenv('MONGO_DB_URL'))
    parser = MagnitParser('promo/?geo=moskva', db_client)
    parser.run()
    collection = parser.collection
