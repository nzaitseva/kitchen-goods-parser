import os
import re
import json
from datetime import date

import requests
import scrapy

from ..items import KitchengoodsItem


class MielesSpider(scrapy.Spider):
	name = 'mieles'
	custom_settings = {
		"MYSQL_TABLE": "mieles",
	}
	start_urls = [
		"https://store.tildaapi.com/api/getproductslist/?storepartuid=118745354213&recid=543651734&c=1721045467536&getparts=true&getoptions=true&slice=1&size=100",
		"https://store.tildaapi.com/api/getproductslist/?storepartuid=118745354213&recid=543651734&c=1721045467536&getparts=true&getoptions=true&slice=2&size=100",
		"https://store.tildaapi.com/api/getproductslist/?storepartuid=118745354213&recid=543651734&c=1721045467536&getparts=true&getoptions=true&slice=3&size=100",
		"https://store.tildaapi.com/api/getproductslist/?storepartuid=118745354213&recid=543651734&c=1721045467536&getparts=true&getoptions=true&slice=4&size=100"
	]

	def __init__(self,images="./images",*args, **kwargs):
		super(MielesSpider, self).__init__(*args, **kwargs)
		self.img_dir = images
		self.manufacturer = "Miele"
		self.manufacturer_id = 10

	def parse(self, response, **kwargs):
		products = json.loads(response.text)['products']
		for p in products:
			item = KitchengoodsItem()
			item['source_url'] = p['url']
			name = p['title']
			item['name_ru'] = name
			meta_title_ru = f"Купить {name}. Цена в СПб, фото, характеристики"
			meta_description_ru = f"В наличии в интернет-магазине {name} по выгодной цене в Санкт-Петербурге. Купить {name} у официального представителя с гарантией. Акции, бесплатная доставка по городу, рассрочка!"
			meta_keyword_ru = f"Купить, {name}, цена, фото, описание, заказать {name}, в интернет магазине, стоимость, доставка"
			meta_h1_ru = name
			item['meta_title_ru'] = meta_title_ru
			item['meta_description_ru'] = meta_description_ru
			item['meta_keyword_ru'] = meta_keyword_ru
			item['meta_h1_ru'] = meta_h1_ru

			item['manufacturer'] = self.manufacturer
			item['manufacturer_id'] = self.manufacturer_id

			if 'MIELE' in name:
				try:
					jan,mpn = name.split('MIELE')
				except:
					jan = name.split('MIELE')
					mpn = ''
			else:
				jan = ''
				mpn = ''
			item['jan'] = jan
			item['mpn'] = mpn

			try:
				sku = re.search('.*MIELE([A-Z0-9\s]*)\s?\w*','Кофемашина зерновая MIELE CVA7440 OBSW white').groups()
				sku = sku[0].strip()
				item['sku'] = sku
			except:
				item['sku'] = ''
			item['status'] = '1'
			item['stock_status'] = 'В наличии'
			item['stock_status_id'] = '7'

			item['price'] = p['price']

			source_image = p['editions'][0]['img']
			image_name = f'./images/mieles/{source_image.split("/")[-1]}'
			if not os.path.exists(image_name):
				res = requests.get(source_image)
				with open(image_name,'wb') as f:
					f.write(res.content)
			item['source_image'] = source_image
			item['image'] = image_name

			description_ru = ''
			if p['text']:
				description_ru= p['text']
			else:
				description_ru = p['descr']
			item['description_ru'] = description_ru

			sel = scrapy.Selector(text=description_ru)
			sel_text = sel.xpath('//text()').extract()
			specifications = [s for s in sel_text if re.match('.*:\s.*',s) and not ("В наличии" in s or "Цена" in s or "Гарантия" in s)]
			item['product_attribute'] = '|'.join(specifications)

			date_today = date.today().isoformat()
			item['date_added'] = date_today
			item['date_modified'] = date_today

			yield item
