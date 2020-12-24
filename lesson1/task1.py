from pathlib import Path
from typing import List, Dict, Any
import requests

from parser5 import Parser5ka  # highlights as an error, but still runs both in ide and terminal


class CategoryParser5ka(Parser5ka):

    def __init__(self, products_path, categories_path) -> None:
        super().__init__(products_path)
        self.categories_url = f'{self.api_url}{categories_path}'

    def run(self) -> None:
        try:
            for category in self.parse_categories(self.categories_url):
                data = self.get_category_data(category)
                file_path = Path(__file__).parent.joinpath(
                    'categories', f'{category["parent_group_name"]}.json')
                self.save(data, file_path)
        except requests.exceptions.MissingSchema:
            exit()

    def get_category_data(self, category: Dict[str, str]) -> Dict[str, Any]:
        opts = {
            'categories': category['parent_group_code']
        }
        category_data = {
            'name': category['parent_group_name'],
            'code': category['parent_group_code'],
            'products': [
                product for product in self.parse(self.start_url, opts=opts)
            ]
        }

        return category_data

    def parse_categories(self, url: str) -> List[Dict[str, str]]:
        response = self.get_response(url, headers=self.headers)
        data = response.json()
        return data


if __name__ == '__main__':
    parser = CategoryParser5ka('special_offers/', 'categories/')
    parser.run()
