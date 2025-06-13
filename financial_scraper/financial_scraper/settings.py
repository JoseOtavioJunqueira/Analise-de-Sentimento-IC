BOT_NAME = "financial_scraper"
SPIDER_MODULES = ["financial_scraper.spiders"]
NEWSPIDER_MODULE = "financial_scraper.spiders"

ROBOTSTXT_OBEY = True
DOWNLOAD_DELAY = 1

FEEDS = {
    "financial_news.json": {"format": "json", "encoding": "utf8"}
}
