from time import sleep
from datetime import datetime

import requests
import bs4
from urllib.parse import urljoin
import lesson3.database as database


class GbBlogParse:
    _api_url = 'https://geekbrains.ru/api/v2/'
    _headers = {
        'User-Agent':
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
            ' Chrome/87.0.4280.88 Safari/537.36',
    }

    def __init__(self, start_url, db):
        self.db = db
        self.start_url = start_url
        self.done_urls = set()
        self.tasks = [self.posts_feed_parse(self.start_url)]
        self.done_urls.add(self.start_url)
        # ignores all the stored posts
        self.done_urls |= self.db.get_done_urls()

    def _get_soup(self, url):
        response = requests.get(url)
        soup = bs4.BeautifulSoup(response.text, 'lxml')
        return soup

    def _parse_comments(self, comments: list):
        for comment in comments:
            comments.extend(comment['comment']['children'])
            comment['comment'].pop('children')

        return comments

    def _get_comments(self, post_id):
        params = {
            'commentable_type': 'Post',
            'commentable_id': post_id,
            'order': 'desc',
        }
        while True:
            response = requests.get(urljoin(self._api_url, 'comments'),
                                    headers=self._headers,
                                    params=params)
            if response.status_code == 200:
                break
            else:
                print(f'Error: {response.status_code} <{response.reason}>')
        return self._parse_comments(response.json())

    def run(self):
        for task in self.tasks:
            task()
            sleep(0.2)

    def posts_feed_parse(self, url):
        url = url

        def task():
            soup = self._get_soup(url)
            pagination = soup.find('ul', attrs={'class': 'gb__pagination'})
            for task_url in [urljoin(self.start_url, url.get('href'))
                             for url in pagination.find_all('a')]:
                if task_url not in self.done_urls:
                    self.tasks.append(self.posts_feed_parse(task_url))
                    self.done_urls.add(task_url)
            posts_wrapper = soup.find(
                'div', attrs={
                    'class': 'post-items-wrapper'})
            for post_url in {
                urljoin(
                    self.start_url,
                    url.get('href')) for url in posts_wrapper.find_all(
                    'a',
                    attrs={
                        'class': 'post-item__title'})}:
                if post_url not in self.done_urls:
                    self.tasks.append(self.post_parse(post_url))
                    self.done_urls.add(post_url)
            print('\n>', end='')

        return task

    def post_parse(self, url):
        def task():
            soup = self._get_soup(url)
            gb_post_id = soup.find('comments', attrs={'commentable-type': 'Post'}).get('commentable-id')
            comments = self._get_comments(gb_post_id)
            author_name_el = soup.find('div', attrs={'itemprop': 'author'})
            tag_elems = soup\
                .find('article', attrs={'class': 'blogpost__article-wrapper'})\
                .find_all('a', attrs={'class': 'small'})
            time_string = soup.find('time', attrs={'class': 'text-md'}).get('datetime')
            data = {
                'post_data': {
                    'url': url,
                    'gb_id': gb_post_id,
                    'title': soup.find('h1').text,
                    'img': soup.find('div', attrs={'class': 'blogpost-content'}).find('img').get('src'),
                    'published_at': datetime.fromisoformat(time_string)
                },
                'author': {
                    'name': author_name_el.text,
                    'url': urljoin(self.start_url, author_name_el.parent.get('href')),
                },
                'tag_data': [{
                    'name': tag.text,
                    'url': urljoin(self.start_url, tag.get('href')),
                } for tag in tag_elems],
                'comment_data': [{
                    'url': urljoin(url, f'#comment-{comment["comment"]["id"]}'),
                    'site_id': comment['comment']['id'],
                    'username': comment['comment']['user']['full_name'],
                    'content': comment['comment']['body'],
                    'parent_id': comment['comment']['parent_id'],
                    'root_id': comment['comment']['root_comment_id'],
                } for comment in comments],
            }
            self.save(data)
            print('.', end='')

        return task

    def save(self, data):
        self.db.create_post(data)


if __name__ == '__main__':
    db = database.Database('sqlite:///gb_blog.db')
    parser = GbBlogParse('https://geekbrains.ru/posts/', db)
    parser.run()
