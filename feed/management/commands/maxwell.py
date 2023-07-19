from django.core.management.base import BaseCommand
from django.db.models import Q
from feed.models import Maxwell

import os
import environ
import pymysql
import requests
import json

from library import database, debug, common

FILEDIR = f"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/files"

BRAND = "Maxwell"

API_URL = 'https://distribution.pdfsystems.com'
API_KEY = {'x-api-key': '286d17936503cc7c82de30e4c4721a67'}


class Command(BaseCommand):
    help = f"Build {BRAND} Database"

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):

        if "test" in options['functions']:
            processor = Processor()
            processor.test()

        if "feed" in options['functions']:
            processor = Processor()
            products = processor.fetchFeed()
            processor.databaseManager.writeFeed(products=products)

        if "sync" in options['functions']:
            processor = Processor()
            processor.databaseManager.statusSync(fullSync=False)

        if "add" in options['functions']:
            processor = Processor()
            processor.databaseManager.createProducts(formatPrice=True)

        if "update" in options['functions']:
            processor = Processor()
            products = Maxwell.objects.all()
            processor.databaseManager.updateProducts(
                products=products, formatPrice=True)

        if "price" in options['functions']:
            processor = Processor()
            processor.databaseManager.updatePrices(formatPrice=True)

        if "tag" in options['functions']:
            processor = Processor()
            processor.databaseManager.updateTags(category=True)

        if "image" in options['functions']:
            processor = Processor()
            processor.databaseManager.downloadImages(missingOnly=True)


class Processor:
    def __init__(self):
        env = environ.Env()

        self.con = pymysql.connect(host=env('MYSQL_HOST'), user=env('MYSQL_USER'), passwd=env(
            'MYSQL_PASSWORD'), db=env('MYSQL_DATABASE'), connect_timeout=5)
        self.databaseManager = database.DatabaseManager(
            con=self.con, brand=BRAND, Feed=Maxwell)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.con.close()

    def test(self):
        reqList = requests.get(
            f"{API_URL}/api/simple/item/list?count=1000&page={2}", headers=API_KEY)
        rows = json.loads(reqList.text)
        print(rows[0])

        sku = "V95106"
        reqList = requests.get(
            f"{API_URL}/api/simple/item/lookup?sku={sku}", headers=API_KEY)
        row = json.loads(reqList.text)
        print(row)

    def fetchFeed(self):
        debug.debug(BRAND, 0, f"Started fetching data from {BRAND}")

        # Get Product Feed
        products = []

        for page in range(1, 30):
            reqList = requests.get(
                f"{API_URL}/api/simple/item/list?count=1000&page={page}", headers=API_KEY)
            rows = json.loads(reqList.text)

            debug.debug(
                BRAND, 0, f"Fetched {len(rows)} products from page {page}")

            for row in rows:
                # Primary Keys
                mpn = row['sku']
                sku = f"MW {mpn}"
                pattern = row['style']
                color = row['color']

                # Categorization
                brand = BRAND

                collection = row['product_category']

                if "WALLPAPER" in collection:
                    type = "Wallpaper"
                else:
                    type = "Fabric"

                manufacturer = f"{brand} {type}"

                # Main Information
                description = common.formatText(row['tests'])
                width = common.formatFloat(row['width'])
                repeat = common.formatText(row['repeat'])

                # Additional Information
                content = common.formatText(row['content'])

                # Measurement
                if type == "Wallpaper":
                    uom = "Per Roll"
                else:
                    uom = "Per Yard"

                # Pricing
                cost = common.formatFloat(row['price'])

                # Tagging
                tags = collection
                colors = color

                # Image
                thumbnail = row['image_url']

                # Status
                if row['discontinued'] != None:
                    statusP = False
                    statusS = False
                else:
                    statusP = True
                    statusS = True

                # Exception
                if pattern == "VINTAGE (CONTRACT VINYL)":
                    minimum = 30
                    increment = ",".join([str(ii * minimum)
                                         for ii in range(1, 26)])
                else:
                    minimum = 1
                    increment = ""

                product = {
                    'mpn': mpn,
                    'sku': sku,
                    'pattern': pattern,
                    'color': color,

                    'brand': brand,
                    'type': type,
                    'manufacturer': manufacturer,
                    'collection': collection,

                    'description': description,
                    'width': width,
                    'repeat': repeat,

                    'content': content,

                    'cost': cost,

                    'uom': uom,
                    'minimum': minimum,
                    'increment': increment,

                    'tags': tags,
                    'colors': colors,

                    'thumbnail': thumbnail,

                    'statusP': statusP,
                    'statusS': statusS,
                }
                products.append(product)

        debug.debug(BRAND, 0, "Finished fetching data from the supplier")
        return products
