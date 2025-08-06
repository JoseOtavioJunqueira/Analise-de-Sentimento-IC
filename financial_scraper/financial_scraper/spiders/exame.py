import scrapy
from financial_scraper.items import FinancialNewsItem

class ExameSpider(scrapy.Spider):
    name = "exame"
    allowed_domains = ["exame.com"]
    start_urls = ["https://exame.com/invest/"]

    def parse(self, response):
        # Tenta o seletor mais específico que parece existir
        links = response.css('a.touch-area::attr(href)').getall()

        # Se não encontrar links com a classe 'touch-area', tenta uma abordagem mais genérica
        if not links:
            links = response.css('a[href*="/invest/"]::attr(href)').getall()

        for link in links:
            absolute_url = response.urljoin(link)
            # Evita URLs duplicadas e lida com a paginação, se existir
            if absolute_url.startswith("https://exame.com/invest/") and not absolute_url.endswith("/"):
                 yield scrapy.Request(absolute_url, callback=self.parse_article)
            
            # Adiciona uma lógica para seguir a paginação, se necessário
            # (Exemplo: se houver um link "Próxima página")
            # next_page = response.css('a.next-page::attr(href)').get()
            # if next_page:
            #     yield scrapy.Request(response.urljoin(next_page), callback=self.parse)


    def parse_article(self, response):
        item = FinancialNewsItem()
        
        # Título: Usa um seletor mais genérico que captura o texto do primeiro <h1>
        # Se o título estiver em um <h2>, mude para 'h2::text'.
        item['title'] = response.xpath('//h1/text()').get(default='').strip() or \
                        response.css('h1::text').get(default='').strip()
        
        item['url'] = response.url
        
        # Data: Usa o seletor p.body-small, mas com tratamento de texto para lidar com a formatação
        date_raw = response.css('p.body-small::text').getall()
        # Junta os pedaços de texto e remove o prefixo "Última atualização em"
        date_text = "".join(date_raw).replace("Última atualização em", "").strip()
        item['date'] = date_text

        # Conteúdo: Esta parte é a mais provável de falhar.
        # Usa um seletor que busca todos os parágrafos dentro de uma div principal
        # com classes que podem conter o corpo do artigo.
        # A classe 'article-content' é uma suposição. Você precisa verificar.
        content_paragraphs = response.css('div.article-content p::text').getall()

        # Outra tentativa: seletores de classes que parecem comuns em sites
        if not content_paragraphs:
            content_paragraphs = response.css('div[class*="texto"] p::text').getall()

        if not content_paragraphs:
            content_paragraphs = response.css('div.post-content p::text').getall()

        item['content'] = " ".join(content_paragraphs).strip()
        
        item['source'] = "Exame"
        
        # Adiciona a introdução (h2) ao conteúdo se ela existir
        intro_paragraph = response.css('h2.title-medium::text').get(default='').strip()
        if intro_paragraph and item['content']:
            item['content'] = intro_paragraph + " " + item['content']
        elif intro_paragraph:
            item['content'] = intro_paragraph
            
        yield item