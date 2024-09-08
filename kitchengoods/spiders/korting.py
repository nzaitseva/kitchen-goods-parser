import os
from datetime import date

import requests
import scrapy

from ..items import KitchengoodsItem


class KortingSpider(scrapy.Spider):
	name = 'korting'
	custom_settings = {
		"MYSQL_TABLE": "korting",
	}
	start_urls = ['https://store.korting.ru']

	def __init__(self,images='./images',*args, **kwargs):
		super(KortingSpider, self).__init__(*args, **kwargs)
		self.img_dir = images
		self.manufacturer = "Korting"
		self.manufacturer_id = 6

	def parse(self,response):
		category_links = response.xpath('//a[@class="nav-horiz-sub__link"]/@href').extract()
		for link in category_links:
			if not link.startswith('http'):
				link = f'https://store.korting.ru{link}'
			yield scrapy.Request(link,callback=self.parse_product_links)

	def parse_product_links(self,response):
		products = response.xpath('//li[@class="catalog__item catalog__item_thumb js-ecom_product-item"]')
		for p in products:
			purl = p.xpath('.//div[@class="catalog-thumb__name js-catalog-thumb__name"]/a/@href').extract_first()
			purl = "https://store.korting.ru"+purl
			if p.xpath('.//div[@class="not-available"]'):
				return
			else:
				yield scrapy.Request(purl,callback=self.parse_product)

	def parse_product(self, response, **kwargs):
		if "archive-models" in response.url:	#product model archived
			return
		item = KitchengoodsItem()
		name = response.xpath('//h1[contains(@class,"detail__title")]/text()').extract_first().strip()
		sku = ' '.join([s for s in name.split() if (s.isupper() or s.isnumeric())])
		jan = name.replace(sku,'')
		item['name_ru'] = name
		item['sku'] = sku
		item['jan'] = jan
		price = response.xpath('//strong[contains(@class,"detail-desc__price")]/text()').extract_first().replace(' ','').replace('руб.','')
		price = f'{price.strip()}.0000'
		item['price'] = price

		item['status'] = 1
		item['stock_status'] = "В наличии"
		item['stock_status_id'] = 7
		item['manufacturer'] = self.manufacturer
		item['manufacturer_id'] = self.manufacturer_id

		description_ru = response.xpath('//ul[@class="tabs-benefits__list"]').extract_first()
		item['description_ru'] = description_ru

		specs = response.xpath('//li[@class="tabs-settings__item"]')
		product_attributes = []
		for s in specs:
			spec = s.xpath('./span/text()').extract()
			key = spec[0].replace(':','').strip()
			val = ','.join([i.strip() for i in spec[1:]])
			product_attributes.append(f'{key}:{val}')
		product_attribute = '|'.join(product_attributes)
		item['product_attribute'] = product_attribute

		images = response.xpath('//ul[@class="web-gallery__list js-web-gallery__list"]/li/@data-bigphoto').extract()
		if images:
			images_fixed = []
			for i in images:
				if not i.startswith("http"):
					i = f'https://store.korting.ru{i}'
					images_fixed.append(i)
				else:
					images_fixed.append(i)

			main_img_url = images_fixed[0]
			main_img_name = f'{self.img_dir}{"_".join(main_img_url.split("/")[-2:])}'
			item['image'] = main_img_name
			item['source_image'] = main_img_url
			if not os.path.exists(main_img_name):
				res = requests.get(main_img_url)
				with open(main_img_name, 'wb') as f:
					f.write(res.content)

			if len(images_fixed) > 1:
				additional_image_urls = images_fixed[1:]
				additional_image_names = ["_".join(i.split("/")[-2:]) for i in additional_image_urls]
				additional_images = "|".join([f"{self.img_dir}{img}" for img in additional_image_names])
				item['additional_images'] = additional_images
				source_additional_images = "|".join([f"{img_url}" for img_url in additional_image_urls])
				item['source_additional_images'] = source_additional_images
				for img_url in source_additional_images.split('|'):
					for img_name in additional_images.split('|'):
						if not os.path.exists(img_name):
							res = requests.get(img_url)
							with open(img_name, 'wb') as f:
								f.write(res.content)
			else:
				item['additional_images'] = ""
		else:
			item['image'] = ""
			item['additional_images'] = ""

		date_today = date.today().isoformat()
		item['date_added'] = date_today
		item['date_modified'] = date_today
		item['source_url'] = response.url
		yield item







