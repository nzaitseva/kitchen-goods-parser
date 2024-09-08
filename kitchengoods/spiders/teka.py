import os
from datetime import datetime

import requests
import scrapy

from ..items import KitchengoodsItem

class TekaSpider(scrapy.Spider):
	name = 'teka'
	custom_settings = {
		"MYSQL_TABLE": "teka",
	}
	start_urls = ['https://www.teka.com/ru-ru/']

	def __init__(self,images='./images', *args, **kwargs):
		super(TekaSpider, self).__init__(*args, **kwargs)
		self.img_dir = images
		self.manufacturer = "Teka"
		self.manufacturer_id = 12

	def parse(self,response):
		menu_links = response.xpath('//ul[@id="top-menu"]/li/a/@href').extract()
		for link in menu_links:
			yield scrapy.Request(link,
				callback=self.parse_product_links
				)

	def parse_product_links(self, response, **kwargs):
		items=response.xpath('//div[@class="et_pb_portfolio_grid_items product-list"]/div')
		for i in items:
			product_url = i.xpath('.//a[@class="product-link"]/@href').extract_first()
			self.logger.info(f"ITEM {product_url}")
			yield scrapy.Request(product_url,callback=self.parse_product)

	def parse_product(self,response):
		item = KitchengoodsItem()
		url = response.url
		item['source_url'] = url

		breadcrumbs = response.xpath('//div[@id="breadcrumbs"]//a[@class="taxonomy product_cat"]/@title').extract()
		category = breadcrumbs[-1]
		item['product_category'] = category

		sku = response.xpath('//span[@class="product_id"]/text()').extract_first()
		item['sku'] = sku
		ean = response.xpath('//div[@id="ref-ean"]/div[@class="ref ean"]/text()').extract_first().split()[-1]
		item['ean'] = ean

		price = response.xpath('//span[@class="unit_price"]/text()').extract_first()
		price = f'{price}00'
		item['price'] = price

		availability = response.xpath('//span[@class="availability"]/text()').extract_first()
		if availability == 'InStock':
			item['stock_status'] = 'В наличии'
			item['stock_status_id'] = '7'
			item['status'] = '1'
		else:
			return

		main_image_url = response.xpath('//span[@class="image_url"]/text()').extract_first()
		if main_image_url:
			main_img_name = f'{self.img_dir}{main_image_url.split("/")[-1]}'
			item['image'] = main_img_name
			item['source_image'] = main_image_url
			if not os.path.exists(main_img_name):
				res = requests.get(main_image_url)
				with open(main_img_name, 'wb') as f:
					f.write(res.content)
		else:
			item['image'] = ''
			item['source_image'] = ''

		try:
			imgs = response.xpath('//div[@id="product-images"]//ul[@id="product-img-max"]')
			additional_image_urls = imgs.xpath('.//li/img/@data-src').extract()
			additional_image_names = [i.split('/')[-1] for i in additional_image_urls]
			item['additional_images'] = "|".join([f"{self.img_dir}{img}" for img in additional_image_names])
			item['source_additional_images'] = "|".join([f"{img_url}" for img_url in additional_image_urls])

			for img in additional_image_urls:
				img_name = f'{self.img_dir}{img.split("/")[-1]}'
				if not os.path.exists(img_name):
					res = requests.get(img)
					with open(img_name, 'wb') as f:
						f.write(res.content)
		except:
			item['additional_images'] = ''

		#Формат: {наименование} {бренд} {модель} {характеристика} {цвет}
		h1 = response.xpath('//div[@id="product-title"]//h1/text()').extract_first()
		item['jan'] = h1
		h2 = response.xpath('//div[@id="product-title"]//h2/text()').extract_first()
		item['mpn'] = h2
		name_ru = f'{h1} Teka {h2}'
		item['name_ru'] = name_ru
		meta_title_ru = f'Купить {name_ru}. Цена в СПб, фото, характеристики'
		meta_description_ru = f'В наличии в интернет-магазине {name_ru} по выгодной цене в Санкт-Петербурге. Купить {name_ru} у официального представителя с гарантией. Акции, бесплатная доставка по городу, рассрочка!'
		meta_keyword_ru = f'Купить, {name_ru}, цена, фото, описание, заказать {name_ru}, в интернет магазине, стоимость, доставка'
		meta_h1_ru = name_ru
		item['meta_title_ru'] = meta_title_ru
		item['meta_description_ru'] = meta_description_ru
		item['meta_keyword_ru'] = meta_keyword_ru
		item['meta_h1_ru'] = meta_h1_ru

		item['manufacturer'] = self.manufacturer
		item['manufacturer_id'] = self.manufacturer_id

		description = response.xpath('//div[@id="product-content"]/ul').extract_first()
		item['description_ru'] = description

		specification = response.xpath('//div[contains(@class,"technical-detail-accordion")]')
		specification_params = dict()
		for spec in specification:
			lis = spec.xpath('./div[contains(@class,et_pb_toggle_content)]/ul/li')
			for li in lis:
				key = li.xpath('./strong/text()').extract_first()
				value = li.xpath('./text()').extract_first()
				if key.strip() and value.strip():
					specification_params[key.replace(":","").strip()] = value.replace(":","").strip()
		#Формат:'Дисплей:цифровой|Конвекция:есть|Очистка духовки:традиционные...'
		specification_line = '|'.join(f'{k}:{v}' for k, v in specification_params.items())
		item['product_attribute'] = specification_line

		date_today = datetime.now()
		item['date_added'] = date_today.strftime('%d-%m-%y %H:%M:%S')
		item['date_modified'] = date_today

		yield item

