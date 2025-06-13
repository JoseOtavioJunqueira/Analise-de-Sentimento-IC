import scrapy
from financial_scraper.items import FinancialNewsItem

class ValorSpider(scrapy.Spider):
    name = "valor"
    allowed_domains = ["valor.globo.com"]
    start_urls = ["https://valor.globo.com/financas/"]

    def parse(self, response):
        for card in response.css('div.feed-post-body'):
            link = card.css('a.feed-post-link::attr(href)').get()
            if link:
                yield response.follow(link, self.parse_article)

    def parse_article(self, response):
        item = FinancialNewsItem()
        item['title'] = response.css('h1.content-head__title::text').get()
        item['url'] = response.url
        item['date'] = response.css('time::attr(datetime)').get()
        item['content'] = " ".join(response.css('div.content-text__container p::text').getall())
        item['source'] = "Valor Econômico"
        yield item
