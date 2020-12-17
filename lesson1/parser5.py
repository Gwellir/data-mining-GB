import requests
import time
import json
from pathlib import Path
from typing import Dict, Any, Iterator


class StatusCodeError(Exception):
    def __init__(self):
        pass


class Parser5ka:
    api_url = 'https://5ka.ru/api/v2/'
    headers = {
        'User-Agent':
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
            ' Chrome/87.0.4280.88 Safari/537.36',
    }
    default_params = {
        'records_per_page': 20,
    }

    def __init__(self, start_path: str):
        self.start_url = f'{self.api_url}{start_path}'

    def run(self) -> None:
        try:
            for product in self.parse(self.start_url):
                file_path = Path(__file__).parent.joinpath(
                    'products', f'{product["id"]}.json')
                self.save(product, file_path)
        except requests.exceptions.MissingSchema:
            exit()

    def get_response(self, url: str, **kwargs) -> requests.Response:
        while True:
            try:
                response = requests.get(url, **kwargs)
                if response.status_code != 200:
                    raise Exception
                time.sleep(0.05)
                return response
            except (requests.exceptions.HTTPError,
                    StatusCodeError,
                    requests.exceptions.ConnectionError,
                    requests.exceptions.BaseHTTPError,
                    requests.exceptions.ConnectTimeout) as e:
                print(e)
                time.sleep(0.25)

    def parse(self, url: str, opts: Dict[str, str] = None) -> Iterator[Dict[str, Any]]:
        params = self.default_params
        if opts:
            params.update(opts)
        while url:
            response = self.get_response(url, headers=self.headers, params=params)
            data = response.json()
            url = data['next']
            for product in data['results']:
                yield product

    def save(self, data: Dict[str, Any], file_path: str) -> None:
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False)
