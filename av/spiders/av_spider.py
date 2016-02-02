import scrapy
from scrapy.spider import BaseSpider
from scrapy.selector import HtmlXPathSelector
from scrapy.http import request
from av.items import AvItem
import re
#from .celery_tasks import GetURL

# Mongo
from bson import Binary
from pymongo import MongoClient

import urllib2
import json
import re


class AvSpider(scrapy.spider.Spider):
    name = "azbuka_vkusa"
    allowed_domains = ["av.ru"]
    start_urls = [
        "http://av.ru/food/all/",      #  Start from the topmost category
    ]

    def put_to_mongo( self, picture_url, product_name = None, category = None, shop = None ):
        print "put_to_mongo  received "+ picture_url

        r = urllib2.urlopen( picture_url )
        pic_wrapper = Binary( r.read())

        obj_struct = {
                "shop"     : shop,
                "product_name" : product_name,
                "category" : category,          # Food type ( e.g. wine, cheese, etc )
                "image_url" : picture_url,      # Image URL
                "image" : pic_wrapper           # Blob of picture URL
        }
        self.db.product_crawl.insert( obj_struct )

    def parse(self, response):
	item = AvItem()
        hxs = HtmlXPathSelector(response)
	
        self.client = MongoClient()
        self.db     = self.client.product_crawl

	for cat_id in xrange(1,17):
#	        product_category  = hxs.select("//article[@id='main-block']/div/div/ul/li[%d]/a/span[2]" % cat_id)
	        product_category  = hxs.select("/html/body/article/div/div/ul/li[%d]/a" % cat_id)

		link_url = "http://av.ru/" + product_category.select("@href").extract()[0]
		print "Category URL %s" % link_url

		yield request.Request( link_url, callback=self.parse_category, meta={'item': item, 'category_url' : link_url, 'cat_idx' : 0})



    def parse_category(self, response):
        hxs = HtmlXPathSelector(response)
	basic_cat_url = response.meta['category_url']		# This is the basic URL of a current category. We will append next pages suffixes to this url

	print "Basic cat url is %s" % basic_cat_url

	# 0. Get total amount of pages in current category
	
	try:
		last_page_str = hxs.xpath('//*[@class="pagination_item last"]/a[@class="pagination_item_link"]/@href').extract()[0]
		last_page_id  = int(re.match( r'\?p=([0-9]+)', last_page_str ).group(1))

		print "Last page str= %s, %d" % (last_page_str, last_page_id )

		# 1. Get all pics in current page
		for sel in hxs.xpath('//*[@class="item_title"]'): #.extract():
	#	    print "Your sel is %s" % sel

	#	    xs   = HtmlXPathSelector(sel)
		    # you can access your response meta like this
		    item=response.meta['item']
	#	    print "Picture src %s" % sel.xpath('../img/@src').extract()[0]
	#	    print "Picture ialt %s" % sel.xpath('../img/@alt').extract()[0]

		    item['product_url'] = sel.xpath('../img/@src').extract()
		    item['product_name'] = sel.xpath('../img/@alt').extract()		# Product name. E.g. milk, wine, beer etc

		    full_pic_url = "http://av.ru/" + item['product_url'][0]
		    print "Mined picture URL: %s, alt = %s, cat_idx= %d" % ( full_pic_url, item['product_name'], response.meta['cat_idx'] )

		    self.put_to_mongo( full_pic_url, item['product_name'], basic_cat_url, "av")	# This sends a picture URL into a Celery task 'GetURL' asynchronously.
		   # return item

		# 2. Fetch next page ( if it exists )
		if ( response.meta['cat_idx'] == 0):	# this check is to avoid infinite recursion
			print "Seeding all pages in category %s once upon a time!" % basic_cat_url
			for page in xrange(0, last_page_id):
			   yield request.Request( basic_cat_url + "/?p=%d" % page, callback=self.parse_category, meta={'item': item, 'category_url' : basic_cat_url, 'cat_idx' : last_page_id})
	except:
		print "Err: cannot find last item at URL %s idx %d" % ( response.url, response.meta['cat_idx'] )



# TODO: add pagination support here
