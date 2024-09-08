import os

BOT_NAME = "kitchengoods"

SPIDER_MODULES = ["kitchengoods.spiders"]
NEWSPIDER_MODULE = "kitchengoods.spiders"

ROBOTSTXT_OBEY = False

STOCK_STATUSES = {5: "Нет в наличии", 8: "Предзаказ", 7: "В наличии"}

MYSQL_HOST = os.getenv('DB_HOST')
MYSQL_PORT = os.getenv('DB_PORT')
MYSQL_USER = os.getenv('DB_USER')
MYSQL_PASSWORD = os.getenv('DB_PWD')
MYSQL_DB = os.getenv('DB_NAME')
MYSQL_TABLE = os.getenv('DB_TABLE')

DOWNLOADER_MIDDLEWARES = {
	'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
	'scrapy.downloadermiddlewares.retry.RetryMiddleware': None,
	'scrapy_fake_useragent.middleware.RandomUserAgentMiddleware': 400,
	'scrapy_fake_useragent.middleware.RetryUserAgentMiddleware': 401,
}

FAKEUSERAGENT_PROVIDERS = [
	'scrapy_fake_useragent.providers.FakeUserAgentProvider',  # this is the first provider we'll try
	'scrapy_fake_useragent.providers.FakerProvider',
	# if FakeUserAgentProvider fails, we'll use faker to generate a user-agent string for us
	'scrapy_fake_useragent.providers.FixedUserAgentProvider',  # fall back to USER_AGENT value
]
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

ITEM_PIPELINES = {
	'scrapy_mysql_pipeline.MySQLPipeline': 300,
}

# Enable while developing scrapers
#HTTPCACHE_EXPIRATION_SECS = 43200
#HTTPCACHE_DIR = "httpcache"
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

