import scrapy

class FinancialNewsItem(scrapy.Item):
    title = scrapy.Field()
    url = scrapy.Field()
    date = scrapy.Field()
    content = scrapy.Field()
    source = scrapy.Field()
