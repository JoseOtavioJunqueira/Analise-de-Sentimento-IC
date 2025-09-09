import scrapy
from financial_scraper.items import FinancialNewsItem

class ExameSpider(scrapy.Spider):
    name = "exame"
    allowed_domains = ["exame.com"]
    start_urls = ["https://exame.com/invest/"]

    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
    }

    def parse(self, response):
        links = response.xpath('//h3/a/@href').getall()

        for link in links:
            absolute_url = response.urljoin(link)
            if "/invest/" in absolute_url and "lps.exame.com" not in absolute_url:
                yield scrapy.Request(absolute_url, callback=self.parse_article)

    def parse_article(self, response):
        item = FinancialNewsItem()
        
        item['title'] = response.css('h1::text').get(default='').strip()
        item['url'] = response.url
        
        date_text = (
            response.xpath('string(//p[@class="m-0 p-0 text-colors-text xl:text-pretty body-small"])').get(default='').strip() or
            response.xpath('string(//p[contains(@class, "body-small")])').get(default='').strip()
        )
        
        if date_text:
            date_text = date_text.replace("Publicado em", "").replace("Última atualização em", "").strip()
            date_text = date_text.split(' às ')[0].strip()
            date_text = date_text.replace('.', '').strip()
            item['date'] = date_text
        else:
            item['date'] = ''
            
        intro_text = response.css('h2.title-medium::text').get(default='').strip()
        
        content_paragraphs = (
            response.xpath('//div[contains(@class, "article-content")]//p//text()').getall() or
            response.css('div.post-content p::text').getall() or
            response.css('div[class*="texto"] p::text').getall()
        )
        
        full_content = " ".join(content_paragraphs).strip()
        
        if intro_text and full_content:
            item['content'] = intro_text + " " + full_content
        else:
            item['content'] = intro_text or full_content
            
        item['source'] = "Exame"
        
        yield item