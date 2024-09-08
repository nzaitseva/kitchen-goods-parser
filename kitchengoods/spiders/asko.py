import os
from datetime import date

import requests
import scrapy
from scrapy import Selector

from ..items import KitchengoodsItem


class AskoSpider(scrapy.Spider):
	name = 'asko'
	custom_settings = {
		"MYSQL_TABLE": "asko",
	}
	start_urls = ['https://ru.asko.com/sitemap?type=Product']

	def __init__(self,images='./images', *args, **kwargs):  # mode=filter
		super(AskoSpider, self).__init__(*args, **kwargs)
		self.img_dir = images
		self.manufacturer = "Asko"
		self.manufacturer_id = 15

	def parse(self,response):
		sel = Selector(text=response.text)
		product_links = sel.xpath('//loc/text()').extract()
		for link in product_links:
			yield scrapy.Request(link,callback=self.parse_product)

	def parse_product(self, response, **kwargs):
		item = KitchengoodsItem()
		item['source_url'] = response.url
		title = [s.strip() for s in response.xpath('//title/text()').extract_first().split('-')[:-1]]
		jan= title[0]
		item['jan'] =jan
		sku=title[1]
		item['sku'] = sku
		product_name = f'{jan} {sku}'
		item['name_ru'] = product_name
    	meta_title_ru = f'Купить {product_name}. Цена в СПб, фото, характеристики'
		meta_description_ru = f'В наличии в интернет-магазине {product_name} по выгодной цене в Санкт-Петербурге. Купить {product_name} у официального представителя с гарантией. Акции, бесплатная доставка по городу, рассрочка!'
		meta_keyword_ru = f'Купить, {product_name}, цена, фото, описание, заказать {product_name}, в интернет магазине, стоимость, доставка'
		meta_h1_ru = product_name
		item['meta_title_ru'] = meta_title_ru
		item['meta_description_ru'] = meta_description_ru
		item['meta_keyword_ru'] = meta_keyword_ru
		item['meta_h1_ru'] = meta_h1_ru

		desc1 = response.xpath('//div[@class="product__detail-top-content-text"]').extract_first()
		desc2 = response.xpath('//div[@class="product__detail-top-content-list"]').extract_first()
		item['description_ru'] = ''.join([desc1,desc2])

		price = response.xpath('//div[@class="price"]/text()').extract_first().strip().replace('\xa0', '')
		price = f'{price.split(",")[0]}.0000'
		item['price'] = price
		item['manufacturer'] = self.manufacturer
		item['manufacturer_id'] = self.manufacturer_id
		item['status'] = '1'
		item['stock_status'] = 'В наличии'
		item['stock_status_id'] = '7'

		model = response.xpath('//section[@class="ProductDetailsTop"]/@data-product-item-id').extract_first().replace('0','')
		model = f'ASK-{model}'
		item['model'] = model

		specifications = []
		specs = response.xpath('//div[@class="product-spec-tbody-container"]')
		for s in specs:
			tr = s.xpath('.//tbody/tr')
			for t in tr:
				param = t.xpath('./td/text()').extract()
				key = param[0]
				val = ','.join(param[1:])
				specifications.append(f'{key.strip()}:{val.strip()}')
		specification_line = '|'.join(specifications)
		item['product_attribute'] = specification_line

		images = response.xpath('//div[contains(@class,"product-images-nav")]//img/@src').extract()
		main_img_url = images[0]
		main_img_name = f'{self.img_dir}ASK-{sku.replace("/","")}.png'
		if not os.path.exists(main_img_name):
			res = requests.get(main_img_url)
			with open(main_img_name, 'wb') as f:
				f.write(res.content)
		item['image'] = main_img_name
		item['source_image'] = main_img_url
		try:
			additional_image_urls = images[1:]
		except: pass
		else:
			additional_images = []
			for img in additional_image_urls:
				img_name = f'{self.img_dir}ASK-{sku.replace("/","")}-{additional_image_urls.index(img)}.png'
				additional_images.append(img_name)
				if not os.path.exists(img_name):
					res = requests.get(img)
					with open(img_name,'wb') as f:
						f.write(res.content)
			item['additional_images'] = "|".join(additional_images)

		date_today = date.today().isoformat()
		item['date_added'] = date_today
		item['date_modified'] = date_today

		yield item

