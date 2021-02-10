import re
from urllib.parse import urljoin

import scrapy
from ..loaders import VacancyLoader, EmployerLoader


class HeadhunterSpider(scrapy.Spider):
    name = 'headhunter'
    allowed_domains = ['*.hh.ru', 'hh.ru']
    start_urls = ['https://hh.ru/search/vacancy?schedule=remote&L_profession_id=0&area=113']

    company_search_url = 'hh.ru/search/vacancy?st=searchVacancy&from=employerPage&employer_id='

    xpath_query = {
        'pagination': '//a[contains(@class, "HH-Pager-Control")]/@href',
        'ad': '//a[contains(@class, "HH-LinkModifier")]/@href',
    }

    vacancy_template = {
        'title': '//h1[contains(@data-qa, "vacancy-title")]/span/text()',
        'salary': '//p[contains(@class, "vacancy-salary")]/span/text()',
        'desc': '//div[contains(@class, "vacancy-description")]/descendant::*/text()',
        'tag_list': '//div[contains(@class, "bloko-tag")]/span/text()',
        'employer_url': '//a[contains(@class, "vacancy-company-name")]/@href',
    }

    employer_template = {
        'name': '//div[contains(@class, "company-header")]//span[contains(@data-qa, "company-header-title-name")]/text()',
        'site': '//a[contains(@data-qa, "sidebar-company-site")]/@href',
        'areas': '//div[contains(text(), "Сферы деятельности")]/../p/text()',
        'desc': '//div[contains(@class, "company-description")]/text()',
    }

    def parse(self, response):
        for vacancy_link in response.xpath(self.xpath_query['ad']):
            yield response.follow(vacancy_link, callback=self.vacancy_parse)

        for link in response.xpath(self.xpath_query['pagination']):
            yield response.follow(link, callback=self.parse)

    def vacancy_parse(self, response: scrapy.http.HtmlResponse):
        loader = VacancyLoader(response=response)
        loader.add_value('url', response.url)
        for name, selector in self.vacancy_template.items():
            loader.add_xpath(name, selector)
        vacancy = loader.load_item()
        yield response.follow(vacancy['employer_url'], callback=self.employer_parse)
        yield vacancy

    def employer_parse(self, response: scrapy.http.HtmlResponse):
        loader = EmployerLoader(response=response)
        loader.add_value('url', response.url)
        loader.add_value('site_id', re.findall(r'.*/(\d+)(\?.*)?$', response.url)[0])
        for name, selector in self.employer_template.items():
            loader.add_xpath(name, selector)
        employer = loader.load_item()
        yield employer
        yield response.follow(urljoin(self.company_search_url, employer['site_id']), callback=self.parse)
