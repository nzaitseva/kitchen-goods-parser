import scrapy

class KitchengoodsItem(scrapy.Item):
    source_url = scrapy.Field()
    product_category = scrapy.Field()
    sku = scrapy.Field()
    jan = scrapy.Field()
    ean = scrapy.Field()
    price = scrapy.Field()
    model = scrapy.Field()
    image = scrapy.Field()
    source_image = scrapy.Field()
    additional_images = scrapy.Field()
    source_additional_images = scrapy.Field()
    manufacturer_id = scrapy.Field()
    manufacturer = scrapy.Field()
    status = scrapy.Field() #всегда 1 т.к. парсим только в наличии/на складе
    stock_status = scrapy.Field()  # В наличии, Предзаказ
    stock_status_id = scrapy.Field()
    date_added = scrapy.Field()
    date_modified = scrapy.Field()
    mpn = scrapy.Field()
    name_ru = scrapy.Field()
    description_ru = scrapy.Field()
    description_params = scrapy.Field()
    meta_title_ru = scrapy.Field()
    meta_description_ru = scrapy.Field()
    meta_keyword_ru = scrapy.Field()
    meta_h1_ru = scrapy.Field()
    product_attribute = scrapy.Field()

