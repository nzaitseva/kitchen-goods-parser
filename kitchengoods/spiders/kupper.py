import os
from datetime import datetime

import requests
import scrapy

from ..items import KitchengoodsItem

class KupperSpider(scrapy.Spider):
	name = 'kupper'
	custom_settings = {
		"MYSQL_TABLE": "kupper",
	}
	start_urls = [
		"https://kuppersbusch-shop.ru/cat/dukhovye-shkafy/",
		"https://kuppersbusch-shop.ru/cat/parovye-shkafy/",
		"https://kuppersbusch-shop.ru/cat/varochnye-paneli/",
		"https://kuppersbusch-shop.ru/cat/vytyazhki_kuppersbusch/",
		"https://kuppersbusch-shop.ru/cat/vakuumatory-vydvizhnye-yashchiki-podogrevateli-posudy/",
		"https://kuppersbusch-shop.ru/cat/mikrovolnovye-pechi/",
		"https://kuppersbusch-shop.ru/cat/kofemashiny/",
		"https://kuppersbusch-shop.ru/cat/malaya_bytovaya_tekhnika/",
		"https://kuppersbusch-shop.ru/cat/kholodilnye-i-morozilnye-shkafy/",
		"https://kuppersbusch-shop.ru/cat/vstraivaemye-vinnye-shkafy/",
		"https://kuppersbusch-shop.ru/cat/posudomoechnye-mashiny/",
		"https://kuppersbusch-shop.ru/cat/stiralnye-i-sushilnye-mashiny/",
		"https://kuppersbusch-shop.ru/cat/zhk-televizory/",
		"https://kuppersbusch-shop.ru/cat/aksessuary_kuppersbusch/"
	]

	def __init__(self, images="./images", *args, **kwargs):	#mode=update
		super(KupperSpider, self).__init__(*args, **kwargs)
		self.img_dir = images
		self.manufacturer = "Kuppersbusch"
		self.manufacturer_id = 17

	def parse(self,response, **kwargs):
		products = response.xpath('//div[@class="catalog__inner"]/div[contains(@class,"card_color")]/a/@href').extract()
		for p in products:
			yield scrapy.Request(f"https://kuppersbusch-shop.ru{p}",
								 callback=self.parse_product)

	def parse_product(self, response, **kwargs):
		item = KitchengoodsItem()
		item['source_url'] = response.url
		availability = response.xpath('//div[contains(@class,"availability")]/text()').extract_first()
		if 'в наличии' in availability:
			item['stock_status'] = 'В наличии'
			item['stock_status_id'] = '7'
		elif 'под заказ' in availability:
			item['stock_status'] = 'Под заказ'
			item['stock_status_id'] = '8'
		else:
			self.logger.info(f'DROP ITEM NOT AVAILABLE {response.url}')
			return
		name = response.xpath('//h1/text()').extract_first()
		item['name_ru'] = name
		if 'Kuppersbusch' in name:
			name_sp = name.split('Kuppersbusch')
			jan = name_sp[0]
			mpn = 'Kuppersbusch' + name_sp[-1]
			item['jan'] = jan
			item['mpn'] = mpn
		meta_title_ru = f'Купить {name}. Цена в СПб, фото, характеристики'
		meta_description_ru = f'В наличии в интернет-магазине {name} по выгодной цене в Санкт-Петербурге. Купить {name} у официального представителя с гарантией. Акции, бесплатная доставка по городу, рассрочка!'
		meta_keyword_ru = f'Купить, {name}, цена, фото, описание, заказать {name}, в интернет магазине, стоимость, доставка'
		meta_h1_ru = name
		item['meta_title_ru'] = meta_title_ru
		item['meta_description_ru'] = meta_description_ru
		item['meta_keyword_ru'] = meta_keyword_ru
		item['meta_h1_ru'] = meta_h1_ru

		item['manufacturer'] = self.manufacturer
		item['manufacturer_id'] = self.manufacturer_id

		price = response.xpath('//span[@class="old__price"]/text()').extract_first()
		price = f'{price.strip().replace(" ", "")}.0000'
		item['price'] = price

		html_description = response.xpath('//div[@class="rich-top-desc"]/div/ul').extract_first()
		if not html_description:
			html_description = ''.join(response.xpath('//div[@id="tab-2"]/text()').extract()).strip()
		item['description_ru'] = html_description

		html_specification_tables = response.xpath('//div[@class="wdu_propsorter"]/table/tbody')
		specifications = []
		for table in html_specification_tables:
			tr = table.xpath('.//tr')
			for td in tr[1:]:
				spec = ':'.join([s.strip() for s in td.xpath('./td/span/text()').extract()])
				if 'Артикул' in spec:
					sku = spec.split(':')[-1]
					item['sku'] = sku
					if 'jan' not in item.keys() and not 'mpn' in item.keys():
						name_sp = name.split(sku)
						item['jan'] = name_sp[0]
						item['mpn'] = f'{sku} {name_sp[-1]}'
				elif 'Модель' in spec:
					item['model'] = spec.split(':')[-1]
				specifications.append(f'Default:{spec}')
		specification_line = '|'.join(specifications)
		item['product_attribute'] = specification_line

		images = response.xpath('//img[@class="lazyScroll__img"]')
		if images:
			main_image = images[0]
			main_img_url = f"https://kuppersbusch-shop.ru{main_image.attrib['src']}"
			main_img_name = f"{self.img_dir}{main_img_url.split('/')[-1]}"

			if not os.path.exists(main_img_name):
				photo = requests.get(main_img_url)
				with open(main_img_name,'wb') as f:
					f.write(photo.content)
			item['image'] = main_img_name
			item['source_image'] = main_img_url
			if len(images) > 1:
				more_images = [i.attrib["src"] for i in images[1:]]
				more_image_urls = "|".join([f"https://kuppersbusch-shop.ru{i}" for i in more_images] )
				more_image_names = "|".join([f"{self.img_dir}{i.split('/')[-1]}" for i in more_images] )
				item['additional_images'] = more_image_names
				item['source_additional_images'] = more_image_urls
				for img_url in more_image_urls.split('|'):
					for img_name in more_image_names.split('|'):
						if not os.path.exists(img_name):
							photo = requests.get(img_url)
							with open(img_name,'wb') as f:
								f.write(photo.content)

		date_today = datetime.now()
		item['date_added'] = date_today.strftime('%d-%m-%y %H:%M:%S')
		item['date_modified'] = date_today
		
		yield item
