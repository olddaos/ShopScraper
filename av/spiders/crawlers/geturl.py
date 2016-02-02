from celery import Celery
from celery import Task

# Mongo
from bson import Binary
from pymongo import MongoClient

import urllib2


# As the name suggests, it only gets URL, stores it at the disk and updates Mongo to fix that fact
class GetURL(Task):
    def __init__( self ):
        self.queue      = 'urls_queue'
        self.client = MongoClient()
        self.db     = self.client.test_crawl

    def run(self,  picture_url, product_name = None, category = None, shop = None ):
        print "GetURL received %s, product name %s" % ( picture_url, product_name )

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
