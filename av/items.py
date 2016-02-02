# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy.item import Item, Field

class AvItem(Item):
    # define the fields for your item here like:
    # name = Field()
	product_name = Field()
	product_url  = Field()
	img_url      = Field()

