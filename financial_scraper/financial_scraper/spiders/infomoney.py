import scrapy
from financial_scraper.items import FinancialNewsItem

class InfoMoneySpider(scrapy.Spider):
    name = "infomoney"
    allowed_domains = ["infomoney.com.br"]
    #start_urls = ["https://www.infomoney.com.br/ultimas-noticias/"]
    start_urls = ["https://www.infomoney.com.br/mercados/"]

    def parse(self, response):
        for card in response.css('h2.font-im-sans a'):
            link = card.css('::attr(href)').get()
            if link:
                yield response.follow(link, self.parse_article)

    def parse_article(self, response):
        item = FinancialNewsItem()
        item['title'] = response.css('h1::text').get()
        item['url'] = response.url
        item['date'] = response.css('time::attr(datetime)').get()
        item['content'] = " ".join(response.css('div[class="text-lg md:text-xl font-medium tracking-tight text-wl-neutral-600"]::text').getall())
        item['source'] = "InfoMoney"
        yield item
     
    """   
    def parse(self, response):
        # ALTERAÇÃO 1 (laço for inteiro)
        for card in response.css('h2.font-im-sans a'):
            url = card.css('::attr(href)').get()
            title = card.css('::text').get()

            if url:
                yield response.follow(
                    url,
                    self.parse_article,
                    cb_kwargs={'title': title, 'url': url}
                )

    # ALTERAÇÃO 3 (assinatura da função)
    def parse_article(self, response, title, url):
        item = FinancialNewsItem()
        # ALTERAÇÃO 3 (atribuição de itens)
        item['title'] = title
        item['url'] = url
        item['date'] =

        # ALTERAÇÃO 2 (seletor de conteúdo)
        content_paragraphs = response.css('div.im-article-content p::text').getall()
        item['content'] = " ".join(p.strip() for p in content_paragraphs if p.strip())
        
        item['source'] = "InfoMoney"
        yield item"""

    """def parse(self, response):
        # Seleciona todos os links de notícias na página inicial
        # O seletor foi ajustado para encontrar os links dentro de títulos de notícias,
        # independentemente da classe específica, o que o torna mais robusto
        links = response.css('div.block-news-list a::attr(href)').getall()
        for link in links:
            if link:
                yield response.follow(link, self.parse_article)

    def parse_article(self, response):
        item = FinancialNewsItem()

        # Extrai o título do artigo
        item['title'] = response.css('h1.entry-title::text').get()

        # Extrai a URL
        item['url'] = response.url

        # Extrai a data e hora da publicação
        item['date'] = response.css('time.entry-date::attr(datetime)').get()

        # Extrai o subtítulo da notícia
        item['content'] = response.css('div.article-lead p::text').get()

        # Define a fonte
        item['source'] = "InfoMoney"

        yield item"""