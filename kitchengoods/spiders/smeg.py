import os
from datetime import datetime

import requests
import scrapy

from ..items import KitchengoItem
from ..db import MySQLHandler

class SmegstoreSpider(scrapy.Spider):
    name = "smeg"
    custom_settings = {
        "MYSQL_TABLE": "smeg",
    }
    start_urls = ['https://smeg-store.ru/']

    def __init__(self,mode=None,images='./images',*args, **kwargs):
        super(SmegstoreSpider, self).__init__(*args, **kwargs)
        self.db = MySQLHandler()
        self.mode = mode
        self.img_dir = images
        self.manufacturer = "Smeg"
        self.manufacturer_id = 5

    def parse(self,response):
        category_links = response.xpath('//a[contains(@href,"category/")]/@href').extract()
        for link in category_links:
            if not link.startswith('https'):
                link = f'https://smeg-store.ru{link}'
            yield scrapy.Request(link, callback=self.parse_product_links)

    def parse_product_links(self,response):
        products = response.xpath('//ul[contains(@class,"s-products-list")]/li')
        for p in products:
            url = p.xpath('.//h5[@class="s-product-header"]/a/@href').extract_first()
            url = f'https://smeg-store.ru{url}'
            available = p.xpath('.//form[@class="add-to-cart"]')
            if available:
                yield scrapy.Request(url, callback=self.parse_product)
            else:
                self.logger.info(f'Skipping not available {url}')

        next_page = response.xpath('//ul[@class="s-paging-list"]/li[@class="selected"]/following-sibling::li/a/@href').extract_first()
        if next_page:
            next_page = f'https://smeg-store.ru{next_page}'
            yield scrapy.Request(next_page,callback=self.parse_product_links)

    def parse_product(self,response):
        item = KitchengoItem()
        url = response.url
        item['source_url'] = url

        breadcrumbs = response.xpath('//a[@class="s-breadcrumb-link"]/text()').extract()
        category = breadcrumbs[1]
        item['product_category'] = category

        name = response.xpath('//h1[@class="s-product-header"]/text()').extract_first()

        sku = name.split()[-1]
        item['sku'] = sku
        ean = response.xpath('//td[@class="Product__features-title"]/span[contains(text(),"EAN")]/parent::td/following-sibling::td/text()').extract_first()
        item['ean'] = ean

        short_desc = response.xpath('//p[@class="additional-short-description"]/text()').extract_first()
        if short_desc:
            jan = short_desc.split(',')[0]
            name_ru_tail = ','.join(short_desc.split(',')[1:])
        else:
            jan = ''
            name_ru_tail = ''

        item['jan'] = jan
        mpn = f'{sku} {name_ru_tail}'.replace('  ',' ')
        #Формат: {наименование} {бренд} {модель} {характеристика} {цвет}
        product_name = f'{jan} {self.manufacturer} {mpn}'
        item['name_ru'] = product_name
        meta_title_ru = f'Купить {product_name}. Цена в СПб, фото, характеристики'
        meta_description_ru = f'В наличии в интернет-магазине {product_name} по выгодной цене в Санкт-Петербурге. Купить {product_name} у официального представителя с гарантией. Акции, бесплатная доставка по городу, рассрочка!'
        meta_keyword_ru = f'Купить, {product_name}, цена, фото, описание, заказать {product_name}, в интернет магазине, стоимость, доставка'
        meta_h1_ru = product_name
        item['meta_title_ru'] = meta_title_ru
        item['meta_description_ru'] = meta_description_ru
        item['meta_keyword_ru'] = meta_keyword_ru
        item['meta_h1_ru'] = meta_h1_ru

        price = response.xpath('//span[contains(@class,"compare-at-price")]/@data-compare-price').extract_first()
        if price == '0':
            price = response.xpath('//span[@class="price nowrap"]/@data-price').extract_first()
            if not price:
                self.logger.info(f"NO PRICE {response.url}")
                return
        price = f'{price}.0000'
        item['price'] = price

        available = response.xpath('//div[@class="submit-wrapper"]/input[@value="Купить"]')
        if available:
            item['stock_status'] = 'В наличии'
            item['stock_status_id'] = '7'
            item['status'] = '1'
        else:
            preorder = response.xpath('//div[@class="submit-wrapper"]/input[@value="Предзаказ"]')
            if preorder:
                item['status'] = '1'
                item['stock_status'] = 'Предзаказ'
                item['stock_status_id'] = '8'
            else:
                self.logger.info(f'DROP ITEM: product not available {url}')
                return

        main_img_url = response.xpath('//a[@id="s-photo-main"]/@href').extract_first()
        if main_img_url:
            main_img_name = f'{self.img_dir}{main_img_url.split("/")[-1]}'
            item['image'] = main_img_name
            item['source_image'] = main_img_url
            if not os.path.exists(main_img_name):
                res = requests.get("https://smeg-store.ru"+main_img_url)
                with open(main_img_name, 'wb') as f:
                    f.write(res.content)
        else:
            item['image'] = ''
            item['source_image'] = ''
        try:
            additional_image_urls = response.xpath('//li[contains(@class,"s-photo-thumb")]/a/@href').extract().remove(main_img_url)
            additional_image_names = [i.split('/')[-1] for i in additional_image_urls]
            item['additional_images'] = "|".join([f"{self.img_dir}{img}" for img in additional_image_names])
            item['source_additional_images'] = "|".join([f"{img_url}" for img_url in additional_image_urls])

            for img in additional_image_urls:
                img_name = f'{self.img_dir}{img.split("/")[-1]}'
                if not os.path.exists(img_name):
                    res = requests.get("https://smeg-store.ru"+img)
                    with open(img_name, 'wb') as f:
                        f.write(res.content)
        except:
            item['additional_images'] = ''

        description = response.xpath('//table[@class="Product__features"]').extract_first()
        if not description:
            description = ""
        description_html = response.xpath('//p[@class="additional-short-description"]').extract_first()
        if not description_html:
            description_html = ""
        item['description_ru'] = description+description_html

        #Xарактеристики
        specification = response.xpath('//tr[@class="s-feature-column"]')
        specification_params = dict()
        for spec in specification:
            key = spec.xpath('./td[@class="name"]//span/text()').extract_first()
            value = spec.xpath('./td[@class="value"]/text()').extract_first()
            if key.strip() and value.strip():
                specification_params[key] = value
        #Формат:'Дисплей:цифровой|Конвекция:есть|Очистка духовки:традиционные...'
        specification_line = '|'.join(f'{k}:{v}' for k,v in specification_params.items())
        item['product_attribute'] = specification_line

        date_today = datetime.now()
        item['date_added'] = date_today.strftime('%d-%m-%y %H:%M:%S')
        item['date_modified'] = date_today

        item['manufacturer'] = self.manufacturer
        item['manufacturer_id'] = self.manufacturer_id
        yield item
