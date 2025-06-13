import scrapy
from financial_scraper.items import FinancialNewsItem

class ExameSpider(scrapy.Spider):
    name = "exame"
    allowed_domains = ["exame.com"]
    start_urls = ["https://exame.com/ultimas-noticias/1/"]

    def parse(self, response):
        for card in response.css('section.ultimas-noticias article'):
            link = card.css('a::attr(href)').get()
            if link:
                yield response.follow(link, self.parse_article)

    def parse_article(self, response):
        item = FinancialNewsItem()
        item['title'] = response.css('h1::text').get()
        item['url'] = response.url
        item['date'] = response.css('time::attr(datetime)').get()
        item['content'] = " ".join(response.css('div.texto p::text').getall())
        item['source'] = "Exame"
        yield item
