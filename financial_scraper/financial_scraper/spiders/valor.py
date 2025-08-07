import scrapy
from financial_scraper.items import FinancialNewsItem

class ValorSpider(scrapy.Spider):
    name = "valor"
    allowed_domains = ["valor.globo.com"]
    start_urls = ["https://valor.globo.com/financas/"]

    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
    }

    def parse(self, response):
        for card in response.css('div.feed-post-body'):
            link = card.css('a.feed-post-link::attr(href)').get()
            if link and "valor.globo.com" in link and "video" not in link:
                yield response.follow(link, self.parse_article)

    def parse_article(self, response):
        item = FinancialNewsItem()
        
        title = response.css('h1.content-head__title::text').get() or response.css('h1::text').get()
        item['title'] = title.strip() if title else ''

        item['url'] = response.url
        
        date = response.css('time::attr(datetime)').get() or response.css('p.content-publication-data__updated::text').get()
        item['date'] = date.strip() if date else ''
        
        subtitle_text = response.css('h2.content-head__subtitle::text').get(default='').strip()
        
        content_paragraphs = (
            response.css('div.content-text__container p::text').getall() or
            response.css('div.container--article p::text').getall() or
            response.css('div.content p::text').getall() or
            response.xpath('//div[@itemprop="articleBody"]//p//text()').getall()
        )
        
        body_content = " ".join(content_paragraphs).strip()
        
        if subtitle_text and body_content:
            item['content'] = subtitle_text + " " + body_content
        else:
            item['content'] = subtitle_text or body_content

        item['source'] = "Valor Econômico"
        
        yield item