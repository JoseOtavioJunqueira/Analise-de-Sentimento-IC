BOT_NAME = "financial_scraper"
SPIDER_MODULES = ["financial_scraper.spiders"]
NEWSPIDER_MODULE = "financial_scraper.spiders"

ROBOTSTXT_OBEY = True
DOWNLOAD_DELAY = 1

FEEDS = {
    "financial_news.json": {"format": "json", "encoding": "utf8"}
}

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
