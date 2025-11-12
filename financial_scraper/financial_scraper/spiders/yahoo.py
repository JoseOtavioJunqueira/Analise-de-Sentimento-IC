import scrapy
from financial_scraper.items import FinancialNewsItem

# nao estamos mais usando esse!!!!
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

class YahooSpider(scrapy.Spider):
    name = "yahoo"
    allowed_domains = ["finance.yahoo.com"]
    start_urls = ["https://finance.yahoo.com/"]

    def parse(self, response):
        for card in response.css('li.js-stream-content'):
            link = card.css('a.js-content-viewer::attr(href)').get()
            if link:
                yield response.follow(link, self.parse_article)

    def parse_article(self, response):
        item = FinancialNewsItem()
        item['title'] = response.css('h1::text').get()
        item['url'] = response.url
        item['date'] = response.css('time::attr(datetime)').get()
        item['content'] = " ".join(response.css('article p::text').getall())
        item['source'] = "Yahoo Finance"
        yield item
