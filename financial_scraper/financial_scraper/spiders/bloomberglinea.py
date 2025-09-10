import scrapy
from financial_scraper.items import FinancialNewsItem

class BloombergSpider(scrapy.Spider):
    name = "bloomberg"
    allowed_domains = ["bloomberglinea.com.br"]
    start_urls = ["https://www.bloomberglinea.com.br/mercados/"]

    """def parse(self, response):
        for card in response.css('h2.font-im-sans a'):
            link = card.css('::attr(href)').get()
            if link:
                yield response.follow(link, self.parse_article)"""
    
    def parse(self, response):
        article_links = response.css('a.hover\\:text-hover.hover\\:underline::attr(href)').getall()
        for link in article_links:
            yield response.follow(link, self.parse_article)

    def parse_article(self, response):
        item = FinancialNewsItem()
        item['title'] = response.css('h1.hp-article-title::text').get()
        item['url'] = response.url
        item['date'] = response.css('small.text-sm.leading-tight::text').get()
        item['content'] = response.css('p.text-base.leading-tight.text-center.md\\:text-left::text').get()
        #item['content'] = " ".join(response.css('div[class="text-lg md:text-xl font-medium tracking-tight text-wl-neutral-600"]::text').getall())
        item['source'] = "BloombergLinea"
        yield item