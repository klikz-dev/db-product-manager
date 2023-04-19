from django.core.management.base import BaseCommand
from feed.models import Schumacher

import os
import environ
import pymysql
import xlrd

from library import database, debug

FILEDIR = "{}/files/".format(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))

BRAND = "Schumacher"


class Command(BaseCommand):
    help = "Build {} Database".format(BRAND)

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):
        processor = Processor()

        if "feed" in options['functions']:
            products = processor.fetchFeed()
            processor.databaseManager.writeFeed(products=products)

        if "sync" in options['functions']:
            processor.databaseManager.statusSync(fullSync=False)

        if "add" in options['functions']:
            processor.databaseManager.createProducts(formatPrice=True)

        if "update" in options['functions']:
            products = Schumacher.objects.all()
            processor.databaseManager.updateProducts(
                products=products, formatPrice=True)

        if "price" in options['functions']:
            processor.databaseManager.updatePrices(formatPrice=True)

        if "tag" in options['functions']:
            processor.databaseManager.updateTags(category=True)

        if "image" in options['functions']:
            processor.databaseManager.downloadImages(missingOnly=True)


class Processor:
    def __init__(self):
        env = environ.Env()
        self.con = pymysql.connect(host=env('MYSQL_HOST'), user=env('MYSQL_USER'), passwd=env(
            'MYSQL_PASSWORD'), db=env('MYSQL_DATABASE'), connect_timeout=5)

        self.databaseManager = database.DatabaseManager(self.con, BRAND)

    def __del__(self):
        self.con.close()

    def fetchFeed(self):
        debug.debug(BRAND, 0, "Started fetching data from {}".format(BRAND))

        # Get Product Feed
        products = []

        wb = xlrd.open_workbook(FILEDIR + 'stark-studio-master.xlsx')
        for index in [0, 1, 2]:
            sh = wb.sheet_by_index(index)
            for i in range(2, sh.nrows):
                try:
                    # Primary Keys

                    # Categorization

                    # Main Information

                    # Additional Information

                    # Measurement

                    # Pricing

                    # Tagging

                    # Custom Stock and Price data

                    pass

                except Exception as e:
                    debug.debug(BRAND, 1, str(e))
                    continue

                # product = {
                #     'mpn': mpn,
                #     'sku': sku,
                #     'upc': upc,
                #     'pattern': pattern,
                #     'color': color,

                #     'brand': brand,
                #     'type': type,
                #     'manufacturer': manufacturer,
                #     'collection': collection,

                #     'description': description,
                #     'width': width,
                #     'length': length,
                #     'weight': weight,

                #     'material': material,
                #     'country': country,

                #     'uom': uom,

                #     'tags': tags,
                #     'colors': colors,

                #     'cost': cost,
                #     'map': map,

                #     'statusP': statusP,
                #     'statusS': statusS,

                #     'stockP': stockP,
                #     'stockNote': stockNote,
                #     'whiteShip': whiteShip
                # }
                # products.append(product)

        debug.debug(BRAND, 0, "Finished fetching data from the supplier")
        return products
