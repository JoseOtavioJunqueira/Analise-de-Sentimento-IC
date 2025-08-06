import scrapy
from financial_scraper.items import FinancialNewsItem

class InfoMoneySpider(scrapy.Spider):
    name = "infomoney"
    allowed_domains = ["infomoney.com.br"]
    #start_urls = ["https://www.infomoney.com.br/ultimas-noticias/"]
    start_urls = ["https://www.infomoney.com.br/mercados/"]

    def parse(self, response):
        for card in response.css('a.hover:underline::attr(href)'):
            link = card.css('a::attr(href)').get()
            if link:
                yield response.follow(link, self.parse_article)

    def parse_article(self, response):
        item = FinancialNewsItem()
        item['title'] = response.css('h1::text').get()
        item['url'] = response.url
        item['date'] = response.css('time::attr(datetime)').get()
        item['content'] = " ".join(response.css('div.text-lg md:text-xl font-medium tracking-tight text-wl-neutral-600" p::text').getall())
        item['source'] = "InfoMoney"
        yield item
