import os.path
import re
import logging
from datetime import date

import requests
import scrapy
from scrapy.utils.project import get_project_settings

from ..items import KitchengoodsItem


class NeffShopSpider(scrapy.Spider):
    name = 'neff'
    custom_settings = {
        "MYSQL_TABLE": "neff",
    }
    def __init__(self, images='./images', *args, **kwargs):
        super(NeffShopSpider, self).__init__(*args, **kwargs)
        self.img_dir = images
        settings = get_project_settings()
        self.stock_statuses = settings.get('STOCK_STATUSES')
        self.manufacturer = "Neff"
        self.manufacturer_id = 16


    def parse(self, response, **kwargs):
        item = KitchengoodsItem()
        url = response.url
        item['source_url'] = url

        breadcrumbs = response.xpath('//ul[@class="breadcrumb"]/li/a/text()').extract()
        category = breadcrumbs[-2]
        subcategory = breadcrumbs[2]
        product_category = f'{category}|{category}>{subcategory}'
        item['product_category'] = product_category

        name = breadcrumbs[-1]
        try:
            sku = name.split("NEFF")[1].replace(' ','')
        except:
            sku = ""
        item['sku'] = sku
        jan = name.split("NEFF")[0].strip()
        item['jan']= jan

        price_div =  response.xpath('//p[@class="price"]/following-sibling::div').extract_first()
        price = re.search(r'(\d{1,6})+\D\.',price_div).groups()[0]
        price = f'{price}.0000'
        item['price'] = price

        data = response.xpath('//ul[@class="list-unstyled"]')
        model = data.xpath('./li[contains(text(),"Код")]/span/text()').extract_first()
        item['model'] = model
        available = data.xpath('./li[contains(text(),"Наличие")]/span/text()').extract_first()
        if available == '5':
            stock_status = 'В наличии'
            item['stock_status_id'] = '7'

        elif available.startswith('9'):
            stock_status = 'Предзаказ'
            item['stock_status_id'] = '8'
        else:
            self.logger.info(f'DROP ITEM: product not available {url}')
            return

        item['status'] = '1'
        item['stock_status'] = stock_status

        item['manufacturer'] = self.manufacturer
        item['manufacturer_id'] = self.manufacturer_id

        main_img_url = response.xpath('//div[@class="product-zoom-image"]/a/@href').extract_first()
        if main_img_url:
            main_img_name = f'{self.img_dir}{main_img_url.split("/")[-1]}'
            item['image'] = main_img_name
            item['source_image'] = main_img_url
            if not os.path.exists(main_img_name):
                res = requests.get(main_img_url)
                with open(main_img_name,'wb') as f:
                    f.write(res.content)

        additional_image_urls = response.xpath('//a[contains(@class,"sub-image")]/@href').extract()
        if additional_image_urls:
            additional_image_names = [i.split('/')[-1] for i in additional_image_urls]

            additional_images = "|".join([f"{self.img_dir}{img}" for img in additional_image_names])
            item['additional_images'] = additional_images
            source_additional_images = "|".join([f"{img_url}" for img_url in additional_image_urls])
            item['source_additional_images'] = source_additional_images
            for img_url in source_additional_images.split('|'):
                for img_name in additional_images.split('|'):
                    if not os.path.exists(img_name):
                        res = requests.get(img_url)
                        with open(img_name,'wb') as f:
                            f.write(res.content)

        description = response.xpath('//div[@id="tab-description"]/table')
        description_html = description.extract_first()
        item['description_ru'] = description_html
        description_params = dict()
        description_params_single = []
        for p in description.xpath('.//tr'):
            print(p.xpath('./td/text()').extract())
            try:
                key, value = p.xpath('./td/text()').extract()
                description_params[key] = value
            except:
                description_params_single.append(p.xpath('./td/text()').extract_first())
        description_line = '|'.join(f'{k}:{v}' for k,v in description_params.items())
        description_line = description_line + '|'.join(description_params_single)
        item['description_params'] = description_line

        try:
            specification = response.xpath('//div[@id="tab-specification"]/table')
        except:
            specification = description
        specification_html = specification.extract_first()
        specification_params = dict()
        for p in specification.xpath('.//tr'):
            print(p.xpath('./td/text()').extract())
            key,value = p.xpath('./td/text()').extract()
            if key.strip() and value.strip():
                specification_params[key] = value
        # Дисплей:цифровой|Конвекция:есть...'
        specification_line = '|'.join(f'Default:{k}:{v}' for k,v in specification_params.items())
        item['product_attribute'] = specification_line


        mpn = f'{self.manufacturer} {sku}'
        product_name = f'{jan} {mpn}'
        item['name_ru'] = product_name

        meta_title_ru = f'Купить {product_name}. Цена в СПб, фото, характеристики'
        meta_description_ru = f'В наличии в интернет-магазине {product_name} по выгодной цене в Санкт-Петербурге. Купить {product_name} у официального представителя с гарантией. Акции, бесплатная доставка по городу, рассрочка!'
        meta_keyword_ru = f'Купить, {product_name}, цена, фото, описание, заказать {product_name}, в интернет магазине, стоимость, доставка'
        meta_h1_ru = product_name
        item['meta_title_ru'] = meta_title_ru
        item['meta_description_ru'] = meta_description_ru
        item['meta_keyword_ru'] = meta_keyword_ru
        item['meta_h1_ru'] = meta_h1_ru

        date_today = date.today().isoformat()
        item['date_added'] = date_today
        item['date_modified'] = date_today
        yield item
